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
            _LOGGER.info(
                "🏗️ SELECT: %s -> '%s' | ID:%s | Options:%s | Value:%s",
                prop, select.name, getattr(select, 'entity_id', 'not_set').split('.')[-1],
                select.options, select.current_option
            )

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

        # Generate entity ID and unique ID with proper xcc_ prefix
        base_entity_id = entity_data['entity_id']

        # Ensure xcc_ prefix is present
        if not base_entity_id.startswith('xcc_'):
            base_entity_id = f"xcc_{base_entity_id}"

        self._attr_unique_id = f"{coordinator.ip_address}_{base_entity_id}"
        self.entity_id = f"select.{base_entity_id}"

        # Set friendly name using coordinator's language-aware method
        friendly_name = coordinator._get_friendly_name(self._entity_config, self._prop)
        if friendly_name and friendly_name != self._prop:
            self._attr_name = friendly_name
        else:
            self._attr_name = entity_data.get("friendly_name", entity_data.get("name", self._prop))

        # Set options from descriptor using language-aware selection
        options = self._entity_config.get('options', [])
        if options:
            # Use coordinator's language preference for option text
            self._attr_options = []
            self._option_to_value = {}

            for opt in options:
                # Get localized option text using coordinator's language preference
                if coordinator.language == "en":
                    # English preference: text_en -> text -> value
                    option_text = opt.get('text_en', opt.get('text', opt.get('value', '')))
                else:
                    # Czech preference: text -> text_en -> value
                    option_text = opt.get('text', opt.get('text_en', opt.get('value', '')))

                self._attr_options.append(option_text)
                self._option_to_value[option_text] = opt.get('value', '')

            self._value_to_option = {v: k for k, v in self._option_to_value.items()}

            # Debug logging for enum options
            _LOGGER.debug(
                "🔍 SELECT OPTIONS: %s -> %s (language: %s)",
                self._prop, self._attr_options, coordinator.language
            )
        else:
            self._attr_options = []
            self._option_to_value = {}
            self._value_to_option = {}

        # Device info
        self._attr_device_info = coordinator.device_info

    @property
    def current_option(self) -> str | None:
        """Return the selected entity option."""
        # Get current entity data from coordinator's processed data structure
        entity_id = self._entity_data["entity_id"]

        # Look in the selects dictionary where coordinator stores select entity data
        selects_data = self.coordinator.data.get("selects", {})
        entity_data = selects_data.get(entity_id)

        if entity_data:
            state = entity_data.get("state", "")
            # Convert XCC value to display option
            return self._value_to_option.get(state, state)
        else:
            # Fallback: try the entities list (for backward compatibility)
            for entity in self.coordinator.data.get("entities", []):
                if entity.get("entity_id") == entity_id:
                    state = entity.get("state", "")
                    return self._value_to_option.get(state, state)

        _LOGGER.warning("No data found for select entity %s in coordinator", entity_id)
        return None

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        try:
            # Convert display option to XCC value
            value = self._option_to_value.get(option, option)

            _LOGGER.info("📋 Setting select %s (%s) to %s (value: %s)", self.name, self._prop, option, value)

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

        # Add current raw state from selects data
        entity_id = self._entity_data["entity_id"]
        selects_data = self.coordinator.data.get("selects", {})
        entity_data = selects_data.get(entity_id)

        if entity_data:
            attributes["raw_state"] = entity_data.get("state", "Unknown")
        else:
            # Fallback to entities list
            for entity in self.coordinator.data.get("entities", []):
                if entity.get("entity_id") == entity_id:
                    attributes["raw_state"] = entity.get("state", "Unknown")
                    break
            else:
                attributes["raw_state"] = "Unknown"

        return attributes
