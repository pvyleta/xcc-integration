"""Number platform for XCC Heat Pump Controller integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.number import NumberEntity, NumberEntityDescription, NumberMode
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
    """Set up XCC number entities from a config entry."""
    coordinator: XCCDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    # Wait for first data update to ensure descriptors are loaded
    await coordinator.async_config_entry_first_refresh()

    # Create number entities for all writable number properties
    numbers = []
    for entity_data in coordinator.data.get("entities", []):
        prop = entity_data.get("prop", "").upper()
        entity_type = coordinator.get_entity_type(prop)

        if entity_type == "number" and coordinator.is_writable(prop):
            number = XCCNumber(coordinator, entity_data)
            numbers.append(number)
            _LOGGER.debug("Created number entity: %s (%s)", number.name, prop)

    if numbers:
        async_add_entities(numbers)
        _LOGGER.info("Added %d XCC number entities", len(numbers))


class XCCNumber(CoordinatorEntity[XCCDataUpdateCoordinator], NumberEntity):
    """Representation of an XCC number."""

    def __init__(
        self,
        coordinator: XCCDataUpdateCoordinator,
        entity_data: dict[str, Any],
    ) -> None:
        """Initialize the number."""
        super().__init__(coordinator)

        self._entity_data = entity_data
        self._prop = entity_data.get("prop", "").upper()
        self._entity_config = coordinator.get_entity_config(self._prop)

        # Generate entity ID and unique ID
        self._attr_unique_id = f"{coordinator.ip_address}_{entity_data['entity_id']}"
        self.entity_id = f"number.{entity_data['entity_id']}"

        # Set friendly name from descriptor or fallback to entity data
        friendly_name = self._entity_config.get('friendly_name_en') or self._entity_config.get('friendly_name')
        if friendly_name:
            self._attr_name = friendly_name
        else:
            self._attr_name = entity_data.get("friendly_name", entity_data.get("name", self._prop))

        # Set number properties from descriptor
        self._attr_native_min_value = self._entity_config.get('min', 0)
        self._attr_native_max_value = self._entity_config.get('max', 100)
        self._attr_native_step = self._entity_config.get('step', 1.0)

        # Set unit of measurement
        unit = self._entity_config.get('unit_en') or self._entity_config.get('unit', '')
        if unit:
            self._attr_native_unit_of_measurement = unit

        # Set mode based on step size
        if self._attr_native_step >= 1:
            self._attr_mode = NumberMode.BOX
        else:
            self._attr_mode = NumberMode.SLIDER

        # Device info
        self._attr_device_info = coordinator.device_info

    @property
    def native_value(self) -> float | None:
        """Return the entity value."""
        # Get current entity data from coordinator's processed data structure
        entity_id = self._entity_data["entity_id"]

        # Look in the numbers dictionary where coordinator stores number entity data
        numbers_data = self.coordinator.data.get("numbers", {})
        entity_data = numbers_data.get(entity_id)

        if entity_data:
            state = entity_data.get("state", "")
            try:
                value = float(state)
                # Log value updates occasionally to verify regular updates
                import random
                if random.random() < 0.05:  # Log ~5% of value retrievals
                    import time
                    timestamp = time.strftime("%H:%M:%S")
                    _LOGGER.info("📊 ENTITY VALUE UPDATE [%s]: %s = %s (number from coordinator numbers data)",
                               timestamp, self.entity_id, value)
                return value
            except (ValueError, TypeError):
                _LOGGER.warning("Could not convert state '%s' to float for number entity %s", state, entity_id)
                return None
        else:
            # Fallback: try the entities list (for backward compatibility)
            for entity in self.coordinator.data.get("entities", []):
                if entity.get("entity_id") == entity_id:
                    state = entity.get("state", "")
                    try:
                        value = float(state)
                        _LOGGER.debug("📊 FALLBACK: Found number value %s = %s in entities list", entity_id, value)
                        return value
                    except (ValueError, TypeError):
                        return None

        _LOGGER.warning("No data found for number entity %s in coordinator", entity_id)
        return None

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        try:
            # Convert float to string for XCC
            str_value = str(value)

            _LOGGER.info("🔢 Setting number %s (%s) to %s", self.name, self._prop, str_value)

            # Use coordinator's set_entity_value method
            success = await self.coordinator.async_set_entity_value(
                self._entity_data["entity_id"],
                str_value
            )

            if success:
                _LOGGER.info("Successfully set number %s to %s", self.name, value)
                # Request immediate data refresh to update state
                await self.coordinator.async_request_refresh()
            else:
                _LOGGER.error("Failed to set number %s to %s", self.name, value)

        except Exception as err:
            _LOGGER.error("Error setting number %s: %s", self.name, err)

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

        # Add range information
        attributes["min_value"] = self._attr_native_min_value
        attributes["max_value"] = self._attr_native_max_value
        attributes["step"] = self._attr_native_step

        # Add current raw state from numbers data
        entity_id = self._entity_data["entity_id"]
        numbers_data = self.coordinator.data.get("numbers", {})
        entity_data = numbers_data.get(entity_id)

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
