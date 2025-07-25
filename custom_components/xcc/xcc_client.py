"""XCC Heat Pump Controller Client Library

Reusable authentication and data fetching for CLI, pyscript, and HA integration.
"""

import asyncio
import hashlib
import json
import os

import aiohttp
from lxml import etree
from yarl import URL

try:
    from .descriptor_parser import XCCDescriptorParser
except ImportError:
    # For standalone usage
    from descriptor_parser import XCCDescriptorParser

# Global lock to prevent concurrent authentication attempts to the same IP
_auth_locks = {}


class XCCClient:
    """Client for XCC heat pump controller communication."""

    def __init__(
        self,
        ip: str,
        username: str = "xcc",
        password: str = "xcc",
        cookie_file: str | None = None,
    ):
        self.ip = ip
        self.username = username
        self.password = password
        self.cookie_file = cookie_file
        self.session = None
        self.descriptor_parser = XCCDescriptorParser()

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def close(self):
        """Close the session and clean up connections."""
        import logging

        _LOGGER = logging.getLogger(__name__)

        if self.session and not self.session.closed:
            _LOGGER.debug("Closing XCC client session for %s", self.ip)
            await self.session.close()
            # Wait a bit for connections to close properly
            await asyncio.sleep(0.1)

    async def connect(self):
        """Establish connection with session reuse."""
        cookie_jar = aiohttp.CookieJar(unsafe=True)

        # Try to reuse existing session
        if self.cookie_file and os.path.exists(self.cookie_file):
            try:
                # Use async file operations to avoid blocking
                import aiofiles

                async with aiofiles.open(self.cookie_file) as f:
                    content = await f.read()
                    saved = json.loads(content)
                    session_cookie = saved.get("SoftPLC")
                    if session_cookie:
                        cookie_jar.update_cookies(
                            {"SoftPLC": session_cookie},
                            response_url=URL(f"http://{self.ip}/"),
                        )
            except Exception:
                pass  # Continue with fresh login

        # Create session with strict connection limits for XCC controllers
        connector = aiohttp.TCPConnector(
            limit=1,  # Total connection pool limit
            limit_per_host=1,  # Per-host connection limit
            ttl_dns_cache=300,  # DNS cache TTL
            use_dns_cache=True,
            keepalive_timeout=30,
            enable_cleanup_closed=True,
        )
        self.session = aiohttp.ClientSession(
            connector=connector,
            cookie_jar=cookie_jar,
            timeout=aiohttp.ClientTimeout(total=30),
        )

        # Test if existing session works, otherwise authenticate
        import logging

        _LOGGER = logging.getLogger(__name__)

        _LOGGER.debug("Checking if existing session is valid")
        if not await self._test_session():
            _LOGGER.debug("Session invalid, performing authentication")

            # Use global lock to prevent concurrent authentication to same IP
            if self.ip not in _auth_locks:
                _auth_locks[self.ip] = asyncio.Lock()

            async with _auth_locks[self.ip]:
                # Re-test session in case another client just authenticated
                if not await self._test_session():
                    await self._authenticate()
                else:
                    _LOGGER.debug("Session became valid while waiting for lock")
        else:
            _LOGGER.debug("Existing session is valid, skipping authentication")

    async def _test_session(self) -> bool:
        """Test if current session is valid."""
        import logging

        _LOGGER = logging.getLogger(__name__)

        try:
            _LOGGER.debug("Testing session validity for %s", self.ip)
            # Use INDEX.XML like the working script
            async with self.session.get(f"http://{self.ip}/INDEX.XML") as resp:
                raw = await resp.read()
                text = raw.decode(resp.get_encoding() or "utf-8")
                is_valid = (
                    resp.status == 200 and "<LOGIN>" not in text and "500" not in text
                )
                _LOGGER.debug(
                    "Session test result: status=%d, contains_login=%s, contains_500=%s, valid=%s",
                    resp.status,
                    "<LOGIN>" in text,
                    "500" in text,
                    is_valid,
                )
                if not is_valid:
                    _LOGGER.debug("Session test content: %s", text[:200])
                return is_valid
        except Exception as e:
            _LOGGER.debug("Session test failed with exception: %s", e)
            return False

    async def _authenticate(self):
        """Perform authentication and save session with retry logic."""
        import asyncio
        import logging

        _LOGGER = logging.getLogger(__name__)

        _LOGGER.debug(
            "Starting authentication for %s with username %s", self.ip, self.username
        )

        # Retry logic for connection limit errors
        max_retries = 3
        retry_delay = 2  # seconds

        for attempt in range(max_retries):
            try:
                # Get login page for session ID
                async with self.session.get(f"http://{self.ip}/LOGIN.XML") as resp:
                    if resp.status == 500:
                        error_text = await resp.text()
                        if "maximum number of connection" in error_text.lower():
                            if attempt < max_retries - 1:
                                _LOGGER.warning(
                                    "XCC connection limit reached, retrying in %d seconds (attempt %d/%d)",
                                    retry_delay,
                                    attempt + 1,
                                    max_retries,
                                )
                                await asyncio.sleep(retry_delay)
                                retry_delay *= 2  # Exponential backoff
                                continue
                            _LOGGER.error(
                                "XCC connection limit reached after %d attempts",
                                max_retries,
                            )
                            raise Exception("XCC controller connection limit reached")

                    if resp.status != 200:
                        _LOGGER.error("Failed to get LOGIN.XML: status %d", resp.status)
                        raise Exception("Failed to get LOGIN.XML")
                    _LOGGER.debug("Successfully retrieved LOGIN.XML")
                    break  # Success, exit retry loop

            except Exception as e:
                if attempt < max_retries - 1:
                    _LOGGER.warning(
                        "Authentication attempt %d failed: %s, retrying...",
                        attempt + 1,
                        e,
                    )
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                raise

        # Extract session ID from cookie
        session_id = None
        _LOGGER.debug("Extracting session ID from cookies")
        for cookie in self.session.cookie_jar:
            _LOGGER.debug("Found cookie: %s=%s", cookie.key, cookie.value)
            if cookie.key == "SoftPLC":
                session_id = cookie.value
                break

        if not session_id:
            _LOGGER.error(
                "No SoftPLC cookie found in %d cookies",
                len(list(self.session.cookie_jar)),
            )
            raise Exception("No SoftPLC cookie found")

        _LOGGER.debug("Found session ID: %s", session_id)

        # Login with hashed password
        passhash = hashlib.sha1(f"{session_id}{self.password}".encode()).hexdigest()
        login_data = {"USER": self.username, "PASS": passhash}

        _LOGGER.debug(
            "Attempting login with username=%s, passhash=%s",
            self.username,
            passhash[:10] + "...",
        )

        async with self.session.post(
            f"http://{self.ip}/RPC/WEBSES/create.asp", data=login_data
        ) as resp:
            response_text = await resp.text()
            _LOGGER.debug(
                "Login response: status=%d, content=%s",
                resp.status,
                response_text[:200],
            )

            # Check both status and content like the working script
            if resp.status != 200 or "<LOGIN>" in response_text:
                _LOGGER.error(
                    "Authentication failed: status=%d, contains_login=%s, content=%s",
                    resp.status,
                    "<LOGIN>" in response_text,
                    response_text[:200],
                )
                raise Exception("Authentication failed")

            _LOGGER.info("Authentication successful for %s", self.ip)

        # Save session cookie
        if self.cookie_file:
            _LOGGER.debug("Saving session cookie to %s", self.cookie_file)
            await self._save_session()

    async def _save_session(self):
        """Save session cookie to file."""
        try:
            os.makedirs(os.path.dirname(self.cookie_file), exist_ok=True)
            session_data = {}
            for cookie in self.session.cookie_jar:
                if cookie.key == "SoftPLC":
                    session_data["SoftPLC"] = cookie.value
                    break

            # Use async file operations to avoid blocking
            import aiofiles

            async with aiofiles.open(self.cookie_file, "w") as f:
                await f.write(json.dumps(session_data))
        except Exception:
            pass  # Non-critical

    async def fetch_page(self, page: str) -> str:
        """Fetch XML page content with proper encoding detection."""
        import logging
        import re

        _LOGGER = logging.getLogger(__name__)

        async with self.session.get(f"http://{self.ip}/{page}") as resp:
            if resp.status != 200:
                raise Exception(f"Failed to fetch {page}: {resp.status}")

            # Use proper encoding detection like the working script
            raw_bytes = await resp.read()

            # Extract declared encoding from XML header
            encoding = "utf-8"  # default
            match = re.search(
                rb'<\?xml[^>]+encoding=["\']([^"\']+)["\']', raw_bytes[:200]
            )
            if match:
                encoding = match.group(1).decode("ascii", errors="replace").lower()

            _LOGGER.debug("Page %s: detected encoding %s", page, encoding)

            try:
                content = raw_bytes.decode(encoding, errors="replace")
                # Basic sanitization like the working script
                content = (
                    content.replace("\u00a0", " ")
                    .replace("\u202f", " ")
                    .replace("\u200b", "")
                    .replace("\ufeff", "")
                )
                return content
            except Exception as e:
                _LOGGER.warning("Failed to decode %s with %s: %s", page, encoding, e)
                return raw_bytes.decode("utf-8", errors="replace")

    async def fetch_pages(self, pages: list[str]) -> dict[str, str]:
        """Fetch multiple pages with delays to avoid overwhelming XCC controller."""
        import asyncio
        import logging

        _LOGGER = logging.getLogger(__name__)

        results = {}
        for i, page in enumerate(pages):
            try:
                # Add small delay between requests to avoid connection limit
                if i > 0:
                    await asyncio.sleep(0.2)  # 200ms delay between requests

                results[page] = await self.fetch_page(page)
                _LOGGER.debug(
                    "Successfully fetched page %s (%d/%d)", page, i + 1, len(pages)
                )
            except Exception as e:
                _LOGGER.warning("Error fetching page %s: %s", page, e)
                results[page] = f"Error: {e}"
        return results

    def _extract_name_mapping_from_xml(self, xml_content: str) -> dict[str, str]:
        """Extract the mapping of property names to internal NAME attributes from XML."""
        import re

        name_mapping = {}

        # Find all INPUT elements with P and NAME attributes (flexible attribute order)
        # Use more flexible regex that handles any attribute order
        input_pattern = r'<INPUT\s+([^>]+)>'
        input_matches = re.findall(input_pattern, xml_content)

        for attributes in input_matches:
            # Extract P and NAME attributes from the attribute string
            p_match = re.search(r'P="([^"]+)"', attributes)
            name_match = re.search(r'NAME="([^"]+)"', attributes)

            if p_match and name_match:
                prop = p_match.group(1)
                internal_name = name_match.group(1)
                name_mapping[prop] = internal_name

        return name_mapping

    async def set_value(self, prop: str, value: str) -> bool:
        """Set a value on the XCC controller."""
        import logging

        _LOGGER = logging.getLogger(__name__)

        try:
            _LOGGER.info("🔧 Setting XCC property %s to value %s", prop, value)

            # First, try to get the internal NAME for this property by fetching the current page
            internal_name = None
            page_to_fetch = None

            # Determine which page this property might be on based on common patterns
            prop_upper = prop.upper()
            _LOGGER.debug("🔍 Analyzing property %s for page selection", prop)

            # Check for TUV/DHW related properties (including Czech terms)
            tuv_keywords = ["TUV", "DHW", "ZASOBNIK", "TEPLOTA", "TALT"]  # Added Czech DHW-related terms
            if any(tuv_word in prop_upper for tuv_word in tuv_keywords):
                page_to_fetch = "TUV11.XML"
                _LOGGER.debug("🎯 Property contains TUV/DHW keywords, using TUV11.XML")
            elif any(fve_word in prop_upper for fve_word in ["FVE", "SOLAR", "PV"]):
                page_to_fetch = "FVE4.XML"
                _LOGGER.debug("🎯 Property contains FVE/SOLAR/PV keywords, using FVE4.XML")
            elif any(okruh_word in prop_upper for okruh_word in ["OKRUH", "CIRCUIT"]):
                page_to_fetch = "OKRUH10.XML"
                _LOGGER.debug("🎯 Property contains OKRUH/CIRCUIT keywords, using OKRUH10.XML")
            elif any(biv_word in prop_upper for biv_word in ["BIV", "BIVALENCE"]):
                page_to_fetch = "BIV1.XML"
                _LOGGER.debug("🎯 Property contains BIV/BIVALENCE keywords, using BIV1.XML")
            else:
                page_to_fetch = "STAVJED1.XML"  # Default page
                _LOGGER.debug("🎯 Property doesn't match known patterns, using default STAVJED1.XML")

            # Try to fetch the page and extract NAME mapping
            try:
                _LOGGER.info(
                    "🔍 Fetching %s to find internal NAME for property %s",
                    page_to_fetch,
                    prop,
                )
                page_content = await self.fetch_page(page_to_fetch)
                name_mapping = self._extract_name_mapping_from_xml(page_content)
                internal_name = name_mapping.get(prop)
                if internal_name:
                    _LOGGER.info(
                        "✅ Found internal NAME: %s for property %s",
                        internal_name,
                        prop,
                    )
                else:
                    _LOGGER.warning(
                        "⚠️ Could not find internal NAME for property %s in %s",
                        prop,
                        page_to_fetch,
                    )
            except Exception as fetch_err:
                _LOGGER.warning(
                    "⚠️ Could not fetch page %s: %s", page_to_fetch, fetch_err
                )

            # XCC devices use different API patterns depending on the model and firmware
            # Let's try multiple approaches in order of likelihood

            endpoints_to_try = []

            # If we have the internal NAME, try using it first
            if internal_name:
                endpoints_to_try.extend(
                    [
                        # Method 1: Using internal NAME via POST with proper headers (confirmed working)
                        {
                            "method": "POST",
                            "url": f"http://{self.ip}/{page_to_fetch}",
                            "data": {internal_name: value},
                            "headers": {
                                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                                "X-Requested-With": "XMLHttpRequest",
                                "Accept": "application/xml, text/xml, */*; q=0.01",
                                "Referer": f"http://{self.ip}/{page_to_fetch.lower().replace('.xml', '1.xml')}?tab=1",
                            },
                            "description": f"Internal NAME POST to {page_to_fetch} (confirmed format)",
                        },
                        # Method 2: Using internal NAME via GET
                        {
                            "method": "GET",
                            "url": f"http://{self.ip}/{page_to_fetch}?{internal_name}={value}",
                            "description": f"Internal NAME GET to {page_to_fetch}",
                        },
                    ]
                )

            # Add fallback methods using property name
            endpoints_to_try.extend(
                [
                    # Method 3: Direct property setting via GET
                    {
                        "method": "GET",
                        "url": f"http://{self.ip}/{page_to_fetch}?{prop}={value}",
                        "description": "Property name GET",
                    },
                    # Method 4: Property setting via POST to property page
                    {
                        "method": "POST",
                        "url": f"http://{self.ip}/{page_to_fetch}",
                        "data": {prop: value},
                        "description": "Property name POST",
                    },
                    # Method 5: Generic RPC endpoint
                    {
                        "method": "POST",
                        "url": f"http://{self.ip}/RPC/WEBSES/set.asp",
                        "data": {prop: value},
                        "description": "Generic RPC POST",
                    },
                ]
            )

            for i, endpoint in enumerate(endpoints_to_try, 1):
                try:
                    _LOGGER.info(
                        "🔄 Attempt %d/%d: %s",
                        i,
                        len(endpoints_to_try),
                        endpoint["description"],
                    )

                    if endpoint["method"] == "GET":
                        async with self.session.get(endpoint["url"]) as resp:
                            # Handle encoding issues like we do for XML parsing
                            try:
                                response_text = await resp.text()
                            except UnicodeDecodeError:
                                # Try with different encodings if UTF-8 fails
                                response_bytes = await resp.read()
                                for encoding in ['windows-1250', 'iso-8859-2', 'utf-8']:
                                    try:
                                        response_text = response_bytes.decode(encoding)
                                        break
                                    except UnicodeDecodeError:
                                        continue
                                else:
                                    response_text = response_bytes.decode('utf-8', errors='ignore')

                            _LOGGER.info("📡 GET response: status=%d", resp.status)

                            if resp.status == 200:
                                _LOGGER.info(
                                    "✅ Successfully set XCC property %s to %s via GET",
                                    prop,
                                    value,
                                )
                                return True
                    else:
                        # Use custom headers if provided
                        headers = endpoint.get("headers", {})
                        async with self.session.post(
                            endpoint["url"],
                            data=endpoint.get("data", {}),
                            headers=headers,
                        ) as resp:
                            # Handle encoding issues like we do for XML parsing
                            try:
                                response_text = await resp.text()
                            except UnicodeDecodeError:
                                # Try with different encodings if UTF-8 fails
                                response_bytes = await resp.read()
                                for encoding in ['windows-1250', 'iso-8859-2', 'utf-8']:
                                    try:
                                        response_text = response_bytes.decode(encoding)
                                        break
                                    except UnicodeDecodeError:
                                        continue
                                else:
                                    response_text = response_bytes.decode('utf-8', errors='ignore')

                            _LOGGER.info("📡 POST response: status=%d", resp.status)

                            if (
                                resp.status == 200
                                and "ERROR" not in response_text.upper()
                            ):
                                _LOGGER.info(
                                    "✅ Successfully set XCC property %s to %s via POST",
                                    prop,
                                    value,
                                )
                                return True

                except Exception as endpoint_err:
                    _LOGGER.warning("⚠️ Endpoint %d failed: %s", i, endpoint_err)
                    continue

            _LOGGER.error(
                "❌ All endpoints failed for setting XCC property %s to %s", prop, value
            )
            return False

        except Exception as err:
            _LOGGER.error(
                "❌ Error setting XCC property %s to %s: %s", prop, value, err
            )
            return False

    async def close(self):
        """Close the session."""
        if self.session:
            await self.session.close()


def parse_xml_entities(
    xml_content: str, page_name: str, entity_prefix: str = "xcc"
) -> list[dict]:
    """Parse XML content into entity data."""
    import logging

    _LOGGER = logging.getLogger(__name__)

    entities = []

    _LOGGER.debug(
        "Parsing XML for page %s, content length: %d bytes", page_name, len(xml_content)
    )

    try:
        # xml_content is already a properly decoded string from fetch_page()
        # Remove XML declaration if present to avoid encoding issues with etree.fromstring()
        import re
        xml_clean = re.sub(r'<\?xml[^>]*\?>', '', xml_content).strip()

        try:
            root = etree.fromstring(xml_clean)
            _LOGGER.debug("Successfully parsed XML content for %s", page_name)
        except Exception as e:
            _LOGGER.warning(
                "Failed to parse XML for %s: %s", page_name, e
            )
            return entities
    except Exception as e:
        _LOGGER.error("Unexpected error parsing XML for %s: %s", page_name, e)
        return entities

    # Try different XCC XML formats
    _LOGGER.debug("XML root element: %s", root.tag if root is not None else "None")

    # Format 1: XCC Values format (STAVJED1.XML style) - <INPUT P="name" VALUE="value"/>
    input_elements = root.xpath(".//INPUT[@P and @VALUE]")
    _LOGGER.debug(
        "Found %d INPUT elements with P and VALUE attributes", len(input_elements)
    )

    if input_elements:
        _LOGGER.debug("Processing INPUT elements for %s", page_name)
        processed_count = 0
        skipped_count = 0

        for i, elem in enumerate(input_elements):
            prop = elem.get("P")
            value = elem.get("VALUE")

            # Only log first 3 elements once per function call to avoid spam (they're always the same)
            # Use a global variable since this is a standalone function
            if not hasattr(parse_xml_entities, "_logged_input_elements"):
                parse_xml_entities._logged_input_elements = False

            if i < 3 and not parse_xml_entities._logged_input_elements:
                _LOGGER.debug("INPUT element %d: P='%s' VALUE='%s'", i, prop, value)
                if i == 2:  # After logging the 3rd element, mark as logged
                    parse_xml_entities._logged_input_elements = True

            if not prop:
                _LOGGER.debug("Skipping element %d: no P attribute", i)
                skipped_count += 1
                continue
            if not value:
                _LOGGER.debug("Skipping element %d: no VALUE attribute", i)
                skipped_count += 1
                continue

            entity_id = f"{entity_prefix}_{prop.lower().replace('-', '_')}"

            # Determine entity type and attributes
            entity_type = "sensor"
            attributes = {
                "page": page_name,  # Fixed: use "page" instead of "source_page"
                "field_name": prop,
                "friendly_name": prop.replace("-", " ").replace("_", " ").title(),
            }

            # Parse NAME attribute for more info
            name_attr = elem.get("NAME", "")
            if "_REAL_" in name_attr:
                # Only assign temperature device class if it's actually a temperature sensor
                if any(
                    temp_indicator in prop.upper()
                    for temp_indicator in ["TEMP", "TEPLOTA", "SVENKU", "SVNITR"]
                ):
                    attributes["device_class"] = "temperature"
                    attributes["unit_of_measurement"] = "°C"
                elif any(
                    power_indicator in prop.upper()
                    for power_indicator in ["POWER", "VYKON", "WATT"]
                ):
                    attributes["device_class"] = "power"
                    attributes["unit_of_measurement"] = "W"
                elif any(
                    energy_indicator in prop.upper()
                    for energy_indicator in ["ENERGY", "ENERGIE", "KWH"]
                ):
                    attributes["device_class"] = "energy"
                    attributes["unit_of_measurement"] = "kWh"
                elif any(
                    current_indicator in prop.upper()
                    for current_indicator in ["CURRENT", "PROUD", "AMP"]
                ):
                    attributes["device_class"] = "current"
                    attributes["unit_of_measurement"] = "A"
                elif any(
                    voltage_indicator in prop.upper()
                    for voltage_indicator in ["VOLTAGE", "NAPETI", "VOLT"]
                ):
                    attributes["device_class"] = "voltage"
                    attributes["unit_of_measurement"] = "V"
                elif any(
                    price_indicator in prop.upper()
                    for price_indicator in ["PRICE", "CENA", "COST"]
                ):
                    attributes["device_class"] = "monetary"
                    attributes["unit_of_measurement"] = "CZK"
                # Don't assign device class for other REAL values
            elif "_BOOL_" in name_attr:
                entity_type = "binary_sensor"
                value = "1" if value == "1" else "0"
            elif "_USINT_" in name_attr or "_UINT_" in name_attr:
                try:
                    value = str(int(float(value)))
                except:
                    pass

            entities.append(
                {
                    "entity_id": entity_id,
                    "entity_type": entity_type,
                    "state": value,
                    "attributes": attributes,
                }
            )
            processed_count += 1

        _LOGGER.debug(
            "INPUT processing complete: %d processed, %d skipped, %d total entities",
            processed_count,
            skipped_count,
            len(entities),
        )
        return entities

    # Format 2: XCC Structure format with values (prop attributes with text)
    prop_elements = root.xpath(".//*[@prop and text()]")
    _LOGGER.debug(
        "Found %d elements with prop attributes and text content", len(prop_elements)
    )

    if prop_elements:
        _LOGGER.debug("Processing prop elements for %s", page_name)

    for elem in prop_elements:
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
            "friendly_name": prop.replace("-", " ").title(),
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

        entities.append(
            {
                "entity_id": entity_id,
                "entity_type": entity_type,
                "state": value,
                "attributes": attributes,
            }
        )

    _LOGGER.debug(
        "XML parsing complete for %s: %d total entities found", page_name, len(entities)
    )
    if len(entities) == 0:
        _LOGGER.warning(
            "No entities found in %s - this may indicate an XML format issue", page_name
        )
        # Log a sample of the XML content for debugging
        sample_content = xml_content[:500] if len(xml_content) > 500 else xml_content
        _LOGGER.debug("Sample XML content for %s: %s", page_name, sample_content)

    return entities


def _get_device_class(unit: str) -> str | None:
    """Map units to device classes."""
    unit_map = {
        "°C": "temperature",
        "kW": "power",
        "kWh": "energy",
        "V": "voltage",
        "A": "current",
        "%": "battery" if "batt" in unit.lower() else None,
        "bar": "pressure",
    }
    return unit_map.get(unit)


async def fetch_all_data_with_descriptors(
    client: "XCCClient",
) -> tuple[dict[str, str], dict[str, str]]:
    """Fetch all XCC data pages and their corresponding descriptor files."""
    import asyncio

    # Data pages (with values)
    data_pages = [
        "STAVJED1.XML",
        "OKRUH10.XML",
        "TUV11.XML",
        "BIV1.XML",
        "FVE4.XML",
        "SPOT1.XML",
    ]
    # Descriptor pages (with UI definitions)
    descriptor_pages = [
        "STAVJED.XML",
        "OKRUH.XML",
        "TUV1.XML",
        "BIV.XML",
        "FVE.XML",
        "SPOT.XML",
    ]

    all_data = {}
    all_descriptors = {}

    # Fetch data pages
    for page in data_pages:
        try:
            data = await client.fetch_page(page)
            if data:
                all_data[page] = data
                print(f"✓ Successfully fetched data {page} ({len(data)} bytes)")
            else:
                print(f"✗ Failed to fetch data {page}")

            # Small delay between requests
            await asyncio.sleep(0.2)

        except Exception as e:
            print(f"✗ Error fetching data {page}: {e}")

    # Fetch descriptor pages
    for page in descriptor_pages:
        try:
            data = await client.fetch_page(page)
            if data:
                all_descriptors[page] = data
                print(f"✓ Successfully fetched descriptor {page} ({len(data)} bytes)")
            else:
                print(f"✗ Failed to fetch descriptor {page}")

            # Small delay between requests
            await asyncio.sleep(0.2)

        except Exception as e:
            print(f"✗ Error fetching descriptor {page}: {e}")

    return all_data, all_descriptors


# Standard page sets for different use cases
STANDARD_PAGES = [
    "stavjed.xml",
    "STAVJED1.XML",  # Status
    "okruh.xml",
    "OKRUH10.XML",  # Heating circuits
    "tuv1.xml",
    "TUV11.XML",  # Hot water
    "biv.xml",
    "BIV1.XML",  # Bivalent heating
    "fve.xml",
    "FVE4.XML",  # Photovoltaics
    "spot.xml",
    "SPOT1.XML",  # Spot pricing
]

MINIMAL_PAGES = [
    "stavjed.xml",
    "okruh.xml",
    "tuv1.xml",
    "fve.xml",
]
