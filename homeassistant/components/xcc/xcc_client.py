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
        # Try different encodings for XCC XML files
        encodings = ['utf-8', 'windows-1250', 'iso-8859-1']
        root = None

        for encoding in encodings:
            try:
                root = etree.fromstring(xml_content.encode(encoding))
                break
            except (UnicodeEncodeError, UnicodeDecodeError):
                continue
            except Exception:
                continue

        if root is None:
            # If encoding fails, try parsing as-is (already a string)
            try:
                root = etree.fromstring(xml_content)
            except Exception:
                return entities
    except Exception:
        return entities

    # Try different XCC XML formats

    # Format 1: XCC Values format (STAVJED1.XML style) - <INPUT P="name" VALUE="value"/>
    input_elements = root.xpath(".//INPUT[@P and @VALUE]")
    if input_elements:
        for elem in input_elements:
            prop = elem.get("P")
            value = elem.get("VALUE")

            if not prop or not value:
                continue

            entity_id = f"{entity_prefix}_{prop.lower().replace('-', '_')}"

            # Determine entity type and attributes
            entity_type = "sensor"
            attributes = {
                "source_page": page_name,
                "field_name": prop,
                "friendly_name": prop.replace("-", " ").replace("_", " ").title()
            }

            # Parse NAME attribute for more info
            name_attr = elem.get("NAME", "")
            if "_REAL_" in name_attr:
                attributes["device_class"] = "temperature" if "T" in prop.upper() else None
                attributes["unit_of_measurement"] = "°C" if "T" in prop.upper() else None
            elif "_BOOL_" in name_attr:
                entity_type = "binary_sensor"
                value = "1" if value == "1" else "0"
            elif "_USINT_" in name_attr or "_UINT_" in name_attr:
                try:
                    value = str(int(float(value)))
                except:
                    pass

            entities.append({
                "entity_id": entity_id,
                "type": entity_type,
                "value": value,
                **attributes
            })

        return entities

    # Format 2: XCC Structure format with values (prop attributes with text)
    for elem in root.xpath(".//*[@prop and text()]"):
        prop = elem.get("prop")
        if not prop:
            continue

        value = elem.text.strip() if elem.text else ""
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
        if elem.get("unit"):
            attributes["unit_of_measurement"] = elem.get("unit")
            attributes["device_class"] = _get_device_class(elem.get("unit"))
            
        if elem.get("min") and elem.get("max"):
            try:
                attributes["min_value"] = float(elem.get("min"))
                attributes["max_value"] = float(elem.get("max"))
            except ValueError:
                pass
                
        # Handle boolean values
        if value in ("0", "1") and not elem.get("unit"):
            entity_type = "binary_sensor"
            value = value == "1"
            
        entities.append({
            "entity_id": entity_id,
            "entity_type": entity_type,
            "state": value,
            "attributes": attributes
        })
        
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
