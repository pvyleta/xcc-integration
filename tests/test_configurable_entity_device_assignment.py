"""Test that configurable entities (number, switch, select) are assigned to correct devices."""

import pytest
from unittest.mock import Mock, patch
from custom_components.xcc.coordinator import XCCDataUpdateCoordinator
from custom_components.xcc.number import XCCNumber
from custom_components.xcc.switch import XCCSwitch
from custom_components.xcc.select import XCCSelect


@pytest.fixture
def mock_coordinator():
    """Create a mock coordinator with device assignment logic."""
    coordinator = Mock(spec=XCCDataUpdateCoordinator)
    coordinator.ip_address = "192.168.1.100"
    
    # Mock main device info
    coordinator.device_info = {
        "identifiers": {("xcc", "192.168.1.100")},
        "name": "XCC Controller (192.168.1.100)",
        "manufacturer": "XCC",
        "model": "Heat Pump Controller",
    }
    
    # Mock sub-device info for different pages
    coordinator.sub_device_info = {
        "FVE": {
            "identifiers": {("xcc", "192.168.1.100_fve")},
            "name": "XCC Photovoltaics",
            "manufacturer": "XCC",
            "model": "PV Module",
        },
        "OKRUH": {
            "identifiers": {("xcc", "192.168.1.100_okruh")},
            "name": "XCC Heating Circuit",
            "manufacturer": "XCC", 
            "model": "Heating Module",
        },
        "TUV1": {
            "identifiers": {("xcc", "192.168.1.100_tuv1")},
            "name": "XCC Hot Water",
            "manufacturer": "XCC",
            "model": "Hot Water Module",
        }
    }
    
    # Mock entity metadata storage
    coordinator.entities = {
        "xcc_fve_battery_charge": {
            "device": "FVE",
            "page": "FVE.XML",
            "prop": "FVE-BATTERY-CHARGE"
        },
        "xcc_okruh_temp_set": {
            "device": "OKRUH", 
            "page": "OKRUH1.XML",
            "prop": "OKRUH-TEMP-SET"
        },
        "xcc_tuv1_mode_select": {
            "device": "TUV1",
            "page": "TUV1.XML", 
            "prop": "TUV1-MODE-SELECT"
        }
    }
    
    def mock_get_device_info_for_entity(entity_id):
        """Mock device info lookup based on entity assignment."""
        entity_data = coordinator.entities.get(entity_id)
        if not entity_data:
            return coordinator.device_info
            
        device_name = entity_data.get("device")
        if device_name and device_name in coordinator.sub_device_info:
            return coordinator.sub_device_info[device_name]
            
        return coordinator.device_info
    
    coordinator.get_device_info_for_entity = mock_get_device_info_for_entity
    
    # Mock entity config methods
    coordinator.get_entity_config = Mock(return_value={
        "min": 0, "max": 100, "step": 1, "unit_en": "%"
    })
    coordinator._get_friendly_name = Mock(return_value="Test Entity")
    coordinator.language = "en"  # Add language attribute for select entities
    
    return coordinator


def test_number_entity_device_assignment(mock_coordinator):
    """Test that number entities are assigned to correct devices."""
    # Test FVE device assignment
    entity_data = {
        "entity_id": "xcc_fve_battery_charge",
        "prop": "FVE-BATTERY-CHARGE",
        "name": "Battery Charge",
        "device": "FVE"
    }
    
    number_entity = XCCNumber(mock_coordinator, entity_data)
    
    # Verify device info is from FVE device, not main controller
    assert number_entity._attr_device_info["name"] == "XCC Photovoltaics"
    assert number_entity._attr_device_info["identifiers"] == {("xcc", "192.168.1.100_fve")}
    assert number_entity._attr_device_info["model"] == "PV Module"
    
    print("✅ Number entity correctly assigned to FVE device")


def test_switch_entity_device_assignment(mock_coordinator):
    """Test that switch entities are assigned to correct devices."""
    # Test OKRUH device assignment  
    entity_data = {
        "entity_id": "xcc_okruh_temp_set",
        "prop": "OKRUH-TEMP-SET",
        "name": "Temperature Set",
        "device": "OKRUH"
    }
    
    switch_entity = XCCSwitch(mock_coordinator, entity_data)
    
    # Verify device info is from OKRUH device, not main controller
    assert switch_entity._attr_device_info["name"] == "XCC Heating Circuit"
    assert switch_entity._attr_device_info["identifiers"] == {("xcc", "192.168.1.100_okruh")}
    assert switch_entity._attr_device_info["model"] == "Heating Module"
    
    print("✅ Switch entity correctly assigned to OKRUH device")


def test_select_entity_device_assignment(mock_coordinator):
    """Test that select entities are assigned to correct devices."""
    # Test TUV1 device assignment
    entity_data = {
        "entity_id": "xcc_tuv1_mode_select", 
        "prop": "TUV1-MODE-SELECT",
        "name": "Mode Select",
        "device": "TUV1"
    }
    
    # Mock select-specific config
    mock_coordinator.get_entity_config.return_value = {
        "options": [
            {"value": "auto", "text_en": "Auto", "text": "Auto"},
            {"value": "manual", "text_en": "Manual", "text": "Manual"},
            {"value": "off", "text_en": "Off", "text": "Off"}
        ],
        "unit_en": ""
    }
    
    select_entity = XCCSelect(mock_coordinator, entity_data)
    
    # Verify device info is from TUV1 device, not main controller
    assert select_entity._attr_device_info["name"] == "XCC Hot Water"
    assert select_entity._attr_device_info["identifiers"] == {("xcc", "192.168.1.100_tuv1")}
    assert select_entity._attr_device_info["model"] == "Hot Water Module"
    
    print("✅ Select entity correctly assigned to TUV1 device")


def test_fallback_to_main_device(mock_coordinator):
    """Test that entities without device assignment fall back to main device."""
    # Test entity not in coordinator.entities (should fallback to main device)
    entity_data = {
        "entity_id": "xcc_unknown_entity",
        "prop": "UNKNOWN-PROP", 
        "name": "Unknown Entity",
        "device": "UNKNOWN"
    }
    
    number_entity = XCCNumber(mock_coordinator, entity_data)
    
    # Should fallback to main controller device
    assert number_entity._attr_device_info["name"] == "XCC Controller (192.168.1.100)"
    assert number_entity._attr_device_info["identifiers"] == {("xcc", "192.168.1.100")}
    assert number_entity._attr_device_info["model"] == "Heat Pump Controller"
    
    print("✅ Unknown entity correctly falls back to main controller device")


def test_device_assignment_consistency():
    """Test that device assignment is consistent across entity types."""
    print("\n🔍 DEVICE ASSIGNMENT CONSISTENCY TEST")
    print("=" * 50)
    
    # Verify that all configurable entity types use the same device assignment method
    from custom_components.xcc import number, switch, select
    import inspect
    
    # Check that all entity types call get_device_info_for_entity
    number_source = inspect.getsource(number.XCCNumber.__init__)
    switch_source = inspect.getsource(switch.XCCSwitch.__init__)  
    select_source = inspect.getsource(select.XCCSelect.__init__)
    
    assert "get_device_info_for_entity" in number_source, "Number entity should use get_device_info_for_entity"
    assert "get_device_info_for_entity" in switch_source, "Switch entity should use get_device_info_for_entity"
    assert "get_device_info_for_entity" in select_source, "Select entity should use get_device_info_for_entity"
    
    # Verify they don't use hardcoded coordinator.device_info
    assert "coordinator.device_info" not in number_source.replace("get_device_info_for_entity", ""), "Number should not use hardcoded device_info"
    assert "coordinator.device_info" not in switch_source.replace("get_device_info_for_entity", ""), "Switch should not use hardcoded device_info"  
    assert "coordinator.device_info" not in select_source.replace("get_device_info_for_entity", ""), "Select should not use hardcoded device_info"
    
    print("✅ All configurable entity types use proper device assignment")
    print("✅ No hardcoded device_info usage found")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
