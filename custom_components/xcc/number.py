"""Number platform for XCC Heat Pump Controller integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.number import NumberEntity, NumberEntityDescription, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import XCCDataUpdateCoordinator
from .entity import XCCEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up XCC number entities from a config entry."""
    coordinator: XCCDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    # Get all number entities from coordinator
    number_entities = coordinator.get_entities_by_type("numbers")
    
    entities = []
    for entity_id, entity_data in number_entities.items():
        try:
            entity = XCCNumber(coordinator, entity_id)
            entities.append(entity)
            _LOGGER.debug("Created number entity: %s", entity_id)
        except Exception as err:
            _LOGGER.error("Error creating number entity %s: %s", entity_id, err)

    if entities:
        async_add_entities(entities)
        _LOGGER.info("Added %d XCC number entities", len(entities))


class XCCNumber(XCCEntity, NumberEntity):
    """Representation of an XCC number."""

    def __init__(self, coordinator: XCCDataUpdateCoordinator, entity_id: str) -> None:
        """Initialize the XCC number."""
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
