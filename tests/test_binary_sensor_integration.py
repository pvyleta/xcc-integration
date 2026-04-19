"""Integration tests for XCC binary sensor platform.

These tests verify:
1. Binary sensors are created from coordinator.get_entities_by_type("binary_sensor")
2. STATUS.XML boolean fields are routed to binary_sensors, not sensors
3. XCCBinarySensor class structure is correct (inheritance, methods)
4. STATUS_XML_DESCRIPTOR has correct entity_type declarations
"""

import sys
from pathlib import Path
import importlib
import inspect

import pytest

# Import directly from the component directory to avoid pulling in homeassistant.*
_XCC_DIR = Path(__file__).parent.parent / "custom_components" / "xcc"
sys.path.insert(0, str(_XCC_DIR))

from const import STATUS_XML_DESCRIPTOR  # noqa: E402


# ---------------------------------------------------------------------------
# Test XCCBinarySensor class structure (via source code inspection)
# ---------------------------------------------------------------------------

def test_xccbinarysensor_inheritance_from_source():
    """Verify XCCBinarySensor inherits from XCCEntity by inspecting source code."""
    binary_sensor_path = _XCC_DIR / "binary_sensor.py"
    source = binary_sensor_path.read_text(encoding="utf-8")

    # Verify the class definition includes XCCEntity as base class
    assert "class XCCBinarySensor(XCCEntity," in source, (
        "XCCBinarySensor must inherit from XCCEntity (not just CoordinatorEntity)"
    )

    # Verify import statement
    assert "from .entity import XCCEntity" in source, (
        "binary_sensor.py must import XCCEntity"
    )


def test_xccbinarysensor_takes_entity_data_not_entity_id():
    """Verify XCCBinarySensor.__init__ signature matches other platforms."""
    binary_sensor_path = _XCC_DIR / "binary_sensor.py"
    source = binary_sensor_path.read_text(encoding="utf-8")

    # The __init__ should take entity_data (like sensor.py, switch.py, etc.)
    # not a bare entity_id string
    assert "def __init__(\n        self, coordinator: XCCDataUpdateCoordinator, entity_data: dict[str, Any]" in source, (
        "XCCBinarySensor.__init__ should take entity_data dict, not entity_id string"
    )


def test_binary_sensor_platform_uses_get_entities_by_type_singular():
    """Verify async_setup_entry calls get_entities_by_type('binary_sensor') not plural."""
    binary_sensor_path = _XCC_DIR / "binary_sensor.py"
    source = binary_sensor_path.read_text(encoding="utf-8")

    # Bug was: coordinator.get_entities_by_type("binary_sensors") — wrong!
    # Fix is: coordinator.get_entities_by_type("binary_sensor") — correct
    assert 'get_entities_by_type("binary_sensor")' in source, (
        "async_setup_entry must call get_entities_by_type('binary_sensor') (singular)"
    )
    assert 'get_entities_by_type("binary_sensors")' not in source, (
        "Must NOT use plural 'binary_sensors' — coordinator stores type as singular"
    )


# ---------------------------------------------------------------------------
# Test STATUS.XML fields are declared as binary_sensor
# ---------------------------------------------------------------------------

def test_status_xml_descriptor_declares_binary_sensors():
    """All BOOL fields in STATUS_XML_DESCRIPTOR have entity_type='binary_sensor'."""
    bool_fields = [
        "SCHLAZENI", "STEPTUV", "SHDOIGNORE", "SHDOSTAV",
        "SSTAVJEDNOTKY", "SSTAVKOTLU",
    ] + [f"SOBEH{i}RUN" for i in range(10)] + [f"SOBEH{i}VIS" for i in range(10)]
    
    for field in bool_fields:
        assert field in STATUS_XML_DESCRIPTOR, f"{field} missing from STATUS_XML_DESCRIPTOR"
        assert STATUS_XML_DESCRIPTOR[field]["entity_type"] == "binary_sensor", (
            f"{field} should have entity_type='binary_sensor', got "
            f"{STATUS_XML_DESCRIPTOR[field]['entity_type']!r}"
        )


if __name__ == "__main__":
    test_xccbinarysensor_inheritance_from_source()
    test_xccbinarysensor_takes_entity_data_not_entity_id()
    test_binary_sensor_platform_uses_get_entities_by_type_singular()
    test_status_xml_descriptor_declares_binary_sensors()
    print("✅ All binary_sensor integration tests passed!")
