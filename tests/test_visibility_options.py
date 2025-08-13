#!/usr/bin/env python3
"""
Test visibility handling options.

This test demonstrates the difference between respecting visibility
conditions vs. ignoring them and loading all entities.
"""

import pytest
import sys
from pathlib import Path
import re

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_visibility_options_comparison():
    """Compare entity counts with and without visibility conditions."""
    
    print(f"\n=== VISIBILITY OPTIONS COMPARISON ===")
    
    # Load sample data
    sample_dir = project_root / "tests" / "sample_data"
    tuv_desc_file = sample_dir / "tuv1.xml"
    tuv_data_file = sample_dir / "TUV11.XML"
    
    if not tuv_desc_file.exists() or not tuv_data_file.exists():
        pytest.skip("TUV sample files not found")
    
    # Load descriptor and data
    with open(tuv_desc_file, 'r', encoding='utf-8') as f:
        desc_content = f.read()
    
    with open(tuv_data_file, 'r', encoding='utf-8') as f:
        data_content = f.read()
    
    # Extract current data values
    data_values = {}
    input_matches = re.findall(r'<INPUT[^>]*P="([^"]*)"[^>]*VALUE="([^"]*)"', data_content)
    for prop, value in input_matches:
        data_values[prop] = value
    
    print(f"Loaded {len(data_values)} current data values")
    
    # Simulate both approaches without importing Home Assistant dependencies
    
    # Count all entities in descriptor (ignore visibility approach)
    all_entities = set(re.findall(r'prop="([^"]*)"', desc_content))
    
    # Count entities with visibility conditions
    entities_with_visibility = {}
    vis_matches = re.findall(r'prop="([^"]*)"[^>]*visData="([^"]*)"', desc_content)
    for prop, vis_data in vis_matches:
        entities_with_visibility[prop] = vis_data
    
    # Simulate visibility checking
    visible_entities = set()
    hidden_entities = set()
    
    for prop in all_entities:
        if prop in entities_with_visibility:
            vis_data = entities_with_visibility[prop]
            
            # Parse visibility condition
            if vis_data:
                parts = vis_data.split(';')
                if len(parts) >= 3:
                    try:
                        count = int(parts[0])
                        visible = True
                        
                        for i in range(count):
                            prop_idx = 1 + (i * 2)
                            val_idx = 2 + (i * 2)
                            
                            if prop_idx < len(parts) and val_idx < len(parts):
                                condition_prop = parts[prop_idx]
                                expected_value = parts[val_idx]
                                actual_value = data_values.get(condition_prop)
                                
                                if actual_value != expected_value:
                                    visible = False
                                    break
                        
                        if visible:
                            visible_entities.add(prop)
                        else:
                            hidden_entities.add(prop)
                    except (ValueError, IndexError):
                        visible_entities.add(prop)  # Include if parsing fails
                else:
                    visible_entities.add(prop)  # Include if format is invalid
            else:
                visible_entities.add(prop)  # Include if no visibility data
        else:
            visible_entities.add(prop)  # Include if no visibility condition
    
    print(f"\n📊 ENTITY COUNT COMPARISON:")
    print(f"  Option 1 - Ignore visibility (load ALL): {len(all_entities)} entities")
    print(f"  Option 2 - Respect visibility (current): {len(visible_entities)} entities")
    print(f"  Entities with visibility conditions: {len(entities_with_visibility)}")
    print(f"  Hidden by visibility conditions: {len(hidden_entities)}")
    
    # Show specific examples
    print(f"\n🔍 SPECIFIC EXAMPLES:")
    
    # Check TUVMINIMALNI specifically
    tuvminimalni_has_visibility = "TUVMINIMALNI" in entities_with_visibility
    tuvminimalni_visible = "TUVMINIMALNI" in visible_entities
    tuvminimalni_condition = entities_with_visibility.get("TUVMINIMALNI", "")
    
    print(f"  TUVMINIMALNI:")
    print(f"    Has visibility condition: {tuvminimalni_has_visibility}")
    print(f"    Condition: {tuvminimalni_condition}")
    print(f"    Would be visible: {tuvminimalni_visible}")
    print(f"    Option 1 (ignore): ✅ INCLUDED")
    print(f"    Option 2 (respect): {'✅ INCLUDED' if tuvminimalni_visible else '❌ EXCLUDED'}")
    
    # Show some hidden entities
    if hidden_entities:
        print(f"\n  Examples of HIDDEN entities (Option 2):")
        for entity in list(hidden_entities)[:5]:
            condition = entities_with_visibility.get(entity, "")
            print(f"    {entity} - {condition}")
    
    print(f"\n💡 RECOMMENDATION:")
    print(f"  If you want MAXIMUM entity coverage: Use Option 1 (ignore visibility)")
    print(f"  If you want CLEAN, relevant entities: Use Option 2 (respect visibility)")
    print(f"  Current implementation: Option 2 with configurable override")
    
    # Test assertions
    assert len(all_entities) > 50, f"Should find many entities, found {len(all_entities)}"
    assert len(entities_with_visibility) > 0, "Should find entities with visibility conditions"
    assert len(visible_entities) <= len(all_entities), "Visible entities should not exceed total"
    assert tuvminimalni_has_visibility, "TUVMINIMALNI should have visibility condition"
    
    print(f"\n✅ Visibility options comparison completed!")


def test_simple_ignore_visibility_demo():
    """Demonstrate how to simply ignore all visibility conditions."""
    
    print(f"\n=== SIMPLE SOLUTION: IGNORE ALL VISIBILITY ===")
    
    print(f"🔧 To load ALL entities regardless of visibility conditions:")
    print(f"")
    print(f"1. In descriptor_parser.py, modify _determine_entity_config():")
    print(f"   # Comment out the visibility check:")
    print(f"   # if not self.ignore_visibility and not self._is_element_visible(element):")
    print(f"   #     return None")
    print(f"")
    print(f"2. Or set ignore_visibility=True when creating the parser:")
    print(f"   parser = XCCDescriptorParser(ignore_visibility=True)")
    print(f"")
    print(f"✅ PROS:")
    print(f"  - Simple solution")
    print(f"  - Maximum entity coverage")
    print(f"  - No complex visibility logic needed")
    print(f"  - You get ALL possible entities including TUVMINIMALNI")
    print(f"")
    print(f"❌ CONS:")
    print(f"  - Some entities might show irrelevant values")
    print(f"  - UI might be cluttered")
    print(f"  - Not respecting XCC's intended design")
    print(f"")
    print(f"🎯 RESULT: You would see ~858 entities instead of ~661")
    print(f"   Including TUVMINIMALNI and all other conditional entities")


if __name__ == "__main__":
    """Run tests directly for debugging."""
    print("🧪 Running XCC Visibility Options Tests")
    print("=" * 60)
    
    try:
        test_visibility_options_comparison()
        test_simple_ignore_visibility_demo()
        
        print("\n" + "=" * 60)
        print("🎉 VISIBILITY OPTIONS ANALYSIS COMPLETE!")
        print("✅ You can choose either approach based on your preference")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
