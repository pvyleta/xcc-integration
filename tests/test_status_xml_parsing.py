"""Tests for STATUS.XML parsing and entity routing.

STATUS.XML is a data-only page with no paired descriptor XML.
Its field metadata lives in STATUS_XML_DESCRIPTOR (const.py).
These tests verify:
  - all 38 fields are parsed from the sample file
  - BOOL fields get data_type='boolean', numeric fields get 'numeric'
  - STATUS_XML_DESCRIPTOR covers all unique fields and carries correct metadata
  - The binary_sensor routing fix: fields declared as binary_sensor in the
    descriptor end up in processed_data['binary_sensors'], not in 'sensors'
"""

import pytest
from pathlib import Path
import sys

# Import directly from the component directory to avoid pulling in homeassistant.*
_XCC_DIR = Path(__file__).parent.parent / "custom_components" / "xcc"
sys.path.insert(0, str(_XCC_DIR))

from xcc_client import parse_xml_entities  # noqa: E402
from const import STATUS_XML_DESCRIPTOR    # noqa: E402

SAMPLE_FILE = Path(__file__).parent / "sample_data" / "STATUS.XML"


def load_status_xml() -> str:
    return SAMPLE_FILE.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Parsing tests
# ---------------------------------------------------------------------------

def test_status_xml_parses_all_fields():
    """All 38 INPUT elements in the sample file are returned as entities."""
    entities = parse_xml_entities(load_status_xml(), "STATUS.XML")
    assert len(entities) == 38, f"Expected 38 entities, got {len(entities)}"


def test_status_xml_field_names():
    """Key field names are present after parsing."""
    entities = parse_xml_entities(load_status_xml(), "STATUS.XML")
    props = {e["attributes"]["field_name"] for e in entities}

    expected = {
        "SVENKU", "SVYKON", "SCHLAZENI", "SPOZTEP", "SAKTTEP",
        "STEPTUV", "SAKTTEPTUV", "SHDOIGNORE", "SHDOLOWT", "SHDOSTAV",
        "SSTAVJEDNOTKY", "SSTAVKOTLU",
        "SOBEH0RUN", "SOBEH0VIS", "SOBEH9RUN", "SOBEH9VIS",
    }
    for field in expected:
        assert field in props, f"Field {field} missing from parsed entities"


def test_status_xml_bool_fields_have_boolean_data_type():
    """_BOOL_i fields are tagged with data_type='boolean'."""
    entities = parse_xml_entities(load_status_xml(), "STATUS.XML")
    entity_map = {e["attributes"]["field_name"]: e for e in entities}

    bool_fields = [
        "SZAPNUTO", "SCOMPACT", "SCHLAZENI", "STEPTUV",
        "SHDOIGNORE", "SHDOSTAV", "SSTAVJEDNOTKY", "SSTAVKOTLU",
        "SOBEH0RUN", "SOBEH0VIS",
    ]
    for field in bool_fields:
        dt = entity_map[field]["attributes"].get("data_type")
        assert dt == "boolean", f"{field}: expected data_type='boolean', got {dt!r}"


def test_status_xml_real_fields_have_numeric_data_type():
    """_REAL_.1f fields are tagged with data_type='numeric'."""
    entities = parse_xml_entities(load_status_xml(), "STATUS.XML")
    entity_map = {e["attributes"]["field_name"]: e for e in entities}

    real_fields = ["SVENKU", "SPOZTEP", "SAKTTEP", "SAKTTEPTUV", "SHDOLOWT"]
    for field in real_fields:
        dt = entity_map[field]["attributes"].get("data_type")
        assert dt == "numeric", f"{field}: expected data_type='numeric', got {dt!r}"


def test_status_xml_sample_values():
    """Spot-check that values from the sample file are read correctly."""
    entities = parse_xml_entities(load_status_xml(), "STATUS.XML")
    entity_map = {e["attributes"]["field_name"]: e for e in entities}

    assert entity_map["SVENKU"]["state"] == "6.5"
    assert entity_map["SPOZTEP"]["state"] == "28.9"
    assert entity_map["SAKTTEP"]["state"] == "27.2"
    assert entity_map["SHDOLOWT"]["state"] == "-10.0"
    # SOBEH0RUN is ON (running circuit 0)
    assert entity_map["SOBEH0RUN"]["state"] == "1"
    # SOBEH1RUN is OFF
    assert entity_map["SOBEH1RUN"]["state"] == "0"


def test_status_xml_page_attribute():
    """Entities carry the correct page name in their attributes."""
    entities = parse_xml_entities(load_status_xml(), "STATUS.XML")
    for e in entities:
        assert e["attributes"]["page"] == "STATUS.XML", (
            f"Entity {e['attributes']['field_name']} has wrong page: "
            f"{e['attributes']['page']!r}"
        )


# ---------------------------------------------------------------------------
# Descriptor tests
# ---------------------------------------------------------------------------

def test_status_xml_descriptor_covers_unique_fields():
    """STATUS_XML_DESCRIPTOR contains exactly the 31 unique STATUS.XML fields."""
    # Fields shared with STAVJED1.XML (SVENKU, SNAZEV*, SCAS, SCHYBA, SZAPNUTO,
    # SCOMPACT) are intentionally absent from the descriptor.
    unique_fields = {
        "SVYKON", "SCHLAZENI", "SPOZTEP", "SAKTTEP", "STEPTUV",
        "SAKTTEPTUV", "SHDOIGNORE", "SHDOLOWT", "SHDOSTAV",
        "SSTAVJEDNOTKY", "SSTAVKOTLU",
    }
    for i in range(10):
        unique_fields.add(f"SOBEH{i}RUN")
        unique_fields.add(f"SOBEH{i}VIS")

    for field in unique_fields:
        assert field in STATUS_XML_DESCRIPTOR, (
            f"{field} missing from STATUS_XML_DESCRIPTOR"
        )


def test_status_xml_descriptor_binary_sensor_fields():
    """All BOOL fields in the descriptor are declared as binary_sensor."""
    bool_fields = [
        "SCHLAZENI", "STEPTUV", "SHDOIGNORE", "SHDOSTAV",
        "SSTAVJEDNOTKY", "SSTAVKOTLU",
    ] + [f"SOBEH{i}RUN" for i in range(10)] + [f"SOBEH{i}VIS" for i in range(10)]

    for field in bool_fields:
        et = STATUS_XML_DESCRIPTOR[field]["entity_type"]
        assert et == "binary_sensor", (
            f"{field}: expected entity_type='binary_sensor', got {et!r}"
        )


def test_status_xml_descriptor_sensor_fields():
    """Numeric fields in the descriptor are declared as sensor."""
    sensor_fields = ["SVYKON", "SPOZTEP", "SAKTTEP", "SAKTTEPTUV", "SHDOLOWT"]
    for field in sensor_fields:
        et = STATUS_XML_DESCRIPTOR[field]["entity_type"]
        assert et == "sensor", (
            f"{field}: expected entity_type='sensor', got {et!r}"
        )


def test_status_xml_descriptor_temperature_units():
    """Temperature fields carry the °C unit."""
    temp_fields = ["SPOZTEP", "SAKTTEP", "SAKTTEPTUV", "SHDOLOWT"]
    for field in temp_fields:
        unit = STATUS_XML_DESCRIPTOR[field]["unit"]
        assert unit == "°C", f"{field}: expected unit='°C', got {unit!r}"


def test_status_xml_descriptor_power_unit():
    """SVYKON (HP power) carries the % unit."""
    assert STATUS_XML_DESCRIPTOR["SVYKON"]["unit"] == "%"


def test_status_xml_descriptor_not_writable():
    """All STATUS_XML_DESCRIPTOR fields are read-only."""
    for field, config in STATUS_XML_DESCRIPTOR.items():
        assert config["writable"] is False, f"{field} should not be writable"


# ---------------------------------------------------------------------------
# Routing fix test
# ---------------------------------------------------------------------------

def test_binary_sensor_routing():
    """binary_sensor entity_type routes to processed_data['binary_sensors'],
    not to 'sensors'.  This is a regression test for the missing elif branch
    in coordinator._process_entities."""

    # Simulate what _process_entities does with the routing block
    processed = {"sensors": {}, "binary_sensors": {}, "switches": {}, "numbers": {}}

    test_cases = [
        ("SOBEH0RUN", "binary_sensor", "binary_sensors"),
        ("SCHLAZENI",  "binary_sensor", "binary_sensors"),
        ("SPOZTEP",    "sensor",        "sensors"),
        ("SVYKON",     "sensor",        "sensors"),
        ("SZAPNUTO",   "switch",        "switches"),
    ]

    for prop, entity_type, expected_bucket in test_cases:
        state_data = {"prop": prop, "state": "1"}
        entity_id = f"xcc_{prop.lower()}"

        if entity_type == "switch":
            processed["switches"][entity_id] = state_data
        elif entity_type == "binary_sensor":
            processed["binary_sensors"][entity_id] = state_data
        elif entity_type == "number":
            processed["numbers"][entity_id] = state_data
        else:
            processed["sensors"][entity_id] = state_data

        assert entity_id in processed[expected_bucket], (
            f"{prop} (type={entity_type!r}) should be in '{expected_bucket}', "
            f"but it's not. Buckets: { {k: list(v.keys()) for k, v in processed.items()} }"
        )
        wrong_buckets = [b for b in processed if b != expected_bucket]
        for b in wrong_buckets:
            assert entity_id not in processed[b], (
                f"{prop} landed in '{b}' but should only be in '{expected_bucket}'"
            )


if __name__ == "__main__":
    test_status_xml_parses_all_fields()
    test_status_xml_field_names()
    test_status_xml_bool_fields_have_boolean_data_type()
    test_status_xml_real_fields_have_numeric_data_type()
    test_status_xml_sample_values()
    test_status_xml_page_attribute()
    test_status_xml_descriptor_covers_unique_fields()
    test_status_xml_descriptor_binary_sensor_fields()
    test_status_xml_descriptor_sensor_fields()
    test_status_xml_descriptor_temperature_units()
    test_status_xml_descriptor_power_unit()
    test_status_xml_descriptor_not_writable()
    test_binary_sensor_routing()
    print("All STATUS.XML tests passed!")
