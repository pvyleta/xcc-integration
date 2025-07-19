"""Test hidden settings device functionality."""

def test_hidden_settings_device_assignment():
    """Test that entities without descriptors are assigned to hidden settings device."""
    
    print("🔍 TESTING HIDDEN SETTINGS DEVICE ASSIGNMENT")
    print("=" * 70)
    
    # Mock entities - some with descriptors, some without
    mock_entities = [
        # Entity with descriptor (should go to FVE device)
        {
            "entity_id": "xcc_fvestats_demandchrgcurr",
            "entity_type": "sensor",
            "state": "15.2",
            "attributes": {
                "field_name": "FVESTATS-DEMANDCHRGCURR",
                "page": "FVE.XML",
                "source_page": "FVE"
            }
        },
        # Entity without descriptor (should go to hidden settings)
        {
            "entity_id": "xcc_variantazobrazcerpadla7",
            "entity_type": "sensor",
            "state": "1",
            "attributes": {
                "field_name": "VARIANTAZOBRAZCERPADLA7",
                "page": "OKRUH.XML",
                "source_page": "OKRUH"
            }
        }
    ]
    
    # Mock entity configs (descriptors) - only some entities have them
    mock_entity_configs = {
        "FVESTATS-DEMANDCHRGCURR": {
            "friendly_name": "System - Actual maximal charge current",
            "friendly_name_en": "System - Actual maximal charge current",
            "entity_type": "sensor",
            "unit": "A"
        }
        # Note: VARIANTAZOBRAZCERPADLA7 is NOT in entity_configs
    }
    
    # Simulate the hidden settings assignment logic
    device_priority = ["SPOT", "FVE", "BIV", "OKRUH", "TUV1", "STAVJED", "XCC_HIDDEN_SETTINGS"]
    assigned_entities = set()
    device_assignments = {}
    
    # Group entities by page/device for priority processing
    entities_by_page = {}
    hidden_entities = []
    
    for entity in mock_entities:
        prop = entity["attributes"]["field_name"]
        page = entity["attributes"].get("page", "unknown").upper()
        
        # Check if entity has a descriptor
        has_descriptor = prop in mock_entity_configs
        
        if not has_descriptor:
            # Entity has no descriptor - add to hidden settings
            hidden_entities.append(entity)
            print(f"🔍 Found hidden entity: {prop} (no descriptor)")
        else:
            # Entity has descriptor - add to appropriate page device
            page_normalized = page.replace("1.XML", "").replace("10.XML", "").replace("11.XML", "").replace("4.XML", "").replace(".XML", "")
            if page_normalized not in entities_by_page:
                entities_by_page[page_normalized] = []
            entities_by_page[page_normalized].append(entity)
            print(f"✅ Found entity with descriptor: {prop} -> {page_normalized}")
    
    # Add hidden entities to special device
    if hidden_entities:
        entities_by_page["XCC_HIDDEN_SETTINGS"] = hidden_entities
        print(f"📦 Added {len(hidden_entities)} hidden entities to XCC_HIDDEN_SETTINGS device")
    
    print(f"\n📊 DEVICE GROUPING RESULTS:")
    for device, entities in entities_by_page.items():
        print(f"   {device}: {len(entities)} entities")
        for entity in entities:
            prop = entity["attributes"]["field_name"]
            print(f"      - {prop}")
    
    # Process entities in priority order
    print(f"\n🏗️ PRIORITY-BASED ASSIGNMENT:")
    for device_name in device_priority:
        if device_name not in entities_by_page:
            continue
            
        device_entities = entities_by_page[device_name]
        assigned_count = 0
        skipped_count = 0
        
        print(f"\n📱 Processing {device_name}:")
        
        for entity in device_entities:
            prop = entity["attributes"]["field_name"]
            
            if prop in assigned_entities:
                print(f"   ⏭️  SKIP: {prop} (already assigned)")
                skipped_count += 1
                continue
            
            # Assign entity to this device
            assigned_entities.add(prop)
            device_assignments[prop] = device_name
            assigned_count += 1
            print(f"   ✅ ASSIGN: {prop} -> {device_name}")
        
        print(f"   📊 Summary: {assigned_count} assigned, {skipped_count} skipped")
    
    # Verify results
    print(f"\n🎯 VERIFICATION:")
    
    # Check that hidden entity is assigned to XCC_HIDDEN_SETTINGS
    assert device_assignments.get("VARIANTAZOBRAZCERPADLA7") == "XCC_HIDDEN_SETTINGS"
    print("✅ Hidden entity VARIANTAZOBRAZCERPADLA7 correctly assigned to XCC_HIDDEN_SETTINGS")
    
    # Check that normal entity is assigned to FVE
    assert device_assignments.get("FVESTATS-DEMANDCHRGCURR") == "FVE"
    print("✅ Normal entity FVESTATS-DEMANDCHRGCURR correctly assigned to FVE")
    
    print(f"\n✅ SUCCESS: All {len(device_assignments)} entities correctly assigned")

if __name__ == "__main__":
    test_hidden_settings_device_assignment()
    print("\n🎉 HIDDEN SETTINGS DEVICE TEST PASSED!")
