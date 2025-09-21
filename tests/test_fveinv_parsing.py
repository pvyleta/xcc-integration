"""Test FVEINV (PV Inverter) page parsing functionality."""

import pytest
import os
from pathlib import Path

# Import the parsing functions
import sys
sys.path.append(str(Path(__file__).parent.parent))

from custom_components.xcc.xcc_client import parse_xml_entities
from custom_components.xcc.descriptor_parser import XCCDescriptorParser


def load_sample_file(filename: str) -> str:
    """Load a sample XML file."""
    sample_path = Path(__file__).parent / "sample_data" / filename
    with open(sample_path, 'r', encoding='utf-8') as f:
        return f.read()


def test_fveinv_descriptor_parsing():
    """Test parsing of FVEINV.XML descriptor file."""
    # Load the descriptor file
    descriptor_content = load_sample_file("FVEINV.XML")
    
    # Parse using descriptor parser
    parser = XCCDescriptorParser()
    entity_configs = parser.parse_descriptor_files({"fveinv.xml": descriptor_content})
    
    # Verify we found entities
    assert len(entity_configs) > 0, "Should find entities in FVEINV descriptor"
    
    # Check for some key inverter entities
    expected_entities = [
        "FVESTATS-MENIC-TOTALGENERATED",
        "FVESTATS-MENIC-TODAYGENERATED", 
        "FVESTATS-MENIC-TOTALINVPOWER",
        "FVESTATS-MENIC-BATTERY-SOC",
        "FVESTATS-MENIC-BATTERY-POWER",
        "FVESTATS-MENIC-STRINGS0-POWER",
    ]
    
    found_entities = list(entity_configs.keys())
    print(f"Found {len(found_entities)} entities in FVEINV descriptor")
    print(f"First 10 entities: {found_entities[:10]}")
    
    for expected in expected_entities:
        assert expected in entity_configs, f"Should find {expected} in descriptor"
        
    # Verify entity properties
    battery_soc = entity_configs.get("FVESTATS-MENIC-BATTERY-SOC")
    if battery_soc:
        assert battery_soc["unit"] == "%", "Battery SOC should have % unit"
        assert "Battery" in battery_soc["friendly_name"], "Should have Battery in friendly name"


def test_fveinv_data_parsing():
    """Test parsing of FVEINV10.XML data file."""
    # Load the data file
    data_content = load_sample_file("FVEINV10.XML")
    
    # Parse entities from data file
    entities = parse_xml_entities(data_content, "FVEINV10.XML")
    
    # Verify we found entities
    assert len(entities) > 0, "Should find entities in FVEINV data file"
    
    # Check for specific entities with expected values
    entity_dict = {e["attributes"]["field_name"]: e for e in entities}
    
    # Verify some key values
    assert "FVESTATS-MENIC-TOTALGENERATED" in entity_dict
    assert entity_dict["FVESTATS-MENIC-TOTALGENERATED"]["state"] == "12345"
    
    assert "FVESTATS-MENIC-BATTERY-SOC" in entity_dict
    assert entity_dict["FVESTATS-MENIC-BATTERY-SOC"]["state"] == "85"
    
    assert "FVESTATS-MENIC-BATTERY-POWER" in entity_dict
    assert entity_dict["FVESTATS-MENIC-BATTERY-POWER"]["state"] == "-500"
    
    print(f"Found {len(entities)} entities in FVEINV data file")
    print(f"Sample entities: {list(entity_dict.keys())[:5]}")


def test_fveinv_combined_parsing():
    """Test combined parsing of descriptor and data files."""
    # Load both files
    descriptor_content = load_sample_file("FVEINV.XML")
    data_content = load_sample_file("FVEINV10.XML")
    
    # Parse descriptor first
    parser = XCCDescriptorParser()
    entity_configs = parser.parse_descriptor_files({"fveinv.xml": descriptor_content})
    
    # Parse data
    data_entities = parse_xml_entities(data_content, "FVEINV10.XML")
    data_dict = {e["attributes"]["field_name"]: e for e in data_entities}
    
    # Verify we can combine them
    combined_entities = []
    for prop, config in entity_configs.items():
        if prop in data_dict:
            # Create combined entity with descriptor config and data value
            combined_entity = {
                "entity_id": f"xcc_{prop.lower().replace('-', '_')}",
                "entity_type": config.get("entity_type", "sensor"),
                "state": data_dict[prop]["state"],
                "attributes": {
                    **config,
                    "field_name": prop,
                    "current_value": data_dict[prop]["state"],
                }
            }
            combined_entities.append(combined_entity)
    
    assert len(combined_entities) > 0, "Should create combined entities"
    
    # Find battery SOC entity
    battery_soc_entities = [e for e in combined_entities if "BATTERY-SOC" in e["attributes"]["field_name"]]
    assert len(battery_soc_entities) > 0, "Should find battery SOC entity"
    
    battery_soc = battery_soc_entities[0]
    assert battery_soc["state"] == "85", "Battery SOC should have correct value"
    assert battery_soc["attributes"]["unit"] == "%", "Battery SOC should have % unit"
    
    print(f"Successfully combined {len(combined_entities)} entities")


def test_fveinv_entity_types():
    """Test that FVEINV entities get correct entity types."""
    descriptor_content = load_sample_file("FVEINV.XML")
    
    parser = XCCDescriptorParser()
    entity_configs = parser.parse_descriptor_files({"fveinv.xml": descriptor_content})
    
    # Most FVEINV entities should be sensors (readonly)
    sensor_count = sum(1 for config in entity_configs.values() if config.get("entity_type") == "sensor")
    total_count = len(entity_configs)
    
    print(f"Found {sensor_count} sensors out of {total_count} total entities")
    assert sensor_count > 0, "Should find sensor entities"
    
    # Check specific entity types
    if "FVESTATS-MENIC-BATTERY-SOC" in entity_configs:
        soc_config = entity_configs["FVESTATS-MENIC-BATTERY-SOC"]
        assert soc_config["entity_type"] == "sensor", "Battery SOC should be a sensor"
        assert soc_config["device_class"] == "battery", "Battery SOC should have battery device class"


if __name__ == "__main__":
    # Run tests directly
    test_fveinv_descriptor_parsing()
    test_fveinv_data_parsing()
    test_fveinv_combined_parsing()
    test_fveinv_entity_types()
    print("All FVEINV parsing tests passed!")
