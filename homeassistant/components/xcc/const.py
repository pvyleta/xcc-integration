"""Constants for the XCC Heat Pump Controller integration."""

from __future__ import annotations

from typing import Final

# Integration domain
DOMAIN: Final = "xcc"
VERSION: Final = "1.5.5"  # Integration version for debugging

# Configuration constants
CONF_IP_ADDRESS: Final = "ip_address"
CONF_USERNAME: Final = "username"
CONF_PASSWORD: Final = "password"
CONF_SCAN_INTERVAL: Final = "scan_interval"
CONF_ENTITY_TYPE: Final = "entity_type"

# Default values
DEFAULT_USERNAME: Final = "xcc"
DEFAULT_PASSWORD: Final = "xcc"
DEFAULT_SCAN_INTERVAL: Final = 30  # seconds
DEFAULT_TIMEOUT: Final = 10  # seconds

# Entity type options
ENTITY_TYPE_INTEGRATION: Final = "integration"
ENTITY_TYPE_MQTT: Final = "mqtt"
DEFAULT_ENTITY_TYPE: Final = ENTITY_TYPE_MQTT

# Device information
MANUFACTURER: Final = "XCC"
MODEL: Final = "Heat Pump Controller"

# Entity categories
ENTITY_CATEGORY_CONFIG: Final = "config"
ENTITY_CATEGORY_DIAGNOSTIC: Final = "diagnostic"

# MQTT constants
MQTT_DISCOVERY_PREFIX: Final = "homeassistant"
MQTT_DEVICE_PREFIX: Final = "xcc"

# Update intervals
UPDATE_INTERVAL_FAST: Final = 30  # seconds - for frequently changing values
UPDATE_INTERVAL_SLOW: Final = 300  # seconds - for configuration values

# Entity platforms supported
PLATFORMS: Final = [
    "sensor",
    "binary_sensor", 
    "switch",
    "number",
    "select",
    "climate",
]

# XCC specific constants
XCC_PAGES: Final = [
    "stavjed.xml", "STAVJED1.XML",  # Status
    "okruh.xml", "OKRUH10.XML",     # Heating circuits  
    "tuv1.xml", "TUV11.XML",        # Hot water
    "biv.xml", "BIV1.XML",          # Bivalent heating
    "fve.xml", "FVE4.XML",          # Photovoltaics
    "spot.xml", "SPOT1.XML",        # Spot pricing
]

# Entity types mapping
ENTITY_TYPE_MAPPING: Final = {
    "numeric": "number",
    "enum": "select", 
    "boolean": "switch",
    "readonly": "sensor",
    "status": "binary_sensor",
}

# Device classes for sensors
DEVICE_CLASS_TEMPERATURE: Final = "temperature"
DEVICE_CLASS_PRESSURE: Final = "pressure"
DEVICE_CLASS_POWER: Final = "power"
DEVICE_CLASS_ENERGY: Final = "energy"
DEVICE_CLASS_VOLTAGE: Final = "voltage"
DEVICE_CLASS_CURRENT: Final = "current"
DEVICE_CLASS_FREQUENCY: Final = "frequency"

# Units of measurement
UNIT_CELSIUS: Final = "°C"
UNIT_KELVIN: Final = "K"
UNIT_PERCENT: Final = "%"
UNIT_WATT: Final = "W"
UNIT_KILOWATT: Final = "kW"
UNIT_KILOWATT_HOUR: Final = "kWh"
UNIT_VOLT: Final = "V"
UNIT_AMPERE: Final = "A"
UNIT_HERTZ: Final = "Hz"
UNIT_BAR: Final = "bar"
UNIT_PASCAL: Final = "Pa"
UNIT_SECONDS: Final = "s"
UNIT_MINUTES: Final = "min"
UNIT_HOURS: Final = "h"

# State classes
STATE_CLASS_MEASUREMENT: Final = "measurement"
STATE_CLASS_TOTAL: Final = "total"
STATE_CLASS_TOTAL_INCREASING: Final = "total_increasing"
