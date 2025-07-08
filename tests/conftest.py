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
homeassistant.exceptions = create_mock_module('homeassistant.exceptions')
homeassistant.helpers = create_mock_module('homeassistant.helpers')
homeassistant.helpers.update_coordinator = create_mock_module('homeassistant.helpers.update_coordinator')
homeassistant.helpers.entity = create_mock_module('homeassistant.helpers.entity')
homeassistant.helpers.entity_platform = create_mock_module('homeassistant.helpers.entity_platform')
homeassistant.helpers.device_registry = create_mock_module('homeassistant.helpers.device_registry')
homeassistant.components = create_mock_module('homeassistant.components')
homeassistant.components.sensor = create_mock_module('homeassistant.components.sensor')
homeassistant.components.binary_sensor = create_mock_module('homeassistant.components.binary_sensor')
homeassistant.components.number = create_mock_module('homeassistant.components.number')
homeassistant.components.switch = create_mock_module('homeassistant.components.switch')
homeassistant.components.select = create_mock_module('homeassistant.components.select')
homeassistant.components.button = create_mock_module('homeassistant.components.button')
homeassistant.const = create_mock_module('homeassistant.const')

# Mock classes and constants
homeassistant.core.HomeAssistant = MagicMock
homeassistant.core.callback = lambda func: func  # Mock callback decorator
homeassistant.config_entries.ConfigEntry = MagicMock
homeassistant.exceptions.ConfigEntryNotReady = Exception
homeassistant.exceptions.ConfigEntryAuthFailed = Exception
homeassistant.helpers.update_coordinator.DataUpdateCoordinator = MagicMock
homeassistant.helpers.update_coordinator.UpdateFailed = Exception
homeassistant.helpers.entity.Entity = MagicMock
homeassistant.helpers.entity.EntityDescription = MagicMock
homeassistant.helpers.entity_platform.AddEntitiesCallback = MagicMock
homeassistant.helpers.device_registry.DeviceInfo = dict  # DeviceInfo is a TypedDict
homeassistant.components.sensor.SensorEntity = MagicMock
homeassistant.components.sensor.SensorDeviceClass = MagicMock
homeassistant.components.sensor.SensorStateClass = MagicMock
homeassistant.components.sensor.SensorEntityDescription = MagicMock
homeassistant.components.binary_sensor.BinarySensorEntity = MagicMock
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
    BINARY_SENSOR = "binary_sensor"
    NUMBER = "number"
    SWITCH = "switch"
    SELECT = "select"
    BUTTON = "button"

homeassistant.const.Platform = MockPlatform

# Mock other constants that might be needed
homeassistant.const.STATE_ON = "on"
homeassistant.const.STATE_OFF = "off"
homeassistant.const.PERCENTAGE = "%"

# Mock unit classes
class MockUnit:
    CELSIUS = "°C"
    FAHRENHEIT = "°F"
    KELVIN = "K"
    WATT = "W"
    KILOWATT = "kW"
    KILOWATT_HOUR = "kWh"
    VOLT = "V"
    AMPERE = "A"
    HERTZ = "Hz"
    PASCAL = "Pa"
    BAR = "bar"
    SECOND = "s"
    MINUTE = "min"
    HOUR = "h"

homeassistant.const.UnitOfTemperature = MockUnit
homeassistant.const.UnitOfPower = MockUnit
homeassistant.const.UnitOfEnergy = MockUnit
homeassistant.const.UnitOfElectricPotential = MockUnit
homeassistant.const.UnitOfElectricCurrent = MockUnit
homeassistant.const.UnitOfFrequency = MockUnit
homeassistant.const.UnitOfPressure = MockUnit
homeassistant.const.UnitOfTime = MockUnit


@pytest.fixture
def sample_data_dir():
    """Return the path to the sample data directory."""
    return Path(__file__).parent.parent / "sample_data"
