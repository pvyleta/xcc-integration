#!/usr/bin/env python3
"""
Test script to verify XCC integration fixes.
This script can be run to test the integration without Home Assistant.
"""

import asyncio
import logging
import sys
import os

# Add the custom_components directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'custom_components'))

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
_LOGGER = logging.getLogger(__name__)

async def test_xcc_client():
    """Test XCC client functionality."""
    try:
        from custom_components.xcc.xcc_client import XCCClient, parse_xml_entities
        from custom_components.xcc.const import XCC_DATA_PAGES
        
        # Test with sample data if available
        sample_data_dir = "sample_data"
        if os.path.exists(sample_data_dir):
            _LOGGER.info("Testing with sample data from %s", sample_data_dir)
            
            # Load sample XML files
            for page in XCC_DATA_PAGES:
                sample_file = os.path.join(sample_data_dir, page)
                if os.path.exists(sample_file):
                    _LOGGER.info("Loading sample file: %s", sample_file)
                    with open(sample_file, 'r', encoding='windows-1250') as f:
                        xml_content = f.read()
                    
                    # Parse entities
                    entities = parse_xml_entities(xml_content, page)
                    _LOGGER.info("Parsed %d entities from %s", len(entities), page)
                    
                    # Show first few entities
                    for i, entity in enumerate(entities[:5]):
                        prop = entity["attributes"]["field_name"]
                        value = entity["attributes"].get("value", "")
                        _LOGGER.info("  Entity %d: %s = %s", i+1, prop, value)
                else:
                    _LOGGER.warning("Sample file not found: %s", sample_file)
        else:
            _LOGGER.warning("Sample data directory not found: %s", sample_data_dir)
            _LOGGER.info("To test with real data, you would need XCC controller credentials")
            
    except Exception as e:
        _LOGGER.error("Error testing XCC client: %s", e)
        import traceback
        _LOGGER.error("Traceback: %s", traceback.format_exc())

async def test_coordinator():
    """Test coordinator data processing."""
    try:
        from custom_components.xcc.coordinator import XCCDataUpdateCoordinator
        from custom_components.xcc.const import CONF_IP_ADDRESS, CONF_USERNAME, CONF_PASSWORD
        
        # Mock config entry for testing
        class MockConfigEntry:
            def __init__(self):
                self.data = {
                    CONF_IP_ADDRESS: "192.168.1.100",
                    CONF_USERNAME: "test",
                    CONF_PASSWORD: "test"
                }
                self.entry_id = "test_entry"
        
        class MockHass:
            def __init__(self):
                self.config = MockConfig()
                
        class MockConfig:
            def __init__(self):
                self.config_dir = "/tmp"
        
        # Create coordinator
        hass = MockHass()
        entry = MockConfigEntry()
        coordinator = XCCDataUpdateCoordinator(hass, entry)
        
        _LOGGER.info("Created coordinator for testing")
        _LOGGER.info("Coordinator entity configs: %d", len(coordinator.entity_configs))
        
    except Exception as e:
        _LOGGER.error("Error testing coordinator: %s", e)
        import traceback
        _LOGGER.error("Traceback: %s", traceback.format_exc())

async def main():
    """Main test function."""
    _LOGGER.info("=== XCC Integration Test ===")
    
    _LOGGER.info("Testing XCC client...")
    await test_xcc_client()
    
    _LOGGER.info("Testing coordinator...")
    await test_coordinator()
    
    _LOGGER.info("=== Test Complete ===")

if __name__ == "__main__":
    asyncio.run(main())
