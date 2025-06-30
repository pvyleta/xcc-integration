"""Select platform for XCC Heat Pump Controller integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import XCCDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up XCC select entities from a config entry."""
    coordinator: XCCDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    # Wait for first data update to ensure descriptors are loaded
    await coordinator.async_config_entry_first_refresh()

    # Create select entities for all writable select properties
    selects = []
    for entity_data in coordinator.data.get("entities", []):
        prop = entity_data.get("prop", "").upper()
        entity_type = coordinator.get_entity_type(prop)

        if entity_type == "select" and coordinator.is_writable(prop):
            select = XCCSelect(coordinator, entity_data)
            selects.append(select)
            _LOGGER.debug("Created select entity: %s (%s)", select.name, prop)

    if selects:
        async_add_entities(selects)
        _LOGGER.info("Added %d XCC select entities", len(selects))


class XCCSelect(CoordinatorEntity[XCCDataUpdateCoordinator], SelectEntity):
    """Representation of an XCC select."""

    def __init__(
        self,
        coordinator: XCCDataUpdateCoordinator,
        entity_data: dict[str, Any],
    ) -> None:
        """Initialize the select."""
        super().__init__(coordinator)

        self._entity_data = entity_data
        self._prop = entity_data.get("prop", "").upper()
        self._entity_config = coordinator.get_entity_config(self._prop)

        # Generate entity ID and unique ID
        self._attr_unique_id = f"{coordinator.ip_address}_{entity_data['entity_id']}"
        self.entity_id = f"select.{entity_data['entity_id']}"

        # Set friendly name from descriptor or fallback to entity data
        friendly_name = self._entity_config.get('friendly_name_en') or self._entity_config.get('friendly_name')
        if friendly_name:
            self._attr_name = friendly_name
        else:
            self._attr_name = entity_data.get("friendly_name", entity_data.get("name", self._prop))

        # Set options from descriptor
        options = self._entity_config.get('options', [])
        if options:
            # Use English text if available, otherwise use regular text
            self._attr_options = [
                opt.get('text_en', opt.get('text', opt.get('value', '')))
                for opt in options
            ]
            # Create mapping from display text to values
            self._option_to_value = {
                opt.get('text_en', opt.get('text', opt.get('value', ''))): opt.get('value', '')
                for opt in options
            }
            self._value_to_option = {v: k for k, v in self._option_to_value.items()}
        else:
            self._attr_options = []
            self._option_to_value = {}
            self._value_to_option = {}

        # Device info
        self._attr_device_info = coordinator.device_info

    @property
    def current_option(self) -> str | None:
        """Return the selected entity option."""
        # Find current entity data in coordinator
        for entity in self.coordinator.data.get("entities", []):
            if entity.get("entity_id") == self._entity_data["entity_id"]:
                state = entity.get("state", "")
                # Convert XCC value to display option
                return self._value_to_option.get(state, state)
        return None

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        try:
            # Convert display option to XCC value
            value = self._option_to_value.get(option, option)

            _LOGGER.debug("Setting select %s (%s) to %s (value: %s)", self.name, self._prop, option, value)

            # Use coordinator's set_entity_value method
            success = await self.coordinator.async_set_entity_value(
                self._entity_data["entity_id"],
                value
            )

            if success:
                _LOGGER.info("Successfully set select %s to %s", self.name, option)
                # Request immediate data refresh to update state
                await self.coordinator.async_request_refresh()
            else:
                _LOGGER.error("Failed to set select %s to %s", self.name, option)

        except Exception as err:
            _LOGGER.error("Error setting select %s: %s", self.name, err)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional state attributes."""
        attributes = {}

        # Add property name for debugging
        attributes["prop"] = self._prop
        attributes["page"] = self._entity_config.get("page", "Unknown")

        # Add options information
        attributes["available_options"] = self._attr_options

        # Add current raw state
        for entity in self.coordinator.data.get("entities", []):
            if entity.get("entity_id") == self._entity_data["entity_id"]:
                attributes["raw_state"] = entity.get("state", "Unknown")
                break

        return attributes
