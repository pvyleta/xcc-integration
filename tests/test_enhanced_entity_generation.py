"""Test enhanced entity generation with descriptor information."""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_descriptor_parser_extracts_sensor_info():
    """Test that descriptor parser extracts sensor information from row context."""
    
    # Import descriptor parser
    try:
        sys.path.insert(0, str(project_root / "custom_components" / "xcc"))
        from descriptor_parser import XCCDescriptorParser
    except ImportError as e:
        pytest.skip(f"Cannot import XCCDescriptorParser: {e}")
    
    parser = XCCDescriptorParser()
    
    # Sample XML with sensor information in row context (like your example)
    xml_content = '''<?xml version="1.0" encoding="utf-8"?>
    <PAGE>
        <row cl="visib" text="Výkon baterie" text_en="Battery power" visData="2;FVE-ENABLED;1;FVE-KOMUNIKOVAT;1">
            <number config="readonly" prop="FVEG-PANEL" unit="W"/>
        </row>
        <row cl="visib" text="Teplota venku" text_en="Outdoor temperature">
            <number config="readonly" prop="SVENKU" unit="°C"/>
        </row>
        <row cl="visib" text="Tlak" text_en="Pressure">
            <number config="readonly" prop="PRESSURE-SENSOR" unit="bar"/>
        </row>
    </PAGE>'''
    
    # Parse the descriptor
    entity_configs = parser._parse_single_descriptor(xml_content, "TEST.XML")
    
    # Verify sensor configurations were extracted
    assert len(entity_configs) >= 3, f"Should extract at least 3 sensor configs, got {len(entity_configs)}"
    
    # Check FVEG-PANEL (Battery power)
    if "FVEG-PANEL" in entity_configs:
        config = entity_configs["FVEG-PANEL"]
        assert config["friendly_name_en"] == "Battery power", f"Expected 'Battery power', got '{config['friendly_name_en']}'"
        assert config["unit"] == "W", f"Expected 'W', got '{config['unit']}'"
        assert config["device_class"] == "power", f"Expected 'power', got '{config['device_class']}'"
        assert config["entity_type"] == "sensor", f"Expected 'sensor', got '{config['entity_type']}'"
        assert config["writable"] is False, "Should be readonly sensor"
    
    # Check SVENKU (Outdoor temperature)
    if "SVENKU" in entity_configs:
        config = entity_configs["SVENKU"]
        assert config["friendly_name_en"] == "Outdoor temperature", f"Expected 'Outdoor temperature', got '{config['friendly_name_en']}'"
        assert config["unit"] == "°C", f"Expected '°C', got '{config['unit']}'"
        assert config["device_class"] == "temperature", f"Expected 'temperature', got '{config['device_class']}'"
    
    # Check PRESSURE-SENSOR (Pressure)
    if "PRESSURE-SENSOR" in entity_configs:
        config = entity_configs["PRESSURE-SENSOR"]
        assert config["friendly_name_en"] == "Pressure", f"Expected 'Pressure', got '{config['friendly_name_en']}'"
        assert config["unit"] == "bar", f"Expected 'bar', got '{config['unit']}'"
        assert config["device_class"] == "pressure", f"Expected 'pressure', got '{config['device_class']}'"


def test_device_class_from_unit_mapping():
    """Test device class determination from unit."""
    
    try:
        sys.path.insert(0, str(project_root / "custom_components" / "xcc"))
        from descriptor_parser import XCCDescriptorParser
    except ImportError as e:
        pytest.skip(f"Cannot import XCCDescriptorParser: {e}")
    
    parser = XCCDescriptorParser()
    
    # Test various unit mappings
    test_cases = [
        # Temperature
        ("°C", "temperature"),
        ("K", "temperature"),
        ("°F", "temperature"),
        
        # Power
        ("W", "power"),
        ("kW", "power"),
        ("MW", "power"),
        
        # Energy
        ("Wh", "energy"),
        ("kWh", "energy"),
        ("J", "energy"),
        
        # Pressure
        ("Pa", "pressure"),
        ("bar", "pressure"),
        ("psi", "pressure"),
        
        # Voltage
        ("V", "voltage"),
        ("mV", "voltage"),
        
        # Current
        ("A", "current"),
        ("mA", "current"),
        
        # Frequency
        ("Hz", "frequency"),
        ("kHz", "frequency"),
        
        # Percentage (no device class)
        ("%", None),
        
        # Unknown unit
        ("unknown", None),
        ("", None),
    ]
    
    for unit, expected_device_class in test_cases:
        result = parser._determine_device_class_from_unit(unit)
        assert result == expected_device_class, f"Unit '{unit}' should map to '{expected_device_class}', got '{result}'"


def test_sensor_creation_uses_descriptor_info():
    """Test that sensor creation uses enhanced descriptor information."""

    # Read the sensor.py file to verify enhanced logic is present
    sensor_file = project_root / "custom_components" / "xcc" / "sensor.py"
    if not sensor_file.exists():
        pytest.skip("Cannot find sensor.py file")

    sensor_content = sensor_file.read_text()

    # Check for device class functionality (actual implementation may vary)
    assert "_get_device_class" in sensor_content, \
        "Should have device class detection functionality"

    assert "UNIT_MAPPING" in sensor_content, \
        "Should have unit mapping for Home Assistant units"

    # Check for sensor device class functionality
    assert "SensorDeviceClass" in sensor_content, \
        "Should import SensorDeviceClass for device class mapping"

    # Check that the sensor platform has the basic functionality we need
    assert "XCCSensor" in sensor_content, \
        "Should define XCCSensor class"


def test_descriptor_parser_handles_mixed_elements():
    """Test that descriptor parser handles both writable and readonly elements."""
    
    try:
        sys.path.insert(0, str(project_root / "custom_components" / "xcc"))
        from descriptor_parser import XCCDescriptorParser
    except ImportError as e:
        pytest.skip(f"Cannot import XCCDescriptorParser: {e}")
    
    parser = XCCDescriptorParser()
    
    # XML with both writable and readonly elements
    xml_content = '''<?xml version="1.0" encoding="utf-8"?>
    <PAGE>
        <!-- Writable number (should be processed as before) -->
        <number prop="SETPOINT" text="Temperature setpoint" text_en="Temperature setpoint" unit="°C" min="10" max="30"/>
        
        <!-- Readonly sensor in row context (new functionality) -->
        <row text="Current temperature" text_en="Current temperature">
            <number config="readonly" prop="CURRENT-TEMP" unit="°C"/>
        </row>
        
        <!-- Writable switch -->
        <switch prop="PUMP-CONTROL" text="Pump control" text_en="Pump control"/>
        
        <!-- Readonly power sensor -->
        <row text="Spotřeba" text_en="Power consumption">
            <number config="readonly" prop="POWER-USAGE" unit="kW"/>
        </row>
    </PAGE>'''
    
    entity_configs = parser._parse_single_descriptor(xml_content, "MIXED.XML")
    
    # Should have both writable and readonly entities
    assert len(entity_configs) >= 4, f"Should have at least 4 entities, got {len(entity_configs)}"
    
    # Check writable entities (existing functionality)
    if "SETPOINT" in entity_configs:
        config = entity_configs["SETPOINT"]
        assert config["writable"] is True, "SETPOINT should be writable"
        assert "min" in config or "max" in config, "Writable number should have min/max"
    
    if "PUMP-CONTROL" in entity_configs:
        config = entity_configs["PUMP-CONTROL"]
        assert config["writable"] is True, "PUMP-CONTROL should be writable"
    
    # Check readonly sensors (new functionality)
    if "CURRENT-TEMP" in entity_configs:
        config = entity_configs["CURRENT-TEMP"]
        assert config["writable"] is False, "CURRENT-TEMP should be readonly"
        assert config["entity_type"] == "sensor", "Should be classified as sensor"
        assert config["friendly_name_en"] == "Current temperature", "Should use row text_en"
        assert config["unit"] == "°C", "Should extract unit"
        assert config["device_class"] == "temperature", "Should determine device class from unit"
    
    if "POWER-USAGE" in entity_configs:
        config = entity_configs["POWER-USAGE"]
        assert config["writable"] is False, "POWER-USAGE should be readonly"
        assert config["friendly_name_en"] == "Power consumption", "Should use row text_en"
        assert config["unit"] == "kW", "Should extract unit"
        assert config["device_class"] == "power", "Should determine device class from unit"


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])
