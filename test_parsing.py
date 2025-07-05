#!/usr/bin/env python3
"""
Simple test to verify XCC data parsing works with sample data.
"""

import os
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
_LOGGER = logging.getLogger(__name__)

def test_xml_parsing():
    """Test XML parsing with sample data."""
    try:
        # Import the parsing function directly
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'custom_components', 'xcc'))
        from xcc_client import parse_xml_entities
        
        # Test with sample data
        sample_file = "sample_data/STAVJED1.XML"
        if os.path.exists(sample_file):
            _LOGGER.info("Testing with sample file: %s", sample_file)
            
            with open(sample_file, 'r', encoding='windows-1250') as f:
                xml_content = f.read()
            
            # Parse entities
            entities = parse_xml_entities(xml_content, "STAVJED1.XML")
            _LOGGER.info("Parsed %d entities from sample file", len(entities))
            
            # Show first 10 entities with their values
            _LOGGER.info("Sample entities and values:")
            for i, entity in enumerate(entities[:10]):
                prop = entity["attributes"]["field_name"]
                value = entity["attributes"].get("value", "")
                _LOGGER.info("  %d. %s = %s", i+1, prop, value)
            
            # Test the data structure that would be created by coordinator
            _LOGGER.info("\nTesting coordinator data structure:")
            
            # Simulate what the coordinator does
            processed_data = {
                "sensors": {},
                "switches": {},
                "numbers": {},
                "selects": {},
                "buttons": {},
            }
            
            for entity in entities[:5]:  # Just test first 5
                prop = entity["attributes"]["field_name"]
                entity_type = "sensor"  # Default for this test
                
                entity_id = f"xcc_{prop.lower()}"
                state_value = entity["attributes"].get("value", "")
                
                state_data = {
                    "state": state_value,
                    "attributes": entity["attributes"],
                    "entity_id": entity_id,
                    "prop": prop,
                    "name": prop,
                    "unit": entity["attributes"].get("unit", ""),
                    "page": "STAVJED1.XML",
                }
                
                processed_data["sensors"][entity_id] = state_data
                _LOGGER.info("  Stored: %s = %s", entity_id, state_value)
            
            # Test value retrieval like the entity would do
            _LOGGER.info("\nTesting value retrieval:")
            for entity_id, state_data in processed_data["sensors"].items():
                retrieved_value = state_data.get("state")
                _LOGGER.info("  Retrieved: %s = %s", entity_id, retrieved_value)
            
            return True
            
        else:
            _LOGGER.error("Sample file not found: %s", sample_file)
            return False
            
    except Exception as e:
        _LOGGER.error("Error testing XML parsing: %s", e)
        import traceback
        _LOGGER.error("Traceback: %s", traceback.format_exc())
        return False

def main():
    """Main test function."""
    _LOGGER.info("=== XCC Data Parsing Test ===")
    
    success = test_xml_parsing()
    
    if success:
        _LOGGER.info("✅ Test completed successfully!")
        _LOGGER.info("The data parsing and structure should work correctly.")
    else:
        _LOGGER.error("❌ Test failed!")
    
    _LOGGER.info("=== Test Complete ===")

if __name__ == "__main__":
    main()
