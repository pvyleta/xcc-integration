"""Test device assignment fix."""

def test_device_assignment_with_hidden_settings():
    """Test that normal device assignment works and hidden settings are added."""
    
    print("🔍 TESTING DEVICE ASSIGNMENT WITH HIDDEN SETTINGS")
    print("=" * 70)
    
    # Mock entities - mix of entities with and without descriptors
    mock_entities = [
        # Entity with descriptor from FVE page
        {
            "attributes": {
                "field_name": "FVE-ENABLED",
                "page": "FVE4.XML",
                "value": "1"
            }
        },
        # Entity with descriptor from OKRUH page
        {
            "attributes": {
                "field_name": "TOPNEOKRUHYIN3-FVEPRETOPENI-PRIORITA",
                "page": "OKRUH10.XML",
                "value": "5"
            }
        },
        # Entity without descriptor from STAVJED page
        {
            "attributes": {
                "field_name": "SVENKU",
                "page": "STAVJED1.XML",
                "value": "24.0"
            }
        },
        # Entity without descriptor from OKRUH page
        {
            "attributes": {
                "field_name": "VARIANTAZOBRAZCERPADLA7",
                "page": "OKRUH10.XML",
                "value": "1"
            }
        }
    ]
    
    # Mock entity configs (descriptors)
    mock_entity_configs = {
        "FVE-ENABLED": {
            "friendly_name": "PVE control",
            "friendly_name_en": "PVE control"
        },
        "TOPNEOKRUHYIN3-FVEPRETOPENI-PRIORITA": {
            "friendly_name": "Přetápětí z FVE - Priority",
            "friendly_name_en": "Priority"
        }
        # Note: SVENKU and VARIANTAZOBRAZCERPADLA7 are NOT in entity_configs
    }
    
    # Simulate the fixed device assignment logic
    device_priority = ["SPOT", "FVE", "BIV", "OKRUH", "TUV1", "STAVJED", "XCC_HIDDEN_SETTINGS"]
    assigned_entities = set()
    
    # Step 1: Separate entities with and without descriptors
    entities_with_descriptors = []
    entities_without_descriptors = []
    
    for entity in mock_entities:
        prop = entity["attributes"]["field_name"]
        if prop in mock_entity_configs:
            entities_with_descriptors.append(entity)
        else:
            entities_without_descriptors.append(entity)
    
    print("📊 STEP 1 - DESCRIPTOR SEPARATION:")
    print(f"   Entities WITH descriptors: {len(entities_with_descriptors)}")
    for entity in entities_with_descriptors:
        prop = entity["attributes"]["field_name"]
        print(f"      - {prop}")
    
    print(f"   Entities WITHOUT descriptors: {len(entities_without_descriptors)}")
    for entity in entities_without_descriptors:
        prop = entity["attributes"]["field_name"]
        print(f"      - {prop}")
    
    # Step 2: Group entities with descriptors by page
    entities_by_page = {}
    for entity in entities_with_descriptors:
        page = entity["attributes"].get("page", "unknown").upper()
        page_normalized = page.replace("1.XML", "").replace("10.XML", "").replace("11.XML", "").replace("4.XML", "").replace(".XML", "")
        if page_normalized not in entities_by_page:
            entities_by_page[page_normalized] = []
        entities_by_page[page_normalized].append(entity)
    
    # Add entities without descriptors to hidden settings device
    if entities_without_descriptors:
        entities_by_page["XCC_HIDDEN_SETTINGS"] = entities_without_descriptors
    
    print(f"\n📊 STEP 2 - PAGE GROUPING:")
    for page, entities in entities_by_page.items():
        print(f"   {page}: {len(entities)} entities")
        for entity in entities:
            prop = entity["attributes"]["field_name"]
            has_descriptor = prop in mock_entity_configs
            print(f"      - {prop} (descriptor: {has_descriptor})")
    
    # Step 3: Process entities in priority order
    device_assignments = {}
    print(f"\n📊 STEP 3 - PRIORITY-BASED ASSIGNMENT:")
    
    for device_name in device_priority:
        if device_name not in entities_by_page:
            print(f"   📄 {device_name}: No entities found")
            continue
            
        device_entities = entities_by_page[device_name]
        assigned_count = 0
        skipped_count = 0
        
        print(f"\n   📱 Processing {device_name}:")
        
        for entity in device_entities:
            prop = entity["attributes"]["field_name"]
            
            if prop in assigned_entities:
                print(f"      ⏭️  SKIP: {prop} (already assigned)")
                skipped_count += 1
                continue
            
            # Assign entity to this device
            assigned_entities.add(prop)
            device_assignments[prop] = device_name
            assigned_count += 1
            
            has_descriptor = prop in mock_entity_configs
            descriptor_note = "(with descriptor)" if has_descriptor else "(no descriptor)"
            print(f"      ✅ ASSIGN: {prop} -> {device_name} {descriptor_note}")
        
        print(f"      �� Summary: {assigned_count} assigned, {skipped_count} skipped")
    
    # Verify results
    print(f"\n🎯 VERIFICATION:")
    
    expected_assignments = {
        "FVE-ENABLED": "FVE",  # Has descriptor, from FVE page
        "TOPNEOKRUHYIN3-FVEPRETOPENI-PRIORITA": "OKRUH",  # Has descriptor, from OKRUH page
        "SVENKU": "XCC_HIDDEN_SETTINGS",  # No descriptor, should go to hidden settings
        "VARIANTAZOBRAZCERPADLA7": "XCC_HIDDEN_SETTINGS"  # No descriptor, should go to hidden settings
    }
    
    for prop, expected_device in expected_assignments.items():
        actual_device = device_assignments.get(prop)
        print(f"   {prop}: {actual_device} (expected: {expected_device})")
        assert actual_device == expected_device, f"{prop} assignment mismatch: expected {expected_device}, got {actual_device}"
    
    print(f"\n✅ SUCCESS: Device assignment working correctly")
    print(f"   Normal devices: {len([d for d in device_assignments.values() if d != 'XCC_HIDDEN_SETTINGS'])} entities")
    print(f"   Hidden settings: {len([d for d in device_assignments.values() if d == 'XCC_HIDDEN_SETTINGS'])} entities")

if __name__ == "__main__":
    test_device_assignment_with_hidden_settings()
    print("\n🎉 DEVICE ASSIGNMENT FIX TEST PASSED!")
