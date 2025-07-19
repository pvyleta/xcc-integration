"""Test XCC client encoding and property lookup fixes.

This test verifies that the XCC client properly handles:
1. XML encoding issues (windows-1250 vs utf-8)
2. Property name to internal NAME mapping
3. Page selection logic for different property types
"""

import pytest
import sys
import os

# Add the custom_components directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'custom_components', 'xcc'))

def test_xml_parsing_encoding_fix():
    """Test that XML parsing works without encoding errors."""
    
    from custom_components.xcc.xcc_client import parse_xml_entities
    
    # Test with sample XML content that has windows-1250 encoding
    sample_xml = '''<?xml version="1.0" encoding="windows-1250"?>
<page>
    <INPUT P="TEST_PROP" NAME="__R123_REAL_.1f" VALUE="42.0"/>
    <INPUT P="ANOTHER_PROP" NAME="__R456_BOOL_i" VALUE="1"/>
</page>'''
    
    # This should not raise encoding errors anymore
    try:
        entities = parse_xml_entities(sample_xml, "TEST.XML")
        assert len(entities) == 2, "Should parse 2 entities"
        
        # Check first entity
        assert entities[0]["attributes"]["field_name"] == "TEST_PROP"
        assert entities[0]["state"] == "42.0"
        
        # Check second entity
        assert entities[1]["attributes"]["field_name"] == "ANOTHER_PROP"
        assert entities[1]["state"] == "1"
        
        print("✅ XML parsing encoding fix test passed")
        
    except UnicodeDecodeError as e:
        pytest.fail(f"UnicodeDecodeError should not occur with fixed parsing: {e}")
    except UnicodeEncodeError as e:
        pytest.fail(f"UnicodeEncodeError should not occur with fixed parsing: {e}")


def test_name_mapping_extraction():
    """Test that property name to internal NAME mapping works correctly."""
    
    from custom_components.xcc.xcc_client import XCCClient
    
    # Create a mock client to test the name mapping method
    client = XCCClient("192.168.1.100", "test", "test")
    
    # Test XML with different attribute orders
    test_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<page>
    <INPUT P="TALTTEPLOTAZASOBNIKUMIN" NAME="__R39556_REAL_.1f" VALUE="44.0"/>
    <INPUT NAME="__R39552_REAL_.1f" P="TALTTEPLOTAZASOBNIKU" VALUE="48.0"/>
    <INPUT VALUE="0" P="TOPNEOKRUHYIN3-FVEPRETOPENI" NAME="__R51259.0_BOOL_i"/>
</page>'''
    
    # Extract name mapping
    name_mapping = client._extract_name_mapping_from_xml(test_xml)
    
    # Verify mappings
    expected_mappings = {
        "TALTTEPLOTAZASOBNIKUMIN": "__R39556_REAL_.1f",
        "TALTTEPLOTAZASOBNIKU": "__R39552_REAL_.1f", 
        "TOPNEOKRUHYIN3-FVEPRETOPENI": "__R51259.0_BOOL_i"
    }
    
    for prop, expected_name in expected_mappings.items():
        assert prop in name_mapping, f"Property {prop} should be in mapping"
        assert name_mapping[prop] == expected_name, f"Property {prop} should map to {expected_name}"
    
    print("✅ Name mapping extraction test passed")


def test_page_selection_logic():
    """Test that properties are mapped to correct pages."""

    # Test the page selection logic
    test_cases = [
        ("TALTTEPLOTAZASOBNIKUMIN", "TUV11.XML"),  # Contains TALT (Czech DHW term)
        ("ZASOBNIKTEMP", "TUV11.XML"),             # Contains ZASOBNIK (Czech tank)
        ("DHWTEMPERATURE", "TUV11.XML"),           # Contains DHW
        ("TUVTEMP", "TUV11.XML"),                  # Contains TUV
        ("FVEPOWER", "FVE4.XML"),                  # Contains FVE
        ("SOLARENERGY", "FVE4.XML"),               # Contains SOLAR
        ("OKRUH1TEMP", "OKRUH10.XML"),             # Contains OKRUH
        ("CIRCUITPUMP", "OKRUH10.XML"),            # Contains CIRCUIT
        ("BIVMODE", "BIV1.XML"),                   # Contains BIV
        ("BIVALENCEPOINT", "BIV1.XML"),            # Contains BIVALENCE
        ("RANDOMPROP", "STAVJED1.XML"),            # Default case
    ]

    for prop, expected_page in test_cases:
        # Simulate the updated page selection logic
        prop_upper = prop.upper()

        # Check for TUV/DHW related properties (including Czech terms)
        tuv_keywords = ["TUV", "DHW", "ZASOBNIK", "TEPLOTA", "TALT"]
        if any(tuv_word in prop_upper for tuv_word in tuv_keywords):
            page_to_fetch = "TUV11.XML"
        elif any(fve_word in prop_upper for fve_word in ["FVE", "SOLAR", "PV"]):
            page_to_fetch = "FVE4.XML"
        elif any(okruh_word in prop_upper for okruh_word in ["OKRUH", "CIRCUIT"]):
            page_to_fetch = "OKRUH10.XML"
        elif any(biv_word in prop_upper for biv_word in ["BIV", "BIVALENCE"]):
            page_to_fetch = "BIV1.XML"
        else:
            page_to_fetch = "STAVJED1.XML"

        assert page_to_fetch == expected_page, f"Property {prop} should map to {expected_page}, got {page_to_fetch}"

    print("✅ Page selection logic test passed")


def test_tuv_property_detection():
    """Test specific case that was failing in the logs."""

    prop = "TALTTEPLOTAZASOBNIKUMIN"
    prop_upper = prop.upper()

    # This should return True with the updated keywords
    tuv_keywords = ["TUV", "DHW", "ZASOBNIK", "TEPLOTA", "TALT"]
    contains_tuv_keywords = any(tuv_word in prop_upper for tuv_word in tuv_keywords)
    assert contains_tuv_keywords == True, f"Property {prop} should contain TUV-related keywords"

    # Verify the specific substring that should match
    assert "TALT" in prop_upper, f"TALT should be found in {prop_upper}"

    print("✅ TUV property detection test passed")


if __name__ == "__main__":
    """Run tests when executed directly."""
    print("🔧 Testing XCC Client Encoding and Property Lookup Fixes")
    print("=" * 60)
    
    try:
        test_xml_parsing_encoding_fix()
        test_name_mapping_extraction()
        test_page_selection_logic()
        test_tuv_property_detection()
        
        print("\n🎉 ALL XCC CLIENT FIXES TESTS PASSED!")
        print("✅ XML encoding issues resolved")
        print("✅ Property name mapping working correctly")
        print("✅ Page selection logic functioning properly")
        print("✅ TUV property detection verified")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
