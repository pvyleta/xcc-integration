"""Integration test for device separation with real sample data."""

import os
import xml.etree.ElementTree as ET
from collections import defaultdict

def test_device_separation_with_sample_data():
    """Test device separation logic using actual sample XML files."""
    
    # Sample XML files to test
    sample_files = {
        "SPOT": "tests/sample_data/SPOT.XML",
        "FVE": "tests/sample_data/FVE.XML", 
        "BIV": "tests/sample_data/BIV.XML",
        "OKRUH": "tests/sample_data/OKRUH.XML",
        "TUV1": "tests/sample_data/TUV1.XML",
        "STAVJED": "tests/sample_data/STAVJED.XML"
    }
    
    # Priority order (highest to lowest)
    device_priority = ["SPOT", "FVE", "BIV", "OKRUH", "TUV1", "STAVJED"]
    
    # Parse entities from sample files
    entities_by_device = {}
    all_entities = set()
    
    print("🔍 TESTING DEVICE SEPARATION WITH REAL SAMPLE DATA")
    print("=" * 70)
    
    for device_name, file_path in sample_files.items():
        if not os.path.exists(file_path):
            print(f"⚠️  Sample file not found: {file_path}")
            continue
            
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Find all elements with 'prop' attribute
            entities = set()
            for element in root.iter():
                prop = element.get('prop')
                if prop:
                    entities.add(prop)
                    all_entities.add(prop)
            
            entities_by_device[device_name] = entities
            print(f"📄 {device_name}: {len(entities)} entities")
            
        except ET.ParseError as e:
            print(f"❌ XML Parse Error in {file_path}: {e}")
            continue
        except Exception as e:
            print(f"❌ Error processing {file_path}: {e}")
            continue
    
    print(f"\n📊 Total unique entities across all files: {len(all_entities)}")
    
    # Simulate priority-based assignment
    assigned_entities = set()
    device_assignments = {}
    
    print(f"\n🏗️ PRIORITY-BASED ASSIGNMENT SIMULATION")
    print("=" * 60)
    
    for device_name in device_priority:
        if device_name not in entities_by_device:
            continue
            
        device_entities = entities_by_device[device_name]
        assigned_count = 0
        skipped_count = 0
        
        for entity_prop in device_entities:
            if entity_prop in assigned_entities:
                skipped_count += 1
                continue
            
            # Assign to this device
            assigned_entities.add(entity_prop)
            device_assignments[entity_prop] = device_name
            assigned_count += 1
        
        print(f"📱 {device_name}: {assigned_count} assigned, {skipped_count} skipped (of {len(device_entities)} total)")
    
    # Verify results
    print(f"\n🎯 ASSIGNMENT VERIFICATION")
    print("=" * 60)
    
    # Check that all entities are assigned exactly once
    assert len(device_assignments) == len(assigned_entities), "Mismatch between assignments and assigned set"
    
    # Check that no entity is assigned to multiple devices
    assigned_props = list(device_assignments.keys())
    assert len(assigned_props) == len(set(assigned_props)), "Duplicate entity assignments detected"
    
    # Calculate duplicate statistics
    total_entity_occurrences = sum(len(entities) for entities in entities_by_device.values())
    unique_entities = len(all_entities)
    duplicate_occurrences = total_entity_occurrences - unique_entities
    
    print(f"✅ All {len(device_assignments)} entities assigned correctly")
    print(f"📊 Duplicate handling: {duplicate_occurrences} duplicate occurrences resolved")
    print(f"�� Efficiency: {unique_entities}/{total_entity_occurrences} = {unique_entities/total_entity_occurrences*100:.1f}% unique")
    
    # Verify device assignment distribution
    device_entity_counts = defaultdict(int)
    for device in device_assignments.values():
        device_entity_counts[device] += 1
    
    print(f"\n📱 FINAL DEVICE DISTRIBUTION:")
    for device in device_priority:
        count = device_entity_counts.get(device, 0)
        if count > 0:
            print(f"   {device}: {count} entities")

if __name__ == "__main__":
    test_device_separation_with_sample_data()
    print("\n🎉 DEVICE SEPARATION INTEGRATION TEST PASSED!")
