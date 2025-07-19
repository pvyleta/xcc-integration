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
    _LOGGER.debug(
        "Coordinator data keys: %s",
        list(coordinator.data.keys()) if coordinator.data else "No data",
    )

    # Create sensor entities from the sensors data structure
    sensors = []

    # Detailed logging of coordinator data structure
    _LOGGER.info("=== SENSOR PLATFORM SETUP DEBUG ===")
    _LOGGER.info("Coordinator data type: %s", type(coordinator.data))
    _LOGGER.info(
        "Coordinator data keys: %s",
        list(coordinator.data.keys()) if coordinator.data else "No data",
    )

    if coordinator.data:
        for key, value in coordinator.data.items():
            if isinstance(value, dict):
                _LOGGER.info("Data[%s]: %d items", key, len(value))
            else:
                _LOGGER.info("Data[%s]: %s", key, type(value))

    sensor_entities = coordinator.get_entities_by_type("sensor")
    _LOGGER.info(
        "Found %d sensor entities in coordinator.get_entities_by_type('sensor')",
        len(sensor_entities),
    )

    # Also check the coordinator data structure directly
    sensors_in_data = coordinator.data.get("sensors", {})
    _LOGGER.info(
        "Found %d sensors in coordinator.data['sensors']", len(sensors_in_data)
    )

    if not sensor_entities and not sensors_in_data:
        _LOGGER.warning(
            "No sensor entities found! Checking alternative data structures..."
        )
        # Check if entities are stored differently
        entities_list = coordinator.data.get("entities", [])
        _LOGGER.info(
            "Found %d entities in coordinator.data['entities']", len(entities_list)
        )

        # Try to find sensors in the entities list
        sensor_count = 0
        for entity in entities_list:
            entity_type = entity.get("type", "unknown")
            if entity_type == "sensor":
                sensor_count += 1
        _LOGGER.info("Found %d sensor-type entities in entities list", sensor_count)

    # Use sensors from coordinator.data if available, otherwise use get_entities_by_type
    if sensors_in_data and not sensor_entities:
        _LOGGER.info(
            "Using sensors from coordinator.data['sensors'] instead of get_entities_by_type"
        )
        # Convert the data structure to match what the sensor creation expects
        sensor_entities = {}
        for entity_id, state_data in sensors_in_data.items():
            sensor_entities[entity_id] = state_data
        _LOGGER.info("Converted %d sensors from coordinator data", len(sensor_entities))

    for entity_id, entity_data in sensor_entities.items():
        try:
            _LOGGER.debug("🔧 Creating sensor: %s | Keys: %s", entity_id,
                         list(entity_data.keys()) if isinstance(entity_data, dict) else "Not a dict")

            # IMPORTANT: Ensure entity_data has entity_id key for sensor initialization
            # The entity_id comes from the dictionary key, but the sensor expects it in the data
            if isinstance(entity_data, dict) and "entity_id" not in entity_data:
                entity_data = dict(
                    entity_data
                )  # Make a copy to avoid modifying original
                entity_data["entity_id"] = entity_id


            sensor = XCCSensor(coordinator, entity_data)
            sensors.append(sensor)
            _LOGGER.info(
                "✅ Successfully created sensor: %s (%s)",
                getattr(sensor, "name", "unknown"),
                entity_id,
            )
        except Exception as err:
            # Use locals().get() to safely access entity_id in case it's not defined
            entity_id_safe = locals().get('entity_id', 'unknown')
            _LOGGER.error("❌ Failed to create sensor for %s: %s", entity_id_safe, err)
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

    def __init__(
        self, coordinator: XCCDataUpdateCoordinator, entity_data: dict[str, Any]
    ) -> None:
        """Initialize the XCC sensor."""
        try:
            # IMPORTANT: entity_id must not be empty - this prevents "Entity data not found for " errors
            entity_id = entity_data.get("entity_id", "")
            if not entity_id:
                # Try to extract from other fields if entity_id is missing
                prop = entity_data.get("prop", "")
                if prop:
                    # Format entity ID properly with xcc_ prefix
                    entity_id_suffix = self._format_entity_id_suffix(prop)
                    entity_id = f"xcc_{entity_id_suffix}"
                    _LOGGER.warning(
                        "Missing entity_id in entity_data, generated from prop: %s",
                        entity_id,
                    )
                else:
                    raise ValueError(
                        f"No entity_id found in entity_data and no prop to generate from. Data keys: {list(entity_data.keys())}"
                    )



            # Create entity description
            description = self._create_entity_description(coordinator, entity_data)

            # Initialize parent class (XCCEntity handles the coordinator and entity setup)
            super().__init__(coordinator, entity_id, description)


        except Exception as err:
            _LOGGER.error(
                "Error in XCCSensor.__init__ for %s: %s",
                entity_data.get("entity_id", "unknown"),
                err,
            )
            raise

    def _format_entity_id_suffix(self, prop: str) -> str:
        """Format XCC property name into valid Home Assistant entity ID suffix."""
        # Convert to lowercase and replace invalid characters with underscores
        entity_id = prop.lower()

        # Replace common XCC separators with underscores
        entity_id = entity_id.replace("-", "_")
        entity_id = entity_id.replace(".", "_")
        entity_id = entity_id.replace(" ", "_")

        # Remove any characters that aren't alphanumeric or underscore
        import re
        entity_id = re.sub(r'[^a-z0-9_]', '_', entity_id)

        # Remove multiple consecutive underscores
        entity_id = re.sub(r'_+', '_', entity_id)

        # Remove leading/trailing underscores
        entity_id = entity_id.strip('_')

        # Ensure it's not empty
        if not entity_id:
            entity_id = "unknown"

        return entity_id

    def _create_entity_description(
        self,
        coordinator: XCCDataUpdateCoordinator,
        entity_data: dict[str, Any],
    ) -> SensorEntityDescription:
        """Create entity description for the sensor."""
        entity_id = entity_data.get("entity_id", "")
        prop = entity_data.get("prop", "").upper()

        # Get entity config from descriptors
        entity_config = coordinator.get_entity_config(prop)

        # Get unit from descriptor or entity data
        xcc_unit = entity_config.get("unit") or entity_data.get("unit", "")
        ha_unit = UNIT_MAPPING.get(xcc_unit, xcc_unit) if xcc_unit else None

        # Determine device class - prioritize descriptor information
        device_class = None

        # First, check if descriptor provides device class
        descriptor_device_class = entity_config.get("device_class")
        if descriptor_device_class:
            # Map string device class to HA device class enum
            device_class_mapping = {
                "temperature": SensorDeviceClass.TEMPERATURE,
                "power": SensorDeviceClass.POWER,
                "energy": SensorDeviceClass.ENERGY,
                "voltage": SensorDeviceClass.VOLTAGE,
                "current": SensorDeviceClass.CURRENT,
                "frequency": SensorDeviceClass.FREQUENCY,
                "pressure": SensorDeviceClass.PRESSURE,
            }
            device_class = device_class_mapping.get(descriptor_device_class)
            _LOGGER.debug(
                "Using device class from descriptor for %s: %s -> %s",
                prop,
                descriptor_device_class,
                device_class,
            )

        # Second, try unit-based device class
        elif ha_unit in DEVICE_CLASS_MAPPING:
            device_class = DEVICE_CLASS_MAPPING[ha_unit]
            _LOGGER.debug(
                "Using device class from unit for %s: %s -> %s",
                prop,
                ha_unit,
                device_class,
            )
        else:
            # Fallback: Try to determine device class from field name patterns
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

            if device_class:
                _LOGGER.debug(
                    "Using device class from field name pattern for %s: %s",
                    prop,
                    device_class,
                )

        # Determine state class based on device class and data type hints
        state_class = None

        # Get XML name for type analysis (used in multiple places)
        xml_name = entity_data.get("attributes", {}).get("name", "") or "unknown"

        # First, check if we have a device class mapping
        if device_class in STATE_CLASS_MAPPING:
            state_class = STATE_CLASS_MAPPING[device_class]
        else:
            # Use data type hints from XML to determine if this should be numeric

            # Check descriptor information for data type
            descriptor_data_type = entity_config.get("data_type", "")

            # Look for clear indicators of string types
            is_clearly_string = (
                "STRING" in xml_name.upper()
                or "TIME" in xml_name.upper()  # Time values like "03:00"
                or "_s" in xml_name  # String suffix
                or "Thh:mm" in xml_name  # Time format indicator
                or descriptor_data_type == "time"  # From descriptor parser
                or prop
                in [
                    "SNAZEV1",
                    "SNAZEV2",
                    "DEVICE_NAME",
                    "LOCATION",
                ]  # Known string fields
            )

            # Look for clear indicators of boolean types (should not have state class)
            is_clearly_boolean = (
                "BOOL" in xml_name.upper()
                or "_BOOL_" in xml_name.upper()
                or prop in [
                    "SZAPNUTO",  # Known boolean system status
                    "ENABLED",
                    "ACTIVE",
                    "STATUS",
                ]  # Known boolean fields
                or (
                    # Check if current value is clearly boolean (0/1 only)
                    entity_data.get("state", "") in ["0", "1", 0, 1]
                    and xml_name.endswith("_i")  # Integer type but likely boolean
                    and len(str(entity_data.get("state", ""))) == 1  # Single digit
                )
            )

            # Look for clear indicators of numeric types (should have state class)
            is_clearly_numeric = (
                "REAL" in xml_name.upper()
                or "INT" in xml_name.upper()
                or "FLOAT" in xml_name.upper()
                or "_f" in xml_name  # Float suffix
                or ("_i" in xml_name and not is_clearly_boolean)  # Integer suffix but not boolean
                or ".1f" in xml_name  # Float format
                or prop
                in [
                    "SVENKU",
                    "TEMPERATURE",
                    "TEMP",
                    "PRESSURE",
                    "POWER",
                ]  # Known numeric fields
            )

            if is_clearly_string or is_clearly_boolean:
                # Definitely a string or boolean sensor - no state class
                state_class = None
                if is_clearly_boolean:
                    _LOGGER.debug(
                        "Entity %s identified as boolean, no state class assigned", prop
                    )
            elif is_clearly_numeric or device_class is not None:
                # Likely numeric or has device class - default to measurement
                state_class = SensorStateClass.MEASUREMENT
            else:
                # Unknown type - check current value as fallback, but be more careful
                current_value = entity_data.get("state", "")
                if current_value is not None:
                    try:
                        numeric_value = float(str(current_value))
                        # Check if this looks like a boolean disguised as numeric
                        if str(current_value) in ["0", "1", "0.0", "1.0"] and xml_name.endswith("_i"):
                            # Likely a boolean value - no state class
                            state_class = None
                            _LOGGER.debug(
                                "Entity %s appears to be boolean (value=%s), no state class assigned",
                                prop, current_value
                            )
                        else:
                            # Current value is numeric and not boolean - probably should have state class
                            state_class = SensorStateClass.MEASUREMENT
                    except (ValueError, TypeError):
                        # Current value is not numeric - no state class
                        state_class = None

        # Get entity name using coordinator's language-aware method
        entity_name = coordinator._get_friendly_name(entity_config, prop)
        if not entity_name or entity_name == prop:
            entity_name = entity_data.get(
                "friendly_name", entity_data.get("name", prop)
            )

        # Debug logging for language preference
        friendly_name_en = entity_config.get("friendly_name_en")
        friendly_name_cs = entity_config.get("friendly_name")
        if friendly_name_cs and friendly_name_en and friendly_name_en != friendly_name_cs:
            _LOGGER.debug(
                "Sensor %s: Using language-aware name '%s' (Czech: '%s', English: '%s')",
                prop,
                entity_name,
                friendly_name_cs,
                friendly_name_en,
            )

        # Log comprehensive entity creation details
        # Ensure xml_name is always defined for logging
        safe_xml_name = locals().get('xml_name', 'undefined')

        _LOGGER.info(
            "🏗️ SENSOR: %s -> '%s' | ID:%s | Class:%s/%s Unit:%s | Value:%s",
            prop, entity_name, entity_id.split('.')[-1], device_class or "none",
            state_class or "none", ha_unit or "none", entity_data.get("state", "N/A")
        )

        # Special logging for entities that might cause state class issues
        if prop in ["SZAPNUTO"] or (safe_xml_name != 'undefined' and "BOOL" in safe_xml_name.upper()):
            _LOGGER.info(
                "🔍 Boolean entity %s: state_class=%s, xml_name=%s, value=%s",
                prop,
                state_class,
                safe_xml_name,
                entity_data.get("state", "N/A"),
            )

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
            _LOGGER.debug(
                "🔍 SENSOR VALUE RETRIEVAL: %s = %s (raw: %s)",
                self.entity_id,
                converted_value,
                raw_value,
            )

        return converted_value

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the unit of measurement."""
        if hasattr(self.entity_description, "native_unit_of_measurement"):
            return self.entity_description.native_unit_of_measurement
        return self._get_unit_of_measurement()

    @property
    def state_class(self) -> SensorStateClass | None:
        """Return the state class."""
        if hasattr(self.entity_description, "state_class"):
            return self.entity_description.state_class
        return self._get_state_class()

    @property
    def device_class(self) -> SensorDeviceClass | None:
        """Return the device class."""
        if hasattr(self.entity_description, "device_class"):
            return self.entity_description.device_class
        return self._get_device_class()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        attrs = super().extra_state_attributes or {}

        # Safety check for _attributes
        if not hasattr(self, "_attributes") or not isinstance(self._attributes, dict):
            _LOGGER.warning(
                "XCCSensor %s missing or invalid _attributes, returning base attributes only",
                getattr(self, "entity_id_suffix", "unknown"),
            )
            return attrs

        # Add enum option text for enum sensors
        if self._attributes.get("data_type") == "enum":
            current_value = str(self.native_value)
            for option in self._attributes.get("options", []):
                if option["value"] == current_value:
                    # Always prefer English option text
                    option_text = option.get("text_en", option.get("text", ""))

                    if option_text:
                        attrs["option_text"] = option_text
                    break

        return attrs
