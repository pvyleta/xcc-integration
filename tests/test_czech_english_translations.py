"""Test Czech and English translations in descriptor parsing."""

import pytest
import xml.etree.ElementTree as ET
from unittest.mock import Mock, patch
import sys
import os

# Add the custom_components directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'custom_components'))

def test_czech_english_translations_comprehensive():
    """Test that both _determine_entity_config and _extract_sensor_info_from_row create proper Czech and English friendly names."""
    
    # Mock the logger to avoid import issues
    with patch('custom_components.xcc.descriptor_parser._LOGGER') as mock_logger:
        from custom_components.xcc.descriptor_parser import XCCDescriptorParser
        
        parser = XCCDescriptorParser(ignore_visibility=True)  # Test all entities regardless of visibility
        
        # Test entities that should have Czech translations - covering both code paths
        test_cases = [
            {
                "name": "TCSTAV3-VYKON (number element - first pass)",
                "xml_file": "tests/sample_data/STAVJED.XML",
                "prop": "TCSTAV3-VYKON",
                "expected_czech": "Výkon TČ (TCSTAV3-VYKON)",
                "expected_english": "Power output by HP (TCSTAV3-VYKON)",
                "element_type": "number"
            },
            {
                "name": "TCSTAV5-FANH (number element - first pass)",
                "xml_file": "tests/sample_data/STAVJED.XML",
                "prop": "TCSTAV5-FANH",
                "expected_czech": "Otáčky horního ventilátoru (TCSTAV5-FANH)",
                "expected_english": "RPM of upper fan (TCSTAV5-FANH)",
                "element_type": "number"
            },
            {
                "name": "TCSTAV3-TCJ (number element - first pass)",
                "xml_file": "tests/sample_data/STAVJED.XML",
                "prop": "TCSTAV3-TCJ", 
                "expected_czech": "Teplota kondenzátu (TCSTAV3-TCJ)",
                "expected_english": "Condensate temperature (TCSTAV3-TCJ)",
                "element_type": "number"
            },
            {
                "name": "TO-POZADOVANA (number element - first pass)",
                "xml_file": "tests/sample_data/OKRUH.XML",
                "prop": "TO-POZADOVANA",
                "expected_czech": "Požadovaná teplota prostoru",
                "expected_english": "Requested room temperature",
                "element_type": "number"
            },
            {
                "name": "TUVEXTERNIOHREVMOTOHODINY (number element - first pass)",
                "xml_file": "tests/sample_data/TUV1.XML",
                "prop": "TUVEXTERNIOHREVMOTOHODINY",
                "expected_czech": "Externí ohřev - Motohodiny",
                "expected_english": "External heating - Runhours",
                "element_type": "number"
            }
        ]
        
        for test_case in test_cases:
            # Parse the descriptor file (descriptor files use UTF-8 encoding)
            with open(test_case['xml_file'], 'r', encoding='utf-8') as f:
                xml_content = f.read()
            
            page_name = test_case['xml_file'].split('/')[-1].replace('.XML', '').lower()
            
            # Parse the XML and get entity configs
            descriptor_data = {page_name: xml_content}
            entity_configs = parser.parse_descriptor_files(descriptor_data)
            
            # Find the specific entity
            entity_config = entity_configs.get(test_case['prop'])
            
            assert entity_config is not None, f"No entity config found for {test_case['prop']}"
            
            # Verify the results
            czech_name = entity_config['friendly_name']
            english_name = entity_config['friendly_name_en']
            
            # Check if the names are correct
            assert czech_name == test_case['expected_czech'], \
                f"Czech name mismatch for {test_case['prop']}: expected '{test_case['expected_czech']}', got '{czech_name}'"
            
            assert english_name == test_case['expected_english'], \
                f"English name mismatch for {test_case['prop']}: expected '{test_case['expected_english']}', got '{english_name}'"
            
            # Ensure Czech and English names are different (unless they should be the same)
            if test_case['expected_czech'] != test_case['expected_english']:
                assert czech_name != english_name, \
                    f"Czech and English names should be different for {test_case['prop']}, but both are '{czech_name}'"

def test_czech_english_fallback_scenarios():
    """Test fallback scenarios for Czech and English translations."""
    
    with patch('custom_components.xcc.descriptor_parser._LOGGER') as mock_logger:
        from custom_components.xcc.descriptor_parser import XCCDescriptorParser
        
        parser = XCCDescriptorParser()
        
        # Test cases for different fallback scenarios using proper XCC XML structure
        fallback_test_cases = [
            {
                "name": "Czech text only",
                "xml": '''<?xml version="1.0" encoding="UTF-8"?><page><block><row text="Český text"><number prop="TEST1"/></row></block></page>''',
                "prop": "TEST1",
                "expected_czech": "Český text",
                "expected_english": "Český text"  # Falls back to Czech when no English
            },
            {
                "name": "English text only",
                "xml": '''<?xml version="1.0" encoding="UTF-8"?><page><block><row text_en="English text"><number prop="TEST2"/></row></block></page>''',
                "prop": "TEST2",
                "expected_czech": "English text",  # Falls back to English when no Czech
                "expected_english": "English text"
            },
            {
                "name": "Both Czech and English text",
                "xml": '''<?xml version="1.0" encoding="UTF-8"?><page><block><row text="Český text" text_en="English text"><number prop="TEST3"/></row></block></page>''',
                "prop": "TEST3",
                "expected_czech": "Český text",
                "expected_english": "English text"
            }
        ]
        
        for test_case in fallback_test_cases:
            # Parse the XML using the descriptor parser
            descriptor_data = {"test": test_case['xml']}
            entity_configs = parser.parse_descriptor_files(descriptor_data)

            # Get entity config for the specific prop
            entity_config = entity_configs.get(test_case['prop'])
            
            assert entity_config is not None, f"No entity config created for {test_case['prop']}"
            
            # Verify the results
            czech_name = entity_config['friendly_name']
            english_name = entity_config['friendly_name_en']
            
            assert czech_name == test_case['expected_czech'], \
                f"Czech fallback failed for {test_case['name']}: expected '{test_case['expected_czech']}', got '{czech_name}'"
            
            assert english_name == test_case['expected_english'], \
                f"English fallback failed for {test_case['name']}: expected '{test_case['expected_english']}', got '{english_name}'"

def test_regression_prevention():
    """Test to prevent regression of the Czech translation bug."""
    
    with patch('custom_components.xcc.descriptor_parser._LOGGER') as mock_logger:
        from custom_components.xcc.descriptor_parser import XCCDescriptorParser
        
        parser = XCCDescriptorParser()
        
        # Test a few key entities to ensure they never regress to English-only
        regression_test_entities = [
            {
                "file": "tests/sample_data/STAVJED.XML",
                "prop": "TCSTAV8-VYKON",
                "must_be_different": True  # Czech and English must be different
            },
            {
                "file": "tests/sample_data/OKRUH.XML", 
                "prop": "TO-EK50",
                "must_be_different": True  # Czech and English must be different
            },
            {
                "file": "tests/sample_data/TUV1.XML",
                "prop": "TUVEXTERNIOHREVMOTOHODINY",
                "must_be_different": True  # Czech and English must be different
            }
        ]
        
        for test_entity in regression_test_entities:
            # Parse the descriptor file
            with open(test_entity['file'], 'r', encoding='utf-8') as f:
                xml_content = f.read()
            
            page_name = test_entity['file'].split('/')[-1].replace('.XML', '').lower()
            
            # Parse the XML and get entity configs
            descriptor_data = {page_name: xml_content}
            entity_configs = parser.parse_descriptor_files(descriptor_data)
            
            # Find the specific entity
            entity_config = entity_configs.get(test_entity['prop'])
            
            assert entity_config is not None, \
                f"REGRESSION: Entity {test_entity['prop']} not found in {test_entity['file']}"
            
            czech_name = entity_config['friendly_name']
            english_name = entity_config['friendly_name_en']
            
            # Ensure both names exist and are not empty
            assert czech_name and czech_name.strip(), \
                f"REGRESSION: Czech friendly_name is empty for {test_entity['prop']}"
            
            assert english_name and english_name.strip(), \
                f"REGRESSION: English friendly_name_en is empty for {test_entity['prop']}"
            
            # If they must be different, ensure they are
            if test_entity['must_be_different']:
                assert czech_name != english_name, \
                    f"REGRESSION: Czech and English names are the same for {test_entity['prop']}:\n" \
                    f"  Both are: '{czech_name}'\n" \
                    f"  This indicates the Czech translation bug has returned!\n" \
                    f"  File: {test_entity['file']}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
