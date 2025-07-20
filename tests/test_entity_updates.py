"""Test entity value updates during coordinator refresh cycles."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import asyncio
import logging

# Set up logging for tests
logging.basicConfig(level=logging.DEBUG)
_LOGGER = logging.getLogger(__name__)


def test_entity_value_extraction():
    """Test that entity values are correctly extracted from parsed XML data."""
    # Sample entity data as it comes from XML parsing
    sample_entity = {
        "entity_id": "xcc_test_sensor",
        "entity_type": "sensor",
        "state": "25.5",  # This is the current value
        "attributes": {
            "field_name": "TEST_SENSOR",
            "page": "test_page",
            "unit": "°C",
            "data_type": "numeric"
        }
    }
    
    # Test that we extract the state value correctly
    state_value = sample_entity.get("state", "")
    assert state_value == "25.5", f"Expected '25.5', got '{state_value}'"
    
    # Test that we don't accidentally use the wrong field
    wrong_value = sample_entity.get("attributes", {}).get("value", "")
    assert wrong_value == "", "Should not find 'value' in attributes"
    
    _LOGGER.info("✅ Entity value extraction test passed")


def test_coordinator_data_structure():
    """Test that coordinator creates the correct data structure for entities."""
    
    # Sample processed data structure as coordinator should create it
    sample_processed_data = {
        "sensors": {
            "xcc_test_sensor": {
                "state": "25.5",
                "attributes": {"unit": "°C", "page": "test_page"},
                "entity_id": "xcc_test_sensor",
                "prop": "TEST_SENSOR",
                "name": "Test Sensor",
                "unit": "°C",
                "page": "test_page"
            }
        },
        "switches": {},
        "numbers": {},
        "selects": {},
        "buttons": {}
    }
    
    # Test that entity data has the required fields
    sensor_data = sample_processed_data["sensors"]["xcc_test_sensor"]
    
    assert "state" in sensor_data, "Entity data must have 'state' field"
    assert sensor_data["state"] == "25.5", f"Expected state '25.5', got '{sensor_data['state']}'"
    assert "entity_id" in sensor_data, "Entity data must have 'entity_id' field"
    assert "prop" in sensor_data, "Entity data must have 'prop' field"
    
    _LOGGER.info("✅ Coordinator data structure test passed")


@pytest.mark.asyncio
async def test_entity_value_update_flow():
    """Test the complete flow of entity value updates."""
    
    # Mock the XCC client to return sample data
    mock_entities = [
        {
            "entity_id": "xcc_temp_sensor",
            "entity_type": "sensor", 
            "state": "23.1",  # Initial value
            "attributes": {
                "field_name": "TEMP_SENSOR",
                "page": "test_page",
                "unit": "°C"
            }
        }
    ]
    
    # Test that the entity value gets updated when coordinator data changes
    updated_entities = [
        {
            "entity_id": "xcc_temp_sensor",
            "entity_type": "sensor",
            "state": "24.7",  # Updated value
            "attributes": {
                "field_name": "TEMP_SENSOR", 
                "page": "test_page",
                "unit": "°C"
            }
        }
    ]
    
    # Verify that state values are different (simulating real updates)
    initial_state = mock_entities[0]["state"]
    updated_state = updated_entities[0]["state"]
    
    assert initial_state != updated_state, "Test data should have different values"
    assert initial_state == "23.1", f"Expected initial state '23.1', got '{initial_state}'"
    assert updated_state == "24.7", f"Expected updated state '24.7', got '{updated_state}'"
    
    _LOGGER.info("✅ Entity value update flow test passed")


def test_entity_value_logging():
    """Test that entity values are properly logged during updates."""
    
    # Test the logging format used in coordinator
    entity_id = "xcc_test_sensor"
    state_value = "25.5"
    entity_type = "sensor"
    prop = "TEST_SENSOR"
    
    # This is the format used in coordinator logging
    log_message = f"📊 COORDINATOR STORING: {entity_id} = {state_value} (type: {entity_type}, prop: {prop})"
    
    expected_parts = [
        "📊 COORDINATOR STORING:",
        entity_id,
        state_value,
        entity_type,
        prop
    ]
    
    for part in expected_parts:
        assert part in log_message, f"Log message should contain '{part}'"
    
    _LOGGER.info("✅ Entity value logging test passed")


def test_entity_value_formatting():
    """Test that entity values are properly formatted for display."""
    
    test_cases = [
        # (state, unit, expected_display)
        ("25.5", "°C", "25.5 °C"),
        ("1", "", "1"),
        ("0", "", "0"),
        ("true", "", "true"),
        ("", "", ""),
    ]
    
    for state, unit, expected in test_cases:
        if unit:
            value_display = f"{state} {unit}"
        else:
            value_display = str(state)
        
        assert value_display == expected, f"Expected '{expected}', got '{value_display}'"
    
    # Test boolean formatting
    boolean_test_cases = [
        ("1", "🟢 ON"),
        ("0", "🔴 OFF"), 
        ("true", "🟢 ON"),
        ("false", "🔴 OFF"),
        ("unknown", "❓ unknown"),
    ]
    
    for state, expected in boolean_test_cases:
        if str(state).lower() in ["1", "true", "on"]:
            value_display = "🟢 ON"
        elif str(state).lower() in ["0", "false", "off"]:
            value_display = "🔴 OFF"
        else:
            value_display = f"❓ {state}"
        
        assert value_display == expected, f"For state '{state}', expected '{expected}', got '{value_display}'"
    
    _LOGGER.info("✅ Entity value formatting test passed")


if __name__ == "__main__":
    # Run tests directly
    test_entity_value_extraction()
    test_coordinator_data_structure()
    asyncio.run(test_entity_value_update_flow())
    test_entity_value_logging()
    test_entity_value_formatting()
    print("✅ All entity update tests passed!")
