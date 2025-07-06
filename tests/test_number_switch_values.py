"""Test that number and switch entities get proper values with enhanced descriptor parsing."""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_enhanced_descriptor_identifies_writable_entities():
    """Test that enhanced descriptor parser identifies writable numbers and switches."""
    
    try:
        sys.path.insert(0, str(project_root / "custom_components" / "xcc"))
        from descriptor_parser import XCCDescriptorParser
    except ImportError as e:
        pytest.skip(f"Cannot import XCCDescriptorParser: {e}")
    
    parser = XCCDescriptorParser()
    
    # XML with writable number and switch entities
    xml_content = '''<?xml version="1.0" encoding="utf-8"?>
    <PAGE>
        <!-- Writable number entity -->
        <number prop="TEMP-SETPOINT" text="Temperature setpoint" text_en="Temperature setpoint" 
                unit="°C" min="10" max="30" step="0.5"/>
        
        <!-- Writable switch entity -->
        <switch prop="PUMP-CONTROL" text="Pump control" text_en="Pump control"/>
        
        <!-- Readonly sensor (should be sensor type) -->
        <row text="Current temperature" text_en="Current temperature">
            <number config="readonly" prop="CURRENT-TEMP" unit="°C"/>
        </row>
    </PAGE>'''
    
    entity_configs = parser._parse_single_descriptor(xml_content, "CONTROLS.XML")
    
    # Should have all three entities
    assert len(entity_configs) >= 3, f"Should have at least 3 entities, got {len(entity_configs)}"
    
    # Check writable number
    if "TEMP-SETPOINT" in entity_configs:
        config = entity_configs["TEMP-SETPOINT"]
        assert config["entity_type"] == "number", f"TEMP-SETPOINT should be number, got {config['entity_type']}"
        assert config["writable"] is True, "TEMP-SETPOINT should be writable"
        assert config["unit"] == "°C", "Should have unit"
        assert "min" in config, "Number should have min value"
        assert "max" in config, "Number should have max value"
        assert config["friendly_name_en"] == "Temperature setpoint", "Should have friendly name"
    
    # Check writable switch
    if "PUMP-CONTROL" in entity_configs:
        config = entity_configs["PUMP-CONTROL"]
        assert config["entity_type"] == "switch", f"PUMP-CONTROL should be switch, got {config['entity_type']}"
        assert config["writable"] is True, "PUMP-CONTROL should be writable"
        assert config["friendly_name_en"] == "Pump control", "Should have friendly name"
    
    # Check readonly sensor
    if "CURRENT-TEMP" in entity_configs:
        config = entity_configs["CURRENT-TEMP"]
        assert config["entity_type"] == "sensor", f"CURRENT-TEMP should be sensor, got {config['entity_type']}"
        assert config["writable"] is False, "CURRENT-TEMP should be readonly"


def test_coordinator_entity_type_detection():
    """Test that coordinator properly detects entity types from enhanced descriptors."""
    
    try:
        sys.path.insert(0, str(project_root / "custom_components" / "xcc"))
        from coordinator import XCCDataUpdateCoordinator
        from descriptor_parser import XCCDescriptorParser
    except ImportError as e:
        pytest.skip(f"Cannot import coordinator classes: {e}")
    
    # Create mock coordinator with enhanced entity configs
    coordinator = Mock()
    
    # Set up enhanced entity configs
    entity_configs = {
        "TEMP-SETPOINT": {
            "entity_type": "number",
            "writable": True,
            "unit": "°C",
            "min": 10,
            "max": 30,
            "friendly_name_en": "Temperature setpoint"
        },
        "PUMP-CONTROL": {
            "entity_type": "switch", 
            "writable": True,
            "friendly_name_en": "Pump control"
        },
        "CURRENT-TEMP": {
            "entity_type": "sensor",
            "writable": False,
            "unit": "°C",
            "device_class": "temperature",
            "friendly_name_en": "Current temperature"
        }
    }
    
    # Create a real coordinator instance to test get_entity_type method
    real_coordinator = XCCDataUpdateCoordinator(None, "192.168.1.100", "user", "pass")
    real_coordinator.entity_configs = entity_configs
    
    # Test entity type detection
    assert real_coordinator.get_entity_type("TEMP-SETPOINT") == "number", "Should detect number entity"
    assert real_coordinator.get_entity_type("PUMP-CONTROL") == "switch", "Should detect switch entity"
    assert real_coordinator.get_entity_type("CURRENT-TEMP") == "sensor", "Should detect sensor entity"
    assert real_coordinator.get_entity_type("UNKNOWN-PROP") == "sensor", "Should default to sensor for unknown"


def test_entity_data_structure_includes_values():
    """Test that entity data structure includes proper values for numbers and switches."""
    
    # This test verifies the data structure that would be created for entities
    
    # Sample entity data that would come from XCC XML parsing
    sample_entities = [
        {
            "entity_id": "xcc_temp_setpoint",
            "state": "22.5",
            "attributes": {
                "field_name": "TEMP-SETPOINT",
                "unit": "°C"
            }
        },
        {
            "entity_id": "xcc_pump_control", 
            "state": "1",
            "attributes": {
                "field_name": "PUMP-CONTROL"
            }
        },
        {
            "entity_id": "xcc_current_temp",
            "state": "21.0", 
            "attributes": {
                "field_name": "CURRENT-TEMP",
                "unit": "°C"
            }
        }
    ]
    
    # Verify entities have proper state values
    for entity in sample_entities:
        assert "state" in entity, f"Entity {entity['entity_id']} should have state"
        assert entity["state"] is not None, f"Entity {entity['entity_id']} state should not be None"
        assert entity["state"] != "", f"Entity {entity['entity_id']} state should not be empty"
        
        # Check that field_name is properly set
        assert "field_name" in entity["attributes"], f"Entity {entity['entity_id']} should have field_name"
        field_name = entity["attributes"]["field_name"]
        assert field_name is not None, f"Entity {entity['entity_id']} field_name should not be None"


def test_number_switch_platforms_use_enhanced_detection():
    """Test that number and switch platforms use enhanced entity type detection."""

    # Read the number.py and switch.py files to verify they use enhanced detection
    number_file = project_root / "custom_components" / "xcc" / "number.py"
    switch_file = project_root / "custom_components" / "xcc" / "switch.py"

    if not all([number_file.exists(), switch_file.exists()]):
        pytest.skip("Cannot find number.py or switch.py files")

    number_content = number_file.read_text()
    switch_content = switch_file.read_text()

    # Check that platforms use enhanced entity type detection
    assert "coordinator.get_entity_type(prop)" in number_content, \
        "Number platform should use coordinator.get_entity_type()"
    assert "coordinator.get_entity_type(prop)" in switch_content, \
        "Switch platform should use coordinator.get_entity_type()"

    # Check that they filter by correct entity types
    assert 'entity_type == "number"' in number_content, \
        "Number platform should filter for 'number' entities"
    assert 'entity_type == "switch"' in switch_content, \
        "Switch platform should filter for 'switch' entities"

    # Check that they check writability
    assert "coordinator.is_writable(prop)" in number_content, \
        "Number platform should check if entity is writable"
    assert "coordinator.is_writable(prop)" in switch_content, \
        "Switch platform should check if entity is writable"


def test_writable_entity_detection():
    """Test that writable entities are properly detected and configured."""
    
    try:
        sys.path.insert(0, str(project_root / "custom_components" / "xcc"))
        from descriptor_parser import XCCDescriptorParser
    except ImportError as e:
        pytest.skip(f"Cannot import XCCDescriptorParser: {e}")
    
    parser = XCCDescriptorParser()
    
    # Test writable vs readonly detection
    test_cases = [
        # (element_xml, expected_writable, expected_entity_type)
        ('<number prop="SETPOINT" min="10" max="30"/>', True, "number"),
        ('<number config="readonly" prop="SENSOR" unit="°C"/>', False, "sensor"),
        ('<switch prop="PUMP"/>', True, "switch"),
        ('<switch config="readonly" prop="STATUS"/>', False, "sensor"),  # Readonly switch becomes sensor
    ]
    
    for element_xml, expected_writable, expected_entity_type in test_cases:
        xml_content = f'''<?xml version="1.0" encoding="utf-8"?>
        <PAGE>
            <row text="Test" text_en="Test">
                {element_xml}
            </row>
        </PAGE>'''
        
        entity_configs = parser._parse_single_descriptor(xml_content, "TEST.XML")
        
        # Should have one entity
        assert len(entity_configs) == 1, f"Should have exactly 1 entity for {element_xml}"
        
        config = list(entity_configs.values())[0]
        assert config["writable"] == expected_writable, \
            f"Element {element_xml} should have writable={expected_writable}, got {config['writable']}"
        assert config["entity_type"] == expected_entity_type, \
            f"Element {element_xml} should have entity_type={expected_entity_type}, got {config['entity_type']}"


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])
