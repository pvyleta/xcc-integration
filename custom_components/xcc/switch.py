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
            _LOGGER.info("🏗️ SWITCH ENTITY CREATION: %s", prop)
            _LOGGER.info("   📝 Friendly Name: '%s'", switch.name)
            _LOGGER.info("   🔧 Entity ID: %s", getattr(switch, 'entity_id', 'not_set'))

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

        # Set friendly name using coordinator's language-aware method
        friendly_name = coordinator._get_friendly_name(self._entity_config, self._prop)
        if friendly_name and friendly_name != self._prop:
            self._attr_name = friendly_name
        else:
            self._attr_name = entity_data.get("friendly_name", entity_data.get("name", self._prop))

        # Device info
        self._attr_device_info = coordinator.device_info

    @property
    def is_on(self) -> bool | None:
        """Return True if entity is on."""
        # Get current entity data from coordinator's processed data structure
        entity_id = self._entity_data["entity_id"]

        # Look in the switches dictionary where coordinator stores switch entity data
        switches_data = self.coordinator.data.get("switches", {})
        entity_data = switches_data.get(entity_id)

        if entity_data:
            state = entity_data.get("state", "").lower()
            result = None

            # Handle various boolean representations
            if state in ["1", "true", "on", "yes", "enabled", "active"]:
                result = True
            elif state in ["0", "false", "off", "no", "disabled", "inactive"]:
                result = False
            else:
                # Try to parse as integer
                try:
                    result = int(float(state)) != 0
                except (ValueError, TypeError):
                    result = None

            # Log value updates occasionally to verify regular updates
            if result is not None:
                import random
                if random.random() < 0.05:  # Log ~5% of value retrievals
                    import time
                    timestamp = time.strftime("%H:%M:%S")
                    status_icon = "🟢 ON" if result else "🔴 OFF"
                    _LOGGER.info("📊 ENTITY VALUE UPDATE [%s]: %s = %s (switch from coordinator switches data)",
                               timestamp, self.entity_id, status_icon)

            return result
        else:
            # Fallback: try the entities list (for backward compatibility)
            for entity in self.coordinator.data.get("entities", []):
                if entity.get("entity_id") == entity_id:
                    state = entity.get("state", "").lower()
                    try:
                        result = int(float(state)) != 0 if state not in ["true", "false"] else state == "true"
                        _LOGGER.debug("📊 FALLBACK: Found switch value %s = %s in entities list", entity_id, result)
                        return result
                    except (ValueError, TypeError):
                        return None

        _LOGGER.warning("No data found for switch entity %s in coordinator", entity_id)
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

            _LOGGER.info("🔘 Setting switch %s (%s) to %s", self.name, self._prop, value)

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

        # Add current raw state from switches data
        entity_id = self._entity_data["entity_id"]
        switches_data = self.coordinator.data.get("switches", {})
        entity_data = switches_data.get(entity_id)

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
