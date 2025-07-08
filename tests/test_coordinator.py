"""Tests for XCC coordinator."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from custom_components.xcc.coordinator import XCCDataUpdateCoordinator
from custom_components.xcc.xcc_client import XCCClient
from homeassistant.core import HomeAssistant


class TestXCCDataUpdateCoordinator:
    """Test the XCC data update coordinator."""

    @pytest.fixture
    def mock_hass(self):
        """Create a mock Home Assistant instance."""
        hass = MagicMock(spec=HomeAssistant)
        hass.data = {}
        return hass

    @pytest.fixture
    def mock_client(self):
        """Create a mock XCC client."""
        client = MagicMock(spec=XCCClient)
        client.ip = "192.168.1.100"
        client.fetch_all_data = AsyncMock(return_value={
            "TUVPOZADOVANA": "50.0",
            "SPOTOVECENYSTATS-DATA0-TIMESTAMP": "08.07.2025",
            "SPOTOVECENYSTATS-DATA1-TIMESTAMP": "09.07.2025",
            "BIVALENCECASODPOJENI": "00:30",
            "SPOTOVECENY-FEEDTOGRIDLIMIT": "1",
            "SPOTOVECENY-DSMODE": "2",
        })
        return client

    @pytest.fixture
    def coordinator(self, mock_hass, mock_client):
        """Create a coordinator instance."""
        return XCCDataUpdateCoordinator(mock_hass, mock_client)

    @pytest.mark.asyncio
    async def test_coordinator_initialization(self, coordinator):
        """Test coordinator initializes correctly."""
        assert coordinator.ip_address == "192.168.1.100"
        assert coordinator.entity_data == {}
        assert coordinator.entity_configs == {}

    @pytest.mark.asyncio
    async def test_data_update_success(self, coordinator, mock_client):
        """Test successful data update."""
        # Mock descriptor parsing
        with patch.object(coordinator, '_load_entity_configs') as mock_load:
            mock_load.return_value = {
                "TUVPOZADOVANA": {
                    "entity_type": "number",
                    "data_type": "float",
                    "unit": "°C",
                    "friendly_name": "DHW Temperature",
                },
                "SPOTOVECENYSTATS-DATA0-TIMESTAMP": {
                    "entity_type": "sensor",
                    "data_type": "string",
                    "unit": None,  # Critical: no numeric unit
                    "device_class": "timestamp",
                    "state_class": None,
                    "friendly_name": "Data 0 Timestamp",
                },
            }
            
            # Perform update
            data = await coordinator._async_update_data()
            
            # Verify data structure
            assert isinstance(data, dict)
            assert "TUVPOZADOVANA" in data
            assert "SPOTOVECENYSTATS-DATA0-TIMESTAMP" in data
            
            # Verify entity configs are loaded
            assert len(coordinator.entity_configs) > 0

    @pytest.mark.asyncio
    async def test_date_entity_no_numeric_unit(self, coordinator, mock_client):
        """Test that date entities don't have numeric units (regression test)."""
        # Mock descriptor parsing to return date entities
        with patch.object(coordinator, '_load_entity_configs') as mock_load:
            mock_load.return_value = {
                "SPOTOVECENYSTATS-DATA0-TIMESTAMP": {
                    "entity_type": "sensor",
                    "data_type": "string",
                    "unit": None,  # Should be None, not "date"
                    "device_class": "timestamp",
                    "state_class": None,
                    "friendly_name": "Data 0 Timestamp",
                },
                "SPOTOVECENYSTATS-DATA1-TIMESTAMP": {
                    "entity_type": "sensor",
                    "data_type": "string",
                    "unit": None,  # Should be None, not "date"
                    "device_class": "timestamp",
                    "state_class": None,
                    "friendly_name": "Data 1 Timestamp",
                },
            }
            
            await coordinator._async_update_data()
            
            # Verify timestamp entities have no numeric units
            for prop in ["SPOTOVECENYSTATS-DATA0-TIMESTAMP", "SPOTOVECENYSTATS-DATA1-TIMESTAMP"]:
                config = coordinator.entity_configs[prop]
                assert config["unit"] is None, f"Entity {prop} should not have a numeric unit"
                assert config["data_type"] == "string"
                assert config["state_class"] is None

    @pytest.mark.asyncio
    async def test_entity_classification(self, coordinator):
        """Test that entities are classified correctly."""
        # Mock entity configs
        coordinator.entity_configs = {
            "TEMP_NUMBER": {"entity_type": "number", "data_type": "float"},
            "TEMP_SWITCH": {"entity_type": "switch", "data_type": "bool"},
            "TEMP_SELECT": {"entity_type": "select", "data_type": "string"},
            "TEMP_SENSOR": {"entity_type": "sensor", "data_type": "string"},
        }
        
        # Mock data
        coordinator.entity_data = {
            "TEMP_NUMBER": "25.5",
            "TEMP_SWITCH": "1",
            "TEMP_SELECT": "option1",
            "TEMP_SENSOR": "sensor_value",
            "UNKNOWN_ENTITY": "unknown_value",
        }
        
        # Get entity distribution
        distribution = coordinator._get_entity_distribution()
        
        assert distribution["numbers"] == 1
        assert distribution["switches"] == 1
        assert distribution["selects"] == 1
        # Sensors should include both configured sensors and unknown entities
        assert distribution["sensors"] >= 2

    @pytest.mark.asyncio
    async def test_unique_id_generation(self, coordinator):
        """Test that unique IDs are generated correctly."""
        # Test unique ID format
        unique_id = coordinator._generate_unique_id("TEST_ENTITY")
        expected = f"{coordinator.ip_address}_TEST_ENTITY"
        assert unique_id == expected

    @pytest.mark.asyncio
    async def test_error_handling(self, coordinator, mock_client):
        """Test error handling during data update."""
        # Make client raise an exception
        mock_client.fetch_all_data.side_effect = Exception("Connection failed")
        
        # Update should handle the error gracefully
        with pytest.raises(Exception):
            await coordinator._async_update_data()

    @pytest.mark.asyncio
    async def test_entity_value_conversion(self, coordinator):
        """Test that entity values are converted correctly."""
        test_cases = [
            # (raw_value, data_type, expected_converted)
            ("25.5", "float", 25.5),
            ("1", "bool", True),
            ("0", "bool", False),
            ("string_value", "string", "string_value"),
            ("", "string", ""),
            ("invalid_float", "float", "invalid_float"),  # Should handle gracefully
        ]
        
        for raw_value, data_type, expected in test_cases:
            converted = coordinator._convert_entity_value(raw_value, data_type)
            assert converted == expected

    @pytest.mark.asyncio
    async def test_no_duplicate_entities_in_distribution(self, coordinator):
        """Test that entity distribution doesn't count duplicates."""
        # Set up entity configs with potential duplicates
        coordinator.entity_configs = {
            "ENTITY1": {"entity_type": "number", "data_type": "float"},
            "ENTITY2": {"entity_type": "number", "data_type": "float"},
        }
        
        coordinator.entity_data = {
            "ENTITY1": "25.0",
            "ENTITY2": "30.0",
            "ENTITY1": "25.0",  # Duplicate key (should be overwritten)
        }
        
        distribution = coordinator._get_entity_distribution()
        
        # Should only count unique entities
        assert distribution["numbers"] == 2
        assert distribution["total"] == 2

    @pytest.mark.asyncio
    async def test_regression_date_sensor_unit_error(self, coordinator, mock_client):
        """Regression test for date sensor unit ValueError."""
        # This tests the exact scenario that was causing errors
        with patch.object(coordinator, '_load_entity_configs') as mock_load:
            mock_load.return_value = {
                "SPOTOVECENYSTATS-DATA0-TIMESTAMP": {
                    "entity_type": "sensor",
                    "data_type": "string",
                    "unit": None,  # Fixed: was "date" causing ValueError
                    "device_class": "timestamp",
                    "state_class": None,
                    "friendly_name": "Data 0 Timestamp",
                },
            }
            
            # Mock data with string date value
            mock_client.fetch_all_data.return_value = {
                "SPOTOVECENYSTATS-DATA0-TIMESTAMP": "08.07.2025"
            }
            
            # This should not raise ValueError
            data = await coordinator._async_update_data()
            
            # Verify the data is handled correctly
            assert data["SPOTOVECENYSTATS-DATA0-TIMESTAMP"] == "08.07.2025"
            
            # Verify entity config is correct
            config = coordinator.entity_configs["SPOTOVECENYSTATS-DATA0-TIMESTAMP"]
            assert config["unit"] is None
            assert config["data_type"] == "string"
