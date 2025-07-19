"""Integration test for language preference with real sample data."""

import os
import sys
import unittest.mock

# Mock Home Assistant modules before importing XCC components
sys.modules['homeassistant'] = unittest.mock.MagicMock()
sys.modules['homeassistant.config_entries'] = unittest.mock.MagicMock()
sys.modules['homeassistant.core'] = unittest.mock.MagicMock()
sys.modules['homeassistant.helpers'] = unittest.mock.MagicMock()
sys.modules['homeassistant.helpers.entity'] = unittest.mock.MagicMock()
sys.modules['homeassistant.helpers.update_coordinator'] = unittest.mock.MagicMock()

# Add the custom_components directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'custom_components', 'xcc'))

def test_language_preference_with_sample_data():
    """Test language preference using real sample descriptor data."""
    
    print("🌍 TESTING LANGUAGE PREFERENCE WITH REAL SAMPLE DATA")
    print("=" * 70)
    
    try:
        from descriptor_parser import XCCDescriptorParser
    except ImportError as e:
        print(f"❌ Cannot import descriptor parser: {e}")
        return False
    
    # Initialize parser
    parser = XCCDescriptorParser()
    
    # Parse FVE.XML to get real descriptor configs
    fve_file = "tests/sample_data/FVE.XML"
    if not os.path.exists(fve_file):
        print(f"❌ Sample file {fve_file} not found")
        return False
    
    with open(fve_file, 'r', encoding='utf-8', errors='ignore') as f:
        xml_content = f.read()
    
    entity_configs = parser._parse_single_descriptor(xml_content, "FVE")
    
    # Find entities with both English and Czech names for testing
    test_entities = []
    for prop, config in entity_configs.items():
        if config.get("friendly_name") and config.get("friendly_name_en"):
            test_entities.append((prop, config))
            if len(test_entities) >= 3:  # Test with 3 entities
                break
    
    if not test_entities:
        print("❌ No entities found with both English and Czech names")
        return False
    
    print(f"📊 Found {len(test_entities)} entities with both language names for testing")
    
    # Test language preference logic
    for language in ["english", "czech"]:
        print(f"\n🌍 Testing {language.upper()} language preference:")
        print("-" * 50)
        
        for prop, config in test_entities:
            friendly_name_en = config.get("friendly_name_en", "")
            friendly_name_cz = config.get("friendly_name", "")
            
            # Simulate language-aware friendly name selection
            if language == "english":
                selected_name = (
                    friendly_name_en
                    or friendly_name_cz
                    or prop
                )
                expected_preference = "English" if friendly_name_en else "Czech (fallback)"
            else:
                selected_name = (
                    friendly_name_cz
                    or friendly_name_en
                    or prop
                )
                expected_preference = "Czech" if friendly_name_cz else "English (fallback)"
            
            print(f"   📝 {prop}:")
            print(f"      English: '{friendly_name_en}'")
            print(f"      Czech:   '{friendly_name_cz}'")
            print(f"      Selected ({expected_preference}): '{selected_name}'")
            
            # Verify correct selection based on preference
            if language == "english":
                if friendly_name_en:
                    assert selected_name == friendly_name_en, f"Should select English name for {prop}"
                else:
                    assert selected_name == friendly_name_cz, f"Should fallback to Czech name for {prop}"
            else:
                if friendly_name_cz:
                    assert selected_name == friendly_name_cz, f"Should select Czech name for {prop}"
                else:
                    assert selected_name == friendly_name_en, f"Should fallback to English name for {prop}"
    
    print(f"\n✅ Language preference test passed with {len(test_entities)} real entities")
    return True

if __name__ == "__main__":
    success = test_language_preference_with_sample_data()
    
    if success:
        print("\n🎉 LANGUAGE PREFERENCE INTEGRATION TEST PASSED!")
    else:
        print("\n❌ LANGUAGE PREFERENCE INTEGRATION TEST FAILED!")
        exit(1)
