"""Number platform for XCC Heat Pump Controller integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.number import (
    NumberEntity,
    NumberMode,
)
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
            _LOGGER.info(
                "🏗️ NUMBER: %s -> '%s' | ID:%s | Range:[%s-%s] Step:%s Unit:%s | Value:%s",
                prop, number.name, getattr(number, 'entity_id', 'not_set').split('.')[-1],
                number.native_min_value, number.native_max_value, number.native_step,
                number.native_unit_of_measurement or "none", number.native_value
            )

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

        # Set friendly name using coordinator's language-aware method
        friendly_name = coordinator._get_friendly_name(self._entity_config, self._prop)
        if friendly_name and friendly_name != self._prop:
            self._attr_name = friendly_name
        else:
            self._attr_name = entity_data.get(
                "friendly_name", entity_data.get("name", self._prop)
            )

        # Set number properties from descriptor with safe defaults
        # Handle None values from descriptor parser when XML doesn't specify min/max
        # Use Python's float limits for unlimited ranges
        import sys

        min_val = self._entity_config.get("min")
        max_val = self._entity_config.get("max")

        # Use full float range when limits are not specified
        self._attr_native_min_value = min_val if min_val is not None else -sys.float_info.max
        self._attr_native_max_value = max_val if max_val is not None else sys.float_info.max
        self._attr_native_step = self._entity_config.get("step", 1.0)

        # Log when using unlimited range for debugging
        if min_val is None or max_val is None:
            _LOGGER.debug(
                "Number entity %s using unlimited range: min=%s->%s, max=%s->%s",
                self.entity_id,
                min_val, "unlimited" if min_val is None else min_val,
                max_val, "unlimited" if max_val is None else max_val
            )

        # Set unit of measurement
        unit = self._entity_config.get("unit_en") or self._entity_config.get("unit", "")
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
                    _LOGGER.info(
                        "📊 ENTITY VALUE UPDATE [%s]: %s = %s (number from coordinator numbers data)",
                        timestamp,
                        self.entity_id,
                        value,
                    )
                return value
            except (ValueError, TypeError):
                _LOGGER.warning(
                    "Could not convert state '%s' to float for number entity %s",
                    state,
                    entity_id,
                )
                return None
        else:
            # Fallback: try the entities list (for backward compatibility)
            for entity in self.coordinator.data.get("entities", []):
                if entity.get("entity_id") == entity_id:
                    state = entity.get("state", "")
                    try:
                        value = float(state)
                        _LOGGER.debug(
                            "📊 FALLBACK: Found number value %s = %s in entities list",
                            entity_id,
                            value,
                        )
                        return value
                    except (ValueError, TypeError):
                        return None

        _LOGGER.warning("No data found for number entity %s in coordinator", entity_id)
        return None

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        try:
            # Validate input value
            if value is None:
                _LOGGER.error("❌ Cannot set number %s: value is None", self.name)
                return

            # Convert float to string for XCC
            str_value = str(value)

            _LOGGER.info(
                "🔢 Setting number %s (%s) to %s", self.name, self._prop, str_value
            )
            _LOGGER.debug("Entity data for %s: %s", self.name, self._entity_data)

            # Validate entity data
            if not self._entity_data:
                _LOGGER.error("❌ Cannot set number %s: no entity data available", self.name)
                return

            entity_id = self._entity_data.get("entity_id")
            if not entity_id:
                _LOGGER.error("❌ Cannot set number %s: no entity_id in entity data", self.name)
                return

            # Use coordinator's set_entity_value method
            _LOGGER.debug("Calling coordinator.async_set_entity_value with entity_id=%s, value=%s", entity_id, str_value)
            success = await self.coordinator.async_set_entity_value(entity_id, str_value)

            if success:
                _LOGGER.info("✅ Successfully set number %s to %s", self.name, value)
                # Note: coordinator already requests refresh, no need to do it again here
            else:
                _LOGGER.error("❌ Failed to set number %s to %s", self.name, value)

        except Exception as err:
            _LOGGER.error("❌ Exception setting number %s to %s: %s", self.name, value, err)
            import traceback
            _LOGGER.debug("Full traceback: %s", traceback.format_exc())

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
