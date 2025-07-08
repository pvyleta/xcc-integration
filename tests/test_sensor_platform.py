"""Tests for XCC sensor platform."""
import pytest
from unittest.mock import MagicMock, AsyncMock
from custom_components.xcc.sensor import XCCSensor
from custom_components.xcc.coordinator import XCCDataUpdateCoordinator
from homeassistant.core import HomeAssistant


class TestXCCSensor:
    """Test the XCC sensor entity."""

    @pytest.fixture
    def mock_hass(self):
        """Create a mock Home Assistant instance."""
        return MagicMock(spec=HomeAssistant)

    @pytest.fixture
    def mock_coordinator(self):
        """Create a mock coordinator."""
        coordinator = MagicMock(spec=XCCDataUpdateCoordinator)
        coordinator.ip_address = "192.168.1.100"
        coordinator.entity_data = {
            "TEST_SENSOR": "25.5",
            "TIMESTAMP_SENSOR": "08.07.2025",
            "TIME_SENSOR": "14:30",
        }
        coordinator.entity_configs = {
            "TEST_SENSOR": {
                "entity_type": "sensor",
                "data_type": "float",
                "unit": "°C",
                "device_class": "temperature",
                "state_class": "measurement",
                "friendly_name": "Test Temperature",
            },
            "TIMESTAMP_SENSOR": {
                "entity_type": "sensor",
                "data_type": "string",
                "unit": None,  # Critical: no numeric unit
                "device_class": "timestamp",
                "state_class": None,
                "friendly_name": "Timestamp Sensor",
            },
            "TIME_SENSOR": {
                "entity_type": "sensor",
                "data_type": "string",
                "unit": None,
                "device_class": None,
                "state_class": None,
                "friendly_name": "Time Sensor",
            },
        }
        return coordinator

    def test_sensor_initialization(self, mock_hass, mock_coordinator):
        """Test sensor initialization."""
        entity_data = {
            "prop": "TEST_SENSOR",
            "entity_id": "test_sensor",
            "friendly_name": "Test Temperature",
        }
        
        sensor = XCCSensor(mock_coordinator, entity_data)
        
        assert sensor._attr_unique_id == "192.168.1.100_test_sensor"
        assert sensor.entity_id == "sensor.test_sensor"
        assert sensor._attr_name == "Test Temperature"

    def test_numeric_sensor_properties(self, mock_hass, mock_coordinator):
        """Test numeric sensor properties."""
        entity_data = {
            "prop": "TEST_SENSOR",
            "entity_id": "test_sensor",
            "friendly_name": "Test Temperature",
        }
        
        sensor = XCCSensor(mock_coordinator, entity_data)
        
        assert sensor.native_value == 25.5
        assert sensor.native_unit_of_measurement == "°C"
        assert sensor.device_class == "temperature"
        assert sensor.state_class == "measurement"

    def test_timestamp_sensor_properties(self, mock_hass, mock_coordinator):
        """Test timestamp sensor properties (regression test)."""
        entity_data = {
            "prop": "TIMESTAMP_SENSOR",
            "entity_id": "timestamp_sensor",
            "friendly_name": "Timestamp Sensor",
        }
        
        sensor = XCCSensor(mock_coordinator, entity_data)
        
        # Critical: timestamp sensors should not have numeric units
        assert sensor.native_value == "08.07.2025"
        assert sensor.native_unit_of_measurement is None  # Should be None, not "date"
        assert sensor.device_class == "timestamp"
        assert sensor.state_class is None  # Should be None for string values

    def test_time_sensor_properties(self, mock_hass, mock_coordinator):
        """Test time sensor properties."""
        entity_data = {
            "prop": "TIME_SENSOR",
            "entity_id": "time_sensor",
            "friendly_name": "Time Sensor",
        }
        
        sensor = XCCSensor(mock_coordinator, entity_data)
        
        assert sensor.native_value == "14:30"
        assert sensor.native_unit_of_measurement is None
        assert sensor.device_class is None
        assert sensor.state_class is None

    def test_sensor_with_missing_data(self, mock_hass, mock_coordinator):
        """Test sensor behavior when data is missing."""
        entity_data = {
            "prop": "MISSING_SENSOR",
            "entity_id": "missing_sensor",
            "friendly_name": "Missing Sensor",
        }
        
        sensor = XCCSensor(mock_coordinator, entity_data)
        
        # Should handle missing data gracefully
        assert sensor.native_value is None

    def test_sensor_with_invalid_numeric_data(self, mock_hass, mock_coordinator):
        """Test sensor behavior with invalid numeric data."""
        # Add invalid data to coordinator
        mock_coordinator.entity_data["INVALID_SENSOR"] = "not_a_number"
        mock_coordinator.entity_configs["INVALID_SENSOR"] = {
            "entity_type": "sensor",
            "data_type": "float",
            "unit": "°C",
            "device_class": "temperature",
            "state_class": "measurement",
            "friendly_name": "Invalid Sensor",
        }
        
        entity_data = {
            "prop": "INVALID_SENSOR",
            "entity_id": "invalid_sensor",
            "friendly_name": "Invalid Sensor",
        }
        
        sensor = XCCSensor(mock_coordinator, entity_data)
        
        # Should handle invalid numeric data gracefully
        assert sensor.native_value == "not_a_number"  # Return as string

    def test_sensor_unique_id_normalization(self, mock_hass, mock_coordinator):
        """Test that unique IDs are normalized correctly."""
        entity_data = {
            "prop": "TEST-SENSOR-WITH-HYPHENS",
            "entity_id": "test-sensor-with-hyphens",
            "friendly_name": "Test Sensor",
        }
        
        sensor = XCCSensor(mock_coordinator, entity_data)
        
        # Hyphens should be replaced with underscores
        assert sensor._attr_unique_id == "192.168.1.100_test_sensor_with_hyphens"

    def test_regression_no_numeric_unit_for_strings(self, mock_hass, mock_coordinator):
        """Regression test: string sensors should not have numeric units."""
        # Test various string-type sensors that should not have numeric units
        string_sensors = [
            ("SPOTOVECENYSTATS-DATA0-TIMESTAMP", "08.07.2025", "timestamp"),
            ("SPOTOVECENYSTATS-DATA1-TIMESTAMP", "09.07.2025", "timestamp"),
            ("BIVALENCECASODPOJENI", "00:30", None),
            ("BIVALENCECASSPUSTENI", "00:30", None),
        ]
        
        for prop, value, device_class in string_sensors:
            # Add to coordinator
            mock_coordinator.entity_data[prop] = value
            mock_coordinator.entity_configs[prop] = {
                "entity_type": "sensor",
                "data_type": "string",
                "unit": None,  # Critical: should be None
                "device_class": device_class,
                "state_class": None,  # Critical: should be None for strings
                "friendly_name": f"Test {prop}",
            }
            
            entity_data = {
                "prop": prop,
                "entity_id": prop.lower().replace("-", "_"),
                "friendly_name": f"Test {prop}",
            }
            
            sensor = XCCSensor(mock_coordinator, entity_data)
            
            # These should not have numeric units that would cause ValueError
            assert sensor.native_value == value
            assert sensor.native_unit_of_measurement is None
            assert sensor.state_class is None
            if device_class:
                assert sensor.device_class == device_class

    def test_sensor_device_info(self, mock_hass, mock_coordinator):
        """Test sensor device info."""
        entity_data = {
            "prop": "TEST_SENSOR",
            "entity_id": "test_sensor",
            "friendly_name": "Test Temperature",
        }
        
        sensor = XCCSensor(mock_coordinator, entity_data)
        
        device_info = sensor.device_info
        assert device_info is not None
        assert device_info["identifiers"] == {("xcc", "192.168.1.100")}
        assert device_info["name"] == "XCC Heat Pump (192.168.1.100)"
        assert device_info["manufacturer"] == "XCC"

    def test_sensor_available_property(self, mock_hass, mock_coordinator):
        """Test sensor availability."""
        entity_data = {
            "prop": "TEST_SENSOR",
            "entity_id": "test_sensor",
            "friendly_name": "Test Temperature",
        }
        
        sensor = XCCSensor(mock_coordinator, entity_data)
        
        # Should be available when coordinator has data
        mock_coordinator.last_update_success = True
        assert sensor.available is True
        
        # Should be unavailable when coordinator fails
        mock_coordinator.last_update_success = False
        assert sensor.available is False
