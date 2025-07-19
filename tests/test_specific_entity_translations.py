"""Test specific entity translations that were showing incorrect names in logs."""

import pytest
from unittest.mock import patch
import sys
import os

# Add the custom_components directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'custom_components'))

def test_specific_problematic_entities():
    """Test the specific entities that were showing English-only names in the logs."""
    
    with patch('custom_components.xcc.descriptor_parser._LOGGER') as mock_logger:
        from xcc.descriptor_parser import DescriptorParser
        
        parser = DescriptorParser()
        
        # These are the exact entities from the user's logs that were showing incorrect names
        problematic_entities = [
            {
                "file": "tests/sample_data/STAVJED.XML",
                "entities": [
                    {
                        "prop": "TCSTAV0-FANL",
                        "expected_czech": "Otáčky spodního ventilátoru",
                        "expected_english": "RPM of lower fan"
                    },
                    {
                        "prop": "TCSTAV3-TCJ", 
                        "expected_czech": "Teplota kondenzátu",
                        "expected_english": "Condensate temperature"
                    },
                    {
                        "prop": "TCSTAV5-FANH",
                        "expected_czech": "Otáčky horního ventilátoru", 
                        "expected_english": "RPM of upper fan"
                    },
                    {
                        "prop": "TCSTAV8-VYKON",
                        "expected_czech": "Výkon TČ",
                        "expected_english": "Power output by HP"
                    }
                ]
            },
            {
                "file": "tests/sample_data/OKRUH.XML",
                "entities": [
                    {
                        "prop": "TO-EK50",
                        "expected_czech": "Posun křivky",
                        "expected_english": "Curve shift"
                    },
                    {
                        "prop": "TO-PR-VITR-POSUN",
                        "expected_czech": "Posunout ekvitermní křivku o - na každý 1m/s rychlosti větru",
                        "expected_english": "Move equithermal curve by - for every 1m/s of wind speed"
                    },
                    {
                        "prop": "TO-ADAPTACE-ROZPTYLEKV",
                        "expected_czech": "Povolené pásmo adaptace",
                        "expected_english": "Allowed adaptation band"
                    }
                ]
            }
        ]
        
        for file_data in problematic_entities:
            # Parse the descriptor file
            with open(file_data['file'], 'r', encoding='utf-8') as f:
                xml_content = f.read()
            
            page_name = file_data['file'].split('/')[-1].replace('.XML', '').lower()
            
            # Parse the XML and get entity configs
            entity_configs = parser.parse_descriptor_xml(xml_content, page_name)
            
            for entity_data in file_data['entities']:
                prop = entity_data['prop']
                expected_czech = entity_data['expected_czech']
                expected_english = entity_data['expected_english']
                
                # Find the specific entity
                entity_config = entity_configs.get(prop)
                
                assert entity_config is not None, f"No entity config found for {prop} in {file_data['file']}"
                
                # Verify the results
                actual_czech = entity_config['friendly_name']
                actual_english = entity_config['friendly_name_en']
                
                # These assertions will fail if the fix is not working
                assert actual_czech == expected_czech, \
                    f"CZECH TRANSLATION FAILED for {prop}:\n" \
                    f"  Expected: '{expected_czech}'\n" \
                    f"  Actual:   '{actual_czech}'\n" \
                    f"  File:     {file_data['file']}"
                
                assert actual_english == expected_english, \
                    f"ENGLISH TRANSLATION FAILED for {prop}:\n" \
                    f"  Expected: '{expected_english}'\n" \
                    f"  Actual:   '{actual_english}'\n" \
                    f"  File:     {file_data['file']}"
                
                # Ensure they are different (unless they should be the same)
                if expected_czech != expected_english:
                    assert actual_czech != actual_english, \
                        f"TRANSLATION DIFFERENTIATION FAILED for {prop}:\n" \
                        f"  Both Czech and English are: '{actual_czech}'\n" \
                        f"  They should be different!\n" \
                        f"  File: {file_data['file']}"

def test_log_format_verification():
    """Test that the debug logs will show the correct format after the fix."""
    
    with patch('custom_components.xcc.descriptor_parser._LOGGER') as mock_logger:
        from xcc.descriptor_parser import DescriptorParser
        
        parser = DescriptorParser()
        
        # Parse a sample file to trigger debug logging
        with open("tests/sample_data/STAVJED.XML", 'r', encoding='utf-8') as f:
            xml_content = f.read()
        
        entity_configs = parser.parse_descriptor_xml(xml_content, "stavjed")
        
        # Verify that debug logging was called
        assert mock_logger.debug.called, "Debug logging should have been called"
        
        # Get all debug calls
        debug_calls = [call[0][0] for call in mock_logger.debug.call_args_list]
        
        # Look for the specific debug messages we expect
        descriptor_parsing_calls = [call for call in debug_calls if "🔍 DESCRIPTOR PARSING:" in call]
        
        # Verify that we have the expected debug log types
        assert len(descriptor_parsing_calls) > 0, "Should have descriptor parsing debug logs"
        
        # Check that at least some logs show different Czech and English names
        different_names_found = False
        for call in descriptor_parsing_calls:
            if "friendly_name='" in call and "friendly_name_en='" in call:
                # Extract the friendly names from the log message
                parts = call.split("friendly_name='")
                if len(parts) >= 2:
                    czech_part = parts[1].split("'")[0]
                    if "friendly_name_en='" in call:
                        english_part = call.split("friendly_name_en='")[1].split("'")[0]
                        if czech_part != english_part:
                            different_names_found = True
                            break
        
        assert different_names_found, \
            "At least some debug logs should show different Czech and English friendly names"

def test_both_code_paths_working():
    """Test that both _determine_entity_config and _extract_sensor_info_from_row work correctly."""
    
    with patch('custom_components.xcc.descriptor_parser._LOGGER') as mock_logger:
        from xcc.descriptor_parser import DescriptorParser
        
        parser = DescriptorParser()
        
        # Parse multiple files to ensure both code paths are tested
        test_files = [
            "tests/sample_data/STAVJED.XML",
            "tests/sample_data/OKRUH.XML", 
            "tests/sample_data/TUV1.XML"
        ]
        
        total_entities_processed = 0
        entities_with_different_names = 0
        
        for xml_file in test_files:
            with open(xml_file, 'r', encoding='utf-8') as f:
                xml_content = f.read()
            
            page_name = xml_file.split('/')[-1].replace('.XML', '').lower()
            entity_configs = parser.parse_descriptor_xml(xml_content, page_name)
            
            for prop, config in entity_configs.items():
                total_entities_processed += 1
                
                czech_name = config['friendly_name']
                english_name = config['friendly_name_en']
                
                # Ensure both names exist
                assert czech_name and czech_name.strip(), f"Czech name is empty for {prop}"
                assert english_name and english_name.strip(), f"English name is empty for {prop}"
                
                # Count entities with different Czech and English names
                if czech_name != english_name:
                    entities_with_different_names += 1
        
        # We should have processed some entities
        assert total_entities_processed > 0, "Should have processed some entities"
        
        # At least some entities should have different Czech and English names
        # (This indicates the fix is working)
        assert entities_with_different_names > 0, \
            f"At least some entities should have different Czech and English names. " \
            f"Processed {total_entities_processed} entities, but none had different names. " \
            f"This suggests the Czech translation fix is not working."
        
        print(f"✅ Processed {total_entities_processed} entities")
        print(f"✅ {entities_with_different_names} entities have different Czech and English names")
        print(f"✅ Both code paths are working correctly")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
