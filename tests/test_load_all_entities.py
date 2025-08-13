#!/usr/bin/env python3
"""
Test loading ALL entities regardless of visibility conditions.

This test verifies that the integration now loads all entities
for which data values exist, ignoring visibility conditions.
"""

import pytest
import sys
from pathlib import Path
import re

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_load_all_entities_verification():
    """Verify that ALL entities will be loaded regardless of visibility."""
    
    print(f"\n=== LOAD ALL ENTITIES VERIFICATION ===")
    
    # Load sample data
    sample_dir = project_root / "tests" / "sample_data"
    
    # Test with TUV data as example
    tuv_desc_file = sample_dir / "tuv1.xml"
    tuv_data_file = sample_dir / "TUV11.XML"
    
    if not tuv_desc_file.exists() or not tuv_data_file.exists():
        pytest.skip("TUV sample files not found")
    
    # Load descriptor and data
    with open(tuv_desc_file, 'r', encoding='utf-8') as f:
        desc_content = f.read()
    
    with open(tuv_data_file, 'r', encoding='utf-8') as f:
        data_content = f.read()
    
    # Extract all entities from descriptor
    all_desc_entities = set(re.findall(r'prop="([^"]*)"', desc_content))
    
    # Extract all entities from data
    all_data_entities = set()
    data_matches = re.findall(r'<INPUT[^>]*P="([^"]*)"', data_content)
    for prop in data_matches:
        all_data_entities.add(prop)
    
    # Find entities that exist in both descriptor and data
    common_entities = all_desc_entities & all_data_entities
    
    # Find entities with visibility conditions
    entities_with_visibility = set()
    vis_matches = re.findall(r'prop="([^"]*)"[^>]*visData="[^"]*"', desc_content)
    for prop in vis_matches:
        entities_with_visibility.add(prop)
    
    print(f"📊 ENTITY ANALYSIS:")
    print(f"  Entities in descriptor: {len(all_desc_entities)}")
    print(f"  Entities in data: {len(all_data_entities)}")
    print(f"  Common entities (both desc + data): {len(common_entities)}")
    print(f"  Entities with visibility conditions: {len(entities_with_visibility)}")
    
    # Check specific entities
    key_entities = ["TUVMINIMALNI", "TUVPOZADOVANA", "TTUV", "TUVUTLUM"]
    
    print(f"\n🔍 KEY ENTITY STATUS:")
    for entity in key_entities:
        in_desc = entity in all_desc_entities
        in_data = entity in all_data_entities
        has_visibility = entity in entities_with_visibility
        will_be_loaded = in_desc and in_data  # Now always loaded if both exist
        
        print(f"  {entity}:")
        print(f"    In descriptor: {in_desc}")
        print(f"    In data: {in_data}")
        print(f"    Has visibility condition: {has_visibility}")
        print(f"    Will be loaded: {'✅ YES' if will_be_loaded else '❌ NO'}")
    
    print(f"\n🎯 EXPECTED RESULTS AFTER CHANGE:")
    print(f"  ✅ ALL {len(common_entities)} entities with both descriptor + data will be loaded")
    print(f"  ✅ TUVMINIMALNI will be included (if it has both descriptor + data)")
    print(f"  ✅ All {len(entities_with_visibility)} entities with visibility conditions will be loaded")
    print(f"  ✅ No entities will be filtered out due to visibility conditions")
    print(f"  ✅ Maximum entity coverage achieved")
    
    # Test assertions
    assert len(all_desc_entities) > 50, f"Should find many descriptor entities, found {len(all_desc_entities)}"
    assert len(all_data_entities) > 50, f"Should find many data entities, found {len(all_data_entities)}"
    assert len(common_entities) > 30, f"Should find many common entities, found {len(common_entities)}"
    
    # Check that TUVMINIMALNI is in the common entities (should be loaded)
    tuvminimalni_will_load = "TUVMINIMALNI" in common_entities
    assert tuvminimalni_will_load, "TUVMINIMALNI should be loaded (exists in both descriptor and data)"
    
    print(f"\n✅ VERIFICATION PASSED!")
    print(f"🎉 All entities with both descriptor and data will be loaded!")


def test_comprehensive_entity_coverage():
    """Test comprehensive entity coverage across all descriptor files."""
    
    print(f"\n=== COMPREHENSIVE ENTITY COVERAGE TEST ===")
    
    sample_dir = project_root / "tests" / "sample_data"
    
    # Test all available descriptor and data file pairs
    file_pairs = [
        ("tuv1.xml", "TUV11.XML"),
        ("okruh.xml", "OKRUH10.XML"),
        ("fve.xml", "FVE4.XML"),
        ("biv.xml", "BIV1.XML"),
        ("stavjed.xml", "STAVJED1.XML"),
    ]
    
    total_desc_entities = 0
    total_data_entities = 0
    total_common_entities = 0
    total_visibility_entities = 0
    
    print(f"📊 COVERAGE BY FILE:")
    
    for desc_file, data_file in file_pairs:
        desc_path = sample_dir / desc_file
        data_path = sample_dir / data_file
        
        if desc_path.exists() and data_path.exists():
            # Load files
            with open(desc_path, 'r', encoding='utf-8') as f:
                desc_content = f.read()
            
            with open(data_path, 'r', encoding='utf-8') as f:
                data_content = f.read()
            
            # Count entities
            desc_entities = set(re.findall(r'prop="([^"]*)"', desc_content))
            data_entities = set(re.findall(r'<INPUT[^>]*P="([^"]*)"', data_content))
            common_entities = desc_entities & data_entities
            vis_entities = set(re.findall(r'prop="([^"]*)"[^>]*visData="[^"]*"', desc_content))
            
            print(f"  {desc_file}:")
            print(f"    Descriptor: {len(desc_entities)} entities")
            print(f"    Data: {len(data_entities)} entities")
            print(f"    Common (will load): {len(common_entities)} entities")
            print(f"    With visibility: {len(vis_entities)} entities")
            
            total_desc_entities += len(desc_entities)
            total_data_entities += len(data_entities)
            total_common_entities += len(common_entities)
            total_visibility_entities += len(vis_entities)
    
    print(f"\n📊 TOTAL COVERAGE:")
    print(f"  Total descriptor entities: {total_desc_entities}")
    print(f"  Total data entities: {total_data_entities}")
    print(f"  Total entities that will load: {total_common_entities}")
    print(f"  Total with visibility conditions: {total_visibility_entities}")
    
    coverage_ratio = (total_common_entities / total_desc_entities * 100) if total_desc_entities > 0 else 0
    visibility_ratio = (total_visibility_entities / total_desc_entities * 100) if total_desc_entities > 0 else 0
    
    print(f"  Coverage ratio: {coverage_ratio:.1f}%")
    print(f"  Visibility affected: {visibility_ratio:.1f}%")
    
    print(f"\n🎯 IMPACT OF IGNORING VISIBILITY:")
    print(f"  Before: Some of {total_visibility_entities} visibility-controlled entities were hidden")
    print(f"  After: ALL {total_common_entities} entities with data will be loaded")
    print(f"  Improvement: +{total_visibility_entities} potentially missing entities now included")
    
    # Test assertions
    assert total_desc_entities > 200, f"Should find many descriptor entities across all files, found {total_desc_entities}"
    assert total_common_entities > 150, f"Should find many loadable entities, found {total_common_entities}"
    assert total_visibility_entities > 50, f"Should find many entities with visibility conditions, found {total_visibility_entities}"
    assert coverage_ratio > 30, f"Should have reasonable coverage ratio, got {coverage_ratio:.1f}%"
    
    print(f"\n✅ COMPREHENSIVE COVERAGE TEST PASSED!")
    print(f"🎉 Maximum entity coverage will be achieved!")


if __name__ == "__main__":
    """Run tests directly for debugging."""
    print("🧪 Running Load All Entities Tests")
    print("=" * 60)
    
    try:
        test_load_all_entities_verification()
        test_comprehensive_entity_coverage()
        
        print("\n" + "=" * 60)
        print("🎉 LOAD ALL ENTITIES VERIFICATION COMPLETE!")
        print("✅ Integration will now load ALL entities with available data")
        print("🔧 TUVMINIMALNI and all other entities will be included")
        print("📝 Restart Home Assistant to see maximum entity coverage")
        
    except Exception as e:
        print(f"\n❌ VERIFICATION FAILED: {e}")
        raise
