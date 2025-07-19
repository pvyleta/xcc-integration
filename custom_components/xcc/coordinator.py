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
    DOMAIN,
    LANGUAGE_ENGLISH,
    XCC_DATA_PAGES,
    XCC_DESCRIPTOR_PAGES,
)

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)  # Force debug logging for coordinator


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

            # Load descriptors on first run to determine entity types
            if not self._descriptors_loaded:
                await self._load_descriptors(client)

            # Fetch only data pages (not descriptors)
            _LOGGER.debug(
                "Fetching %d XCC data pages: %s", len(XCC_DATA_PAGES), XCC_DATA_PAGES
            )
            _LOGGER.debug(
                "Update triggered by: %s", getattr(self, "_update_source", "unknown")
            )
            pages_data = await asyncio.wait_for(
                client.fetch_pages(XCC_DATA_PAGES),
                timeout=DEFAULT_TIMEOUT,
            )
            _LOGGER.debug(
                "Successfully fetched %d pages from XCC controller", len(pages_data)
            )

            # Parse entities from all pages
            all_entities = []
            for page_name, xml_content in pages_data.items():
                if not xml_content.startswith("Error:"):
                    entities = parse_xml_entities(xml_content, page_name)
                    _LOGGER.debug(
                        "Parsed %d entities from page %s", len(entities), page_name
                    )
                    all_entities.extend(entities)
                else:
                    _LOGGER.warning(
                        "Error fetching page %s: %s", page_name, xml_content
                    )

            # Process entities and organize data
            _LOGGER.debug(
                "Processing %d total entities from all pages", len(all_entities)
            )
            processed_data = self._process_entities(all_entities)

            # Log summary of processed data
            entity_counts = {key: len(value) for key, value in processed_data.items()}
            _LOGGER.info("XCC data update successful: %s", entity_counts)

            # Update device info on first successful fetch
            if not self.device_info:
                self.device_info = {
                    "identifiers": {(DOMAIN, self.ip_address)},
                    "name": f"XCC Controller ({self.ip_address})",
                    "manufacturer": "XCC",
                    "model": "Heat Pump Controller",
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
        """Process raw entities into organized data structure with priority-based device assignment."""
        processed_data = {
            "sensors": {},
            "binary_sensors": {},
            "switches": {},
            "numbers": {},
            "selects": {},
            "buttons": {},
            "climates": {},
        }

        # Create entities list for the new platform approach
        entities_list = []

        # Priority-based device assignment: each entity appears only once
        # Priority order (highest to lowest): SPOT, FVE, BIV, OKRUH, TUV1, STAVJED, XCC_HIDDEN_SETTINGS
        device_priority = [
            "SPOT",
            "FVE",
            "BIV",
            "OKRUH",
            "TUV1",
            "STAVJED",
            "XCC_HIDDEN_SETTINGS"  # Special device for entities without descriptors
        ]

        # Track assigned entities to prevent duplicates
        assigned_entities = set()

        # Separate entities with and without descriptors
        entities_with_descriptors = []
        entities_without_descriptors = []

        # Track descriptor stats by page for consolidated logging
        descriptor_stats_by_page = {}

        for entity in entities:
            prop = entity["attributes"]["field_name"]
            page = entity["attributes"].get("page", "unknown")
            has_descriptor = prop in self.entity_configs

            # Track stats by page
            if page not in descriptor_stats_by_page:
                descriptor_stats_by_page[page] = {"with": [], "without": []}

            if has_descriptor:
                entities_with_descriptors.append(entity)
                descriptor_stats_by_page[page]["with"].append(prop)
            else:
                entities_without_descriptors.append(entity)
                descriptor_stats_by_page[page]["without"].append(prop)

        # Log consolidated descriptor stats by page
        _LOGGER.debug("📊 DESCRIPTOR STATS: %d total entities, %d configs available", len(entities), len(self.entity_configs))
        for page, stats in descriptor_stats_by_page.items():
            with_count = len(stats["with"])
            without_count = len(stats["without"])
            if with_count > 0 and without_count > 0:
                _LOGGER.debug("📄 %s: ✅%d WITH | ❌%d WITHOUT descriptors", page, with_count, without_count)
            elif with_count > 0:
                _LOGGER.debug("📄 %s: ✅%d WITH descriptors", page, with_count)
            elif without_count > 0:
                _LOGGER.debug("📄 %s: ❌%d WITHOUT descriptors", page, without_count)

        # Group entities with descriptors by page/device for priority processing
        entities_by_page = {}
        _LOGGER.debug("🔍 PAGE GROUPING DEBUG:")

        for entity in entities_with_descriptors:
            page = entity["attributes"].get("page", "unknown").upper()
            prop = entity["attributes"]["field_name"]
            # Normalize page names (remove numbers and .XML extension)
            page_normalized = page.replace("1.XML", "").replace("10.XML", "").replace("11.XML", "").replace("4.XML", "").replace(".XML", "")

            _LOGGER.debug("   Entity %s: page='%s' -> normalized='%s'", prop, page, page_normalized)

            if page_normalized not in entities_by_page:
                entities_by_page[page_normalized] = []
            entities_by_page[page_normalized].append(entity)

        # Add entities without descriptors to hidden settings device
        if entities_without_descriptors:
            entities_by_page["XCC_HIDDEN_SETTINGS"] = entities_without_descriptors
            _LOGGER.debug("   Added %d entities to XCC_HIDDEN_SETTINGS", len(entities_without_descriptors))

        _LOGGER.debug("📊 PAGE GROUPING RESULTS:")
        for page_name, page_entities in entities_by_page.items():
            _LOGGER.debug("   %s: %d entities", page_name, len(page_entities))

        _LOGGER.info("🏗️ PRIORITY-BASED DEVICE ASSIGNMENT")
        _LOGGER.info("   Device priority order: %s", " > ".join(device_priority))
        _LOGGER.info("   Pages found: %s", list(entities_by_page.keys()))

        # Process entities in priority order
        for device_name in device_priority:
            if device_name not in entities_by_page:
                _LOGGER.debug("   📄 %s: No entities found", device_name)
                continue

            device_entities = entities_by_page[device_name]
            assigned_count = 0
            skipped_count = 0

            for entity in device_entities:
                prop = entity["attributes"]["field_name"]

                # Skip if entity already assigned to higher priority device
                if prop in assigned_entities:
                    skipped_count += 1
                    continue

                # Mark entity as assigned
                assigned_entities.add(prop)
                assigned_count += 1

                entity_type = self.get_entity_type(prop)

                # Only log missing descriptors once per entity to avoid spam
                if entity_type == "sensor" and prop not in self.entity_configs:
                    if not hasattr(self, "_logged_missing_descriptors"):
                        self._logged_missing_descriptors = set()

                    if prop not in self._logged_missing_descriptors:
                        _LOGGER.debug(
                            "Entity %s: no descriptor found, defaulting to sensor", prop
                        )
                        self._logged_missing_descriptors.add(prop)

                # Get descriptor information for this entity
                descriptor_config = self.entity_configs.get(prop, {})

                # Use descriptor friendly name based on language preference
                friendly_name = self._get_friendly_name(descriptor_config, prop)

                unit = descriptor_config.get("unit") or entity["attributes"].get("unit", "")

                # Create entity data structure for new platforms with device assignment
                # Ensure proper entity ID formatting with xcc_ prefix and valid characters
                entity_id_suffix = self._format_entity_id(prop)
                entity_data = {
                    "entity_id": f"xcc_{entity_id_suffix}",
                    "prop": prop,
                    "name": friendly_name,
                    "friendly_name": friendly_name,
                    "state": entity["attributes"].get("value", ""),
                    "unit": unit,
                    "page": entity["attributes"].get("page", "unknown"),
                    "device": device_name,  # Add device assignment
                }

                entities_list.append(entity_data)

                # Store entity metadata for later use (use entity_id as key for proper lookup)
                self.entities[entity_data["entity_id"]] = {
                    "type": entity_type,
                    "data": entity,
                    "page": entity["attributes"].get("page", "unknown"),
                    "prop": prop,  # Keep prop for reference
                    "descriptor_config": descriptor_config,  # Include descriptor config for platforms
                    "device": device_name,  # Add device assignment
                }

                # Create state data structure that entities can use to retrieve values
                # This is the key fix - store data in the format that _get_current_value expects
                # IMPORTANT: Extract state from the correct field - entities have "state", not "value" in attributes
                state_value = entity.get("state", "")

                # IMPORTANT: Define entity_id BEFORE using it in logging to avoid UnboundLocalError
                entity_id = entity_data["entity_id"]

                state_data = {
                    "state": state_value,
                    "attributes": entity["attributes"],
                    "entity_id": entity_id,
                    "prop": prop,
                    "name": friendly_name,  # Use enhanced friendly name
                    "unit": unit,  # Use enhanced unit from descriptor
                    "page": entity["attributes"].get("page", "unknown"),
                    "device": device_name,  # Add device assignment
                }

                # Store in processed_data with the correct structure for entity value retrieval
                if entity_type == "switch":
                    processed_data["switches"][entity_id] = state_data
                elif entity_type == "number":
                    processed_data["numbers"][entity_id] = state_data
                elif entity_type == "select":
                    processed_data["selects"][entity_id] = state_data
                elif entity_type == "button":
                    processed_data["buttons"][entity_id] = state_data
                else:
                    processed_data["sensors"][entity_id] = state_data

            # Log device assignment summary
            _LOGGER.info("   📄 %s: Assigned %d entities, skipped %d duplicates", device_name, assigned_count, skipped_count)



        # Store entities list for new platforms
        processed_data["entities"] = entities_list

        # Log final entity distribution with detailed breakdown
        entity_counts = {
            "switches": len(processed_data["switches"]),
            "numbers": len(processed_data["numbers"]),
            "selects": len(processed_data["selects"]),
            "buttons": len(processed_data["buttons"]),
            "sensors": len(processed_data["sensors"]),
            "total": len(entities_list),
        }
        _LOGGER.info("=== COORDINATOR ENTITY PROCESSING COMPLETE ===")
        _LOGGER.info("Final entity distribution: %s", entity_counts)

        # Print current values for all entity types
        self._print_entity_values(processed_data)

        # Log data structure that will be returned
        _LOGGER.info(
            "Returning processed_data with keys: %s", list(processed_data.keys())
        )

        return processed_data

    def _format_entity_id(self, prop: str) -> str:
        """Format XCC property name into valid Home Assistant entity ID suffix."""
        # Convert to lowercase and replace invalid characters with underscores
        entity_id = prop.lower()

        # Replace common XCC separators with underscores
        entity_id = entity_id.replace("-", "_")
        entity_id = entity_id.replace(".", "_")
        entity_id = entity_id.replace(" ", "_")

        # Remove any characters that aren't alphanumeric or underscore
        import re
        entity_id = re.sub(r'[^a-z0-9_]', '_', entity_id)

        # Remove multiple consecutive underscores
        entity_id = re.sub(r'_+', '_', entity_id)

        # Remove leading/trailing underscores
        entity_id = entity_id.strip('_')

        # Ensure it's not empty
        if not entity_id:
            entity_id = "unknown"

        return entity_id

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
        # Device names and descriptions
        device_configs = {
            "SPOT": {"name": "Spot Prices", "model": "Energy Market Data"},
            "FVE": {"name": "Solar PV System", "model": "Photovoltaic Controller"},
            "BIV": {"name": "Heat Pump", "model": "Bivalent Heat Pump"},
            "OKRUH": {"name": "Heating Circuits", "model": "Heating Zone Controller"},
            "TUV1": {"name": "Hot Water System", "model": "Domestic Hot Water"},
            "STAVJED": {"name": "Unit Status", "model": "System Status Monitor"},
            "XCC_HIDDEN_SETTINGS": {"name": "Hidden Settings", "model": "Advanced Configuration"},
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

    def _print_entity_values(self, processed_data: dict[str, Any]) -> None:
        """Print current values for all entity types in an organized way."""
        _LOGGER.info("=== CURRENT ENTITY VALUES ===")

        # Define the order and display names for entity types
        entity_type_info = {
            "sensors": ("📊 SENSORS", "°C", "W", "kWh", "V", "A", "bar"),
            "binary_sensors": ("🔘 BINARY SENSORS", "ON", "OFF"),
            "switches": ("🔄 SWITCHES", "ON", "OFF"),
            "numbers": ("🔢 NUMBERS", ""),
            "selects": ("📋 SELECTS", ""),
            "buttons": ("🔲 BUTTONS", ""),
            "climates": ("🌡️ CLIMATES", "°C"),
        }

        total_entities = 0

        for entity_type, (display_name, *unit_examples) in entity_type_info.items():
            entities = processed_data.get(entity_type, {})
            if not entities:
                continue

            total_entities += len(entities)
            _LOGGER.info("%s (%d entities):", display_name, len(entities))

            # Sort entities by name for consistent output
            sorted_entities = sorted(entities.items(), key=lambda x: x[0])

            # Print first 10 entities of each type to avoid log spam
            for i, (entity_id, entity_data) in enumerate(sorted_entities[:10]):
                state = entity_data.get("state", "unknown")
                unit = entity_data.get("unit", "")
                prop = entity_data.get("prop", entity_id)
                page = entity_data.get("page", "unknown")

                # Format the value display
                if unit:
                    value_display = f"{state} {unit}"
                else:
                    value_display = str(state)

                # Special formatting for boolean values
                if entity_type in ["binary_sensors", "switches"]:
                    if str(state).lower() in ["1", "true", "on"]:
                        value_display = "🟢 ON"
                    elif str(state).lower() in ["0", "false", "off"]:
                        value_display = "🔴 OFF"
                    else:
                        value_display = f"❓ {state}"

                # Add timestamp to show this is fresh data
                import time

                timestamp = time.strftime("%H:%M:%S")
                _LOGGER.info(
                    "  %2d. %-25s = %-15s [%s] (%s)",
                    i + 1,
                    prop,
                    value_display,
                    timestamp,
                    page,
                )

            # Show count if there are more entities
            if len(sorted_entities) > 10:
                _LOGGER.info(
                    "  ... and %d more %s", len(sorted_entities) - 10, entity_type
                )

            _LOGGER.info("")  # Empty line for readability

        if total_entities == 0:
            _LOGGER.warning(
                "❌ NO ENTITIES FOUND - This indicates a problem with entity processing!"
            )
        else:
            _LOGGER.info("✅ Total entities processed: %d", total_entities)

        _LOGGER.info("=== END ENTITY VALUES ===")

    async def async_force_update(self) -> None:
        """Force an immediate update of all entity values."""
        _LOGGER.info("🔄 FORCING IMMEDIATE COORDINATOR UPDATE")
        self._update_source = "force_update"
        await self.async_request_refresh()

    def _determine_entity_type(self, entity: dict[str, Any]) -> str:
        """Determine the appropriate Home Assistant entity type for an XCC entity."""
        attributes = entity.get("attributes", {})
        data_type = attributes.get("data_type", "unknown")
        element_type = attributes.get("element_type", "unknown")
        is_settable = attributes.get("is_settable", False)

        # Determine entity type based on XCC field characteristics
        if data_type == "boolean":
            return "switches" if is_settable else "binary_sensors"
        if data_type == "enum":
            return "selects" if is_settable else "sensors"
        if data_type == "numeric":
            return "numbers" if is_settable else "sensors"
        if element_type in ["INPUT", "SELECT"]:
            return "numbers" if data_type == "numeric" else "selects"
        return "sensors"

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

            # Find the entity configuration to get the property name
            prop = None
            search_methods = []

            # Method 1: Try to find the property in the coordinator's entity data
            for entity_type in ["numbers", "switches", "selects"]:
                entities_data = self.data.get(entity_type, {})
                if entity_id in entities_data:
                    entity_data = entities_data[entity_id]
                    # Look for prop in the attributes
                    prop = entity_data.get("attributes", {}).get("prop")
                    if prop:
                        search_methods.append(f"found in {entity_type} data")
                        break

            # Method 2: If not found in type-specific data, try the general entities list
            if not prop:
                for entity in self.data.get("entities", []):
                    if entity.get("entity_id") == entity_id:
                        prop = entity.get("prop", "").upper()
                        if prop:
                            search_methods.append("found in general entities list")
                            break

            # Method 3: Try entity configs (descriptor data)
            if not prop:
                # Look for the property in entity_configs by matching entity_id patterns
                entity_suffix = entity_id.replace("number.xcc_", "").replace("switch.xcc_", "").replace("select.xcc_", "")
                for config_prop, config in self.entity_configs.items():
                    if config_prop.lower() == entity_suffix.upper():
                        prop = config_prop
                        search_methods.append("found in entity configs")
                        break

            # Method 4: If still not found, try to derive from entity_id
            if not prop:
                # Remove common prefixes and convert to uppercase
                prop = (
                    entity_id.replace("number.xcc_", "")
                    .replace("switch.xcc_", "")
                    .replace("select.xcc_", "")
                )
                prop = (
                    prop.replace("number.", "")
                    .replace("switch.", "")
                    .replace("select.", "")
                )
                prop = prop.upper()
                search_methods.append("derived from entity_id")

            if not prop:
                _LOGGER.error(
                    "❌ Could not determine property name for entity %s. Tried methods: %s",
                    entity_id, ", ".join(search_methods) if search_methods else "none"
                )
                _LOGGER.debug("Available entity types in data: %s", list(self.data.keys()))
                _LOGGER.debug("Available entity configs: %d properties", len(self.entity_configs))
                return False

            _LOGGER.debug("🔍 Property resolution: %s -> %s (method: %s)",
                         entity_id, prop, search_methods[-1] if search_methods else "unknown")

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
                    success = await client.set_value(prop, value)
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
                        success = await client.set_value(prop, value)
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

    async def _load_descriptors(self, client: XCCClient) -> None:
        """Load descriptor files to determine entity types."""
        try:
            import asyncio

            from .descriptor_parser import XCCDescriptorParser

            _LOGGER.debug("Loading XCC descriptor files for entity type detection")

            # Use the proper descriptor pages from const
            descriptor_data = {}
            for page in XCC_DESCRIPTOR_PAGES:
                try:
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

                except Exception as e:
                    _LOGGER.error("Error loading descriptor %s: %s", page, e)

            # Parse descriptors to determine entity types
            if descriptor_data:
                self.descriptor_parser = XCCDescriptorParser()
                self.entity_configs = self.descriptor_parser.parse_descriptor_files(
                    descriptor_data
                )

                _LOGGER.info(
                    "Loaded %d entity configurations from %d descriptor files",
                    len(self.entity_configs),
                    len(descriptor_data),
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

        # First try exact match
        config = self.entity_configs.get(prop)
        if config:
            return config.get("entity_type", "sensor")

        # Try normalized matching (handle different naming conventions)
        normalized_prop = self._normalize_property_name(prop)
        for config_prop, config in self.entity_configs.items():
            if self._normalize_property_name(config_prop) == normalized_prop:
                return config.get("entity_type", "sensor")

        # No match found - default to sensor
        return "sensor"

    def _normalize_property_name(self, prop: str) -> str:
        """Normalize property names for matching."""
        # Convert to uppercase and replace common separators
        normalized = prop.upper().replace("_", "-").replace(".", "-")

        # Handle common prefixes/suffixes that might differ
        # Remove common prefixes that might be added/removed
        prefixes_to_remove = ["WEB-", "MAIN-", "CONFIG-"]
        for prefix in prefixes_to_remove:
            if normalized.startswith(prefix):
                normalized = normalized[len(prefix) :]

        return normalized

    def is_writable(self, prop: str) -> bool:
        """Check if a property is writable with smart matching."""
        if not self.entity_configs:
            return False

        # First try exact match
        config = self.entity_configs.get(prop)
        if config:
            return config.get("writable", False)

        # Try normalized matching
        normalized_prop = self._normalize_property_name(prop)
        for config_prop, config in self.entity_configs.items():
            if self._normalize_property_name(config_prop) == normalized_prop:
                return config.get("writable", False)

        return False

    def get_entity_config(self, prop: str) -> dict:
        """Get the full entity configuration for a property with smart matching."""
        # First try exact match
        config = self.entity_configs.get(prop)
        if config:
            return config

        # Try normalized matching
        normalized_prop = self._normalize_property_name(prop)
        for config_prop, config in self.entity_configs.items():
            if self._normalize_property_name(config_prop) == normalized_prop:
                return config

        return {}
