#!/usr/bin/env python3
"""
Test descriptor parser visibility condition handling.

This test verifies that the descriptor parser correctly includes/excludes
entities based on visibility conditions (visData attributes).
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_descriptor_parser_with_visibility():
    """Test that descriptor parser handles visibility conditions correctly."""
    
    try:
        from custom_components.xcc.descriptor_parser import XCCDescriptorParser
    except ImportError:
        pytest.skip("XCC descriptor parser not available (Home Assistant dependencies missing)")
    
    print(f"\n=== TESTING DESCRIPTOR PARSER WITH VISIBILITY CONDITIONS ===")
    
    # Load real TUV data and descriptor
    sample_dir = project_root / "tests" / "sample_data"
    tuv_data_file = sample_dir / "TUV11.XML"
    tuv_desc_file = sample_dir / "tuv1.xml"
    
    if not tuv_data_file.exists() or not tuv_desc_file.exists():
        pytest.skip("TUV sample files not found")
    
    # Load TUV data to extract current values
    with open(tuv_data_file, 'r', encoding='utf-8') as f:
        tuv_data_content = f.read()
    
    # Load TUV descriptor
    with open(tuv_desc_file, 'r', encoding='utf-8') as f:
        tuv_desc_content = f.read()
    
    # Extract current data values from TUV11.XML
    import re
    data_values = {}
    input_matches = re.findall(r'<INPUT[^>]*P="([^"]*)"[^>]*VALUE="([^"]*)"', tuv_data_content)
    for prop, value in input_matches:
        data_values[prop] = value
    
    print(f"Extracted {len(data_values)} data values from TUV11.XML")
    
    # Test 1: Parse without visibility data (should include TUVMINIMALNI)
    parser1 = XCCDescriptorParser()
    configs1 = parser1.parse_descriptor_files({"tuv1.xml": tuv_desc_content})
    
    tuvminimalni_without_visibility = "TUVMINIMALNI" in configs1
    print(f"TUVMINIMALNI included without visibility data: {tuvminimalni_without_visibility}")
    
    # Test 2: Parse with visibility data where condition is met (should include TUVMINIMALNI)
    parser2 = XCCDescriptorParser()
    parser2.update_data_values(data_values)
    configs2 = parser2.parse_descriptor_files({"tuv1.xml": tuv_desc_content})
    
    tuvminimalni_with_visibility_met = "TUVMINIMALNI" in configs2
    print(f"TUVMINIMALNI included with visibility condition met: {tuvminimalni_with_visibility_met}")
    
    # Test 3: Parse with visibility data where condition is NOT met (should exclude TUVMINIMALNI)
    modified_data_values = data_values.copy()
    modified_data_values["TUVSCHOVANITEPLOT"] = "1"  # Change condition to not met
    
    parser3 = XCCDescriptorParser()
    parser3.update_data_values(modified_data_values)
    configs3 = parser3.parse_descriptor_files({"tuv1.xml": tuv_desc_content})
    
    tuvminimalni_with_visibility_not_met = "TUVMINIMALNI" in configs3
    print(f"TUVMINIMALNI included with visibility condition NOT met: {tuvminimalni_with_visibility_not_met}")
    
    # Verify the visibility condition values
    tuvschovaniteplot_value = data_values.get("TUVSCHOVANITEPLOT")
    print(f"TUVSCHOVANITEPLOT current value: {tuvschovaniteplot_value}")
    
    # Test assertions
    assert not tuvminimalni_without_visibility, "TUVMINIMALNI should be excluded when no visibility data is provided (can't evaluate condition)"
    assert tuvminimalni_with_visibility_met, "TUVMINIMALNI should be included when visibility condition is met"
    assert not tuvminimalni_with_visibility_not_met, "TUVMINIMALNI should be excluded when visibility condition is not met"
    assert tuvschovaniteplot_value == "0", "TUVSCHOVANITEPLOT should be 0 for condition to be met"
    
    print(f"\n✅ Descriptor parser visibility handling test PASSED!")
    
    # Additional verification: check entity counts
    print(f"\nEntity counts:")
    print(f"  Without visibility: {len(configs1)} entities")
    print(f"  With visibility (met): {len(configs2)} entities")
    print(f"  With visibility (not met): {len(configs3)} entities")
    
    # The count with visibility not met should be less than when met
    assert len(configs3) < len(configs2), "Should have fewer entities when visibility conditions are not met"


def test_descriptor_parser_visibility_methods():
    """Test the visibility condition methods directly."""
    
    try:
        from custom_components.xcc.descriptor_parser import XCCDescriptorParser
    except ImportError:
        pytest.skip("XCC descriptor parser not available (Home Assistant dependencies missing)")
    
    print(f"\n=== TESTING DESCRIPTOR PARSER VISIBILITY METHODS ===")
    
    parser = XCCDescriptorParser()
    
    # Test visibility condition parsing
    test_cases = [
        ("1;TUVSCHOVANITEPLOT;0", [("TUVSCHOVANITEPLOT", "0")]),
        ("2;FVE-ENABLED;1;FVE-KOMUNIKOVAT;1", [("FVE-ENABLED", "1"), ("FVE-KOMUNIKOVAT", "1")]),
        ("", []),
        ("0", []),
    ]
    
    for vis_data, expected in test_cases:
        result = parser._parse_visibility_condition(vis_data)
        print(f"Parse '{vis_data}' -> {result}")
        assert result == expected, f"Expected {expected}, got {result}"
    
    # Test visibility condition checking
    parser.update_data_values({
        "TUVSCHOVANITEPLOT": "0",
        "FVE-ENABLED": "1",
        "FVE-KOMUNIKOVAT": "0"
    })
    
    check_cases = [
        ([("TUVSCHOVANITEPLOT", "0")], True),
        ([("TUVSCHOVANITEPLOT", "1")], False),
        ([("FVE-ENABLED", "1"), ("FVE-KOMUNIKOVAT", "1")], False),  # Second condition not met
        ([("FVE-ENABLED", "1")], True),
        ([], True),  # No conditions = always visible
    ]
    
    for conditions, expected in check_cases:
        result = parser._check_visibility_conditions(conditions)
        print(f"Check {conditions} -> {result}")
        assert result == expected, f"Expected {expected}, got {result}"
    
    print(f"✅ Descriptor parser visibility methods test PASSED!")


if __name__ == "__main__":
    """Run tests directly for debugging."""
    print("🧪 Running XCC Descriptor Parser Visibility Tests")
    print("=" * 60)
    
    try:
        test_descriptor_parser_with_visibility()
        test_descriptor_parser_visibility_methods()
        
        print("\n" + "=" * 60)
        print("🎉 ALL DESCRIPTOR VISIBILITY TESTS PASSED!")
        print("✅ Descriptor parser correctly handles visibility conditions")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
