"""Test XCC config flow integration with Home Assistant."""

import pytest
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Use pytest-homeassistant-custom-component
pytest_plugins = "pytest_homeassistant_custom_component"

from homeassistant import config_entries
from homeassistant.const import CONF_IP_ADDRESS, CONF_USERNAME, CONF_PASSWORD
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.core import HomeAssistant

from custom_components.xcc.const import DOMAIN, CONF_SCAN_INTERVAL
from custom_components.xcc.config_flow import CannotConnect, InvalidAuth


@pytest.fixture
def mock_xcc_client():
    """Mock XCC client for testing."""
    with patch('custom_components.xcc.config_flow.XCCClient') as mock_client:
        mock_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_instance
        mock_instance.fetch_page.return_value = "<xml>test</xml>"
        yield mock_client


@pytest.fixture
def mock_xcc_client_error():
    """Mock XCC client that raises connection errors."""
    with patch('custom_components.xcc.config_flow.XCCClient') as mock_client:
        mock_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_instance
        mock_instance.fetch_page.side_effect = Exception("Connection failed")
        yield mock_client


async def test_config_flow_user_form(hass: HomeAssistant):
    """Test the user config flow form is displayed."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    
    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {}
    assert result["step_id"] == "user"


async def test_config_flow_successful_connection(hass: HomeAssistant, mock_xcc_client):
    """Test successful connection and config entry creation."""
    # Start the config flow
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    
    # Submit valid configuration
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_IP_ADDRESS: "192.168.1.100",
            CONF_USERNAME: "xcc",
            CONF_PASSWORD: "xcc",
            CONF_SCAN_INTERVAL: 30,
        },
    )
    
    # Check that config entry was created successfully
    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert result2["title"] == "XCC Controller (192.168.1.100)"
    assert result2["data"] == {
        CONF_IP_ADDRESS: "192.168.1.100",
        CONF_USERNAME: "xcc", 
        CONF_PASSWORD: "xcc",
        CONF_SCAN_INTERVAL: 30,
    }
    
    # Verify XCC client was called correctly
    mock_xcc_client.assert_called_once_with(
        ip="192.168.1.100",
        username="xcc",
        password="xcc"
    )


async def test_config_flow_connection_error(hass: HomeAssistant, mock_xcc_client_error):
    """Test connection error handling in config flow."""
    # Start the config flow
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    
    # Submit configuration that will fail
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_IP_ADDRESS: "192.168.1.100",
            CONF_USERNAME: "xcc",
            CONF_PASSWORD: "wrong",
            CONF_SCAN_INTERVAL: 30,
        },
    )
    
    # Check that error is shown
    assert result2["type"] == FlowResultType.FORM
    assert result2["errors"] == {"base": "cannot_connect"}
    assert result2["step_id"] == "user"


async def test_config_flow_timeout_error(hass: HomeAssistant):
    """Test timeout error handling in config flow."""
    import asyncio
    
    with patch('custom_components.xcc.config_flow.XCCClient') as mock_client:
        mock_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_instance
        mock_instance.fetch_page.side_effect = asyncio.TimeoutError()
        
        # Start the config flow
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        
        # Submit configuration that will timeout
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_IP_ADDRESS: "192.168.1.100",
                CONF_USERNAME: "xcc",
                CONF_PASSWORD: "xcc",
                CONF_SCAN_INTERVAL: 30,
            },
        )
        
        # Check that error is shown
        assert result2["type"] == FlowResultType.FORM
        assert result2["errors"] == {"base": "cannot_connect"}


async def test_config_flow_already_configured(hass: HomeAssistant, mock_xcc_client):
    """Test that duplicate config entries are prevented."""
    # Create an existing config entry
    existing_entry = hass.config_entries.async_add(
        hass.config_entries.async_create_entry(
            title="XCC Controller (192.168.1.100)",
            domain=DOMAIN,
            data={
                CONF_IP_ADDRESS: "192.168.1.100",
                CONF_USERNAME: "xcc",
                CONF_PASSWORD: "xcc",
                CONF_SCAN_INTERVAL: 30,
            },
            unique_id="192.168.1.100",
        )
    )
    
    # Try to add the same controller again
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_IP_ADDRESS: "192.168.1.100",
            CONF_USERNAME: "xcc",
            CONF_PASSWORD: "xcc",
            CONF_SCAN_INTERVAL: 30,
        },
    )
    
    # Should abort with already_configured
    assert result2["type"] == FlowResultType.ABORT
    assert result2["reason"] == "already_configured"


async def test_config_flow_import_validation(hass: HomeAssistant):
    """Test that config flow can import and use XCC client without errors."""
    # This test specifically validates that the import paths work
    from custom_components.xcc.config_flow import validate_input
    
    with patch('custom_components.xcc.config_flow.XCCClient') as mock_client:
        mock_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_instance
        mock_instance.fetch_page.return_value = "<xml>test</xml>"
        
        test_data = {
            CONF_IP_ADDRESS: "192.168.1.100",
            CONF_USERNAME: "xcc",
            CONF_PASSWORD: "xcc",
            CONF_SCAN_INTERVAL: 30,
        }
        
        # This should not raise ImportError
        result = await validate_input(hass, test_data)
        
        assert result["ip_address"] == "192.168.1.100"
        assert result["title"] == "XCC Controller (192.168.1.100)"


async def test_config_flow_different_ips(hass: HomeAssistant, mock_xcc_client):
    """Test that multiple controllers with different IPs can be configured."""
    # Add first controller
    result1 = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    
    result1_final = await hass.config_entries.flow.async_configure(
        result1["flow_id"],
        {
            CONF_IP_ADDRESS: "192.168.1.100",
            CONF_USERNAME: "xcc",
            CONF_PASSWORD: "xcc",
            CONF_SCAN_INTERVAL: 30,
        },
    )
    
    assert result1_final["type"] == FlowResultType.CREATE_ENTRY
    
    # Add second controller with different IP
    result2 = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    
    result2_final = await hass.config_entries.flow.async_configure(
        result2["flow_id"],
        {
            CONF_IP_ADDRESS: "192.168.1.101",
            CONF_USERNAME: "xcc",
            CONF_PASSWORD: "xcc",
            CONF_SCAN_INTERVAL: 30,
        },
    )
    
    assert result2_final["type"] == FlowResultType.CREATE_ENTRY
    assert result2_final["title"] == "XCC Controller (192.168.1.101)"


@pytest.mark.asyncio
async def test_validate_input_direct():
    """Test validate_input function directly."""
    from custom_components.xcc.config_flow import validate_input
    
    with patch('custom_components.xcc.config_flow.XCCClient') as mock_client:
        mock_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_instance
        mock_instance.fetch_page.return_value = "<xml>test</xml>"
        
        test_data = {
            CONF_IP_ADDRESS: "192.168.1.100",
            CONF_USERNAME: "xcc",
            CONF_PASSWORD: "xcc",
            CONF_SCAN_INTERVAL: 30,
        }
        
        result = await validate_input(None, test_data)
        
        # Verify all expected fields are returned
        expected_fields = ["title", "ip_address", "username", "password", "scan_interval"]
        for field in expected_fields:
            assert field in result, f"Result must contain '{field}' field"
        
        # Verify values are correct
        assert result["ip_address"] == "192.168.1.100"
        assert result["username"] == "xcc"
        assert result["password"] == "xcc"
        assert result["scan_interval"] == 30
