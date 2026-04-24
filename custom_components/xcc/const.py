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
    "fveinv.xml",  # PV Inverter descriptor
    "spot.xml",  # Spot pricing descriptor
    # Note: nast.xml (Heat pump settings) is added dynamically if accessible
]

# Data files (fetched on every update)
XCC_DATA_PAGES: Final = [
    "STAVJED1.XML",  # Heat pump unit status
    "STATUS.XML",   # Main-page status summary (31 fields not present in STAVJED1.XML)
    "OKRUH10.XML",  # Heating circuits data
    "TUV11.XML",  # Hot water data
    "BIV1.XML",  # Bivalent heating data
    "FVE4.XML",  # Photovoltaics data
    "FVEINV10.XML",  # PV Inverter data
    "SPOT1.XML",  # Spot pricing data
    # Note: NAST.XML (Heat pump settings) is added dynamically if accessible
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

# Static descriptor for STATUS.XML fields.
# STATUS.XML is a data-only endpoint; unlike other pages it has no paired descriptor XML.
# Field labels, units, and types were extracted from TRANSF.XSL (the XSL that renders the
# main-page status popup). Only the 31 fields not already covered by STAVJED1.XML are listed.
STATUS_XML_DESCRIPTOR: dict = {
    "SVYKON": {
        "friendly_name": "Výkon TČ",
        "friendly_name_en": "HP power",
        "unit": "%",
        "entity_type": "sensor",
        "writable": False,
    },
    "SCHLAZENI": {
        "friendly_name": "Režim chlazení",
        "friendly_name_en": "Cooling mode",
        "unit": "",
        "entity_type": "binary_sensor",
        "writable": False,
    },
    "SPOZTEP": {
        "friendly_name": "Požadovaná teplota topné vody",
        "friendly_name_en": "Requested heat water temperature",
        "unit": "°C",
        "entity_type": "sensor",
        "writable": False,
    },
    "SAKTTEP": {
        "friendly_name": "Aktuální teplota topné vody",
        "friendly_name_en": "Actual heat water temperature",
        "unit": "°C",
        "entity_type": "sensor",
        "writable": False,
    },
    "STEPTUV": {
        "friendly_name": "Požadavek ohřevu TUV",
        "friendly_name_en": "DHW heating requested",
        "unit": "",
        "entity_type": "binary_sensor",
        "writable": False,
    },
    "SAKTTEPTUV": {
        "friendly_name": "Aktuální teplota topné vody pro TUV",
        "friendly_name_en": "Actual DHW heat water temperature",
        "unit": "°C",
        "entity_type": "sensor",
        "writable": False,
    },
    "SHDOIGNORE": {
        "friendly_name": "Ignorovat HDO",
        "friendly_name_en": "Ignore LRT",
        "unit": "",
        "entity_type": "binary_sensor",
        "writable": False,
    },
    "SHDOLOWT": {
        "friendly_name": "Ignorovat HDO pod venkovní teplotu",
        "friendly_name_en": "Ignore LRT under outdoor temperature",
        "unit": "°C",
        "entity_type": "sensor",
        "writable": False,
    },
    "SHDOSTAV": {
        "friendly_name": "Stav HDO",
        "friendly_name_en": "LRT state",
        "unit": "",
        "entity_type": "binary_sensor",
        "writable": False,
    },
    "SSTAVJEDNOTKY": {
        "friendly_name": "Stavy venkovních jednotek dostupné",
        "friendly_name_en": "Outdoor units states available",
        "unit": "",
        "entity_type": "binary_sensor",
        "writable": False,
    },
    "SSTAVKOTLU": {
        "friendly_name": "Stavy kotle dostupné",
        "friendly_name_en": "Boiler states available",
        "unit": "",
        "entity_type": "binary_sensor",
        "writable": False,
    },
}
# SOBEH0–9: per-circuit run/visibility flags rendered as icon-only switchGo elements in
# TRANSF.XSL — no per-index text labels exist in the XSL, names follow XCC convention.
for _i in range(10):
    STATUS_XML_DESCRIPTOR[f"SOBEH{_i}RUN"] = {
        "friendly_name": f"Oběh {_i} běží",
        "friendly_name_en": f"Circuit {_i} running",
        "unit": "",
        "entity_type": "binary_sensor",
        "writable": False,
    }
    STATUS_XML_DESCRIPTOR[f"SOBEH{_i}VIS"] = {
        "friendly_name": f"Oběh {_i} aktivní",
        "friendly_name_en": f"Circuit {_i} active",
        "unit": "",
        "entity_type": "binary_sensor",
        "writable": False,
    }

# Hidden switches - fields that appear in data pages with _BOOL_i (writable) but have no
# <switch> or <choice> control in descriptor files. These are typically service technician
# settings or installation-time configuration.  We expose them as switches in HA to allow
# advanced users to control hidden features.
#
# Found by running: python find_hidden_switches.py
# Total hidden switches found: 217 across all pages
#
# Only the most useful/safe ones are exposed here. Others remain hidden to avoid
# accidental misconfiguration.
HIDDEN_SWITCHES: dict = {
    # Cooling mode configuration - enables reversible heat pump operation
    "TO-CONFIG-CHLAZENI": {
        "friendly_name": "Konfigurace chlazení topného okruhu",
        "friendly_name_en": "Heating circuit cooling mode configuration",
        "unit": "",
        "entity_type": "switch",
        "writable": True,
        "device_class": None,
        "note": "Enable cooling mode for this heating circuit (requires compatible heat pump hardware)",
    },
    # Add more hidden switches here as needed
}

# Hidden binary sensors - fields that appear in data pages with _BOOL_i (parsed as writable
# switch) but are actually read-only status outputs.  The consumption prioritizer fields
# (BLOKYSPOTREBY) are the main example: they show which consumer the heat pump is currently
# serving, not something a user would ever toggle.
#
# Like HIDDEN_SWITCHES, these entries OVERRIDE the type inferred from the _BOOL_i register
# suffix so the entity appears as a binary_sensor instead of a switch.
HIDDEN_BINARY_SENSORS: dict = {
    # Consumption-prioritizer "active" flags (BLOKYSPOTREBY = consumption block)
    # Each consumer has a -OK flag that turns 1 when the HP is currently serving it.
    # All six share the same semantics and are named systematically as
    # "HP heating/is-serving <consumer>". BLOKYSPOTREBY-OK is included here
    # (overriding the okruh.xml descriptor) because the descriptor reuses the row
    # label from the adjacent <switch prop="TO-POVOLENI"/> control ("Vypínač okruhu"
    # / "Heating circuit switch"), which describes the switch, not the status flag.
    "BLOKYSPOTREBY-OK": {
        "friendly_name": "TČ topí okruh",
        "friendly_name_en": "HP heating circuit",
        "unit": "",
        "entity_type": "binary_sensor",
        "writable": False,
        "device_class": "running",
    },
    "BLOKYSPOTREBY1-OK": {
        "friendly_name": "TČ topí bazén 1",
        "friendly_name_en": "HP heating pool 1",
        "unit": "",
        "entity_type": "binary_sensor",
        "writable": False,
        "device_class": "running",
    },
    "BLOKYSPOTREBY2-OK": {
        "friendly_name": "TČ topí bazénovou místnost",
        "friendly_name_en": "HP heating pool room",
        "unit": "",
        "entity_type": "binary_sensor",
        "writable": False,
        "device_class": "running",
    },
    "BLOKYSPOTREBY3-OK": {
        "friendly_name": "TČ ohřívá TUV",
        "friendly_name_en": "HP heating DHW",
        "unit": "",
        "entity_type": "binary_sensor",
        "writable": False,
        "device_class": "running",
    },
    "BLOKYSPOTREBY6-OK": {
        "friendly_name": "TČ ohřívá TUV 2",
        "friendly_name_en": "HP heating DHW 2",
        "unit": "",
        "entity_type": "binary_sensor",
        "writable": False,
        "device_class": "running",
    },
    "BLOKYSPOTREBY7-OK": {
        "friendly_name": "TČ topí bazén 2",
        "friendly_name_en": "HP heating pool 2",
        "unit": "",
        "entity_type": "binary_sensor",
        "writable": False,
        "device_class": "running",
    },
    # Attenuation flags - consumer is in setback/reduced-output mode
    "BLOKYSPOTREBY-UTLUM": {
        "friendly_name": "Okruh v útlumu",
        "friendly_name_en": "Heating circuit in attenuation",
        "unit": "",
        "entity_type": "binary_sensor",
        "writable": False,
    },
    "BLOKYSPOTREBY1-UTLUM": {
        "friendly_name": "Bazén 1 v útlumu",
        "friendly_name_en": "Pool 1 in attenuation",
        "unit": "",
        "entity_type": "binary_sensor",
        "writable": False,
    },
    "BLOKYSPOTREBY2-UTLUM": {
        "friendly_name": "Bazénová místnost v útlumu",
        "friendly_name_en": "Pool room in attenuation",
        "unit": "",
        "entity_type": "binary_sensor",
        "writable": False,
    },
    "BLOKYSPOTREBY3-UTLUM": {
        "friendly_name": "TUV v útlumu",
        "friendly_name_en": "DHW in attenuation",
        "unit": "",
        "entity_type": "binary_sensor",
        "writable": False,
    },
    "BLOKYSPOTREBY6-UTLUM": {
        "friendly_name": "TUV 2 v útlumu",
        "friendly_name_en": "DHW 2 in attenuation",
        "unit": "",
        "entity_type": "binary_sensor",
        "writable": False,
    },
    "BLOKYSPOTREBY7-UTLUM": {
        "friendly_name": "Bazén 2 v útlumu",
        "friendly_name_en": "Pool 2 in attenuation",
        "unit": "",
        "entity_type": "binary_sensor",
        "writable": False,
    },
}

# Single descriptor-override table consumed by the coordinator at descriptor-load time.
# Sources are grouped above purely for readability; semantically all entries replace any
# config inferred from descriptor XML or from the _BOOL_i register suffix:
#   * STATUS_XML_DESCRIPTOR  — metadata for STATUS.XML (no paired descriptor file)
#   * HIDDEN_SWITCHES        — promotes hidden _BOOL_i fields to writable switches
#   * HIDDEN_BINARY_SENSORS  — pins read-only _BOOL_i status fields as binary_sensor
# Add new manual overrides to whichever of the three source dicts fits the intent.
DESCRIPTOR_OVERRIDES: dict = {
    **STATUS_XML_DESCRIPTOR,
    **HIDDEN_SWITCHES,
    **HIDDEN_BINARY_SENSORS,
}
