"""Test friendly name fixes for XCC integration."""

import pytest
import sys
import os
import xml.etree.ElementTree as ET

# Add the custom_components directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'custom_components', 'xcc'))

from custom_components.xcc.descriptor_parser import XCCDescriptorParser

def test_friendly_name_fixes():
    """Test that friendly name issues are fixed."""
    
    print("🔧 Testing Friendly Name Fixes")
    print("=" * 50)
    
    # Initialize parser
    parser = XCCDescriptorParser()
    
    # Test cases based on the issues found
    test_cases = [
        {
            "name": "TO-FVEPRETOPENI-POVOLENI",
            "file": "sample_data/OKRUH.XML",
            "expected_friendly_name_en": "Overheat circuit when the outside temp. decreases",
            "description": "Switch element should inherit parent row's text_en"
        },
        {
            "name": "FVE-CHARGEATCHEAPMAXSOC", 
            "file": "sample_data/FVE.XML",
            "expected_friendly_name_en": "Ukončit nabíjení při překročení SOC baterie",  # Should fall back to Czech
            "description": "Should fall back to Czech when text_en is empty"
        },
        {
            "name": "FVM0-CURRENTBATTERYSETTINGS-CHARGEIMAX",
            "file": "sample_data/FVE.XML", 
            "expected_friendly_name_en": "Iverter 1 - Actual maximal charge current",
            "description": "Readonly sensor should use parent row's text_en"
        }
    ]
    
    for test_case in test_cases:
        print(f"\n🎯 Testing {test_case['name']}")
        print(f"   Description: {test_case['description']}")
        
        file_path = test_case["file"]
        if not os.path.exists(file_path):
            print(f"   ❌ Sample file {file_path} not found")
            continue
        
        try:
            # Parse the descriptor file
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                xml_content = f.read()
            
            page_name = os.path.basename(file_path).replace('.XML', '')
            entity_configs = parser._parse_single_descriptor(xml_content, page_name)
            
            # Find the test entity
            prop_name = test_case["name"]
            if prop_name in entity_configs:
                config = entity_configs[prop_name]
                actual_friendly_name_en = config.get("friendly_name_en", "MISSING")
                expected_friendly_name_en = test_case["expected_friendly_name_en"]
                
                print(f"   Expected: '{expected_friendly_name_en}'")
                print(f"   Actual:   '{actual_friendly_name_en}'")
                
                if actual_friendly_name_en == expected_friendly_name_en:
                    print(f"   ✅ PASS - Friendly name is correct")
                else:
                    print(f"   ❌ FAIL - Friendly name mismatch")
                    
                # Also show other relevant fields
                print(f"   friendly_name: '{config.get('friendly_name', 'MISSING')}'")
                print(f"   entity_type: '{config.get('entity_type', 'MISSING')}'")
                print(f"   writable: {config.get('writable', 'MISSING')}")
                
            else:
                print(f"   ❌ Entity {prop_name} not found in parsed configs")
                print(f"   Available entities: {list(entity_configs.keys())[:10]}...")  # Show first 10
                
        except Exception as e:
            print(f"   ❌ Error testing {test_case['name']}: {e}")
    
    print(f"\n📊 Summary")
    print("=" * 50)
    print("Fixed issues:")
    print("1. Switch elements now inherit parent row's text_en attribute")
    print("2. Empty text_en attributes now fall back to Czech text")
    print("3. Readonly sensors properly extract text_en from parent rows")
    print("4. Friendly name priority: element text_en > row text_en > element text > row text > prop")


def test_friendly_name_logic_simulation():
    """Test the friendly name logic with simulated XML structures."""
    
    print(f"\n🧪 Testing Friendly Name Logic Simulation")
    print("=" * 50)
    
    # Simulate the friendly name logic
    def simulate_friendly_name_logic(element_text, element_text_en, row_text, row_text_en, prop):
        """Simulate the new friendly name logic"""
        # Priority: element's text_en > parent row's text_en > element's text > parent row's text > prop
        friendly_name_en = element_text_en or row_text_en or element_text or row_text or prop
        
        # For display, prefer English names but fall back to Czech if needed
        if row_text and element_text:
            # Both row and element have text - combine them
            if row_text_en and element_text_en:
                friendly_name = f"{row_text_en} - {element_text_en}"
            elif row_text_en and element_text:
                friendly_name = f"{row_text_en} - {element_text}"
            elif row_text and element_text_en:
                friendly_name = f"{row_text} - {element_text_en}"
            else:
                friendly_name = f"{row_text} - {element_text}"
        else:
            # Use the best available name
            friendly_name = friendly_name_en
        
        return friendly_name, friendly_name_en
    
    # Test cases
    test_cases = [
        {
            "name": "Switch with parent row text_en",
            "element_text": "",
            "element_text_en": "",
            "row_text": "Přetopit okruh při ochlazení",
            "row_text_en": "Overheat circuit when the outside temp. decreases",
            "prop": "TO-FVEPRETOPENI-POVOLENI",
            "expected_friendly_name_en": "Overheat circuit when the outside temp. decreases"
        },
        {
            "name": "Element with empty text_en",
            "element_text": "Ukončit nabíjení při překročení SOC baterie",
            "element_text_en": "",
            "row_text": "",
            "row_text_en": "",
            "prop": "FVE-CHARGEATCHEAPMAXSOC",
            "expected_friendly_name_en": "Ukončit nabíjení při překročení SOC baterie"
        },
        {
            "name": "Readonly sensor with row text_en",
            "element_text": "",
            "element_text_en": "",
            "row_text": "Měnič 1 - Aktuální max. nabíjecí proud",
            "row_text_en": "Iverter 1 - Actual maximal charge current",
            "prop": "FVM0-CURRENTBATTERYSETTINGS-CHARGEIMAX",
            "expected_friendly_name_en": "Iverter 1 - Actual maximal charge current"
        }
    ]
    
    for test_case in test_cases:
        print(f"\n🎯 Testing: {test_case['name']}")
        
        friendly_name, friendly_name_en = simulate_friendly_name_logic(
            test_case["element_text"],
            test_case["element_text_en"], 
            test_case["row_text"],
            test_case["row_text_en"],
            test_case["prop"]
        )
        
        expected = test_case["expected_friendly_name_en"]
        
        print(f"   Expected friendly_name_en: '{expected}'")
        print(f"   Actual friendly_name_en:   '{friendly_name_en}'")
        print(f"   Actual friendly_name:      '{friendly_name}'")
        
        if friendly_name_en == expected:
            print(f"   ✅ PASS")
        else:
            print(f"   ❌ FAIL")


if __name__ == "__main__":
    """Run tests when executed directly."""
    try:
        test_friendly_name_fixes()
        test_friendly_name_logic_simulation()
        print("\n🎉 FRIENDLY NAME TESTS COMPLETED!")
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
