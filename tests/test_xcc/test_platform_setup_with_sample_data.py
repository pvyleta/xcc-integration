"""Test platform setup process using real sample data."""
import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import sys
from pathlib import Path

# Add the custom_components directory to the path
custom_components_path = Path(__file__).parent.parent.parent / "custom_components"
sys.path.insert(0, str(custom_components_path))

# Import with proper module path
from custom_components.xcc.coordinator import XCCDataUpdateCoordinator
from custom_components.xcc.xcc_client import parse_xml_entities


@pytest.fixture
def sample_data_dir():
    """Get the sample data directory."""
    return Path(__file__).parent.parent.parent / "sample_data"


@pytest.fixture
def real_descriptor_files(sample_data_dir):
    """Load real descriptor files from sample_data."""
    descriptor_files = {}
    descriptor_names = ["STAVJED.XML", "OKRUH.XML", "TUV1.XML", "BIV.XML", "FVE.XML", "SPOT.XML"]
    
    for filename in descriptor_names:
        file_path = sample_data_dir / filename
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                descriptor_files[filename] = f.read()
    
    return descriptor_files


@pytest.fixture
def real_data_files(sample_data_dir):
    """Load real data files from sample_data."""
    data_files = {}
    data_names = ["STAVJED1.XML", "OKRUH10.XML", "TUV11.XML", "BIV1.XML", "FVE4.XML", "SPOT1.XML"]
    
    for filename in data_names:
        file_path = sample_data_dir / filename
        if file_path.exists():
            with open(file_path, 'r', encoding='windows-1250') as f:
                data_files[filename] = f.read()
    
    return data_files


@pytest.fixture
def mock_hass():
    """Create a mock Home Assistant instance."""
    hass = Mock()
    hass.config_entries = Mock()
    hass.data = {}
    return hass


@pytest.fixture
def mock_config_entry():
    """Create a mock config entry."""
    entry = Mock()
    entry.data = {
        "ip_address": "192.168.1.100",  # Use correct key
        "username": "test_user",
        "password": "test_pass",
        "entity_mode": "integration",
    }
    entry.entry_id = "test_entry_id"
    return entry


@pytest.fixture
async def coordinator_with_real_data(mock_hass, mock_config_entry, real_descriptor_files, real_data_files):
    """Create a coordinator loaded with real sample data."""
    with patch('custom_components.xcc.coordinator.XCCClient') as mock_client_class:
        # Setup mock client
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        mock_client.fetch_descriptor_files.return_value = real_descriptor_files
        
        # Parse real data files
        all_entities = []
        for filename, content in real_data_files.items():
            entities = parse_xml_entities(content, filename)
            all_entities.extend(entities)
        
        mock_client.fetch_all_pages.return_value = all_entities
        
        # Create and initialize coordinator
        coordinator = XCCDataUpdateCoordinator(mock_hass, mock_config_entry)
        await coordinator._async_update_data()
        
        return coordinator


@pytest.mark.asyncio
async def test_sensor_platform_setup_with_real_data(coordinator_with_real_data, mock_hass, mock_config_entry):
    """Test sensor platform setup with real sample data."""
    coordinator = coordinator_with_real_data
    
    # Mock the sensor platform setup
    mock_async_add_entities = Mock()
    
    # Import and test sensor platform
    try:
        import sensor
        
        # Simulate sensor platform setup
        with patch('sensor.async_add_entities', mock_async_add_entities):
            await sensor.async_setup_entry(mock_hass, mock_config_entry, mock_async_add_entities)
        
        # Verify sensor entities were created
        assert mock_async_add_entities.called, "async_add_entities should be called for sensors"
        
        # Get the entities that would be created
        call_args = mock_async_add_entities.call_args
        if call_args:
            sensor_entities = call_args[0][0]  # First argument is the entities list
            assert len(sensor_entities) > 0, "Should create some sensor entities"
            print(f"✅ Sensor platform would create {len(sensor_entities)} entities")
            
            # Verify sensor entities are read-only
            for entity in sensor_entities[:5]:  # Check first 5
                prop = entity.coordinator.entities[entity._entity_id]["data"]["attributes"]["field_name"]
                assert not coordinator.is_writable(prop), f"Sensor {prop} should not be writable"
        
    except ImportError as e:
        pytest.skip(f"Cannot import sensor platform: {e}")


@pytest.mark.asyncio
async def test_switch_platform_setup_with_real_data(coordinator_with_real_data, mock_hass, mock_config_entry):
    """Test switch platform setup with real sample data."""
    coordinator = coordinator_with_real_data
    
    # Mock the switch platform setup
    mock_async_add_entities = Mock()
    
    try:
        import switch
        
        # Simulate switch platform setup
        with patch('switch.async_add_entities', mock_async_add_entities):
            await switch.async_setup_entry(mock_hass, mock_config_entry, mock_async_add_entities)
        
        # Verify switch entities were created
        assert mock_async_add_entities.called, "async_add_entities should be called for switches"
        
        call_args = mock_async_add_entities.call_args
        if call_args:
            switch_entities = call_args[0][0]
            assert len(switch_entities) > 0, "Should create some switch entities"
            print(f"✅ Switch platform would create {len(switch_entities)} entities")
            
            # Verify switch entities are writable
            for entity in switch_entities[:5]:  # Check first 5
                prop = entity.coordinator.entities[entity._entity_id]["data"]["attributes"]["field_name"]
                assert coordinator.is_writable(prop), f"Switch {prop} should be writable"
                assert coordinator.get_entity_type(prop) == "switch", f"Entity {prop} should be switch type"
        
    except ImportError as e:
        pytest.skip(f"Cannot import switch platform: {e}")


@pytest.mark.asyncio
async def test_number_platform_setup_with_real_data(coordinator_with_real_data, mock_hass, mock_config_entry):
    """Test number platform setup with real sample data."""
    coordinator = coordinator_with_real_data
    
    # Mock the number platform setup
    mock_async_add_entities = Mock()
    
    try:
        import number
        
        # Simulate number platform setup
        with patch('number.async_add_entities', mock_async_add_entities):
            await number.async_setup_entry(mock_hass, mock_config_entry, mock_async_add_entities)
        
        # Verify number entities were created
        assert mock_async_add_entities.called, "async_add_entities should be called for numbers"
        
        call_args = mock_async_add_entities.call_args
        if call_args:
            number_entities = call_args[0][0]
            assert len(number_entities) > 0, "Should create some number entities"
            print(f"✅ Number platform would create {len(number_entities)} entities")
            
            # Verify number entities have proper configuration
            for entity in number_entities[:5]:  # Check first 5
                prop = entity.coordinator.entities[entity._entity_id]["data"]["attributes"]["field_name"]
                assert coordinator.is_writable(prop), f"Number {prop} should be writable"
                assert coordinator.get_entity_type(prop) == "number", f"Entity {prop} should be number type"
                
                # Verify number entity has min/max if available
                config = coordinator.get_entity_config(prop)
                if config.get("min") is not None:
                    assert hasattr(entity, 'native_min_value'), f"Number {prop} should have min_value"
                if config.get("max") is not None:
                    assert hasattr(entity, 'native_max_value'), f"Number {prop} should have max_value"
        
    except ImportError as e:
        pytest.skip(f"Cannot import number platform: {e}")


@pytest.mark.asyncio
async def test_select_platform_setup_with_real_data(coordinator_with_real_data, mock_hass, mock_config_entry):
    """Test select platform setup with real sample data."""
    coordinator = coordinator_with_real_data
    
    # Mock the select platform setup
    mock_async_add_entities = Mock()
    
    try:
        import select
        
        # Simulate select platform setup
        with patch('select.async_add_entities', mock_async_add_entities):
            await select.async_setup_entry(mock_hass, mock_config_entry, mock_async_add_entities)
        
        # Verify select entities were created
        assert mock_async_add_entities.called, "async_add_entities should be called for selects"
        
        call_args = mock_async_add_entities.call_args
        if call_args:
            select_entities = call_args[0][0]
            assert len(select_entities) > 0, "Should create some select entities"
            print(f"✅ Select platform would create {len(select_entities)} entities")
            
            # Verify select entities have options
            for entity in select_entities[:5]:  # Check first 5
                prop = entity.coordinator.entities[entity._entity_id]["data"]["attributes"]["field_name"]
                assert coordinator.is_writable(prop), f"Select {prop} should be writable"
                assert coordinator.get_entity_type(prop) == "select", f"Entity {prop} should be select type"
                
                # Verify select entity has options
                config = coordinator.get_entity_config(prop)
                options = config.get("options", [])
                assert len(options) > 0, f"Select {prop} should have options"
        
    except ImportError as e:
        pytest.skip(f"Cannot import select platform: {e}")


@pytest.mark.asyncio
async def test_all_platforms_no_entity_overlap(coordinator_with_real_data, mock_hass, mock_config_entry):
    """Test that no entity appears in multiple platforms."""
    coordinator = coordinator_with_real_data
    
    # Collect all entities that would be created by each platform
    all_platform_entities = {}
    platforms = ["sensor", "switch", "number", "select", "button"]
    
    for platform in platforms:
        platform_entities = coordinator.get_entities_by_type(f"{platform}s")
        all_platform_entities[platform] = set(platform_entities.keys())
        print(f"{platform.title()}: {len(platform_entities)} entities")
    
    # Check for overlaps between platforms
    for i, platform1 in enumerate(platforms):
        for platform2 in platforms[i+1:]:
            overlap = all_platform_entities[platform1].intersection(all_platform_entities[platform2])
            assert len(overlap) == 0, f"Entity overlap between {platform1} and {platform2}: {overlap}"
    
    # Verify total entity count matches
    total_platform_entities = sum(len(entities) for entities in all_platform_entities.values())
    total_coordinator_entities = len(coordinator.entities)
    
    assert total_platform_entities == total_coordinator_entities, \
        f"Platform entity count mismatch: {total_platform_entities} vs {total_coordinator_entities}"
    
    print(f"✅ No entity overlap detected across {len(platforms)} platforms")
    print(f"✅ Total entities distributed: {total_platform_entities}")


@pytest.mark.asyncio
async def test_entity_data_structure_for_platforms(coordinator_with_real_data):
    """Test that entity data structure is correct for platform consumption."""
    coordinator = coordinator_with_real_data
    
    # Test a few entities from each type
    test_entities = {
        "switches": 3,
        "numbers": 3, 
        "selects": 3,
        "sensors": 3
    }
    
    for entity_type, count in test_entities.items():
        entities = coordinator.get_entities_by_type(entity_type)
        
        if len(entities) >= count:
            for i, (prop, entity_data) in enumerate(list(entities.items())[:count]):
                # Verify required fields exist
                assert "data" in entity_data, f"Missing 'data' in {entity_type} entity {prop}"
                assert "type" in entity_data, f"Missing 'type' in {entity_type} entity {prop}"
                assert "page" in entity_data, f"Missing 'page' in {entity_type} entity {prop}"
                
                # Verify data structure
                data = entity_data["data"]
                assert "attributes" in data, f"Missing 'attributes' in {entity_type} entity {prop}"
                
                attributes = data["attributes"]
                assert "field_name" in attributes, f"Missing 'field_name' in {entity_type} entity {prop}"
                assert "friendly_name" in attributes, f"Missing 'friendly_name' in {entity_type} entity {prop}"
                assert "value" in attributes, f"Missing 'value' in {entity_type} entity {prop}"
                
                # Verify entity type consistency
                expected_type = entity_type.rstrip('s')  # Remove plural 's'
                actual_type = coordinator.get_entity_type(prop)
                assert actual_type == expected_type, f"Type mismatch for {prop}: expected {expected_type}, got {actual_type}"
    
    print("✅ Entity data structure validation passed for all platforms")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
