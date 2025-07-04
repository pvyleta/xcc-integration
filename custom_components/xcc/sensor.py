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
from .entity import XCCEntity

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)  # Force debug logging for sensor platform

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
    _LOGGER.info("Setting up XCC sensor platform")
    coordinator: XCCDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    # Wait for first data update to ensure descriptors are loaded
    _LOGGER.debug("Waiting for coordinator first refresh")
    await coordinator.async_config_entry_first_refresh()
    _LOGGER.debug("Coordinator data keys: %s", list(coordinator.data.keys()) if coordinator.data else "No data")

    # Create sensor entities from the sensors data structure
    sensors = []

    # Detailed logging of coordinator data structure
    _LOGGER.info("=== SENSOR PLATFORM SETUP DEBUG ===")
    _LOGGER.info("Coordinator data type: %s", type(coordinator.data))
    _LOGGER.info("Coordinator data keys: %s", list(coordinator.data.keys()) if coordinator.data else "No data")

    if coordinator.data:
        for key, value in coordinator.data.items():
            if isinstance(value, dict):
                _LOGGER.info("Data[%s]: %d items", key, len(value))
            else:
                _LOGGER.info("Data[%s]: %s", key, type(value))

    sensor_entities = coordinator.get_entities_by_type("sensor")
    _LOGGER.info("Found %d sensor entities in coordinator.get_entities_by_type('sensor')", len(sensor_entities))

    # Also check the coordinator data structure directly
    sensors_in_data = coordinator.data.get("sensors", {})
    _LOGGER.info("Found %d sensors in coordinator.data['sensors']", len(sensors_in_data))

    if not sensor_entities and not sensors_in_data:
        _LOGGER.warning("No sensor entities found! Checking alternative data structures...")
        # Check if entities are stored differently
        entities_list = coordinator.data.get("entities", [])
        _LOGGER.info("Found %d entities in coordinator.data['entities']", len(entities_list))

        # Try to find sensors in the entities list
        sensor_count = 0
        for entity in entities_list:
            entity_type = entity.get("type", "unknown")
            if entity_type == "sensor":
                sensor_count += 1
        _LOGGER.info("Found %d sensor-type entities in entities list", sensor_count)

    # Use sensors from coordinator.data if available, otherwise use get_entities_by_type
    if sensors_in_data and not sensor_entities:
        _LOGGER.info("Using sensors from coordinator.data['sensors'] instead of get_entities_by_type")
        # Convert the data structure to match what the sensor creation expects
        sensor_entities = {}
        for entity_id, state_data in sensors_in_data.items():
            sensor_entities[entity_id] = state_data
        _LOGGER.info("Converted %d sensors from coordinator data", len(sensor_entities))

    for entity_id, entity_data in sensor_entities.items():
        try:
            _LOGGER.debug("Creating sensor for entity_id: %s", entity_id)
            _LOGGER.debug("Entity data keys: %s", list(entity_data.keys()) if isinstance(entity_data, dict) else "Not a dict")

            # IMPORTANT: Ensure entity_data has entity_id key for sensor initialization
            # The entity_id comes from the dictionary key, but the sensor expects it in the data
            if isinstance(entity_data, dict) and "entity_id" not in entity_data:
                entity_data = dict(entity_data)  # Make a copy to avoid modifying original
                entity_data["entity_id"] = entity_id
                _LOGGER.debug("Added missing entity_id to entity_data for %s", entity_id)

            sensor = XCCSensor(coordinator, entity_data)
            sensors.append(sensor)
            _LOGGER.info("✅ Successfully created sensor: %s (%s)", getattr(sensor, 'name', 'unknown'), entity_id)
        except Exception as err:
            _LOGGER.error("❌ Failed to create sensor for %s: %s", entity_id, err)
            import traceback
            _LOGGER.error("Full traceback: %s", traceback.format_exc())

    _LOGGER.info("=== SENSOR CREATION SUMMARY ===")
    _LOGGER.info("Total sensors created: %d", len(sensors))

    if sensors:
        async_add_entities(sensors)
        _LOGGER.info("✅ Added %d XCC sensor entities to Home Assistant", len(sensors))
    else:
        _LOGGER.error("❌ NO SENSORS CREATED - This is the problem!")
        _LOGGER.error("Coordinator data structure: %s", coordinator.data)


class XCCSensor(XCCEntity, SensorEntity):
    """Representation of an XCC sensor."""

    def __init__(self, coordinator: XCCDataUpdateCoordinator, entity_data: dict[str, Any]) -> None:
        """Initialize the XCC sensor."""
        try:
            # IMPORTANT: entity_id must not be empty - this prevents "Entity data not found for " errors
            entity_id = entity_data.get("entity_id", "")
            if not entity_id:
                # Try to extract from other fields if entity_id is missing
                prop = entity_data.get("prop", "")
                if prop:
                    entity_id = f"xcc_{prop.lower()}"
                    _LOGGER.warning("Missing entity_id in entity_data, generated from prop: %s", entity_id)
                else:
                    raise ValueError(f"No entity_id found in entity_data and no prop to generate from. Data keys: {list(entity_data.keys())}")

            _LOGGER.debug("Initializing XCCSensor for entity_id: %s", entity_id)

            # Create entity description
            description = self._create_entity_description(coordinator, entity_data)

            # Initialize parent class (XCCEntity handles the coordinator and entity setup)
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
        xcc_unit = entity_config.get("unit") or entity_data.get("unit", "")
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

        # Determine state class based on value type and device class
        state_class = None

        # Check if the current value is numeric to determine if we should set a state class
        current_value = entity_data.get("state", "")
        is_numeric = False

        if current_value is not None:
            try:
                # Try to convert to float to check if it's numeric
                float(str(current_value))
                is_numeric = True
            except (ValueError, TypeError):
                is_numeric = False

        # Only set state class for numeric values
        if is_numeric and device_class in STATE_CLASS_MAPPING:
            state_class = STATE_CLASS_MAPPING[device_class]
        elif is_numeric and device_class is None:
            # Default to measurement for numeric values without device class
            state_class = SensorStateClass.MEASUREMENT
        # For non-numeric values (strings, etc.), leave state_class as None

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
        converted_value = self._convert_value_for_ha(raw_value)

        # Log value retrieval for debugging (only occasionally to avoid spam)
        import random
        if random.random() < 0.01:  # Log ~1% of value retrievals
            _LOGGER.debug("🔍 SENSOR VALUE RETRIEVAL: %s = %s (raw: %s)",
                         self.entity_id, converted_value, raw_value)

        return converted_value

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
        attrs = super().extra_state_attributes or {}

        # Safety check for _attributes
        if not hasattr(self, '_attributes') or not isinstance(self._attributes, dict):
            _LOGGER.warning("XCCSensor %s missing or invalid _attributes, returning base attributes only",
                          getattr(self, 'entity_id_suffix', 'unknown'))
            return attrs

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
