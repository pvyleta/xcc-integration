"""
XCC Heat Pump Controller Client Library

Reusable authentication and data fetching for CLI, pyscript, and HA integration.
"""

import hashlib
import aiohttp
import json
import os
from typing import Dict, List, Optional, Tuple
from yarl import URL
from lxml import etree


class XCCClient:
    """Client for XCC heat pump controller communication."""
    
    def __init__(self, ip: str, username: str = "xcc",
                 password: str = "xcc", cookie_file: Optional[str] = None):
        self.ip = ip
        self.username = username
        self.password = password
        self.cookie_file = cookie_file
        self.session = None
        
    async def __aenter__(self):
        await self.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
        
    async def connect(self):
        """Establish connection with session reuse."""
        cookie_jar = aiohttp.CookieJar(unsafe=True)
        
        # Try to reuse existing session
        if self.cookie_file and os.path.exists(self.cookie_file):
            try:
                with open(self.cookie_file, "r") as f:
                    saved = json.load(f)
                    session_cookie = saved.get("SoftPLC")
                    if session_cookie:
                        cookie_jar.update_cookies(
                            {"SoftPLC": session_cookie}, 
                            response_url=URL(f"http://{self.ip}/")
                        )
            except Exception:
                pass  # Continue with fresh login
                
        self.session = aiohttp.ClientSession(cookie_jar=cookie_jar)
        
        # Test if existing session works, otherwise authenticate
        if not await self._test_session():
            await self._authenticate()
            
    async def _test_session(self) -> bool:
        """Test if current session is valid."""
        try:
            async with self.session.get(f"http://{self.ip}/stavjed.xml") as resp:
                return resp.status == 200
        except Exception:
            return False
            
    async def _authenticate(self):
        """Perform authentication and save session."""
        # Get login page for session ID
        async with self.session.get(f"http://{self.ip}/LOGIN.XML") as resp:
            if resp.status != 200:
                raise Exception("Failed to get LOGIN.XML")
                
        # Extract session ID from cookie
        session_id = None
        for cookie in self.session.cookie_jar:
            if cookie.key == "SoftPLC":
                session_id = cookie.value
                break
                
        if not session_id:
            raise Exception("No SoftPLC cookie found")
            
        # Login with hashed password
        passhash = hashlib.sha1(f"{session_id}{self.password}".encode()).hexdigest()
        login_data = {"USER": self.username, "PASS": passhash}
        
        async with self.session.post(f"http://{self.ip}/RPC/WEBSES/create.asp", 
                                   data=login_data) as resp:
            if resp.status != 200:
                raise Exception("Authentication failed")
                
        # Save session cookie
        if self.cookie_file:
            self._save_session()
            
    def _save_session(self):
        """Save session cookie to file."""
        try:
            os.makedirs(os.path.dirname(self.cookie_file), exist_ok=True)
            session_data = {}
            for cookie in self.session.cookie_jar:
                if cookie.key == "SoftPLC":
                    session_data["SoftPLC"] = cookie.value
                    break
                    
            with open(self.cookie_file, "w") as f:
                json.dump(session_data, f)
        except Exception:
            pass  # Non-critical
            
    async def fetch_page(self, page: str) -> str:
        """Fetch XML page content."""
        async with self.session.get(f"http://{self.ip}/{page}") as resp:
            if resp.status != 200:
                raise Exception(f"Failed to fetch {page}: {resp.status}")
            return await resp.text()
            
    async def fetch_pages(self, pages: List[str]) -> Dict[str, str]:
        """Fetch multiple pages."""
        results = {}
        for page in pages:
            try:
                results[page] = await self.fetch_page(page)
            except Exception as e:
                results[page] = f"Error: {e}"
        return results
        
    async def close(self):
        """Close the session."""
        if self.session:
            await self.session.close()


def parse_xml_entities(xml_content: str, page_name: str,
                      entity_prefix: str = "xcc") -> List[Dict]:
    """Parse XML content into entity data."""
    entities = []

    try:
        # Handle encoding properly - convert to bytes with proper encoding
        if isinstance(xml_content, str):
            # First try to encode as windows-1250 if the XML declares it
            if 'windows-1250' in xml_content:
                try:
                    xml_bytes = xml_content.encode('windows-1250')
                except UnicodeEncodeError:
                    # Fall back to UTF-8 if windows-1250 fails
                    xml_bytes = xml_content.encode('utf-8')
            else:
                xml_bytes = xml_content.encode('utf-8')
        else:
            xml_bytes = xml_content

        root = etree.fromstring(xml_bytes)
        # Successfully parsed XML
    except Exception as e:
        # Try alternative parsing with encoding fix
        try:
            # Remove encoding declaration and parse as UTF-8
            xml_clean = xml_content.replace('encoding="windows-1250"', 'encoding="utf-8"')
            root = etree.fromstring(xml_clean.encode('utf-8'))
        except Exception:
            return entities
        
    # Extract all INPUT elements with P attribute and VALUE attribute
    # Extract all INPUT elements with P attribute and VALUE attribute
    input_elements = root.xpath(".//INPUT[@P and @VALUE]")

    for elem in input_elements:
        prop = elem.get("P")
        if not prop:
            continue

        value = elem.get("VALUE", "")
        if not value:
            continue
            
        entity_id = f"{entity_prefix}_{prop.lower().replace('-', '_')}"
        
        # Determine entity type and attributes
        entity_type = "sensor"
        attributes = {
            "source_page": page_name,
            "field_name": prop,
            "friendly_name": prop.replace("-", " ").title()
        }
        
        # Add type-specific attributes
        if elem.get("UNIT"):
            attributes["unit_of_measurement"] = elem.get("UNIT")
            attributes["device_class"] = _get_device_class(elem.get("UNIT"))
            
        if elem.get("MIN") and elem.get("MAX"):
            try:
                attributes["min_value"] = float(elem.get("MIN"))
                attributes["max_value"] = float(elem.get("MAX"))
            except ValueError:
                pass
                
        # Handle boolean values
        if value in ("0", "1") and not elem.get("UNIT"):
            entity_type = "binary_sensor"
            value = value == "1"
            
        # Determine data type
        if isinstance(value, bool):
            data_type = "boolean"
        elif isinstance(value, str) and value.replace(".", "").replace("-", "").isdigit():
            data_type = "numeric"
        else:
            data_type = "string"

        # Create entity structure that matches coordinator expectations
        entity = {
            "prop": prop,
            "value": value,
            "attributes": {
                "page": page_name,
                "friendly_name": prop.replace("-", " ").title(),
                "value": value,
                "unit": elem.get("UNIT", ""),
                "data_type": data_type,
                "is_settable": False,  # Data pages are read-only
            }
        }

        # Add unit and device class if available
        if elem.get("UNIT"):
            entity["attributes"]["unit_of_measurement"] = elem.get("UNIT")
            entity["attributes"]["device_class"] = _get_device_class(elem.get("UNIT"))

        # Add min/max if available
        if elem.get("MIN") and elem.get("MAX"):
            try:
                entity["attributes"]["min_value"] = float(elem.get("MIN"))
                entity["attributes"]["max_value"] = float(elem.get("MAX"))
            except ValueError:
                pass

        entities.append(entity)
        
    return entities


def _get_device_class(unit: str) -> Optional[str]:
    """Map units to device classes."""
    unit_map = {
        "°C": "temperature",
        "kW": "power",
        "kWh": "energy",
        "V": "voltage",
        "A": "current",
        "%": "battery" if "batt" in unit.lower() else None,
        "bar": "pressure"
    }
    return unit_map.get(unit)


# Standard page sets for different use cases
STANDARD_PAGES = [
    "stavjed.xml", "STAVJED1.XML",  # Status
    "okruh.xml", "OKRUH10.XML",     # Heating circuits  
    "tuv1.xml", "TUV11.XML",        # Hot water
    "biv.xml", "BIV1.XML",          # Bivalent heating
    "fve.xml", "FVE4.XML",          # Photovoltaics
    "spot.xml", "SPOT1.XML",        # Spot pricing
]

MINIMAL_PAGES = [
    "stavjed.xml", "okruh.xml", "tuv1.xml", "fve.xml"
]
