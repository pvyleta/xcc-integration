"""Test configuration for XCC integration."""
import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock
import types

# Add the custom_components directory to the Python path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

# Mock all Home Assistant modules before any imports
def create_mock_module(name):
    """Create a mock module."""
    module = types.ModuleType(name)
    sys.modules[name] = module
    return module

# Create comprehensive Home Assistant mocks
homeassistant = create_mock_module('homeassistant')
homeassistant.core = create_mock_module('homeassistant.core')
homeassistant.config_entries = create_mock_module('homeassistant.config_entries')
homeassistant.helpers = create_mock_module('homeassistant.helpers')
homeassistant.helpers.update_coordinator = create_mock_module('homeassistant.helpers.update_coordinator')
homeassistant.helpers.entity = create_mock_module('homeassistant.helpers.entity')
homeassistant.helpers.entity_platform = create_mock_module('homeassistant.helpers.entity_platform')
homeassistant.components = create_mock_module('homeassistant.components')
homeassistant.components.sensor = create_mock_module('homeassistant.components.sensor')
homeassistant.components.number = create_mock_module('homeassistant.components.number')
homeassistant.components.switch = create_mock_module('homeassistant.components.switch')
homeassistant.components.select = create_mock_module('homeassistant.components.select')
homeassistant.components.button = create_mock_module('homeassistant.components.button')
homeassistant.const = create_mock_module('homeassistant.const')

# Mock classes and constants
homeassistant.core.HomeAssistant = MagicMock
homeassistant.config_entries.ConfigEntry = MagicMock
homeassistant.helpers.update_coordinator.DataUpdateCoordinator = MagicMock
homeassistant.helpers.entity.Entity = MagicMock
homeassistant.components.sensor.SensorEntity = MagicMock
homeassistant.components.number.NumberEntity = MagicMock
homeassistant.components.switch.SwitchEntity = MagicMock
homeassistant.components.select.SelectEntity = MagicMock
homeassistant.components.button.ButtonEntity = MagicMock

# Mock constants
homeassistant.const.CONF_IP_ADDRESS = "ip_address"
homeassistant.const.CONF_USERNAME = "username"
homeassistant.const.CONF_PASSWORD = "password"

# Mock Platform enum
class MockPlatform:
    SENSOR = "sensor"
    NUMBER = "number"
    SWITCH = "switch"
    SELECT = "select"
    BUTTON = "button"

homeassistant.const.Platform = MockPlatform

# Mock other constants that might be needed
homeassistant.const.STATE_ON = "on"
homeassistant.const.STATE_OFF = "off"


@pytest.fixture
def sample_data_dir():
    """Return the path to the sample data directory."""
    return Path(__file__).parent.parent / "sample_data"
