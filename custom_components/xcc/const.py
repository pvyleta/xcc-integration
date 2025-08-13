"""Constants for the XCC Heat Pump Controller integration."""

from __future__ import annotations

import json
import os
from typing import Final

# Integration domain
DOMAIN: Final = "xcc"


def get_version() -> str:
    """Get version from manifest.json."""
    try:
        manifest_path = os.path.join(os.path.dirname(__file__), "manifest.json")
        with open(manifest_path) as f:
            manifest = json.load(f)
            return manifest.get("version", "unknown")
    except Exception:
        return "unknown"


# Get version from manifest.json automatically
VERSION: Final = get_version()

# Configuration constants
CONF_IP_ADDRESS: Final = "ip_address"
CONF_USERNAME: Final = "username"
CONF_PASSWORD: Final = "password"
CONF_SCAN_INTERVAL: Final = "scan_interval"
CONF_ENTITY_TYPE: Final = "entity_type"
CONF_LANGUAGE: Final = "language"

# Default values
DEFAULT_USERNAME: Final = "xcc"
DEFAULT_PASSWORD: Final = "xcc"
DEFAULT_SCAN_INTERVAL: Final = 120  # seconds (2 minutes)
DEFAULT_TIMEOUT: Final = 10  # seconds

# Language options
LANGUAGE_ENGLISH: Final = "english"
LANGUAGE_CZECH: Final = "czech"
DEFAULT_LANGUAGE: Final = LANGUAGE_ENGLISH

# Visibility handling options
CONF_IGNORE_VISIBILITY: Final = "ignore_visibility_conditions"
DEFAULT_IGNORE_VISIBILITY: Final = False

# Entity type options
ENTITY_TYPE_INTEGRATION: Final = "integration"
DEFAULT_ENTITY_TYPE: Final = ENTITY_TYPE_INTEGRATION

# Device information
MANUFACTURER: Final = "XCC"
MODEL: Final = "Heat Pump Controller"

# Entity categories
ENTITY_CATEGORY_CONFIG: Final = "config"
ENTITY_CATEGORY_DIAGNOSTIC: Final = "diagnostic"


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
# Descriptor files (only fetched once during setup)
XCC_DESCRIPTOR_PAGES: Final = [
    "stavjed.xml",  # Status descriptor
    "okruh.xml",  # Heating circuits descriptor
    "tuv1.xml",  # Hot water descriptor
    "biv.xml",  # Bivalent heating descriptor
    "fve.xml",  # Photovoltaics descriptor
    "spot.xml",  # Spot pricing descriptor
]

# Data files (fetched on every update)
XCC_DATA_PAGES: Final = [
    "STAVJED1.XML",  # Status data
    "OKRUH10.XML",  # Heating circuits data
    "TUV11.XML",  # Hot water data
    "BIV1.XML",  # Bivalent heating data
    "FVE4.XML",  # Photovoltaics data
    "SPOT1.XML",  # Spot pricing data
]

# Legacy combined list (for backward compatibility)
XCC_PAGES: Final = XCC_DESCRIPTOR_PAGES + XCC_DATA_PAGES

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
