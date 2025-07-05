"""Switch platform for XCC Heat Pump Controller integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
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
    """Set up XCC switch entities from a config entry."""
    coordinator: XCCDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    # Wait for first data update to ensure descriptors are loaded
    await coordinator.async_config_entry_first_refresh()

    # Create switch entities for all writable switch properties
    switches = []
    for entity_data in coordinator.data.get("entities", []):
        prop = entity_data.get("prop", "").upper()
        entity_type = coordinator.get_entity_type(prop)

        if entity_type == "switch" and coordinator.is_writable(prop):
            switch = XCCSwitch(coordinator, entity_data)
            switches.append(switch)
            _LOGGER.debug("Created switch entity: %s (%s)", switch.name, prop)

    if switches:
        async_add_entities(switches)
        _LOGGER.info("Added %d XCC switch entities", len(switches))


class XCCSwitch(CoordinatorEntity[XCCDataUpdateCoordinator], SwitchEntity):
    """Representation of an XCC switch."""

    def __init__(
        self,
        coordinator: XCCDataUpdateCoordinator,
        entity_data: dict[str, Any],
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)

        self._entity_data = entity_data
        self._prop = entity_data.get("prop", "").upper()
        self._entity_config = coordinator.get_entity_config(self._prop)

        # Generate entity ID and unique ID
        # Normalize entity_id to avoid duplicates (replace hyphens with underscores)
        normalized_entity_id = entity_data['entity_id'].replace('-', '_')
        self._attr_unique_id = f"{coordinator.ip_address}_{normalized_entity_id}"
        self.entity_id = f"switch.{normalized_entity_id}"

        # Set friendly name from descriptor or fallback to entity data
        friendly_name = self._entity_config.get('friendly_name_en') or self._entity_config.get('friendly_name')
        if friendly_name:
            self._attr_name = friendly_name
        else:
            self._attr_name = entity_data.get("friendly_name", entity_data.get("name", self._prop))

        # Device info
        self._attr_device_info = coordinator.device_info

    @property
    def is_on(self) -> bool | None:
        """Return True if entity is on."""
        # Find current entity data in coordinator
        for entity in self.coordinator.data.get("entities", []):
            if entity.get("entity_id") == self._entity_data["entity_id"]:
                state = entity.get("state", "").lower()
                # Handle various boolean representations
                if state in ["1", "true", "on", "yes", "enabled", "active"]:
                    return True
                elif state in ["0", "false", "off", "no", "disabled", "inactive"]:
                    return False
                else:
                    # Try to parse as integer
                    try:
                        return int(float(state)) != 0
                    except (ValueError, TypeError):
                        return None
        return None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        await self._async_set_state(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        await self._async_set_state(False)

    async def _async_set_state(self, state: bool) -> None:
        """Set the switch state."""
        try:
            # Convert boolean to appropriate value for XCC
            value = "1" if state else "0"

            _LOGGER.debug("Setting switch %s (%s) to %s", self.name, self._prop, value)

            # Use coordinator's set_entity_value method
            success = await self.coordinator.async_set_entity_value(
                self._entity_data["entity_id"],
                value
            )

            if success:
                _LOGGER.info("Successfully set switch %s to %s", self.name, "ON" if state else "OFF")
                # Request immediate data refresh to update state
                await self.coordinator.async_request_refresh()
            else:
                _LOGGER.error("Failed to set switch %s to %s", self.name, "ON" if state else "OFF")

        except Exception as err:
            _LOGGER.error("Error setting switch %s: %s", self.name, err)

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

        # Add current raw state
        for entity in self.coordinator.data.get("entities", []):
            if entity.get("entity_id") == self._entity_data["entity_id"]:
                attributes["raw_state"] = entity.get("state", "Unknown")
                break

        return attributes
