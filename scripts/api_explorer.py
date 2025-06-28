#!/usr/bin/env python3
"""
XCC API Explorer - Reverse engineer the heat pump controller API
This script discovers all available pages and analyzes which fields can be set.
"""

import asyncio
import aiohttp
import os
import json
import re
import logging
from datetime import datetime
from typing import Dict, List, Set, Any
from lxml import etree
from yarl import URL

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('xcc-explorer')

class XCCAPIExplorer:
    def __init__(self, ip: str = "192.168.0.50", username: str = "xcc", password: str = "xcc"):
        self.ip = ip
        self.username = username
        self.password = password
        self.session = None
        self.discovered_pages = set()
        self.settable_fields = {}
        self.field_metadata = {}
        
    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()
        
    async def connect(self):
        """Establish connection and authenticate"""
        cookie_jar = aiohttp.CookieJar(unsafe=True)
        self.session = aiohttp.ClientSession(cookie_jar=cookie_jar)
        
        # Try to authenticate
        await self._authenticate()
        logger.info("Connected and authenticated successfully")
        
    async def disconnect(self):
        """Close the session"""
        if self.session:
            await self.session.close()
            logger.info("Disconnected")
            
    async def _authenticate(self):
        """Perform authentication"""
        import hashlib
        
        # Get login page to establish session
        login_xml_url = f"http://{self.ip}/LOGIN.XML"
        async with self.session.get(login_xml_url) as resp:
            if resp.status != 200:
                raise Exception("Failed to get LOGIN.XML")
                
        # Get session ID from cookie
        session_id = next((c.value for c in self.session.cookie_jar if c.key == "SoftPLC"), None)
        if not session_id:
            raise Exception("No SoftPLC cookie found")
            
        # Create password hash
        passhash = hashlib.sha1(f"{session_id}{self.password}".encode()).hexdigest()
        
        # Perform login
        login_url = f"http://{self.ip}/RPC/WEBSES/create.asp"
        payload = {"USER": self.username, "PASS": passhash}
        
        async with self.session.post(login_url, data=payload) as resp:
            if resp.status != 200:
                raise Exception("Login failed")
                
        logger.info("Authentication successful")
        
    async def discover_pages(self) -> Set[str]:
        """Discover all available XML pages by various methods"""
        logger.info("Starting page discovery...")

        # Start with known working pages from the original script
        known_pages = [
            "stavjed.xml", "STAVJED1.XML",
            "okruh.xml", "OKRUH10.XML",
            "tuv1.xml", "TUV11.XML",
            "biv.xml", "BIV1.XML",
            "fve.xml", "FVE4.XML",
            "spot.xml", "SPOT1.XML",
            "INDEX.XML", "LOGIN.XML", "MAIN.XML"
        ]

        # Test known pages first
        logger.info("Testing known pages...")
        for page_name in known_pages:
            if await self._test_page_exists(page_name):
                self.discovered_pages.add(page_name)

        # Additional patterns to try (more focused)
        base_patterns = [
            "CONFIG", "SETTINGS", "STATUS", "SYSTEM", "NETWORK",
            "TIME", "USERS", "BACKUP", "ALARM", "LOG"
        ]

        logger.info("Testing additional patterns...")
        # Test each pattern with limited variants
        for pattern in base_patterns:
            for ext in [".XML", ".xml"]:
                page_name = f"{pattern}{ext}"
                if await self._test_page_exists(page_name):
                    self.discovered_pages.add(page_name)

            # Try a few numbered variants for each base
            for i in range(5):  # Reduced from 20 to 5
                for ext in [".XML", ".xml"]:
                    page_name = f"{pattern}{i}{ext}"
                    if await self._test_page_exists(page_name):
                        self.discovered_pages.add(page_name)

        logger.info(f"Discovered {len(self.discovered_pages)} pages")
        return self.discovered_pages
        
    async def _test_page_exists(self, page_name: str) -> bool:
        """Test if a page exists"""
        try:
            url = f"http://{self.ip}/{page_name}"
            # Use shorter timeout for faster discovery
            timeout = aiohttp.ClientTimeout(total=5)
            async with self.session.get(url, timeout=timeout) as resp:
                if resp.status == 200:
                    content = await resp.text()
                    # Check if it's actually XML and not an error page
                    if content.strip().startswith('<?xml') or content.strip().startswith('<'):
                        logger.info(f"✓ Found page: {page_name}")
                        return True
                logger.debug(f"✗ Page {page_name}: HTTP {resp.status}")
        except asyncio.TimeoutError:
            logger.debug(f"✗ Page {page_name}: Timeout")
        except Exception as e:
            logger.debug(f"✗ Page {page_name}: {e}")
        return False
        
    async def analyze_pages(self) -> Dict[str, Any]:
        """Analyze all discovered pages for settable fields"""
        logger.info("Analyzing pages for settable fields...")
        
        analysis_results = {
            "pages": {},
            "settable_fields": {},
            "field_types": {},
            "form_actions": {},
            "rpc_endpoints": set()
        }
        
        for page_name in self.discovered_pages:
            logger.info(f"Analyzing {page_name}...")
            page_analysis = await self._analyze_single_page(page_name)
            analysis_results["pages"][page_name] = page_analysis
            
            # Merge settable fields
            if page_analysis.get("settable_fields"):
                analysis_results["settable_fields"][page_name] = page_analysis["settable_fields"]
                
            # Merge field types
            if page_analysis.get("field_types"):
                analysis_results["field_types"].update(page_analysis["field_types"])
                
            # Merge form actions
            if page_analysis.get("form_actions"):
                analysis_results["form_actions"][page_name] = page_analysis["form_actions"]
                
            # Collect RPC endpoints
            if page_analysis.get("rpc_endpoints"):
                analysis_results["rpc_endpoints"].update(page_analysis["rpc_endpoints"])
                
        # Convert set to list for JSON serialization
        analysis_results["rpc_endpoints"] = list(analysis_results["rpc_endpoints"])
        
        return analysis_results
        
    async def _analyze_single_page(self, page_name: str) -> Dict[str, Any]:
        """Analyze a single page for settable fields"""
        try:
            url = f"http://{self.ip}/{page_name}"
            async with self.session.get(url) as resp:
                if resp.status != 200:
                    return {"error": f"HTTP {resp.status}"}
                    
                content = await resp.text()
                
            # Parse XML
            try:
                root = etree.fromstring(content.encode())
            except Exception as e:
                return {"error": f"XML parse error: {e}"}
                
            analysis = {
                "settable_fields": {},
                "field_types": {},
                "form_actions": [],
                "rpc_endpoints": set(),
                "input_elements": [],
                "button_elements": [],
                "metadata": {}
            }
            
            # Find input elements that might be settable
            settable_elements = [
                "number", "choice", "switch", "button", "time",
                "slider", "text", "password", "select", "checkbox", "input"
            ]

            for element_type in settable_elements:
                for elem in root.findall(f".//{element_type}"):
                    field_info = self._extract_field_info(elem, element_type)
                    if field_info and field_info.get("prop"):
                        prop = field_info["prop"]
                        # Skip readonly fields
                        if field_info.get("attributes", {}).get("config") != "readonly":
                            analysis["settable_fields"][prop] = field_info
                            analysis["field_types"][prop] = element_type
                            
            # Look for form actions and RPC endpoints
            for elem in root.iter():
                # Check for action attributes
                if "action" in elem.attrib:
                    action = elem.attrib["action"]
                    analysis["form_actions"].append(action)
                    if "RPC" in action.upper():
                        analysis["rpc_endpoints"].add(action)
                        
                # Check for onclick or similar attributes that might indicate RPC calls
                for attr in ["onclick", "onchange", "onsubmit"]:
                    if attr in elem.attrib:
                        value = elem.attrib[attr]
                        if "RPC" in value.upper():
                            # Extract RPC endpoint from JavaScript
                            rpc_match = re.search(r'["\']([^"\']*RPC[^"\']*)["\']', value)
                            if rpc_match:
                                analysis["rpc_endpoints"].add(rpc_match.group(1))
                                
            # Convert set to list for JSON serialization
            analysis["rpc_endpoints"] = list(analysis["rpc_endpoints"])
            
            return analysis
            
        except Exception as e:
            return {"error": str(e)}
            
    def _extract_field_info(self, elem, element_type: str) -> Dict[str, Any]:
        """Extract field information from an XML element"""
        info = {
            "element_type": element_type,
            "attributes": dict(elem.attrib)
        }

        # Extract common attributes
        for attr in ["prop", "name", "id", "value", "min", "max", "step", "unit", "text", "text_en", "digits"]:
            if attr in elem.attrib:
                info[attr] = elem.attrib[attr]

        # Extract text content
        if elem.text and elem.text.strip():
            info["text_content"] = elem.text.strip()

        # Get friendly name from parent row if available
        parent_row = elem.getparent()
        while parent_row is not None and parent_row.tag != "row":
            parent_row = parent_row.getparent()
        if parent_row is not None:
            info["friendly_name"] = parent_row.attrib.get("text", "")
            info["friendly_name_en"] = parent_row.attrib.get("text_en", "")

        # Determine data type and constraints
        if element_type == "number":
            info["data_type"] = "numeric"
            if "min" in elem.attrib:
                info["min_value"] = float(elem.attrib["min"])
            if "max" in elem.attrib:
                info["max_value"] = float(elem.attrib["max"])
            if "digits" in elem.attrib:
                info["decimal_places"] = int(elem.attrib["digits"])
        elif element_type == "switch":
            info["data_type"] = "boolean"
        elif element_type == "choice":
            info["data_type"] = "enum"
            # Extract options from choice element
            options = []
            for option in elem.findall("option"):
                if "value" in option.attrib:
                    options.append({
                        "value": option.attrib["value"],
                        "text": option.attrib.get("text", option.attrib["value"]),
                        "text_en": option.attrib.get("text_en", option.attrib.get("text", option.attrib["value"]))
                    })
            if options:
                info["options"] = options
        elif element_type == "button":
            info["data_type"] = "action"
        elif element_type == "time":
            info["data_type"] = "time"
        else:
            info["data_type"] = "string"

        return info
        
    async def save_analysis(self, analysis: Dict[str, Any], filename: str = "xcc_api_analysis.json"):
        """Save analysis results to JSON file"""
        # Add metadata
        analysis["metadata"] = {
            "timestamp": datetime.now().isoformat(),
            "ip": self.ip,
            "total_pages": len(self.discovered_pages),
            "total_settable_fields": sum(len(fields) for fields in analysis["settable_fields"].values())
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Analysis saved to {filename}")
        
    def generate_summary_report(self, analysis: Dict[str, Any]) -> str:
        """Generate a human-readable summary report"""
        report = []
        report.append("XCC API Analysis Summary")
        report.append("=" * 50)
        report.append(f"Analysis Date: {analysis['metadata']['timestamp']}")
        report.append(f"Controller IP: {analysis['metadata']['ip']}")
        report.append(f"Total Pages Discovered: {analysis['metadata']['total_pages']}")
        report.append(f"Total Settable Fields: {analysis['metadata']['total_settable_fields']}")
        report.append("")
        
        # Pages summary
        report.append("Discovered Pages:")
        report.append("-" * 20)
        for page in sorted(analysis["pages"].keys()):
            settable_count = len(analysis["pages"][page].get("settable_fields", {}))
            report.append(f"  {page}: {settable_count} settable fields")
        report.append("")
        
        # Field types summary
        field_types = {}
        for fields in analysis["settable_fields"].values():
            for field, info in fields.items():
                field_type = info.get("element_type", "unknown")
                if field_type not in field_types:
                    field_types[field_type] = 0
                field_types[field_type] += 1
                
        report.append("Field Types Distribution:")
        report.append("-" * 25)
        for field_type, count in sorted(field_types.items()):
            report.append(f"  {field_type}: {count}")
        report.append("")
        
        # RPC endpoints
        if analysis["rpc_endpoints"]:
            report.append("Discovered RPC Endpoints:")
            report.append("-" * 25)
            for endpoint in sorted(analysis["rpc_endpoints"]):
                report.append(f"  {endpoint}")
        
        return "\n".join(report)

async def main():
    """Main function to run the API exploration"""
    print("XCC API Explorer")
    print("================")
    print("This tool will discover and analyze the heat pump controller API")
    print("to identify settable fields and endpoints.")
    print()
    
    async with XCCAPIExplorer() as explorer:
        # Discover all pages
        await explorer.discover_pages()
        
        # Analyze pages for settable fields
        analysis = await explorer.analyze_pages()
        
        # Save detailed analysis
        await explorer.save_analysis(analysis)
        
        # Generate and display summary
        summary = explorer.generate_summary_report(analysis)
        print(summary)
        
        # Save summary to file
        with open("xcc_api_summary.txt", "w", encoding="utf-8") as f:
            f.write(summary)
            
        print(f"\nDetailed analysis saved to: xcc_api_analysis.json")
        print(f"Summary report saved to: xcc_api_summary.txt")

if __name__ == "__main__":
    asyncio.run(main())
