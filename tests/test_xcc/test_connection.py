"""Test XCC connection functionality."""

import pytest
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from homeassistant.const import CONF_IP_ADDRESS, CONF_USERNAME, CONF_PASSWORD
from homeassistant.core import HomeAssistant

from custom_components.xcc.const import DOMAIN, CONF_SCAN_INTERVAL
from custom_components.xcc.config_flow import validate_input, CannotConnect, InvalidAuth


@pytest.mark.asyncio
async def test_xcc_client_import():
    """Test that XCC client can be imported correctly."""
    # This should not raise ImportError
    from custom_components.xcc.xcc_client import XCCClient
    assert XCCClient is not None


@pytest.mark.asyncio
async def test_config_flow_import():
    """Test that config flow can import XCC client."""
    # Mock the XCC client to avoid actual network calls
    with patch('custom_components.xcc.config_flow.XCCClient') as mock_client:
        mock_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_instance
        mock_instance.fetch_page.return_value = "<xml>test</xml>"
        
        # This should not raise ImportError
        from custom_components.xcc.config_flow import validate_input
        
        # Test data
        test_data = {
            CONF_IP_ADDRESS: "192.168.1.100",
            CONF_USERNAME: "xcc",
            CONF_PASSWORD: "xcc",
            CONF_SCAN_INTERVAL: 30,
        }
        
        # This should work without import errors
        result = await validate_input(None, test_data)
        assert result["ip_address"] == "192.168.1.100"


@pytest.mark.asyncio
async def test_coordinator_import():
    """Test that coordinator can import XCC client."""
    from custom_components.xcc.coordinator import XCCDataUpdateCoordinator
    from homeassistant.config_entries import ConfigEntry
    
    # Create mock config entry
    config_entry = MagicMock(spec=ConfigEntry)
    config_entry.data = {
        CONF_IP_ADDRESS: "192.168.1.100",
        CONF_USERNAME: "xcc",
        CONF_PASSWORD: "xcc",
        CONF_SCAN_INTERVAL: 30,
    }
    
    # Mock Home Assistant
    hass = MagicMock(spec=HomeAssistant)
    
    # This should not raise ImportError
    coordinator = XCCDataUpdateCoordinator(hass, config_entry)
    assert coordinator is not None


@pytest.mark.asyncio
async def test_validate_input_success():
    """Test successful connection validation."""
    with patch('custom_components.xcc.config_flow.XCCClient') as mock_client:
        # Mock successful connection
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
        
        assert result["title"] == "XCC Controller (192.168.1.100)"
        assert result["ip_address"] == "192.168.1.100"
        assert result["username"] == "xcc"
        assert result["password"] == "xcc"
        assert result["scan_interval"] == 30
        
        # Verify XCC client was called correctly
        mock_client.assert_called_once_with(
            ip="192.168.1.100",
            username="xcc",
            password="xcc"
        )
        mock_instance.fetch_page.assert_called_once_with("stavjed.xml")


@pytest.mark.asyncio
async def test_validate_input_timeout():
    """Test connection timeout handling."""
    import asyncio
    
    with patch('custom_components.xcc.config_flow.XCCClient') as mock_client:
        # Mock timeout
        mock_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_instance
        mock_instance.fetch_page.side_effect = asyncio.TimeoutError()
        
        test_data = {
            CONF_IP_ADDRESS: "192.168.1.100",
            CONF_USERNAME: "xcc",
            CONF_PASSWORD: "xcc",
            CONF_SCAN_INTERVAL: 30,
        }
        
        with pytest.raises(CannotConnect):
            await validate_input(None, test_data)


@pytest.mark.asyncio
async def test_validate_input_connection_error():
    """Test connection error handling."""
    import aiohttp
    
    with patch('custom_components.xcc.config_flow.XCCClient') as mock_client:
        # Mock connection error
        mock_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_instance
        mock_instance.fetch_page.side_effect = aiohttp.ClientError()
        
        test_data = {
            CONF_IP_ADDRESS: "192.168.1.100",
            CONF_USERNAME: "xcc",
            CONF_PASSWORD: "xcc",
            CONF_SCAN_INTERVAL: 30,
        }
        
        with pytest.raises(CannotConnect):
            await validate_input(None, test_data)


@pytest.mark.asyncio
async def test_validate_input_unexpected_error():
    """Test unexpected error handling."""
    with patch('custom_components.xcc.config_flow.XCCClient') as mock_client:
        # Mock unexpected error
        mock_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_instance
        mock_instance.fetch_page.side_effect = Exception("Unexpected error")
        
        test_data = {
            CONF_IP_ADDRESS: "192.168.1.100",
            CONF_USERNAME: "xcc",
            CONF_PASSWORD: "xcc",
            CONF_SCAN_INTERVAL: 30,
        }
        
        with pytest.raises(CannotConnect):
            await validate_input(None, test_data)


@pytest.mark.asyncio
async def test_coordinator_fetch_data():
    """Test coordinator data fetching."""
    from custom_components.xcc.coordinator import XCCDataUpdateCoordinator
    from homeassistant.config_entries import ConfigEntry
    
    # Mock config entry
    config_entry = MagicMock(spec=ConfigEntry)
    config_entry.data = {
        CONF_IP_ADDRESS: "192.168.1.100",
        CONF_USERNAME: "xcc",
        CONF_PASSWORD: "xcc",
        CONF_SCAN_INTERVAL: 30,
    }
    
    # Mock Home Assistant
    hass = MagicMock(spec=HomeAssistant)
    
    coordinator = XCCDataUpdateCoordinator(hass, config_entry)
    
    # Mock XCC client and parse function
    with patch('custom_components.xcc.coordinator.XCCClient') as mock_client, \
         patch('custom_components.xcc.coordinator.parse_xml_entities') as mock_parse:
        
        # Mock successful data fetch
        mock_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_instance
        mock_instance.fetch_pages.return_value = {
            "stavjed.xml": "<xml>test</xml>",
            "STAVJED1.XML": "<xml>values</xml>"
        }
        
        mock_parse.return_value = {
            "T_OUTDOOR": {
                "type": "sensors",
                "data": {
                    "state": "5.2",
                    "attributes": {
                        "field_name": "T_OUTDOOR",
                        "friendly_name": "Outdoor Temperature",
                        "unit": "°C"
                    }
                }
            }
        }
        
        # Test data fetching
        result = await coordinator._async_update_data()
        
        assert result is not None
        assert "T_OUTDOOR" in result
        
        # Verify XCC client was called correctly
        mock_client.assert_called_once_with(
            ip="192.168.1.100",
            username="xcc",
            password="xcc"
        )
