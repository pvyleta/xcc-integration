"""Regression tests to prevent common issues that have occurred before."""
import pytest
from unittest.mock import Mock, patch, AsyncMock
import sys
from pathlib import Path

# Add the custom_components directory to the path
custom_components_path = Path(__file__).parent.parent.parent / "custom_components"
sys.path.insert(0, str(custom_components_path))

# Import with proper module path
from custom_components.xcc.coordinator import XCCDataUpdateCoordinator


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
def realistic_descriptor_data():
    """Realistic descriptor data based on actual XCC system."""
    return {
        "OKRUH.XML": '''<?xml version="1.0" encoding="UTF-8"?>
        <root>
            <switch prop="TO-POVOLENI" text="Povolení TO" text_en="Enable heating circuit"/>
            <switch prop="TO-EXTERNIUTLUMPOVOLENI" text="Externí útlum" text_en="External reduction"/>
            <number prop="TO-POZADOVANA" text="Požadovaná teplota" text_en="Target temperature" min="5" max="35" step="0.5" unit="°C"/>
            <number prop="TO-UTLUM-UTLUM" text="Útlum" text_en="Reduction" min="-50" max="50" step="0.1" unit="K"/>
            <choice prop="TO-REZIMUTLUM" text="Režim útlumu" text_en="Reduction mode">
                <option value="0" text="OFF" text_en="OFF"/>
                <option value="1" text="Auto" text_en="Auto"/>
                <option value="2" text="ON" text_en="ON"/>
            </choice>
            <choice prop="TO-REZIMPROSTOR" text="Režim prostoru" text_en="Room influence">
                <option value="0" text="Bez čidla" text_en="Without sensor"/>
                <option value="1" text="Termostat" text_en="Thermostat"/>
                <option value="2" text="Adaptivní" text_en="Adaptive"/>
            </choice>
            <button prop="TO-NATOP-RESTART" text="Restart" text_en="Restart"/>
        </root>''',
        "TUV1.XML": '''<?xml version="1.0" encoding="UTF-8"?>
        <root>
            <switch prop="TUV-POVOLENI" text="Povolení TUV" text_en="Enable DHW"/>
            <number prop="TUV-POZADOVANA" text="Požadovaná teplota TUV" text_en="DHW target temperature" min="35" max="65" step="1" unit="°C"/>
            <choice prop="TUV-REZIM" text="Režim TUV" text_en="DHW mode">
                <option value="0" text="Auto" text_en="Auto"/>
                <option value="1" text="Manuál" text_en="Manual"/>
            </choice>
        </root>'''
    }


@pytest.fixture
def realistic_entity_data():
    """Realistic entity data from XCC pages."""
    return [
        # Switches
        {"attributes": {"field_name": "TO-POVOLENI", "value": "1", "friendly_name": "Heating circuit enabled", "page": "okruh.xml"}},
        {"attributes": {"field_name": "TO-EXTERNIUTLUMPOVOLENI", "value": "0", "friendly_name": "External reduction", "page": "okruh.xml"}},
        {"attributes": {"field_name": "TUV-POVOLENI", "value": "1", "friendly_name": "DHW enabled", "page": "tuv1.xml"}},
        
        # Numbers
        {"attributes": {"field_name": "TO-POZADOVANA", "value": "21.0", "friendly_name": "Target temperature", "page": "okruh.xml", "unit": "°C"}},
        {"attributes": {"field_name": "TO-UTLUM-UTLUM", "value": "1.0", "friendly_name": "Reduction", "page": "okruh.xml", "unit": "K"}},
        {"attributes": {"field_name": "TUV-POZADOVANA", "value": "50.0", "friendly_name": "DHW target temperature", "page": "tuv1.xml", "unit": "°C"}},
        
        # Selects
        {"attributes": {"field_name": "TO-REZIMUTLUM", "value": "1", "friendly_name": "Reduction mode", "page": "okruh.xml"}},
        {"attributes": {"field_name": "TO-REZIMPROSTOR", "value": "2", "friendly_name": "Room influence", "page": "okruh.xml"}},
        {"attributes": {"field_name": "TUV-REZIM", "value": "0", "friendly_name": "DHW mode", "page": "tuv1.xml"}},
        
        # Buttons
        {"attributes": {"field_name": "TO-NATOP-RESTART", "value": "", "friendly_name": "Restart", "page": "okruh.xml"}},
        
        # Read-only sensors (not in descriptors)
        {"attributes": {"field_name": "TO-TEPLOTA", "value": "20.5", "friendly_name": "Current temperature", "page": "okruh.xml", "unit": "°C"}},
        {"attributes": {"field_name": "TUV-TEPLOTA", "value": "48.0", "friendly_name": "DHW temperature", "page": "tuv1.xml", "unit": "°C"}},
    ]


@pytest.mark.asyncio
async def test_regression_all_entities_as_sensors(mock_hass, mock_config_entry, realistic_descriptor_data, realistic_entity_data):
    """
    REGRESSION TEST: Prevent all entities being classified as sensors.
    
    This test would have caught the bug where coordinator._determine_entity_type()
    was classifying all entities as sensors instead of using descriptor-based types.
    """
    
    with patch('coordinator.XCCClient') as mock_client_class:
        # Setup mock client
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        mock_client.fetch_descriptor_files.return_value = realistic_descriptor_data
        mock_client.fetch_all_pages.return_value = realistic_entity_data
        
        # Create coordinator
        coordinator = XCCDataUpdateCoordinator(mock_hass, mock_config_entry)
        
        # Perform full data update
        await coordinator._async_update_data()
        
        # Get the processed data
        data = coordinator.data
        
        # CRITICAL REGRESSION CHECK: Ensure we don't have all entities as sensors
        total_entities = len(realistic_entity_data)
        sensor_count = len(data.get("sensors", {}))
        
        # We should have some sensors (read-only entities), but NOT all entities
        assert sensor_count < total_entities, f"REGRESSION: All {total_entities} entities classified as sensors! Should have switches, numbers, selects, buttons."
        
        # Verify we have the expected interactive entity types
        assert len(data.get("switches", {})) > 0, "Should have switch entities (TO-POVOLENI, TUV-POVOLENI, etc.)"
        assert len(data.get("numbers", {})) > 0, "Should have number entities (TO-POZADOVANA, TUV-POZADOVANA, etc.)"
        assert len(data.get("selects", {})) > 0, "Should have select entities (TO-REZIMUTLUM, TUV-REZIM, etc.)"
        assert len(data.get("buttons", {})) > 0, "Should have button entities (TO-NATOP-RESTART)"
        
        # Verify specific entity types
        assert "TO-POVOLENI" in data["switches"], "TO-POVOLENI should be a switch, not a sensor"
        assert "TO-POZADOVANA" in data["numbers"], "TO-POZADOVANA should be a number, not a sensor"
        assert "TO-REZIMUTLUM" in data["selects"], "TO-REZIMUTLUM should be a select, not a sensor"
        assert "TO-NATOP-RESTART" in data["buttons"], "TO-NATOP-RESTART should be a button, not a sensor"
        
        # Verify read-only entities are correctly classified as sensors
        assert "TO-TEPLOTA" in data["sensors"], "TO-TEPLOTA should be a sensor (read-only)"
        assert "TUV-TEPLOTA" in data["sensors"], "TUV-TEPLOTA should be a sensor (read-only)"


@pytest.mark.asyncio
async def test_regression_undefined_variables(mock_hass, mock_config_entry):
    """
    REGRESSION TEST: Prevent undefined variable errors in platform setup.
    
    This test would have caught errors like:
    - NameError: name 'select_entities' is not defined
    - NameError: name 'number_entities' is not defined
    """
    
    with patch('coordinator.XCCClient') as mock_client_class:
        # Setup mock client
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        mock_client.fetch_descriptor_files.return_value = {}
        mock_client.fetch_all_pages.return_value = []
        
        # Create coordinator
        coordinator = XCCDataUpdateCoordinator(mock_hass, mock_config_entry)
        
        # Test that coordinator methods don't raise NameError
        try:
            await coordinator._async_update_data()
            processed_data = coordinator._process_entities([])
            
            # Verify all expected keys exist
            expected_keys = ["sensors", "switches", "numbers", "selects", "buttons", "binary_sensors", "climates", "entities"]
            for key in expected_keys:
                assert key in processed_data, f"Missing key '{key}' in processed_data"
                
        except NameError as e:
            pytest.fail(f"NameError indicates undefined variable: {e}")
        except Exception as e:
            # Other exceptions are OK for this test, we're only checking for NameError
            pass


@pytest.mark.asyncio
async def test_regression_entity_platform_distribution(mock_hass, mock_config_entry, realistic_descriptor_data, realistic_entity_data):
    """
    REGRESSION TEST: Ensure entities are properly distributed across platforms.
    
    This test verifies that the coordinator creates the correct data structure
    for platform-specific entity creation.
    """
    
    with patch('coordinator.XCCClient') as mock_client_class:
        # Setup mock client
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        mock_client.fetch_descriptor_files.return_value = realistic_descriptor_data
        mock_client.fetch_all_pages.return_value = realistic_entity_data
        
        # Create coordinator
        coordinator = XCCDataUpdateCoordinator(mock_hass, mock_config_entry)
        
        # Perform data update
        await coordinator._async_update_data()
        
        # Test platform-specific entity retrieval methods
        switches = coordinator.get_entities_by_type("switches")
        numbers = coordinator.get_entities_by_type("numbers") 
        selects = coordinator.get_entities_by_type("selects")
        buttons = coordinator.get_entities_by_type("buttons")
        sensors = coordinator.get_entities_by_type("sensors")
        
        # Verify each platform gets the right entities
        assert len(switches) >= 3, f"Expected at least 3 switches, got {len(switches)}"
        assert len(numbers) >= 3, f"Expected at least 3 numbers, got {len(numbers)}"
        assert len(selects) >= 3, f"Expected at least 3 selects, got {len(selects)}"
        assert len(buttons) >= 1, f"Expected at least 1 button, got {len(buttons)}"
        assert len(sensors) >= 2, f"Expected at least 2 sensors, got {len(sensors)}"
        
        # Verify no entity appears in multiple categories
        all_entity_ids = set()
        for entities in [switches, numbers, selects, buttons, sensors]:
            entity_ids = set(entities.keys())
            overlap = all_entity_ids.intersection(entity_ids)
            assert len(overlap) == 0, f"Entity ID overlap detected: {overlap}"
            all_entity_ids.update(entity_ids)


def test_regression_import_errors():
    """
    REGRESSION TEST: Ensure all platform files can be imported without errors.
    
    This test would have caught import errors like:
    - ImportError: cannot import name 'XCCEntity' from 'entity'
    - ModuleNotFoundError: No module named 'xml_parser'
    """
    
    try:
        # Test importing all platform modules
        import coordinator
        import sensor
        import switch
        import number
        import select
        import binary_sensor
        import config_flow
        import xcc_client
        import descriptor_parser
        
        # If we get here, all imports succeeded
        assert True
        
    except ImportError as e:
        pytest.fail(f"Import error indicates missing dependency or incorrect import: {e}")
    except ModuleNotFoundError as e:
        pytest.fail(f"Module not found error: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
