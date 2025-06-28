#!/usr/bin/env python3
"""
Analyze only the known working pages for settable fields
"""

import asyncio
import aiohttp
import hashlib
import json
import os
from datetime import datetime
from lxml import etree

async def authenticate_session(ip, username, password):
    """Create authenticated session"""
    cookie_jar = aiohttp.CookieJar(unsafe=True)
    session = aiohttp.ClientSession(cookie_jar=cookie_jar)
    
    # Get login page
    login_xml_url = f"http://{ip}/LOGIN.XML"
    async with session.get(login_xml_url) as resp:
        if resp.status != 200:
            raise Exception("Failed to get LOGIN.XML")
            
    # Get session ID
    session_id = next((c.value for c in session.cookie_jar if c.key == "SoftPLC"), None)
    if not session_id:
        raise Exception("No SoftPLC cookie found")
        
    # Login
    passhash = hashlib.sha1(f"{session_id}{password}".encode()).hexdigest()
    login_url = f"http://{ip}/RPC/WEBSES/create.asp"
    payload = {"USER": username, "PASS": passhash}
    
    async with session.post(login_url, data=payload) as resp:
        if resp.status != 200:
            raise Exception("Login failed")
            
    return session

def extract_field_info(elem, element_type: str):
    """Extract field information from an XML element"""
    info = {
        "element_type": element_type,
        "attributes": dict(elem.attrib)
    }
    
    # Extract common attributes
    for attr in ["prop", "name", "id", "value", "min", "max", "step", "unit", "text", "text_en", "digits"]:
        if attr in elem.attrib:
            info[attr] = elem.attrib[attr]
            
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

async def analyze_page(session, ip, page_name):
    """Analyze a single page for settable fields"""
    try:
        url = f"http://{ip}/{page_name}"
        async with session.get(url) as resp:
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
            "rpc_endpoints": [],
            "page_info": {
                "name": root.attrib.get("name", ""),
                "help": root.attrib.get("help", ""),
                "version": root.attrib.get("VERSION", "")
            }
        }
        
        # Find settable elements
        settable_elements = ["number", "choice", "switch", "button", "time"]
        
        for element_type in settable_elements:
            for elem in root.findall(f".//{element_type}"):
                field_info = extract_field_info(elem, element_type)
                if field_info and field_info.get("prop"):
                    prop = field_info["prop"]
                    # Skip readonly fields
                    if field_info.get("attributes", {}).get("config") != "readonly":
                        analysis["settable_fields"][prop] = field_info
                        analysis["field_types"][prop] = element_type
                        
        return analysis
        
    except Exception as e:
        return {"error": str(e)}

async def main():
    ip = "192.168.0.50"
    username = "xcc"
    password = "xcc"
    
    print("Analyzing known pages for settable fields...")
    
    session = await authenticate_session(ip, username, password)
    
    try:
        # Known pages that contain configuration
        pages_to_analyze = [
            "stavjed.xml", "okruh.xml", "tuv1.xml", "biv.xml", "fve.xml", "spot.xml"
        ]
        
        all_analysis = {}
        total_fields = 0
        
        for page in pages_to_analyze:
            print(f"Analyzing {page}...")
            analysis = await analyze_page(session, ip, page)
            all_analysis[page] = analysis
            
            if "settable_fields" in analysis:
                field_count = len(analysis["settable_fields"])
                total_fields += field_count
                print(f"  Found {field_count} settable fields")
                
                # Show some examples
                for i, (prop, info) in enumerate(analysis["settable_fields"].items()):
                    if i < 3:  # Show first 3 fields
                        print(f"    {prop}: {info['data_type']} - {info.get('friendly_name', 'No name')}")
                    elif i == 3:
                        print(f"    ... and {field_count - 3} more")
                        break
            else:
                print(f"  Error: {analysis.get('error', 'Unknown error')}")
                
        # Save detailed analysis
        analysis_data = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "ip": ip,
                "total_pages": len(pages_to_analyze),
                "total_settable_fields": total_fields
            },
            "pages": all_analysis
        }
        
        with open("field_database.json", "w", encoding="utf-8") as f:
            json.dump(analysis_data, f, indent=2, ensure_ascii=False)

        print(f"\nTotal settable fields found: {total_fields}")
        print("Field database saved to: field_database.json")
        
    finally:
        await session.close()

if __name__ == "__main__":
    asyncio.run(main())
