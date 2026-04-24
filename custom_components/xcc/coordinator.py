"""Data update coordinator for XCC Heat Pump Controller integration."""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_IP_ADDRESS, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_LANGUAGE,
    CONF_SCAN_INTERVAL,
    DEFAULT_LANGUAGE,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
    DESCRIPTOR_OVERRIDES,
    DOMAIN,
    LANGUAGE_ENGLISH,
    XCC_DATA_PAGES,
    XCC_DESCRIPTOR_PAGES,
)
from .entity_helpers import (
    format_entity_id_suffix,
    infer_entity_type_from_attributes,
    lookup_with_normalized_fallback,
    normalize_property_name,
    process_entities as _process_entities_core,
)
from .value_writer import resolve_property

_LOGGER = logging.getLogger(__name__)


class XCCDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the XCC controller."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.entry = entry
        self.ip_address = entry.data[CONF_IP_ADDRESS]
        self.username = entry.data[CONF_USERNAME]
        self.password = entry.data[CONF_PASSWORD]

        # Set language preference from config or default
        self.language = entry.data.get(CONF_LANGUAGE, DEFAULT_LANGUAGE)

        # Set update interval from config or default
        scan_interval = entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        update_interval = timedelta(seconds=scan_interval)

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )

        # Store discovered entities and their metadata
        self.entities: dict[str, dict[str, Any]] = {}
        self.device_info: dict[str, Any] = {}
        self._client = None  # Persistent XCC client for session reuse
        self.descriptor_parser = None  # Parser for entity type detection
        self.entity_configs = {}  # Cached entity configurations
        self._descriptors_loaded = False  # Track if descriptors have been loaded

        # One-shot flag set by ``async_setup_entry`` when the user opted in
        # to entity-ID regeneration. ``XCCEntity._migrate_legacy_entity_id``
        # consults this attribute to decide whether to rewrite legacy
        # IP-baked entity_ids on ``async_added_to_hass``. Default False so
        # history attached to existing entity_ids is preserved by default.
        self.regenerate_entity_ids: bool = False

        # Page discovery attributes
        self._pages_discovered = False
        self._discovered_descriptor_pages = []
        self._discovered_data_pages = []

        self._update_lock = asyncio.Lock()  # Prevent concurrent updates
        self._last_update_time = 0  # Track last update time
        self._min_update_interval = 1.0  # Minimum 1 second between updates

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via library."""
        import time

        # Check if we need to throttle updates
        current_time = time.time()
        if current_time - self._last_update_time < self._min_update_interval:
            _LOGGER.debug("Throttling update request - too soon after last update")
            return self.data or {}

        # Use lock to prevent concurrent updates
        async with self._update_lock:
            # Double-check after acquiring lock
            current_time = time.time()
            if current_time - self._last_update_time < self._min_update_interval:
                _LOGGER.debug("Another update completed while waiting for lock")
                return self.data or {}

            _LOGGER.debug("Starting data update for XCC controller %s", self.ip_address)
            self._last_update_time = current_time

        try:
            # Import XCC client here to avoid import issues
            from .xcc_client import XCCClient, parse_xml_entities

            # Create or reuse persistent client for session management
            if self._client is None:
                _LOGGER.debug(
                    "Creating new XCC client for %s with username %s",
                    self.ip_address,
                    self.username,
                )

                # Use Home Assistant's config directory for cookie storage
                cookie_file = f"{self.hass.config.config_dir}/.xcc_session_{self.ip_address.replace('.', '_')}.json"

                self._client = XCCClient(
                    ip=self.ip_address,
                    username=self.username,
                    password=self.password,
                    cookie_file=cookie_file,
                )
                await self._client.__aenter__()  # Initialize the client
            else:
                _LOGGER.debug("Reusing existing XCC client for %s", self.ip_address)

            client = self._client

            # Discover pages on first run
            if not self._pages_discovered:
                await self._discover_pages(client)

            # Load descriptors on first run to determine entity types
            if not self._descriptors_loaded:
                await self._load_descriptors(client)

            # Use discovered data pages or fall back to default
            data_pages = self._discovered_data_pages if self._discovered_data_pages else XCC_DATA_PAGES

            # Fetch only data pages (not descriptors)
            _LOGGER.debug(
                "Fetching %d XCC data pages: %s", len(data_pages), data_pages
            )
            _LOGGER.debug(
                "Update triggered by: %s", getattr(self, "_update_source", "unknown")
            )
            pages_data = await asyncio.wait_for(
                client.fetch_pages(data_pages),
                timeout=DEFAULT_TIMEOUT,
            )
            _LOGGER.debug(
                "Successfully fetched %d pages from XCC controller", len(pages_data)
            )

            # Parse entities from all pages
            all_entities = []
            page_counts = []
            for page_name, xml_content in pages_data.items():
                if not xml_content.startswith("Error:"):
                    entities = parse_xml_entities(xml_content, page_name)
                    page_counts.append(f"{page_name}:{len(entities)}")
                    all_entities.extend(entities)
                else:
                    _LOGGER.warning(
                        "Error fetching page %s: %s", page_name, xml_content
                    )

            # Parse system configuration entities from main.xml
            try:
                main_xml = await asyncio.wait_for(
                    client.fetch_page("main.xml"),
                    timeout=DEFAULT_TIMEOUT,
                )
                if main_xml and not main_xml.startswith("Error:"):
                    sysconfig_entities = client.parse_main_xml_config_entities(main_xml)
                    if sysconfig_entities:
                        all_entities.extend(sysconfig_entities)
                        page_counts.append(f"main.xml(sysconfig):{len(sysconfig_entities)}")
            except Exception as main_err:
                _LOGGER.debug("Could not parse main.xml config entities: %s", main_err)

            # Log consolidated parsing results
            _LOGGER.debug("📄 Parsed %d entities from %d pages: %s", len(all_entities), len(page_counts), ", ".join(page_counts))
            processed_data = self._process_entities(all_entities)

            # Log summary of processed data
            entity_counts = {key: len(value) for key, value in processed_data.items()}
            _LOGGER.info("XCC data update successful: %s", entity_counts)

            # Update device info on first successful fetch
            if not self.device_info:
                # Language-aware main controller name
                if self.language == LANGUAGE_ENGLISH:
                    controller_name = f"XCC Controller ({self.ip_address})"
                    controller_model = "Heat Pump Controller"
                else:
                    controller_name = f"XCC Regulátor ({self.ip_address})"
                    controller_model = "Regulátor tepelného čerpadla"

                self.device_info = {
                    "identifiers": {(DOMAIN, self.ip_address)},
                    "name": controller_name,
                    "manufacturer": "XCC",
                    "model": controller_model,
                    "sw_version": "Unknown",
                    "configuration_url": f"http://{self.ip_address}",
                }

                # Initialize device info for all sub-devices
                self._init_device_info()

            return processed_data

        except TimeoutError as err:
            _LOGGER.error(
                "Timeout communicating with XCC controller %s: %s", self.ip_address, err
            )
            raise UpdateFailed(
                f"Timeout communicating with XCC controller: {err}"
            ) from err
        except Exception as err:
            _LOGGER.error(
                "Error communicating with XCC controller %s: %s", self.ip_address, err
            )
            if "authentication" in str(err).lower() or "login" in str(err).lower():
                raise ConfigEntryAuthFailed(f"Authentication failed: {err}") from err
            raise UpdateFailed(
                f"Error communicating with XCC controller: {err}"
            ) from err

    def _process_entities(self, entities: list[dict[str, Any]]) -> dict[str, Any]:
        """Process raw entities into organized data structure with priority-based device assignment.

        Thin wrapper around :func:`entity_helpers.process_entities` — keeps the
        pipeline pure (and therefore unit-testable without Home Assistant) and
        lets the coordinator stay in charge of stateful bookkeeping
        (``self.entities`` merge, per-page logging).
        """
        # Per-page descriptor stats, logged before the priority pass so the
        # summary line matches what process_entities will act on.
        descriptor_stats_by_page: dict[str, dict[str, list[str]]] = {}
        for entity in entities:
            prop = entity["attributes"]["field_name"]
            page = entity["attributes"].get("page", "unknown")
            has_descriptor = prop in self.entity_configs
            is_nast_entity = page.upper() == "NAST.XML"
            is_sysconfig_entity = prop.startswith("SYSCONFIG-")
            bucket = descriptor_stats_by_page.setdefault(
                page, {"with": [], "without": []}
            )
            if has_descriptor or is_nast_entity or is_sysconfig_entity:
                bucket["with"].append(prop)
            else:
                bucket["without"].append(prop)

        page_stats = []
        for page, stats in descriptor_stats_by_page.items():
            with_count = len(stats["with"])
            without_count = len(stats["without"])
            if with_count and without_count:
                page_stats.append(f"{page}(✅{with_count}/❌{without_count})")
            elif with_count:
                page_stats.append(f"{page}(✅{with_count})")
            elif without_count:
                page_stats.append(f"{page}(❌{without_count})")
        if page_stats:
            _LOGGER.debug(
                "📊 Descriptors: %d entities, %d configs | %s",
                len(entities), len(self.entity_configs), " | ".join(page_stats),
            )

        processed_data, entities_metadata = _process_entities_core(
            entities, self.entity_configs, self.language
        )

        # Merge into the long-lived entities map the rest of the coordinator /
        # platform layer reads from.
        self.entities.update(entities_metadata)

        entity_counts = {
            "switches": len(processed_data["switches"]),
            "binary_sensors": len(processed_data["binary_sensors"]),
            "numbers": len(processed_data["numbers"]),
            "selects": len(processed_data["selects"]),
            "buttons": len(processed_data["buttons"]),
            "sensors": len(processed_data["sensors"]),
            "total": len(processed_data["entities"]),
        }
        _LOGGER.info("=== COORDINATOR ENTITY PROCESSING COMPLETE ===")
        _LOGGER.info("Final entity distribution: %s", entity_counts)
        _LOGGER.info(
            "Returning processed_data with keys: %s", list(processed_data.keys())
        )
        return processed_data

    def _format_entity_id(self, prop: str) -> str:
        """Format XCC property name into valid Home Assistant entity ID suffix."""
        return format_entity_id_suffix(prop)

    def _get_friendly_name(self, descriptor_config: dict[str, Any], prop: str) -> str:
        """Get friendly name based on language preference."""
        if self.language == LANGUAGE_ENGLISH:
            # Prefer English, fallback to Czech, then prop
            return (
                descriptor_config.get("friendly_name_en")
                or descriptor_config.get("friendly_name")
                or prop
            )
        else:
            # Prefer Czech, fallback to English, then prop
            return (
                descriptor_config.get("friendly_name")
                or descriptor_config.get("friendly_name_en")
                or prop
            )

    def _init_device_info(self) -> None:
        """Initialize device info for all sub-devices."""
        # Device names and descriptions with language support
        if self.language == LANGUAGE_ENGLISH:
            device_configs = {
                "SYSCONFIG": {"name": "System Configuration", "model": "Feature & Page Settings"},
                "SPOT": {"name": "Spot Prices", "model": "Energy Market Data"},
                "FVEINV": {"name": "PV Inverter", "model": "Solar Inverter Monitor"},
                "FVE": {"name": "Solar PV System", "model": "Photovoltaic Controller"},
                "BIV": {"name": "Heat Pump", "model": "Bivalent Heat Pump"},
                "OKRUH": {"name": "Heating Circuits", "model": "Heating Zone Controller"},
                "TUV1": {"name": "Hot Water System", "model": "Domestic Hot Water"},
                "STAVJED": {"name": "Unit Status", "model": "System Status Monitor"},
                "NAST": {"name": "Heat Pump Settings", "model": "HP Configuration & Calibration"},
                "XCC_HIDDEN_SETTINGS": {"name": "Hidden Settings", "model": "Advanced Configuration"},
            }
        else:
            # Czech language
            device_configs = {
                "SYSCONFIG": {"name": "Konfigurace systému", "model": "Nastavení funkcí a stránek"},
                "SPOT": {"name": "Spotové ceny", "model": "Data energetického trhu"},
                "FVEINV": {"name": "FV Měnič", "model": "Monitor solárního měniče"},
                "FVE": {"name": "Fotovoltaický systém", "model": "Fotovoltaický regulátor"},
                "BIV": {"name": "Tepelné čerpadlo", "model": "Bivalentní tepelné čerpadlo"},
                "OKRUH": {"name": "Topné okruhy", "model": "Regulátor topných zón"},
                "TUV1": {"name": "Systém teplé vody", "model": "Teplá užitková voda"},
                "STAVJED": {"name": "Stav jednotky", "model": "Monitor stavu systému"},
                "NAST": {"name": "Nastavení TČ", "model": "Konfigurace a kalibrace TČ"},
                "XCC_HIDDEN_SETTINGS": {"name": "Skrytá nastavení", "model": "Pokročilá konfigurace"},
            }

        self.sub_device_info = {}
        for device_name, config in device_configs.items():
            self.sub_device_info[device_name] = {
                "identifiers": {(DOMAIN, f"{self.ip_address}_{device_name}")},
                "name": f"{config['name']} ({self.ip_address})",
                "manufacturer": "XCC",
                "model": config["model"],
                "sw_version": "Unknown",
                "configuration_url": f"http://{self.ip_address}",
                "via_device": (DOMAIN, self.ip_address),  # Link to main controller
            }

    def get_device_info_for_entity(self, entity_id: str) -> dict[str, Any]:
        """Get device info for a specific entity."""
        entity_data = self.entities.get(entity_id)
        if not entity_data:
            # Fallback to main device
            return self.device_info

        device_name = entity_data.get("device")
        if device_name and hasattr(self, 'sub_device_info') and device_name in self.sub_device_info:
            return self.sub_device_info[device_name]

        # Fallback to main device
        return self.device_info



    async def async_force_update(self) -> None:
        """Force an immediate update of all entity values."""
        _LOGGER.info("🔄 FORCING IMMEDIATE COORDINATOR UPDATE")
        self._update_source = "force_update"
        await self.async_request_refresh()

    def _determine_entity_type(self, entity: dict[str, Any]) -> str:
        """Determine the appropriate Home Assistant entity type for an XCC entity."""
        return infer_entity_type_from_attributes(entity)

    def get_entity_data(self, entity_id: str) -> dict[str, Any] | None:
        """Get entity data by ID."""
        return self.entities.get(entity_id)

    def get_entities_by_type(self, entity_type: str) -> dict[str, dict[str, Any]]:
        """Get all entities of a specific type."""
        return {
            entity_id: entity_data
            for entity_id, entity_data in self.entities.items()
            if entity_data["type"] == entity_type
        }

    async def async_set_value(self, entity_id: str, value: Any) -> bool:
        """Set a value on the XCC controller."""
        return await self.async_set_entity_value(entity_id, value)

    async def async_set_entity_value(self, entity_id: str, value: Any) -> bool:
        """Set a value on the XCC controller (method name expected by entities)."""
        try:
            _LOGGER.info("🎛️ Setting entity %s to value %s", entity_id, value)

            resolution = resolve_property(entity_id, self.data, self.entity_configs)
            prop = resolution.prop
            internal_name = resolution.internal_name

            if not prop:
                _LOGGER.error(
                    "❌ Could not determine property name for entity %s. Tried methods: %s",
                    entity_id,
                    ", ".join(resolution.attempted) if resolution.attempted else "none",
                )
                _LOGGER.debug("Available entity types in data: %s", list((self.data or {}).keys()))
                _LOGGER.debug("Available entity configs: %d properties", len(self.entity_configs))
                return False

            _LOGGER.debug(
                "🔍 Property resolution: %s -> %s (method: %s)",
                entity_id, prop, resolution.method,
            )

            _LOGGER.info(
                "🔧 Setting XCC property %s to value %s for entity %s",
                prop,
                value,
                entity_id,
            )

            # Use the persistent client if available, otherwise create a temporary one
            if self._client is not None:
                _LOGGER.debug("Using persistent XCC client for property setting")
                client = self._client
                try:
                    success = await client.set_value(prop, value, internal_name=internal_name)
                    if success:
                        _LOGGER.info("✅ Successfully set XCC property %s to %s", prop, value)
                        # Request immediate data refresh to update state
                        _LOGGER.debug("Requesting data refresh after successful property set")
                        await self.async_request_refresh()
                        return True
                    else:
                        _LOGGER.error("❌ Failed to set XCC property %s to %s (client returned False)", prop, value)
                        return False
                except Exception as client_err:
                    _LOGGER.error("❌ Exception during property setting with persistent client: %s", client_err)
                    return False
            else:
                _LOGGER.debug("Creating temporary XCC client for property setting")
                from .xcc_client import XCCClient

                # Use same cookie file for temporary clients
                cookie_file = f"{self.hass.config.config_dir}/.xcc_session_{self.ip_address.replace('.', '_')}.json"
                try:
                    async with XCCClient(
                        ip=self.ip_address,
                        username=self.username,
                        password=self.password,
                        cookie_file=cookie_file,
                    ) as client:
                        success = await client.set_value(prop, value, internal_name=internal_name)
                        if success:
                            _LOGGER.info("✅ Successfully set XCC property %s to %s", prop, value)
                            # Request immediate data refresh to update state
                            _LOGGER.debug("Requesting data refresh after successful property set")
                            await self.async_request_refresh()
                            return True
                        else:
                            _LOGGER.error("❌ Failed to set XCC property %s to %s (client returned False)", prop, value)
                            return False
                except Exception as client_err:
                    _LOGGER.error("❌ Exception during property setting with temporary client: %s", client_err)
                    return False

        except Exception as err:
            # Use locals().get() to safely access entity_id in case exception occurs before it's used
            entity_id_safe = locals().get('entity_id', entity_id)  # entity_id is the parameter
            _LOGGER.error("❌ Unexpected error setting value for entity %s: %s", entity_id_safe, err)
            import traceback
            _LOGGER.debug("Full traceback: %s", traceback.format_exc())
            return False

    async def async_shutdown(self) -> None:
        """Shutdown the coordinator and clean up resources."""
        if self._client is not None:
            _LOGGER.debug("Closing persistent XCC client for %s", self.ip_address)
            try:
                await self._client.__aexit__(None, None, None)
            except Exception as err:
                _LOGGER.warning("Error closing XCC client: %s", err)
            finally:
                self._client = None

    async def _discover_pages(self, client) -> None:
        """Discover active pages and their data pages automatically."""
        try:
            _LOGGER.info("Starting automatic page discovery for XCC controller %s", self.ip_address)

            # Use the auto-discovery functionality
            descriptor_pages, data_pages = await client.auto_discover_all_pages()

            if descriptor_pages and data_pages:
                self._discovered_descriptor_pages = descriptor_pages
                self._discovered_data_pages = data_pages

                _LOGGER.info(
                    "Page discovery successful: %d descriptor pages, %d data pages",
                    len(descriptor_pages), len(data_pages)
                )
                _LOGGER.info("Discovered descriptor pages: %s", descriptor_pages)
                _LOGGER.info("Discovered data pages: %s", data_pages)

                # Check for additional pages that might not be in main.xml discovery
                await self._check_additional_pages(client)
            else:
                _LOGGER.warning("Page discovery returned no pages, using defaults")
                from .const import XCC_DESCRIPTOR_PAGES, XCC_DATA_PAGES
                self._discovered_descriptor_pages = XCC_DESCRIPTOR_PAGES
                self._discovered_data_pages = XCC_DATA_PAGES

            self._pages_discovered = True

        except Exception as err:
            _LOGGER.error("Failed to discover pages: %s", err)
            _LOGGER.info("Falling back to default page configuration")
            from .const import XCC_DESCRIPTOR_PAGES, XCC_DATA_PAGES
            self._discovered_descriptor_pages = XCC_DESCRIPTOR_PAGES
            self._discovered_data_pages = XCC_DATA_PAGES
            self._pages_discovered = True  # Don't retry on every update

    async def _check_additional_pages(self, client) -> None:
        """Check for additional pages that might not be discovered automatically."""
        try:
            _LOGGER.debug("Checking for additional pages not found in main.xml discovery")

            # List of additional pages to check (descriptor + data page pairs)
            additional_pages = [
                ("nast.xml", "NAST.XML", "Heat pump settings"),
                ("fveinv.xml", "FVEINV10.XML", "PV Inverter details"),
            ]

            # Data-only pages: these have no paired descriptor XML and are probed directly.
            # STATUS.XML is not referenced from main.xml; it is rendered via a JS button
            # on the main page using TRANSF.XSL. Its field labels live in TRANSF.XSL and
            # are captured in STATUS_XML_DESCRIPTOR rather than a descriptor XML file.
            additional_data_only_pages = [
                ("STATUS.XML", "Main-page status summary"),
            ]

            for data_page, description in additional_data_only_pages:
                try:
                    _LOGGER.debug("Probing data-only page %s (%s)", data_page, description)
                    test_data = await client.fetch_page(data_page)
                    if test_data and len(test_data) > 100 and '<LOGIN>' not in test_data:
                        _LOGGER.info("Found data-only page: %s (%s)", data_page, description)
                        if data_page not in self._discovered_data_pages:
                            self._discovered_data_pages.append(data_page)
                    else:
                        _LOGGER.debug("Data-only page %s not accessible or empty", data_page)
                except Exception as e:
                    _LOGGER.debug("Error probing data-only page %s: %s", data_page, e)

            for descriptor_page, data_page, description in additional_pages:
                try:
                    # Test if descriptor page is accessible
                    _LOGGER.debug("Testing accessibility of %s (%s)", descriptor_page, description)
                    test_data = await client.fetch_page(descriptor_page)

                    if test_data and len(test_data) > 100 and '<LOGIN>' not in test_data:
                        _LOGGER.info("✅ Found additional page: %s (%s)", descriptor_page, description)

                        # Add to discovered pages
                        if descriptor_page not in self._discovered_descriptor_pages:
                            self._discovered_descriptor_pages.append(descriptor_page)
                            _LOGGER.info("Added %s to descriptor pages", descriptor_page)

                        # For NAST, the descriptor and data are the same file
                        if data_page not in self._discovered_data_pages:
                            self._discovered_data_pages.append(data_page)
                            _LOGGER.info("Added %s to data pages", data_page)
                    else:
                        _LOGGER.debug("❌ Additional page %s not accessible or invalid", descriptor_page)

                except asyncio.CancelledError:
                    _LOGGER.debug("Request cancelled while testing %s", descriptor_page)
                    continue
                except asyncio.TimeoutError:
                    _LOGGER.debug("Timeout while testing %s", descriptor_page)
                    continue
                except Exception as e:
                    _LOGGER.debug("Error testing %s: %s", descriptor_page, e)
                    continue

        except Exception as e:
            _LOGGER.warning("Error checking additional pages: %s", e)

    async def _load_descriptors(self, client) -> None:
        """Load descriptor files to determine entity types."""
        try:
            import asyncio

            from .descriptor_parser import XCCDescriptorParser

            _LOGGER.debug("Loading XCC descriptor files for entity type detection")

            # Use discovered descriptor pages or fall back to default
            descriptor_pages = self._discovered_descriptor_pages if self._discovered_descriptor_pages else XCC_DESCRIPTOR_PAGES

            descriptor_data = {}
            for page in descriptor_pages:
                try:
                    # Check if page is accessible before trying to fetch it
                    # This prevents errors when pages like nast.xml are in constants but not discovered
                    _LOGGER.debug("Attempting to load descriptor page: %s", page)
                    data = await client.fetch_page(page)
                    if data:
                        descriptor_data[page] = data
                        _LOGGER.debug(
                            "Loaded descriptor %s (%d bytes)", page, len(data)
                        )
                    else:
                        _LOGGER.warning("Failed to load descriptor %s", page)

                    # Small delay between requests
                    await asyncio.sleep(0.1)

                except asyncio.CancelledError:
                    _LOGGER.warning("Request cancelled while loading descriptor %s - skipping", page)
                    continue
                except asyncio.TimeoutError:
                    _LOGGER.warning("Timeout while loading descriptor %s - skipping", page)
                    continue
                except Exception as e:
                    _LOGGER.warning("Error loading descriptor %s: %s - skipping", page, e)
                    continue

            # Parse descriptors to determine entity types
            if descriptor_data:
                self.descriptor_parser = XCCDescriptorParser(ignore_visibility=True)
                self.entity_configs = self.descriptor_parser.parse_descriptor_files(
                    descriptor_data
                )

                # Apply DESCRIPTOR_OVERRIDES — the single source of manual metadata edits.
                # See const.py for the grouping (STATUS_XML_DESCRIPTOR / HIDDEN_SWITCHES /
                # HIDDEN_BINARY_SENSORS). Every entry replaces any descriptor-derived config
                # for that prop because the override table is curated by hand from TRANSF.XSL
                # and field-suffix analysis, while descriptor parsing infers types from
                # register suffixes (e.g. _BOOL_i → switch) which is wrong for read-only
                # status outputs and incomplete for STATUS.XML (no descriptor file exists).
                overridden = 0
                for prop, config in DESCRIPTOR_OVERRIDES.items():
                    if prop in self.entity_configs:
                        overridden += 1
                    self.entity_configs[prop] = config

                _LOGGER.info(
                    "Loaded %d entity configurations from %d descriptor files "
                    "(%d from DESCRIPTOR_OVERRIDES, %d overrides applied)",
                    len(self.entity_configs),
                    len(descriptor_data),
                    len(DESCRIPTOR_OVERRIDES),
                    overridden,
                )

                # Log summary by entity type
                by_type = {}
                for config in self.entity_configs.values():
                    entity_type = config.get("entity_type", "unknown")
                    by_type[entity_type] = by_type.get(entity_type, 0) + 1

                _LOGGER.info("Entity types: %s", by_type)

            self._descriptors_loaded = True

        except Exception as err:
            _LOGGER.error("Failed to load descriptors: %s", err)
            self._descriptors_loaded = True  # Don't retry on every update

    def get_entity_type(self, prop: str) -> str:
        """Get the entity type for a given property with smart matching."""
        if not self.entity_configs:
            return "sensor"  # Default to sensor if no descriptors loaded
        config = lookup_with_normalized_fallback(prop, self.entity_configs)
        return config.get("entity_type", "sensor") if config else "sensor"

    def _normalize_property_name(self, prop: str) -> str:
        """Normalize property names for matching."""
        return normalize_property_name(prop)

    def is_writable(self, prop: str) -> bool:
        """Check if a property is writable with smart matching."""
        if not self.entity_configs:
            return False
        config = lookup_with_normalized_fallback(prop, self.entity_configs)
        return bool(config and config.get("writable", False))

    def get_entity_config(self, prop: str) -> dict:
        """Get the full entity configuration for a property with smart matching."""
        return lookup_with_normalized_fallback(prop, self.entity_configs, default={}) or {}
