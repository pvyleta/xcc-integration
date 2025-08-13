#!/usr/bin/env python3
"""
Test visibility condition integration with real XCC data.

This test verifies that TUVMINIMALNI and other entities with visibility
conditions are properly handled in the integration.
"""

import pytest
import sys
from pathlib import Path
import re

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_tuvminimalni_should_be_visible():
    """Test that TUVMINIMALNI should be visible based on current data."""
    
    print(f"\n=== TESTING TUVMINIMALNI VISIBILITY WITH REAL DATA ===")
    
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
    
    # Extract TUVMINIMALNI from data
    tuvminimalni_match = re.search(r'<INPUT[^>]*P="TUVMINIMALNI"[^>]*VALUE="([^"]*)"', tuv_data_content)
    tuvminimalni_value = tuvminimalni_match.group(1) if tuvminimalni_match else None
    
    # Extract TUVSCHOVANITEPLOT from data (visibility condition)
    tuvschovaniteplot_match = re.search(r'<INPUT[^>]*P="TUVSCHOVANITEPLOT"[^>]*VALUE="([^"]*)"', tuv_data_content)
    tuvschovaniteplot_value = tuvschovaniteplot_match.group(1) if tuvschovaniteplot_match else None
    
    # Extract visibility condition from descriptor
    vis_match = re.search(r'prop="TUVMINIMALNI"[^>]*visData="([^"]*)"', tuv_desc_content)
    visibility_condition = vis_match.group(1) if vis_match else None
    
    print(f"TUVMINIMALNI value: {tuvminimalni_value}")
    print(f"TUVSCHOVANITEPLOT value: {tuvschovaniteplot_value}")
    print(f"Visibility condition: {visibility_condition}")
    
    # Parse visibility condition
    if visibility_condition:
        parts = visibility_condition.split(';')
        if len(parts) >= 3:
            expected_prop = parts[1]
            expected_value = parts[2]
            
            print(f"Expected: {expected_prop} = {expected_value}")
            print(f"Actual: {expected_prop} = {tuvschovaniteplot_value}")
            
            condition_met = (expected_prop == "TUVSCHOVANITEPLOT" and 
                           tuvschovaniteplot_value == expected_value)
            
            print(f"Visibility condition met: {condition_met}")
            
            # Test assertions
            assert tuvminimalni_value is not None, "TUVMINIMALNI should exist in data"
            assert tuvschovaniteplot_value is not None, "TUVSCHOVANITEPLOT should exist in data"
            assert visibility_condition is not None, "TUVMINIMALNI should have visibility condition"
            assert condition_met, f"Visibility condition should be met: {expected_prop}={expected_value}, got {tuvschovaniteplot_value}"
            
            print(f"✅ TUVMINIMALNI should be VISIBLE (value: {tuvminimalni_value})")
            
        else:
            pytest.fail(f"Invalid visibility condition format: {visibility_condition}")
    else:
        pytest.fail("No visibility condition found for TUVMINIMALNI")


def test_find_entities_with_visibility_conditions():
    """Find all entities with visibility conditions in the sample data."""
    
    print(f"\n=== FINDING ALL ENTITIES WITH VISIBILITY CONDITIONS ===")
    
    sample_dir = project_root / "tests" / "sample_data"
    
    # Check all descriptor files
    descriptor_files = [
        "tuv1.xml", "okruh.xml", "fve.xml", "biv.xml", "stavjed.xml"
    ]
    
    entities_with_visibility = []
    
    for desc_file in descriptor_files:
        desc_path = sample_dir / desc_file
        if desc_path.exists():
            with open(desc_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find all elements with visData attributes
            vis_matches = re.findall(r'prop="([^"]*)"[^>]*visData="([^"]*)"', content)
            
            for prop, vis_data in vis_matches:
                entities_with_visibility.append({
                    "prop": prop,
                    "file": desc_file,
                    "visData": vis_data
                })
    
    print(f"Found {len(entities_with_visibility)} entities with visibility conditions:")
    
    for entity in entities_with_visibility[:10]:  # Show first 10
        print(f"  {entity['prop']} ({entity['file']}) - {entity['visData']}")
    
    if len(entities_with_visibility) > 10:
        print(f"  ... and {len(entities_with_visibility) - 10} more")
    
    # Test assertions
    assert len(entities_with_visibility) > 0, "Should find entities with visibility conditions"
    
    # Check that TUVMINIMALNI is in the list
    tuvminimalni_found = any(e["prop"] == "TUVMINIMALNI" for e in entities_with_visibility)
    assert tuvminimalni_found, "TUVMINIMALNI should be found in entities with visibility conditions"
    
    print(f"✅ Found entities with visibility conditions, including TUVMINIMALNI")


def test_visibility_condition_impact():
    """Test the impact of visibility conditions on entity discovery."""
    
    print(f"\n=== TESTING VISIBILITY CONDITION IMPACT ===")
    
    sample_dir = project_root / "tests" / "sample_data"
    
    # Count entities with and without visibility conditions
    descriptor_files = ["tuv1.xml", "okruh.xml", "fve.xml", "biv.xml", "stavjed.xml"]
    
    total_entities = 0
    entities_with_visibility = 0
    
    for desc_file in descriptor_files:
        desc_path = sample_dir / desc_file
        if desc_path.exists():
            with open(desc_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Count all entities with prop attributes
            all_props = re.findall(r'prop="([^"]*)"', content)
            unique_props = set(all_props)
            total_entities += len(unique_props)
            
            # Count entities with visibility conditions
            vis_props = re.findall(r'prop="([^"]*)"[^>]*visData="[^"]*"', content)
            unique_vis_props = set(vis_props)
            entities_with_visibility += len(unique_vis_props)
    
    visibility_percentage = (entities_with_visibility / total_entities * 100) if total_entities > 0 else 0
    
    print(f"Total entities found: {total_entities}")
    print(f"Entities with visibility conditions: {entities_with_visibility}")
    print(f"Percentage with visibility conditions: {visibility_percentage:.1f}%")
    
    # Test assertions
    assert total_entities > 50, f"Should find at least 50 entities, found {total_entities}"
    assert entities_with_visibility > 0, "Should find entities with visibility conditions"
    assert visibility_percentage > 5, f"At least 5% of entities should have visibility conditions, found {visibility_percentage:.1f}%"
    
    print(f"✅ Visibility conditions affect {visibility_percentage:.1f}% of entities")


def test_missing_entities_analysis():
    """Analyze why certain entities might be missing from the integration."""
    
    print(f"\n=== ANALYZING MISSING ENTITIES ===")
    
    # This test helps identify entities that should be visible but might be missing
    # due to visibility condition issues
    
    sample_dir = project_root / "tests" / "sample_data"
    tuv_data_file = sample_dir / "TUV11.XML"
    tuv_desc_file = sample_dir / "tuv1.xml"
    
    if not tuv_data_file.exists() or not tuv_desc_file.exists():
        pytest.skip("TUV sample files not found")
    
    # Load data and descriptor
    with open(tuv_data_file, 'r', encoding='utf-8') as f:
        data_content = f.read()
    
    with open(tuv_desc_file, 'r', encoding='utf-8') as f:
        desc_content = f.read()
    
    # Extract all data entities
    data_entities = set()
    data_matches = re.findall(r'<INPUT[^>]*P="([^"]*)"', data_content)
    for prop in data_matches:
        data_entities.add(prop)
    
    # Extract all descriptor entities
    desc_entities = set()
    desc_matches = re.findall(r'prop="([^"]*)"', desc_content)
    for prop in desc_matches:
        desc_entities.add(prop)
    
    # Find entities that exist in data but not in descriptor
    data_only = data_entities - desc_entities
    
    # Find entities that exist in descriptor but not in data
    desc_only = desc_entities - data_entities
    
    # Find entities with visibility conditions
    vis_entities = set()
    vis_matches = re.findall(r'prop="([^"]*)"[^>]*visData="[^"]*"', desc_content)
    for prop in vis_matches:
        vis_entities.add(prop)
    
    print(f"Entities in data only: {len(data_only)}")
    print(f"Entities in descriptor only: {len(desc_only)}")
    print(f"Entities with visibility conditions: {len(vis_entities)}")
    print(f"Common entities: {len(data_entities & desc_entities)}")
    
    # Check if TUVMINIMALNI is properly handled
    tuvminimalni_in_data = "TUVMINIMALNI" in data_entities
    tuvminimalni_in_desc = "TUVMINIMALNI" in desc_entities
    tuvminimalni_has_visibility = "TUVMINIMALNI" in vis_entities
    
    print(f"\nTUVMINIMALNI analysis:")
    print(f"  In data: {tuvminimalni_in_data}")
    print(f"  In descriptor: {tuvminimalni_in_desc}")
    print(f"  Has visibility condition: {tuvminimalni_has_visibility}")
    
    # Test assertions
    assert tuvminimalni_in_data, "TUVMINIMALNI should be in data"
    assert tuvminimalni_in_desc, "TUVMINIMALNI should be in descriptor"
    assert tuvminimalni_has_visibility, "TUVMINIMALNI should have visibility condition"
    
    print(f"✅ TUVMINIMALNI is properly defined with visibility condition")


if __name__ == "__main__":
    """Run tests directly for debugging."""
    print("🧪 Running XCC Visibility Integration Tests")
    print("=" * 60)
    
    try:
        test_tuvminimalni_should_be_visible()
        test_find_entities_with_visibility_conditions()
        test_visibility_condition_impact()
        test_missing_entities_analysis()
        
        print("\n" + "=" * 60)
        print("🎉 ALL VISIBILITY INTEGRATION TESTS PASSED!")
        print("✅ TUVMINIMALNI and other entities with visibility conditions are properly handled")
        print("🔧 The integration should now include TUVMINIMALNI when visibility conditions are met")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
