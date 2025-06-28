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
    XCC_PAGES,
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
        self._client = None

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via library."""
        try:
            # Import XCC client here to avoid import issues
            from xcc_client import XCCClient, parse_xml_entities

            async with XCCClient(
                ip=self.ip_address,
                username=self.username,
                password=self.password,
            ) as client:
                # Fetch all XCC pages
                pages_data = await asyncio.wait_for(
                    client.fetch_pages(XCC_PAGES), timeout=DEFAULT_TIMEOUT
                )

                # Parse entities from all pages
                all_entities = []
                for page_name, xml_content in pages_data.items():
                    if not xml_content.startswith("Error:"):
                        entities = parse_xml_entities(xml_content, page_name)
                        all_entities.extend(entities)

                # Process entities and organize data
                processed_data = self._process_entities(all_entities)
                
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
            raise UpdateFailed(f"Timeout communicating with XCC controller: {err}") from err
        except Exception as err:
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
            "climates": {},
        }

        for entity in entities:
            entity_id = entity["attributes"]["field_name"]
            entity_type = self._determine_entity_type(entity)
            
            # Store entity metadata for later use
            self.entities[entity_id] = {
                "type": entity_type,
                "data": entity,
                "page": entity["attributes"].get("page", "unknown"),
            }

            # Add to appropriate category
            if entity_type in processed_data:
                processed_data[entity_type][entity_id] = entity

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
            from xcc_client import XCCClient

            async with XCCClient(
                ip=self.ip_address,
                username=self.username,
                password=self.password,
            ) as client:
                # TODO: Implement value setting logic
                # This would require extending the XCC client to support setting values
                _LOGGER.warning("Setting values not yet implemented for entity %s", entity_id)
                return False

        except Exception as err:
            _LOGGER.error("Error setting value for entity %s: %s", entity_id, err)
            return False
