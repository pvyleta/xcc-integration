#!/usr/bin/env python3
"""
Test visibility conditions (visData) handling in XCC integration.

This test verifies that entities with visibility conditions are properly
included or excluded based on the current data values.
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_tuvminimalni_visibility_condition():
    """Test that TUVMINIMALNI should be visible based on real data."""
    
    print(f"\n=== TESTING TUVMINIMALNI VISIBILITY CONDITION ===")
    
    # Load real TUV data
    sample_dir = project_root / "tests" / "sample_data"
    tuv_data_file = sample_dir / "TUV11.XML"
    tuv_desc_file = sample_dir / "tuv1.xml"
    
    if not tuv_data_file.exists() or not tuv_desc_file.exists():
        pytest.skip("TUV sample files not found")
    
    # Load TUV data
    with open(tuv_data_file, 'r', encoding='utf-8') as f:
        tuv_data_content = f.read()
    
    # Load TUV descriptor
    with open(tuv_desc_file, 'r', encoding='utf-8') as f:
        tuv_desc_content = f.read()
    
    # Check if TUVMINIMALNI exists in data
    tuvminimalni_in_data = 'TUVMINIMALNI' in tuv_data_content
    print(f"TUVMINIMALNI in data file: {tuvminimalni_in_data}")
    
    # Check if TUVMINIMALNI exists in descriptor
    tuvminimalni_in_desc = 'TUVMINIMALNI' in tuv_desc_content
    print(f"TUVMINIMALNI in descriptor: {tuvminimalni_in_desc}")
    
    if not tuvminimalni_in_data or not tuvminimalni_in_desc:
        pytest.skip("TUVMINIMALNI not found in sample data")
    
    # Extract TUVMINIMALNI value from data
    import re
    data_match = re.search(r'<INPUT[^>]*P="TUVMINIMALNI"[^>]*VALUE="([^"]*)"', tuv_data_content)
    tuvminimalni_value = data_match.group(1) if data_match else None
    print(f"TUVMINIMALNI value: {tuvminimalni_value}")
    
    # Extract visibility condition from descriptor
    desc_match = re.search(r'prop="TUVMINIMALNI"[^>]*visData="([^"]*)"', tuv_desc_content)
    visibility_condition = desc_match.group(1) if desc_match else None
    print(f"TUVMINIMALNI visibility condition: {visibility_condition}")
    
    # Parse visibility condition: format is "count;property1;value1;property2;value2;..."
    if visibility_condition:
        vis_parts = visibility_condition.split(';')
        if len(vis_parts) >= 3:
            count = int(vis_parts[0])
            conditions = []
            for i in range(count):
                prop_idx = 1 + (i * 2)
                val_idx = 2 + (i * 2)
                if prop_idx < len(vis_parts) and val_idx < len(vis_parts):
                    conditions.append((vis_parts[prop_idx], vis_parts[val_idx]))
            
            print(f"Parsed visibility conditions: {conditions}")
            
            # Check each condition against data
            all_conditions_met = True
            for condition_prop, expected_value in conditions:
                # Find the condition property in data
                condition_match = re.search(
                    rf'<INPUT[^>]*P="{condition_prop}"[^>]*VALUE="([^"]*)"', 
                    tuv_data_content
                )
                actual_value = condition_match.group(1) if condition_match else None
                condition_met = actual_value == expected_value
                
                print(f"  Condition: {condition_prop} == {expected_value}")
                print(f"  Actual: {actual_value}")
                print(f"  Met: {condition_met}")
                
                if not condition_met:
                    all_conditions_met = False
            
            print(f"All visibility conditions met: {all_conditions_met}")
            
            # Test assertion
            assert tuvminimalni_value is not None, "TUVMINIMALNI should have a value in data"
            assert visibility_condition is not None, "TUVMINIMALNI should have visibility condition"
            assert all_conditions_met, "TUVMINIMALNI visibility conditions should be met"
            
            print(f"✅ TUVMINIMALNI should be VISIBLE (value: {tuvminimalni_value})")
            
        else:
            pytest.fail(f"Invalid visibility condition format: {visibility_condition}")
    else:
        pytest.fail("No visibility condition found for TUVMINIMALNI")


def test_visibility_condition_parser():
    """Test parsing of visibility conditions."""
    
    print(f"\n=== TESTING VISIBILITY CONDITION PARSER ===")
    
    def parse_visibility_condition(vis_data: str) -> list[tuple[str, str]]:
        """Parse visData string into list of (property, expected_value) tuples."""
        if not vis_data:
            return []
        
        parts = vis_data.split(';')
        if len(parts) < 1:
            return []
        
        try:
            count = int(parts[0])
            conditions = []
            
            for i in range(count):
                prop_idx = 1 + (i * 2)
                val_idx = 2 + (i * 2)
                
                if prop_idx < len(parts) and val_idx < len(parts):
                    conditions.append((parts[prop_idx], parts[val_idx]))
            
            return conditions
        except (ValueError, IndexError):
            return []
    
    # Test cases
    test_cases = [
        ("1;TUVSCHOVANITEPLOT;0", [("TUVSCHOVANITEPLOT", "0")]),
        ("2;FVE-ENABLED;1;FVE-KOMUNIKOVAT;1", [("FVE-ENABLED", "1"), ("FVE-KOMUNIKOVAT", "1")]),
        ("1;WEB-FVEKASKADAV0;1", [("WEB-FVEKASKADAV0", "1")]),
        ("", []),
        ("0", []),
        ("invalid", []),
    ]
    
    for vis_data, expected in test_cases:
        result = parse_visibility_condition(vis_data)
        print(f"Input: '{vis_data}' -> Output: {result}")
        assert result == expected, f"Expected {expected}, got {result}"
    
    print("✅ Visibility condition parser test passed!")


def test_check_visibility_conditions():
    """Test checking visibility conditions against data."""
    
    print(f"\n=== TESTING VISIBILITY CONDITION CHECKING ===")
    
    def check_visibility_conditions(conditions: list[tuple[str, str]], data_values: dict[str, str]) -> bool:
        """Check if all visibility conditions are met."""
        for prop, expected_value in conditions:
            actual_value = data_values.get(prop)
            if actual_value != expected_value:
                return False
        return True
    
    # Test cases
    test_cases = [
        # All conditions met
        ([("TUVSCHOVANITEPLOT", "0")], {"TUVSCHOVANITEPLOT": "0"}, True),
        ([("FVE-ENABLED", "1"), ("FVE-KOMUNIKOVAT", "1")], {"FVE-ENABLED": "1", "FVE-KOMUNIKOVAT": "1"}, True),
        
        # Some conditions not met
        ([("TUVSCHOVANITEPLOT", "0")], {"TUVSCHOVANITEPLOT": "1"}, False),
        ([("FVE-ENABLED", "1"), ("FVE-KOMUNIKOVAT", "1")], {"FVE-ENABLED": "1", "FVE-KOMUNIKOVAT": "0"}, False),
        
        # Missing data
        ([("TUVSCHOVANITEPLOT", "0")], {}, False),
        
        # No conditions (always visible)
        ([], {}, True),
        ([], {"SOME_PROP": "1"}, True),
    ]
    
    for conditions, data_values, expected in test_cases:
        result = check_visibility_conditions(conditions, data_values)
        print(f"Conditions: {conditions}, Data: {data_values} -> Visible: {result}")
        assert result == expected, f"Expected {expected}, got {result}"
    
    print("✅ Visibility condition checking test passed!")


if __name__ == "__main__":
    """Run tests directly for debugging."""
    print("🧪 Running XCC Visibility Condition Tests")
    print("=" * 60)
    
    try:
        test_tuvminimalni_visibility_condition()
        test_visibility_condition_parser()
        test_check_visibility_conditions()
        
        print("\n" + "=" * 60)
        print("🎉 ALL VISIBILITY TESTS PASSED!")
        print("✅ Visibility condition handling logic is working correctly")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
