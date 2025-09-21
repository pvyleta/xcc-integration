"""Test FVEINV integration with the full XCC client."""

import pytest
import os
from pathlib import Path
from unittest.mock import AsyncMock, patch

# Import the XCC client
import sys
sys.path.append(str(Path(__file__).parent.parent))

from custom_components.xcc.xcc_client import XCCClient, parse_xml_entities


def load_sample_file(filename: str) -> str:
    """Load a sample XML file."""
    sample_path = Path(__file__).parent / "sample_data" / filename
    with open(sample_path, 'r', encoding='utf-8') as f:
        return f.read()


@pytest.mark.asyncio
async def test_fveinv_page_type_detection():
    """Test that FVEINV page is correctly detected as pv_inverter type."""
    client = XCCClient("http://test.com", "user", "pass")
    
    # Test the page type detection
    page_type = client._determine_page_type("https://test.com/fveinv.xml")
    assert page_type == "pv_inverter", f"Expected 'pv_inverter', got '{page_type}'"
    
    # Test with different case
    page_type = client._determine_page_type("https://test.com/FVEINV.XML")
    assert page_type == "pv_inverter", f"Expected 'pv_inverter', got '{page_type}'"


@pytest.mark.asyncio
async def test_fveinv_full_parsing_flow():
    """Test the full parsing flow with FVEINV files."""
    client = XCCClient("http://test.com", "user", "pass")
    
    # Load sample files
    descriptor_content = load_sample_file("FVEINV.XML")
    data_content = load_sample_file("FVEINV10.XML")
    
    # Mock the fetch_page method to return our sample data
    async def mock_fetch_page(page_name):
        if page_name == "fveinv.xml":
            return descriptor_content
        elif page_name == "FVEINV10.XML":
            return data_content
        else:
            raise Exception(f"Unexpected page request: {page_name}")
    
    client.fetch_page = AsyncMock(side_effect=mock_fetch_page)
    
    # Test parsing descriptor pages
    descriptor_data = {"fveinv.xml": descriptor_content}
    entity_configs = client.descriptor_parser.parse_descriptor_files(descriptor_data)
    
    assert len(entity_configs) > 0, "Should find entity configurations"
    
    # Test parsing data pages
    data_entities = parse_xml_entities(data_content, "FVEINV10.XML")
    assert len(data_entities) > 0, "Should find data entities"
    
    # Test that we can find matching entities
    data_dict = {e["attributes"]["field_name"]: e for e in data_entities}
    matching_entities = 0
    
    for prop in entity_configs.keys():
        if prop in data_dict:
            matching_entities += 1
    
    assert matching_entities > 0, "Should find matching entities between descriptor and data"
    print(f"Found {matching_entities} matching entities out of {len(entity_configs)} descriptor configs")


@pytest.mark.asyncio
async def test_fveinv_entity_creation():
    """Test that FVEINV entities are created with correct properties."""
    client = XCCClient("http://test.com", "user", "pass")
    
    # Load sample files
    descriptor_content = load_sample_file("FVEINV.XML")
    data_content = load_sample_file("FVEINV10.XML")
    
    # Parse descriptor
    descriptor_data = {"fveinv.xml": descriptor_content}
    entity_configs = client.descriptor_parser.parse_descriptor_files(descriptor_data)
    
    # Parse data
    data_entities = parse_xml_entities(data_content, "FVEINV10.XML")
    data_dict = {e["attributes"]["field_name"]: e for e in data_entities}
    
    # Test specific entities
    test_entities = [
        ("FVESTATS-MENIC-TOTALGENERATED", "12345", "kWh", "energy"),
        ("FVESTATS-MENIC-BATTERY-SOC", "85", "%", "battery"),
        ("FVESTATS-MENIC-BATTERY-POWER", "-500", "W", "power"),
    ]
    
    for entity_name, expected_value, expected_unit, expected_device_class in test_entities:
        # Check descriptor config
        assert entity_name in entity_configs, f"Should find {entity_name} in descriptor"
        config = entity_configs[entity_name]
        
        assert config["unit"] == expected_unit, f"Expected unit {expected_unit} for {entity_name}"
        assert config["device_class"] == expected_device_class, f"Expected device class {expected_device_class} for {entity_name}"
        assert config["entity_type"] == "sensor", f"Expected sensor type for {entity_name}"
        
        # Check data value
        assert entity_name in data_dict, f"Should find {entity_name} in data"
        data_entity = data_dict[entity_name]
        assert data_entity["state"] == expected_value, f"Expected value {expected_value} for {entity_name}"


@pytest.mark.asyncio
async def test_fveinv_friendly_names():
    """Test that FVEINV entities have proper friendly names."""
    client = XCCClient("http://test.com", "user", "pass")
    
    # Load sample files
    descriptor_content = load_sample_file("FVEINV.XML")
    
    # Parse descriptor
    descriptor_data = {"fveinv.xml": descriptor_content}
    entity_configs = client.descriptor_parser.parse_descriptor_files(descriptor_data)
    
    # Test friendly name generation
    test_cases = [
        ("FVESTATS-MENIC-TOTALGENERATED", "Totalgenerated"),
        ("FVESTATS-MENIC-BATTERY-SOC", "Battery SOC"),
        ("FVESTATS-MENIC-BATTERY-POWER", "Battery Power"),
        ("FVESTATS-MENIC-STRINGS0-POWER", "Strings0 Power"),
    ]
    
    for entity_name, expected_friendly_name in test_cases:
        if entity_name in entity_configs:
            config = entity_configs[entity_name]
            friendly_name = config["friendly_name"]
            assert expected_friendly_name in friendly_name, f"Expected '{expected_friendly_name}' in friendly name '{friendly_name}' for {entity_name}"


if __name__ == "__main__":
    # Run tests directly
    import asyncio
    
    async def run_tests():
        await test_fveinv_page_type_detection()
        await test_fveinv_full_parsing_flow()
        await test_fveinv_entity_creation()
        await test_fveinv_friendly_names()
        print("All FVEINV integration tests passed!")
    
    asyncio.run(run_tests())
