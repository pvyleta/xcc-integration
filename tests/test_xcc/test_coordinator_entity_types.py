"""Test coordinator entity type detection and processing."""
import pytest
from unittest.mock import Mock, patch, AsyncMock
import sys
from pathlib import Path

# Add the custom_components directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "custom_components" / "xcc"))

from coordinator import XCCDataUpdateCoordinator
from descriptor_parser import XCCDescriptorParser


@pytest.fixture
def mock_hass():
    """Create a mock Home Assistant instance."""
    hass = Mock()
    hass.config_entries = Mock()
    return hass


@pytest.fixture
def mock_config_entry():
    """Create a mock config entry."""
    entry = Mock()
    entry.data = {
        "host": "192.168.1.100",
        "username": "test_user",
        "password": "test_pass",
        "entity_mode": "integration",
    }
    entry.entry_id = "test_entry_id"
    return entry


@pytest.fixture
def sample_descriptor_data():
    """Sample descriptor data for testing."""
    return {
        "OKRUH.XML": '''<?xml version="1.0" encoding="UTF-8"?>
        <root>
            <switch prop="TO_POVOLENI" text="Enable heating" text_en="Enable heating"/>
            <number prop="TO_POZADOVANA" text="Target temp" text_en="Target temp" min="10" max="30" step="0.5" unit="°C"/>
            <choice prop="TO_REZIM" text="Mode" text_en="Mode">
                <option value="0" text="Auto" text_en="Auto"/>
                <option value="1" text="Manual" text_en="Manual"/>
            </choice>
            <button prop="TO_RESTART" text="Restart" text_en="Restart"/>
        </root>''',
        "TUV1.XML": '''<?xml version="1.0" encoding="UTF-8"?>
        <root>
            <switch prop="TUV_ENABLED" text="DHW enabled" text_en="DHW enabled"/>
            <number prop="TUV_TEPLOTA" text="DHW temp" text_en="DHW temp" min="40" max="60" step="1" unit="°C"/>
        </root>'''
    }


@pytest.fixture
def sample_entity_data():
    """Sample entity data from XCC pages."""
    return [
        {
            "attributes": {
                "field_name": "TO_POVOLENI",
                "value": "1",
                "friendly_name": "Heating enabled",
                "page": "okruh.xml",
                "unit": "",
            }
        },
        {
            "attributes": {
                "field_name": "TO_POZADOVANA", 
                "value": "21.5",
                "friendly_name": "Target temperature",
                "page": "okruh.xml",
                "unit": "°C",
            }
        },
        {
            "attributes": {
                "field_name": "TO_REZIM",
                "value": "0", 
                "friendly_name": "Heating mode",
                "page": "okruh.xml",
                "unit": "",
            }
        },
        {
            "attributes": {
                "field_name": "TO_RESTART",
                "value": "",
                "friendly_name": "Restart heating",
                "page": "okruh.xml", 
                "unit": "",
            }
        },
        {
            "attributes": {
                "field_name": "SOME_SENSOR",
                "value": "25.0",
                "friendly_name": "Temperature sensor",
                "page": "okruh.xml",
                "unit": "°C",
            }
        }
    ]


@pytest.mark.asyncio
async def test_coordinator_entity_type_detection(mock_hass, mock_config_entry, sample_descriptor_data, sample_entity_data):
    """Test that coordinator correctly detects entity types from descriptors."""
    
    with patch('coordinator.XCCClient') as mock_client_class:
        # Setup mock client
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        mock_client.fetch_descriptor_files.return_value = sample_descriptor_data
        mock_client.fetch_all_pages.return_value = sample_entity_data
        
        # Create coordinator
        coordinator = XCCDataUpdateCoordinator(mock_hass, mock_config_entry)
        
        # Load descriptors
        await coordinator._load_descriptors()
        
        # Verify descriptor parsing worked
        assert len(coordinator.entity_configs) == 6  # 4 from OKRUH + 2 from TUV1
        
        # Test entity type detection
        assert coordinator.get_entity_type("TO_POVOLENI") == "switch"
        assert coordinator.get_entity_type("TO_POZADOVANA") == "number" 
        assert coordinator.get_entity_type("TO_REZIM") == "select"
        assert coordinator.get_entity_type("TO_RESTART") == "button"
        assert coordinator.get_entity_type("TUV_ENABLED") == "switch"
        assert coordinator.get_entity_type("TUV_TEPLOTA") == "number"
        assert coordinator.get_entity_type("SOME_SENSOR") == "sensor"  # Not in descriptors
        
        # Test writability detection
        assert coordinator.is_writable("TO_POVOLENI") == True
        assert coordinator.is_writable("TO_POZADOVANA") == True
        assert coordinator.is_writable("TO_REZIM") == True
        assert coordinator.is_writable("TO_RESTART") == True
        assert coordinator.is_writable("SOME_SENSOR") == False  # Not in descriptors


@pytest.mark.asyncio
async def test_coordinator_entity_processing(mock_hass, mock_config_entry, sample_descriptor_data, sample_entity_data):
    """Test that coordinator processes entities into correct categories."""
    
    with patch('coordinator.XCCClient') as mock_client_class:
        # Setup mock client
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        mock_client.fetch_descriptor_files.return_value = sample_descriptor_data
        mock_client.fetch_all_pages.return_value = sample_entity_data
        
        # Create coordinator
        coordinator = XCCDataUpdateCoordinator(mock_hass, mock_config_entry)
        
        # Load descriptors first
        await coordinator._load_descriptors()
        
        # Process entities
        processed_data = coordinator._process_entities(sample_entity_data)
        
        # Verify entity categorization
        assert len(processed_data["switches"]) == 1  # TO_POVOLENI
        assert len(processed_data["numbers"]) == 1   # TO_POZADOVANA  
        assert len(processed_data["selects"]) == 1   # TO_REZIM
        assert len(processed_data["buttons"]) == 1   # TO_RESTART
        assert len(processed_data["sensors"]) == 1   # SOME_SENSOR
        
        # Verify entities list is created
        assert "entities" in processed_data
        assert len(processed_data["entities"]) == 5
        
        # Verify entity data structure
        entities = processed_data["entities"]
        switch_entity = next(e for e in entities if e["prop"] == "TO_POVOLENI")
        assert switch_entity["entity_id"] == "xcc_to_povoleni"
        assert switch_entity["state"] == "1"
        assert switch_entity["name"] == "Heating enabled"


@pytest.mark.asyncio 
async def test_coordinator_data_update_counts(mock_hass, mock_config_entry, sample_descriptor_data, sample_entity_data):
    """Test that coordinator reports correct entity counts after update."""
    
    with patch('coordinator.XCCClient') as mock_client_class:
        # Setup mock client
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        mock_client.fetch_descriptor_files.return_value = sample_descriptor_data
        mock_client.fetch_all_pages.return_value = sample_entity_data
        
        # Create coordinator
        coordinator = XCCDataUpdateCoordinator(mock_hass, mock_config_entry)
        
        # Perform data update
        await coordinator._async_update_data()
        
        # Verify data structure
        data = coordinator.data
        
        # Check that we have the correct counts (this would have caught the bug!)
        assert len(data["switches"]) > 0, "Should have switch entities, not all sensors!"
        assert len(data["numbers"]) > 0, "Should have number entities, not all sensors!"
        assert len(data["selects"]) > 0, "Should have select entities, not all sensors!"
        assert len(data["buttons"]) > 0, "Should have button entities, not all sensors!"
        
        # Verify entities list exists for new platforms
        assert "entities" in data
        assert len(data["entities"]) == 5


def test_entity_config_retrieval(mock_hass, mock_config_entry, sample_descriptor_data):
    """Test entity configuration retrieval."""
    
    with patch('coordinator.XCCClient'):
        coordinator = XCCDataUpdateCoordinator(mock_hass, mock_config_entry)
        
        # Manually set up entity configs (simulating descriptor loading)
        coordinator.entity_configs = {
            "TO_POZADOVANA": {
                "entity_type": "number",
                "min": 10.0,
                "max": 30.0,
                "step": 0.5,
                "unit": "°C",
                "friendly_name_en": "Target temperature"
            }
        }
        
        # Test config retrieval
        config = coordinator.get_entity_config("TO_POZADOVANA")
        assert config["entity_type"] == "number"
        assert config["min"] == 10.0
        assert config["max"] == 30.0
        assert config["unit"] == "°C"
        
        # Test non-existent entity
        config = coordinator.get_entity_config("NONEXISTENT")
        assert config == {}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
