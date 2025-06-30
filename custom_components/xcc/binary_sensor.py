"""Binary sensor platform for XCC Heat Pump Controller integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
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
    """Set up XCC binary sensor entities from a config entry."""
    coordinator: XCCDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    # Get all binary sensor entities from coordinator
    binary_sensor_entities = coordinator.get_entities_by_type("binary_sensors")

    entities = []
    for entity_id, entity_data in binary_sensor_entities.items():
        try:
            entity = XCCBinarySensor(coordinator, entity_id)
            entities.append(entity)
            _LOGGER.debug("Created binary sensor entity: %s", entity_id)
        except Exception as err:
            _LOGGER.error("Error creating binary sensor entity %s: %s", entity_id, err)

    if entities:
        async_add_entities(entities)
        _LOGGER.info("Added %d XCC binary sensor entities", len(entities))


class XCCBinarySensor(XCCEntity, BinarySensorEntity):
    """Representation of an XCC binary sensor."""

    def __init__(self, coordinator: XCCDataUpdateCoordinator, entity_id: str) -> None:
        """Initialize the XCC binary sensor."""
        # Create entity description
        description = self._create_entity_description(coordinator, entity_id)
        super().__init__(coordinator, entity_id, description)

    def _create_entity_description(
        self, coordinator: XCCDataUpdateCoordinator, entity_id: str
    ) -> BinarySensorEntityDescription:
        """Create entity description for the binary sensor."""
        entity_data = coordinator.get_entity_data(entity_id)
        if not entity_data:
            raise ValueError(f"Entity data not found for {entity_id}")

        # Determine device class from field name patterns
        device_class = self._determine_device_class(entity_id)

        return BinarySensorEntityDescription(
            key=entity_id,
            name=self._get_entity_name(),
            device_class=device_class,
        )

    def _determine_device_class(self, entity_id: str) -> BinarySensorDeviceClass | None:
        """Determine device class from entity ID and attributes."""
        field_name_lower = entity_id.lower()

        # Map common field patterns to device classes
        if any(pattern in field_name_lower for pattern in ["alarm", "error", "chyba", "porucha"]):
            return BinarySensorDeviceClass.PROBLEM
        elif any(pattern in field_name_lower for pattern in ["running", "bezi", "chod", "provoz"]):
            return BinarySensorDeviceClass.RUNNING
        elif any(pattern in field_name_lower for pattern in ["heat", "teplo", "ohrev"]):
            return BinarySensorDeviceClass.HEAT
        elif any(pattern in field_name_lower for pattern in ["cool", "chlad"]):
            return BinarySensorDeviceClass.COLD
        elif any(pattern in field_name_lower for pattern in ["power", "napajeni", "vykon"]):
            return BinarySensorDeviceClass.POWER
        elif any(pattern in field_name_lower for pattern in ["connect", "pripoj", "online"]):
            return BinarySensorDeviceClass.CONNECTIVITY
        elif any(pattern in field_name_lower for pattern in ["door", "dvere", "cover", "kryt"]):
            return BinarySensorDeviceClass.DOOR
        elif any(pattern in field_name_lower for pattern in ["window", "okno"]):
            return BinarySensorDeviceClass.WINDOW
        elif any(pattern in field_name_lower for pattern in ["motion", "pohyb"]):
            return BinarySensorDeviceClass.MOTION
        elif any(pattern in field_name_lower for pattern in ["occupancy", "pritomnost"]):
            return BinarySensorDeviceClass.OCCUPANCY
        elif any(pattern in field_name_lower for pattern in ["safety", "bezpecnost"]):
            return BinarySensorDeviceClass.SAFETY

        # Default to None (generic binary sensor)
        return None

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        raw_value = self._get_current_value()
        return self._convert_value_for_ha(raw_value)

    @property
    def device_class(self) -> BinarySensorDeviceClass | None:
        """Return the device class."""
        if hasattr(self.entity_description, 'device_class'):
            return self.entity_description.device_class
        return self._get_device_class()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        attrs = super().extra_state_attributes

        # Add raw value for debugging
        raw_value = self._get_current_value()
        if raw_value is not None:
            attrs["raw_value"] = raw_value

        return attrs
