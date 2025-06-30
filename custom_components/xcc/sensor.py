"""Sensor platform for XCC Heat Pump Controller integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfPressure,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import XCCDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

# Unit mapping from XCC to Home Assistant
UNIT_MAPPING = {
    "°C": UnitOfTemperature.CELSIUS,
    "K": UnitOfTemperature.KELVIN,
    "%": PERCENTAGE,
    "W": UnitOfPower.WATT,
    "kW": UnitOfPower.KILO_WATT,
    "kWh": UnitOfEnergy.KILO_WATT_HOUR,
    "V": UnitOfElectricPotential.VOLT,
    "A": UnitOfElectricCurrent.AMPERE,
    "Hz": UnitOfFrequency.HERTZ,
    "bar": UnitOfPressure.BAR,
    "Pa": "Pa",  # Pascal not available in this HA version
    "s": UnitOfTime.SECONDS,
    "min": UnitOfTime.MINUTES,
    "h": UnitOfTime.HOURS,
}

# Device class mapping based on unit or field name patterns
DEVICE_CLASS_MAPPING = {
    UnitOfTemperature.CELSIUS: SensorDeviceClass.TEMPERATURE,
    UnitOfTemperature.KELVIN: SensorDeviceClass.TEMPERATURE,
    UnitOfPower.WATT: SensorDeviceClass.POWER,
    UnitOfPower.KILO_WATT: SensorDeviceClass.POWER,
    UnitOfEnergy.KILO_WATT_HOUR: SensorDeviceClass.ENERGY,
    UnitOfElectricPotential.VOLT: SensorDeviceClass.VOLTAGE,
    UnitOfElectricCurrent.AMPERE: SensorDeviceClass.CURRENT,
    UnitOfFrequency.HERTZ: SensorDeviceClass.FREQUENCY,
    UnitOfPressure.BAR: SensorDeviceClass.PRESSURE,
    "Pa": SensorDeviceClass.PRESSURE,  # Pascal not available in this HA version
    PERCENTAGE: SensorDeviceClass.POWER_FACTOR,  # For efficiency percentages
}

# State class mapping
STATE_CLASS_MAPPING = {
    SensorDeviceClass.TEMPERATURE: SensorStateClass.MEASUREMENT,
    SensorDeviceClass.POWER: SensorStateClass.MEASUREMENT,
    SensorDeviceClass.ENERGY: SensorStateClass.TOTAL_INCREASING,
    SensorDeviceClass.VOLTAGE: SensorStateClass.MEASUREMENT,
    SensorDeviceClass.CURRENT: SensorStateClass.MEASUREMENT,
    SensorDeviceClass.FREQUENCY: SensorStateClass.MEASUREMENT,
    SensorDeviceClass.PRESSURE: SensorStateClass.MEASUREMENT,
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up XCC sensor entities from a config entry."""
    coordinator: XCCDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    # Wait for first data update to ensure descriptors are loaded
    await coordinator.async_config_entry_first_refresh()

    # Create sensor entities for read-only properties only
    sensors = []
    for entity_data in coordinator.data.get("entities", []):
        prop = entity_data.get("prop", "").upper()
        entity_type = coordinator.get_entity_type(prop)

        # Only create sensors for read-only entities or entities that don't have specific platforms
        if entity_type == "sensor" or not coordinator.is_writable(prop):
            sensor = XCCSensor(coordinator, entity_data)
            sensors.append(sensor)
            _LOGGER.debug("Created sensor entity: %s (%s)", sensor.name, prop)

    if sensors:
        async_add_entities(sensors)
        _LOGGER.info("Added %d XCC sensor entities", len(sensors))


class XCCSensor(CoordinatorEntity[XCCDataUpdateCoordinator], SensorEntity):
    """Representation of an XCC sensor."""

    def __init__(self, coordinator: XCCDataUpdateCoordinator, entity_data: dict[str, Any]) -> None:
        """Initialize the XCC sensor."""
        try:
            entity_id = entity_data.get("entity_id", "")
            _LOGGER.debug("Initializing XCCSensor for entity_id: %s", entity_id)

            # Create entity description
            description = self._create_entity_description(coordinator, entity_data)
            _LOGGER.debug("Created entity description for %s", entity_id)

            # Initialize parent class
            super().__init__(coordinator, entity_id, description)
            _LOGGER.debug("Successfully initialized XCCSensor for %s", entity_id)

        except Exception as err:
            _LOGGER.error("Error in XCCSensor.__init__ for %s: %s", entity_data.get("entity_id", "unknown"), err)
            raise

    def _create_entity_description(
        self, coordinator: XCCDataUpdateCoordinator, entity_data: dict[str, Any]
    ) -> SensorEntityDescription:
        """Create entity description for the sensor."""
        entity_id = entity_data.get("entity_id", "")
        prop = entity_data.get("prop", "").upper()

        # Get entity config from descriptors
        entity_config = coordinator.get_entity_config(prop)

        # Get unit from descriptor or entity data
        xcc_unit = unit or entity_data.get("unit", "")
        ha_unit = UNIT_MAPPING.get(xcc_unit, xcc_unit) if xcc_unit else None

        # Determine device class
        device_class = None
        if ha_unit in DEVICE_CLASS_MAPPING:
            device_class = DEVICE_CLASS_MAPPING[ha_unit]
        else:
            # Try to determine device class from field name patterns
            field_name_lower = entity_id.lower()
            if "temp" in field_name_lower or "teplota" in field_name_lower:
                device_class = SensorDeviceClass.TEMPERATURE
            elif "power" in field_name_lower or "vykon" in field_name_lower:
                device_class = SensorDeviceClass.POWER
            elif "energy" in field_name_lower or "energie" in field_name_lower:
                device_class = SensorDeviceClass.ENERGY
            elif "voltage" in field_name_lower or "napeti" in field_name_lower:
                device_class = SensorDeviceClass.VOLTAGE
            elif "current" in field_name_lower or "proud" in field_name_lower:
                device_class = SensorDeviceClass.CURRENT
            elif "pressure" in field_name_lower or "tlak" in field_name_lower:
                device_class = SensorDeviceClass.PRESSURE

        # Determine state class
        state_class = None
        if device_class in STATE_CLASS_MAPPING:
            state_class = STATE_CLASS_MAPPING[device_class]
        else:
            # Default to measurement for numeric values
            state_class = SensorStateClass.MEASUREMENT

        # Get entity name from descriptor or entity data
        friendly_name = entity_config.get('friendly_name_en') or entity_config.get('friendly_name')
        if friendly_name:
            entity_name = friendly_name
        else:
            entity_name = entity_data.get("friendly_name", entity_data.get("name", prop))

        return SensorEntityDescription(
            key=entity_id,
            name=entity_name,
            native_unit_of_measurement=ha_unit,
            device_class=device_class,
            state_class=state_class,
        )

    @property
    def native_value(self) -> Any:
        """Return the native value of the sensor."""
        raw_value = self._get_current_value()
        return self._convert_value_for_ha(raw_value)

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the unit of measurement."""
        if hasattr(self.entity_description, 'native_unit_of_measurement'):
            return self.entity_description.native_unit_of_measurement
        return self._get_unit_of_measurement()

    @property
    def state_class(self) -> SensorStateClass | None:
        """Return the state class."""
        if hasattr(self.entity_description, 'state_class'):
            return self.entity_description.state_class
        return self._get_state_class()

    @property
    def device_class(self) -> SensorDeviceClass | None:
        """Return the device class."""
        if hasattr(self.entity_description, 'device_class'):
            return self.entity_description.device_class
        return self._get_device_class()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        attrs = super().extra_state_attributes

        # Safety check for _attributes
        if not hasattr(self, '_attributes') or not isinstance(self._attributes, dict):
            _LOGGER.warning("XCCSensor %s missing or invalid _attributes, returning base attributes only",
                          getattr(self, 'entity_id_suffix', 'unknown'))
            return attrs or {}

        # Add enum option text for enum sensors
        if self._attributes.get("data_type") == "enum":
            current_value = str(self.native_value)
            for option in self._attributes.get("options", []):
                if option["value"] == current_value:
                    # Add localized option text
                    hass_language = self.hass.config.language if self.hass else "en"
                    if hass_language.startswith("cs") or hass_language.startswith("cz"):
                        option_text = option.get("text", option.get("text_en", ""))
                    else:
                        option_text = option.get("text_en", option.get("text", ""))

                    if option_text:
                        attrs["option_text"] = option_text
                    break

        return attrs
