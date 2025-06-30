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
        # Create entity description
        description = self._create_entity_description(coordinator, entity_id)
        super().__init__(coordinator, entity_id, description)

    def _create_entity_description(
        self, coordinator: XCCDataUpdateCoordinator, entity_id: str
    ) -> NumberEntityDescription:
        """Create entity description for the number."""
        entity_data = coordinator.get_entity_data(entity_id)
        if not entity_data:
            raise ValueError(f"Entity data not found for {entity_id}")

        attributes = entity_data["data"].get("attributes", {})
        
        # Get min/max values
        min_value = attributes.get("min_value", 0)
        max_value = attributes.get("max_value", 100)
        step = attributes.get("step", 1)
        
        # Convert to float if needed
        try:
            min_value = float(min_value)
            max_value = float(max_value)
            step = float(step)
        except (ValueError, TypeError):
            min_value = 0.0
            max_value = 100.0
            step = 1.0

        # Determine mode based on step size
        mode = NumberMode.BOX if step < 1 else NumberMode.SLIDER

        return NumberEntityDescription(
            key=entity_id,
            name=self._get_entity_name(),
            native_min_value=min_value,
            native_max_value=max_value,
            native_step=step,
            mode=mode,
        )

    @property
    def native_value(self) -> float | None:
        """Return the native value of the number."""
        raw_value = self._get_current_value()
        converted_value = self._convert_value_for_ha(raw_value)
        
        if converted_value is not None:
            try:
                return float(converted_value)
            except (ValueError, TypeError):
                _LOGGER.warning("Could not convert value %s to float for %s", 
                              converted_value, self.entity_id_suffix)
                return None
        return None

    @property
    def native_min_value(self) -> float:
        """Return the minimum value."""
        if hasattr(self.entity_description, 'native_min_value'):
            return self.entity_description.native_min_value
        return self._attributes.get("min_value", 0.0)

    @property
    def native_max_value(self) -> float:
        """Return the maximum value."""
        if hasattr(self.entity_description, 'native_max_value'):
            return self.entity_description.native_max_value
        return self._attributes.get("max_value", 100.0)

    @property
    def native_step(self) -> float:
        """Return the step value."""
        if hasattr(self.entity_description, 'native_step'):
            return self.entity_description.native_step
        return self._attributes.get("step", 1.0)

    @property
    def mode(self) -> NumberMode:
        """Return the mode."""
        if hasattr(self.entity_description, 'mode'):
            return self.entity_description.mode
        return NumberMode.SLIDER

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the unit of measurement."""
        return self._get_unit_of_measurement()

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        # Validate value is within bounds
        if value < self.native_min_value or value > self.native_max_value:
            _LOGGER.error(
                "Value %s is out of bounds [%s, %s] for %s",
                value, self.native_min_value, self.native_max_value, self.entity_id_suffix
            )
            return

        # Convert to appropriate format for XCC
        xcc_value = self._convert_value_for_xcc(value)
        
        success = await self.async_set_xcc_value(xcc_value)
        if not success:
            _LOGGER.error("Failed to set value %s for number %s", value, self.entity_id_suffix)

    def _convert_value_for_xcc(self, value: float) -> str:
        """Convert Home Assistant value to XCC format."""
        # Check if value should be integer
        if self.native_step >= 1.0 and value == int(value):
            return str(int(value))
        return str(value)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        attrs = super().extra_state_attributes
        
        # Add raw value for debugging
        raw_value = self._get_current_value()
        if raw_value is not None:
            attrs["raw_value"] = raw_value
        
        return attrs
