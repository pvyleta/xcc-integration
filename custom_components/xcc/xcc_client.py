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

    def _is_login_page(self, content: str) -> bool:
        """Check if the given content is a LOGIN page indicating session expiration.

        Args:
            content: The response content to check

        Returns:
            True if the content appears to be a LOGIN page, False otherwise
        """
        return "<LOGIN>" in content and "USER VALUE" in content

    def _is_session_valid(self, status: int, content: str) -> bool:
        """Check if a response indicates a valid session.

        Args:
            status: HTTP response status code
            content: Response content

        Returns:
            True if the session appears to be valid, False otherwise
        """
        return (
            status == 200
            and not self._is_login_page(content)
            and "500" not in content
        )

    def _decode_and_sanitize_content(self, raw_bytes: bytes, encoding: str) -> str:
        """Decode raw bytes and sanitize the content.

        Args:
            raw_bytes: Raw response bytes
            encoding: Character encoding to use

        Returns:
            Decoded and sanitized content string
        """
        content = raw_bytes.decode(encoding, errors="replace")
        # Basic sanitization like the working script
        content = (
            content.replace("\u00a0", " ")
            .replace("\u202f", " ")
            .replace("\u200b", "")
            .replace("\ufeff", "")
        )
        return content

    async def discover_active_pages(self) -> dict[str, dict]:
        """Discover active pages from main.xml and return page information.

        Returns:
            Dictionary with page URLs as keys and page info as values:
            {
                'okruh.xml?page=0': {
                    'name': 'Radiátory',
                    'active': True,
                    'type': 'heating_circuit',
                    'id': 1
                },
                ...
            }
        """
        import logging
        from lxml import etree

        _LOGGER = logging.getLogger(__name__)

        try:
            # Fetch main page
            _LOGGER.debug("Fetching main.xml to discover active pages")
            main_content = await self.fetch_page("main.xml")

            # Parse XML to find active pages
            pages_info = {}

            # Remove XML declaration and parse
            import re
            xml_clean = re.sub(r'<\?xml[^>]*\?>', '', main_content).strip()

            # Wrap in root element if needed
            if not xml_clean.startswith('<PAGE>'):
                xml_clean = f'<PAGE>{xml_clean}</PAGE>'

            root = etree.fromstring(xml_clean)

            # Find all F elements (page definitions)
            for f_elem in root.xpath('.//F'):
                try:
                    page_id = f_elem.get('N')
                    page_url = f_elem.get('U')
                    zone_id = f_elem.get('Z')  # For mixed zones

                    if not page_url:
                        continue

                    # Extract page name from INPUTN elements
                    name_elem = f_elem.xpath('.//INPUTN[@NAME and @VALUE]')
                    page_name = name_elem[0].get('VALUE') if name_elem else f"Page {page_id}"

                    # Check if page is active (INPUTV with VALUE="1")
                    active_elem = f_elem.xpath('.//INPUTV[@VALUE="1"]')
                    is_active = len(active_elem) > 0

                    # Determine page type based on URL
                    page_type = self._determine_page_type(page_url)

                    pages_info[page_url] = {
                        'id': int(page_id) if page_id else None,
                        'name': page_name,
                        'active': is_active,
                        'type': page_type,
                        'zone_id': int(zone_id) if zone_id else None
                    }

                    _LOGGER.debug(
                        "Discovered page: %s (%s) - Active: %s, Type: %s",
                        page_url, page_name, is_active, page_type
                    )

                except Exception as e:
                    _LOGGER.warning("Error parsing page element: %s", e)
                    continue

            _LOGGER.info(
                "Discovered %d pages, %d active",
                len(pages_info),
                sum(1 for p in pages_info.values() if p['active'])
            )

            return pages_info

        except Exception as e:
            _LOGGER.error("Failed to discover active pages: %s", e)
            return {}

    def _determine_page_type(self, page_url: str) -> str:
        """Determine the type of page based on its URL.

        Args:
            page_url: The page URL (e.g., 'okruh.xml?page=0')

        Returns:
            Page type string
        """
        url_lower = page_url.lower()

        if 'okruh.xml' in url_lower:
            return 'heating_circuit'
        elif 'mzona.xml' in url_lower:
            return 'mixed_zone'
        elif 'tuv' in url_lower:
            return 'hot_water'
        elif 'bazen' in url_lower or 'bazmist' in url_lower:
            return 'pool'
        elif 'fve.xml' in url_lower:
            return 'photovoltaics'
        elif 'vzt.xml' in url_lower:
            return 'ventilation'
        elif 'biv' in url_lower:
            return 'bivalent'
        elif 'solar.xml' in url_lower:
            return 'solar'
        elif 'meteo.xml' in url_lower:
            return 'weather_station'
        elif 'pocasi.xml' in url_lower:
            return 'weather_forecast'
        elif 'elmer.xml' in url_lower:
            return 'electricity_meter'
        elif 'spot.xml' in url_lower:
            return 'spot_pricing'
        else:
            return 'other'

    async def discover_data_pages(self, descriptor_pages: list[str]) -> dict[str, list[str]]:
        """Discover data pages by examining descriptor pages for references.

        Args:
            descriptor_pages: List of descriptor page URLs to examine

        Returns:
            Dictionary mapping descriptor pages to their data pages:
            {
                'fve.xml': ['FVE4.XML', 'FVE5.XML'],
                'okruh.xml': ['OKRUH10.XML'],
                ...
            }
        """
        import logging
        import re

        _LOGGER = logging.getLogger(__name__)

        data_pages_map = {}

        for desc_page in descriptor_pages:
            try:
                _LOGGER.debug("Examining descriptor page %s for data page references", desc_page)

                # Fetch the descriptor page
                content = await self.fetch_page(desc_page)

                # Look for common patterns that indicate data pages
                data_pages = []

                # Pattern 1: Look for uppercase XML references (e.g., FVE4.XML)
                uppercase_refs = re.findall(r'[A-Z][A-Z0-9]*\.XML', content)
                data_pages.extend(uppercase_refs)

                # Pattern 2: Look for specific data page patterns based on descriptor name
                base_name = desc_page.replace('.xml', '').upper()

                # Try common data page patterns
                potential_patterns = [
                    f"{base_name}1.XML",
                    f"{base_name}4.XML",
                    f"{base_name}10.XML",
                    f"{base_name}11.XML",
                ]

                for pattern in potential_patterns:
                    if pattern not in data_pages:
                        # Test if this page exists by trying to fetch it
                        try:
                            test_content = await self.fetch_page(pattern)
                            if not self._is_login_page(test_content) and len(test_content) > 100:
                                data_pages.append(pattern)
                                _LOGGER.debug("Found data page %s for descriptor %s", pattern, desc_page)
                        except Exception:
                            # Page doesn't exist or is not accessible
                            pass

                # Remove duplicates and filter valid pages
                unique_pages = list(set(data_pages))
                valid_pages = []

                for page in unique_pages:
                    try:
                        # Quick validation - try to fetch the page
                        test_content = await self.fetch_page(page)
                        if not self._is_login_page(test_content) and len(test_content) > 50:
                            valid_pages.append(page)
                            _LOGGER.debug("Validated data page %s", page)
                    except Exception as e:
                        _LOGGER.debug("Data page %s not accessible: %s", page, e)

                if valid_pages:
                    data_pages_map[desc_page] = valid_pages
                    _LOGGER.info("Found %d data pages for %s: %s", len(valid_pages), desc_page, valid_pages)
                else:
                    _LOGGER.debug("No data pages found for descriptor %s", desc_page)

            except Exception as e:
                _LOGGER.warning("Error examining descriptor page %s: %s", desc_page, e)
                continue

        return data_pages_map

    async def auto_discover_all_pages(self) -> tuple[list[str], list[str]]:
        """Automatically discover all available descriptor and data pages.

        Returns:
            Tuple of (descriptor_pages, data_pages) lists
        """
        import logging

        _LOGGER = logging.getLogger(__name__)

        try:
            # Step 1: Discover active pages from main.xml
            _LOGGER.info("Starting automatic page discovery...")
            pages_info = await self.discover_active_pages()

            # Step 2: Extract descriptor pages from active pages
            descriptor_pages = []
            for page_url, info in pages_info.items():
                if info['active']:
                    # Convert page URL to descriptor format
                    # e.g., 'okruh.xml?page=0' -> 'okruh.xml'
                    desc_page = page_url.split('?')[0]
                    if desc_page not in descriptor_pages:
                        descriptor_pages.append(desc_page)

            _LOGGER.info("Found %d active descriptor pages: %s", len(descriptor_pages), descriptor_pages)

            # Step 3: Discover data pages for each descriptor
            data_pages_map = await self.discover_data_pages(descriptor_pages)

            # Step 4: Flatten data pages list
            data_pages = []
            for desc_page, pages in data_pages_map.items():
                data_pages.extend(pages)

            # Remove duplicates
            data_pages = list(set(data_pages))

            _LOGGER.info(
                "Auto-discovery complete: %d descriptor pages, %d data pages",
                len(descriptor_pages), len(data_pages)
            )

            return descriptor_pages, data_pages

        except Exception as e:
            _LOGGER.error("Auto-discovery failed: %s", e)
            # Return fallback to current static pages
            from .const import XCC_DESCRIPTOR_PAGES, XCC_DATA_PAGES
            return XCC_DESCRIPTOR_PAGES, XCC_DATA_PAGES

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
                is_valid = self._is_session_valid(resp.status, text)

                _LOGGER.debug(
                    "Session test result: status=%d, contains_login=%s, contains_500=%s, valid=%s",
                    resp.status,
                    self._is_login_page(text),
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
        """Fetch XML page content with proper encoding detection and session validation."""
        import asyncio
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
                content = self._decode_and_sanitize_content(raw_bytes, encoding)

                # Check if we received a LOGIN page instead of data - indicates session expired
                if self._is_login_page(content):
                    _LOGGER.warning("Received LOGIN page for %s - session has expired, re-authenticating", page)

                    # Use the same locking mechanism as in connect() to prevent concurrent re-authentication
                    if self.ip not in _auth_locks:
                        _auth_locks[self.ip] = asyncio.Lock()

                    async with _auth_locks[self.ip]:
                        # Test session again in case another request just re-authenticated
                        if await self._test_session():
                            _LOGGER.debug("Session became valid while waiting for re-authentication lock")
                        else:
                            # Re-authenticate
                            await self._authenticate()

                    # Retry the same request with new session
                    async with self.session.get(f"http://{self.ip}/{page}") as retry_resp:
                        if retry_resp.status != 200:
                            raise Exception(f"Failed to fetch {page} after re-authentication: {retry_resp.status}")

                        retry_raw_bytes = await retry_resp.read()
                        retry_content = self._decode_and_sanitize_content(retry_raw_bytes, encoding)

                        # Check if we still get LOGIN page after re-authentication
                        if self._is_login_page(retry_content):
                            _LOGGER.error("Still receiving LOGIN page for %s after re-authentication - authentication may have failed", page)
                            raise Exception(f"Session re-authentication failed for {page}")

                        _LOGGER.info("Successfully re-authenticated and fetched %s", page)
                        return retry_content

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
