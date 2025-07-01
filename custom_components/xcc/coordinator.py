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
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
    DOMAIN,
    XCC_DESCRIPTOR_PAGES,
    XCC_DATA_PAGES,
)

_LOGGER = logging.getLogger(__name__)


class XCCDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the XCC controller."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.entry = entry
        self.ip_address = entry.data[CONF_IP_ADDRESS]
        self.username = entry.data[CONF_USERNAME]
        self.password = entry.data[CONF_PASSWORD]

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

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via library."""
        _LOGGER.debug("Starting data update for XCC controller %s", self.ip_address)
        try:
            # Import XCC client here to avoid import issues
            from .xcc_client import XCCClient, parse_xml_entities
            from .descriptor_parser import XCCDescriptorParser

            # Create or reuse persistent client for session management
            if self._client is None:
                _LOGGER.debug("Creating new XCC client for %s with username %s", self.ip_address, self.username)
                self._client = XCCClient(
                    ip=self.ip_address,
                    username=self.username,
                    password=self.password,
                )
                await self._client.__aenter__()  # Initialize the client
            else:
                _LOGGER.debug("Reusing existing XCC client for %s", self.ip_address)

            client = self._client

            # Load descriptors on first run to determine entity types
            if not self._descriptors_loaded:
                await self._load_descriptors(client)

            # Fetch only data pages (not descriptors)
            _LOGGER.debug("Fetching %d XCC data pages: %s", len(XCC_DATA_PAGES), XCC_DATA_PAGES)
            _LOGGER.debug("Update triggered by: %s", getattr(self, '_update_source', 'unknown'))
            pages_data = await asyncio.wait_for(
                client.fetch_pages(XCC_DATA_PAGES), timeout=DEFAULT_TIMEOUT
            )
            _LOGGER.debug("Successfully fetched %d pages from XCC controller", len(pages_data))

            # Parse entities from all pages
            all_entities = []
            for page_name, xml_content in pages_data.items():
                    if not xml_content.startswith("Error:"):
                        entities = parse_xml_entities(xml_content, page_name)
                        _LOGGER.debug("Parsed %d entities from page %s", len(entities), page_name)
                        all_entities.extend(entities)
                    else:
                        _LOGGER.warning("Error fetching page %s: %s", page_name, xml_content)

            # Process entities and organize data
            _LOGGER.debug("Processing %d total entities from all pages", len(all_entities))
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

            return processed_data

        except asyncio.TimeoutError as err:
            _LOGGER.error("Timeout communicating with XCC controller %s: %s", self.ip_address, err)
            raise UpdateFailed(f"Timeout communicating with XCC controller: {err}") from err
        except Exception as err:
            _LOGGER.error("Error communicating with XCC controller %s: %s", self.ip_address, err)
            if "authentication" in str(err).lower() or "login" in str(err).lower():
                raise ConfigEntryAuthFailed(f"Authentication failed: {err}") from err
            raise UpdateFailed(f"Error communicating with XCC controller: {err}") from err

    def _process_entities(self, entities: list[dict[str, Any]]) -> dict[str, Any]:
        """Process raw entities into organized data structure."""
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

        for entity in entities:
            prop = entity["attributes"]["field_name"]
            entity_type = self.get_entity_type(prop)

            # Debug logging for entity type detection
            if entity_type != "sensor":
                _LOGGER.debug("Entity %s: classified as %s (has descriptor)", prop, entity_type)
            else:
                if prop in self.entity_configs:
                    _LOGGER.debug("Entity %s: has descriptor but classified as sensor", prop)
                else:
                    _LOGGER.debug("Entity %s: no descriptor found, defaulting to sensor", prop)

            # Create entity data structure for new platforms
            entity_data = {
                "entity_id": f"xcc_{prop.lower()}",
                "prop": prop,
                "name": entity["attributes"].get("friendly_name", prop),
                "friendly_name": entity["attributes"].get("friendly_name", prop),
                "state": entity["attributes"].get("value", ""),
                "unit": entity["attributes"].get("unit", ""),
                "page": entity["attributes"].get("page", "unknown"),
            }

            entities_list.append(entity_data)

            # Store entity metadata for later use (keep old format for compatibility)
            self.entities[prop] = {
                "type": entity_type,
                "data": entity,
                "page": entity["attributes"].get("page", "unknown"),
            }

            # Count by entity type for logging
            if entity_type == "switch":
                processed_data["switches"][prop] = entity
            elif entity_type == "number":
                processed_data["numbers"][prop] = entity
            elif entity_type == "select":
                processed_data["selects"][prop] = entity
            elif entity_type == "button":
                processed_data["buttons"][prop] = entity
            else:
                processed_data["sensors"][prop] = entity

        # Store entities list for new platforms
        processed_data["entities"] = entities_list

        # Log final entity distribution
        entity_counts = {
            "switches": len(processed_data["switches"]),
            "numbers": len(processed_data["numbers"]),
            "selects": len(processed_data["selects"]),
            "buttons": len(processed_data["buttons"]),
            "sensors": len(processed_data["sensors"]),
            "total": len(entities_list)
        }
        _LOGGER.info("Final entity distribution: %s", entity_counts)

        return processed_data

    def _determine_entity_type(self, entity: dict[str, Any]) -> str:
        """Determine the appropriate Home Assistant entity type for an XCC entity."""
        attributes = entity.get("attributes", {})
        data_type = attributes.get("data_type", "unknown")
        element_type = attributes.get("element_type", "unknown")
        is_settable = attributes.get("is_settable", False)

        # Determine entity type based on XCC field characteristics
        if data_type == "boolean":
            return "switches" if is_settable else "binary_sensors"
        elif data_type == "enum":
            return "selects" if is_settable else "sensors"
        elif data_type == "numeric":
            return "numbers" if is_settable else "sensors"
        elif element_type in ["INPUT", "SELECT"]:
            return "numbers" if data_type == "numeric" else "selects"
        else:
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
        try:
            # Use the persistent client if available, otherwise create a temporary one
            if self._client is not None:
                client = self._client
            else:
                from .xcc_client import XCCClient
                async with XCCClient(
                    ip=self.ip_address,
                    username=self.username,
                    password=self.password,
                ) as client:
                    # TODO: Implement value setting logic
                    # This would require extending the XCC client to support setting values
                    _LOGGER.warning("Setting values not yet implemented for entity %s", entity_id)
                    return False

            # TODO: Implement value setting logic using persistent client
            # This would require extending the XCC client to support setting values
            _LOGGER.warning("Setting values not yet implemented for entity %s", entity_id)
            return False

        except Exception as err:
            _LOGGER.error("Error setting value for entity %s: %s", entity_id, err)
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

    async def _load_descriptors(self, client: 'XCCClient') -> None:
        """Load descriptor files to determine entity types."""
        try:
            from .descriptor_parser import XCCDescriptorParser
            import asyncio

            _LOGGER.debug("Loading XCC descriptor files for entity type detection")

            # Use the proper descriptor pages from const
            descriptor_data = {}
            for page in XCC_DESCRIPTOR_PAGES:
                try:
                    data = await client.fetch_page(page)
                    if data:
                        descriptor_data[page] = data
                        _LOGGER.debug("Loaded descriptor %s (%d bytes)", page, len(data))
                    else:
                        _LOGGER.warning("Failed to load descriptor %s", page)

                    # Small delay between requests
                    await asyncio.sleep(0.1)

                except Exception as e:
                    _LOGGER.error("Error loading descriptor %s: %s", page, e)

            # Parse descriptors to determine entity types
            if descriptor_data:
                self.descriptor_parser = XCCDescriptorParser()
                self.entity_configs = self.descriptor_parser.parse_descriptor_files(descriptor_data)

                _LOGGER.info("Loaded %d entity configurations from %d descriptor files",
                           len(self.entity_configs), len(descriptor_data))

                # Log summary by entity type
                by_type = {}
                for config in self.entity_configs.values():
                    entity_type = config.get('entity_type', 'unknown')
                    by_type[entity_type] = by_type.get(entity_type, 0) + 1

                _LOGGER.info("Entity types: %s", by_type)

            self._descriptors_loaded = True

        except Exception as err:
            _LOGGER.error("Failed to load descriptors: %s", err)
            self._descriptors_loaded = True  # Don't retry on every update

    def get_entity_type(self, prop: str) -> str:
        """Get the entity type for a given property with smart matching."""
        if not self.entity_configs:
            return 'sensor'  # Default to sensor if no descriptors loaded

        # First try exact match
        config = self.entity_configs.get(prop)
        if config:
            return config.get('entity_type', 'sensor')

        # Try normalized matching (handle different naming conventions)
        normalized_prop = self._normalize_property_name(prop)
        for config_prop, config in self.entity_configs.items():
            if self._normalize_property_name(config_prop) == normalized_prop:
                _LOGGER.debug("Entity %s matched descriptor %s via normalization", prop, config_prop)
                return config.get('entity_type', 'sensor')

        # No match found - default to sensor
        return 'sensor'

    def _normalize_property_name(self, prop: str) -> str:
        """Normalize property names for matching."""
        # Convert to uppercase and replace common separators
        normalized = prop.upper().replace("_", "-").replace(".", "-")

        # Handle common prefixes/suffixes that might differ
        # Remove common prefixes that might be added/removed
        prefixes_to_remove = ["WEB-", "MAIN-", "CONFIG-"]
        for prefix in prefixes_to_remove:
            if normalized.startswith(prefix):
                normalized = normalized[len(prefix):]

        return normalized

    def is_writable(self, prop: str) -> bool:
        """Check if a property is writable with smart matching."""
        if not self.entity_configs:
            return False

        # First try exact match
        config = self.entity_configs.get(prop)
        if config:
            return config.get('writable', False)

        # Try normalized matching
        normalized_prop = self._normalize_property_name(prop)
        for config_prop, config in self.entity_configs.items():
            if self._normalize_property_name(config_prop) == normalized_prop:
                return config.get('writable', False)

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
