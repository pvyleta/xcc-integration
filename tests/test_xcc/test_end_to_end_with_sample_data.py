"""End-to-end tests using real sample data from sample_data folder."""
import pytest
from unittest.mock import Mock, patch, AsyncMock
import sys
from pathlib import Path

# Add the custom_components directory to the path
custom_components_path = Path(__file__).parent.parent.parent / "custom_components"
sys.path.insert(0, str(custom_components_path))

# Import with proper module path
from custom_components.xcc.coordinator import XCCDataUpdateCoordinator
from custom_components.xcc.descriptor_parser import XCCDescriptorParser
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


@pytest.mark.asyncio
async def test_end_to_end_descriptor_parsing_with_real_data(mock_hass, mock_config_entry, real_descriptor_files):
    """Test complete descriptor parsing flow with real sample data."""
    
    # Verify we have the expected descriptor files
    expected_files = ["STAVJED.XML", "OKRUH.XML", "TUV1.XML", "BIV.XML", "FVE.XML", "SPOT.XML"]
    for filename in expected_files:
        assert filename in real_descriptor_files, f"Missing descriptor file: {filename}"
    
    with patch('custom_components.xcc.xcc_client.XCCClient') as mock_client_class:
        # Setup mock client to return real descriptor data
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        mock_client.fetch_descriptor_files.return_value = real_descriptor_files
        
        # Create coordinator
        coordinator = XCCDataUpdateCoordinator(mock_hass, mock_config_entry)
        
        # Load descriptors using real data
        await coordinator._load_descriptors(mock_client)
        
        # Verify descriptor parsing worked with real data
        assert len(coordinator.entity_configs) > 400, f"Expected >400 entities, got {len(coordinator.entity_configs)}"
        
        # Verify we have the expected entity types from real descriptors
        entity_types = {}
        for config in coordinator.entity_configs.values():
            entity_type = config.get('entity_type', 'unknown')
            entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
        
        # Based on our analysis, we expect these counts from real descriptors
        assert entity_types.get('switch', 0) > 90, f"Expected >90 switches, got {entity_types.get('switch', 0)}"
        assert entity_types.get('number', 0) > 250, f"Expected >250 numbers, got {entity_types.get('number', 0)}"
        assert entity_types.get('select', 0) > 50, f"Expected >50 selects, got {entity_types.get('select', 0)}"
        assert entity_types.get('button', 0) >= 2, f"Expected >=2 buttons, got {entity_types.get('button', 0)}"
        
        print(f"✅ Real descriptor parsing: {entity_types}")


@pytest.mark.asyncio
async def test_end_to_end_data_parsing_with_real_data(mock_hass, mock_config_entry, real_data_files):
    """Test complete data parsing flow with real sample data."""
    
    # Verify we have the expected data files
    expected_files = ["STAVJED1.XML", "OKRUH10.XML", "TUV11.XML", "BIV1.XML", "FVE4.XML", "SPOT1.XML"]
    for filename in expected_files:
        assert filename in real_data_files, f"Missing data file: {filename}"
    
    # Test parsing each real data file
    total_entities = 0
    for filename, content in real_data_files.items():
        entities = parse_xml_entities(content, filename)
        assert len(entities) > 0, f"No entities parsed from {filename}"
        total_entities += len(entities)
        print(f"✅ Parsed {len(entities)} entities from {filename}")
    
    assert total_entities > 500, f"Expected >500 total entities, got {total_entities}"
    print(f"✅ Total entities from real data: {total_entities}")


@pytest.mark.asyncio
async def test_end_to_end_complete_flow_with_real_data(mock_hass, mock_config_entry, real_descriptor_files, real_data_files):
    """Test complete flow from descriptor loading to entity creation with real sample data."""
    
    with patch('custom_components.xcc.xcc_client.XCCClient') as mock_client_class:
        # Setup mock client to return real data
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        mock_client.fetch_descriptor_files.return_value = real_descriptor_files
        
        # Parse real data files to create entity list
        all_entities = []
        for filename, content in real_data_files.items():
            entities = parse_xml_entities(content, filename)
            all_entities.extend(entities)
        
        mock_client.fetch_all_pages.return_value = all_entities
        
        # Create coordinator
        coordinator = XCCDataUpdateCoordinator(mock_hass, mock_config_entry)
        
        # Perform complete data update with real data
        await coordinator._async_update_data()
        
        # Verify the complete flow worked
        data = coordinator.data
        
        # CRITICAL REGRESSION CHECK: Ensure we don't have all entities as sensors
        total_entities = len(all_entities)
        sensor_count = len(data.get("sensors", {}))
        
        assert sensor_count < total_entities, f"REGRESSION: All {total_entities} entities classified as sensors! Should have switches, numbers, selects, buttons."
        
        # Verify we have the expected interactive entity types from real data
        switches = data.get("switches", {})
        numbers = data.get("numbers", {})
        selects = data.get("selects", {})
        buttons = data.get("buttons", {})
        sensors = data.get("sensors", {})
        
        # Based on real descriptor analysis, verify expected counts
        assert len(switches) > 90, f"Expected >90 switches from real data, got {len(switches)}"
        assert len(numbers) > 250, f"Expected >250 numbers from real data, got {len(numbers)}"
        assert len(selects) > 50, f"Expected >50 selects from real data, got {len(selects)}"
        assert len(buttons) >= 2, f"Expected >=2 buttons from real data, got {len(buttons)}"
        
        # Verify entities list is created for new platforms
        assert "entities" in data, "Missing 'entities' list for new platform approach"
        entities_list = data["entities"]
        assert len(entities_list) == total_entities, f"Entities list length mismatch: {len(entities_list)} vs {total_entities}"
        
        # Verify specific known entities from real data exist and have correct types
        known_entities = {
            "TO-POVOLENI": "switches",  # Known switch from OKRUH.XML
            "TO-POZADOVANA": "numbers",  # Known number from OKRUH.XML
            "TO-REZIMPROSTOR": "selects",  # Known select from OKRUH.XML
        }
        
        for entity_prop, expected_category in known_entities.items():
            assert entity_prop in data[expected_category], f"{entity_prop} should be in {expected_category}, not sensors"
            
            # Verify entity data structure
            entity_in_list = next((e for e in entities_list if e["prop"] == entity_prop), None)
            assert entity_in_list is not None, f"Entity {entity_prop} missing from entities list"
            assert entity_in_list["entity_id"] == f"xcc_{entity_prop.lower().replace('-', '_')}", f"Incorrect entity_id for {entity_prop}"
        
        print(f"✅ Complete flow with real data:")
        print(f"   Switches: {len(switches)}")
        print(f"   Numbers: {len(numbers)}")
        print(f"   Selects: {len(selects)}")
        print(f"   Buttons: {len(buttons)}")
        print(f"   Sensors: {len(sensors)}")
        print(f"   Total: {total_entities}")


@pytest.mark.asyncio
async def test_platform_entity_creation_simulation(mock_hass, mock_config_entry, real_descriptor_files, real_data_files):
    """Test that platform entity creation would work with real data."""
    
    with patch('custom_components.xcc.xcc_client.XCCClient') as mock_client_class:
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
        
        # Create coordinator
        coordinator = XCCDataUpdateCoordinator(mock_hass, mock_config_entry)
        await coordinator._async_update_data()
        
        # Simulate what each platform would do
        platforms_to_test = ["sensor", "switch", "number", "select", "button"]
        
        for platform in platforms_to_test:
            # Get entities for this platform
            platform_entities = coordinator.get_entities_by_type(f"{platform}s")
            
            if len(platform_entities) > 0:
                print(f"✅ {platform.title()} platform would create {len(platform_entities)} entities")
                
                # Test a few entities from each platform
                for i, (prop, entity_data) in enumerate(list(platform_entities.items())[:3]):
                    # Verify entity has required data
                    assert "data" in entity_data, f"Missing 'data' in entity {prop}"
                    assert "type" in entity_data, f"Missing 'type' in entity {prop}"
                    assert "page" in entity_data, f"Missing 'page' in entity {prop}"
                    
                    # Verify entity type matches platform
                    expected_type = platform if platform != "button" else "button"
                    assert coordinator.get_entity_type(prop) == expected_type, f"Entity {prop} type mismatch"
                    
                    # Verify writability for interactive entities
                    if platform in ["switch", "number", "select", "button"]:
                        assert coordinator.is_writable(prop), f"Interactive entity {prop} should be writable"
            else:
                print(f"⚠️  {platform.title()} platform would create 0 entities")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
