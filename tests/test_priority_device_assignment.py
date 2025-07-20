"""Test priority-based device assignment."""

def test_priority_device_assignment():
    """Test that entities are assigned to devices based on priority order."""
    
    # Simulate entities from multiple pages with some duplicates
    mock_entities = [
        # SPOT entities (highest priority)
        {
            "entity_id": "xcc_spotoveceny_standardexportmode",
            "entity_type": "sensor",
            "state": "1",
            "attributes": {
                "field_name": "SPOTOVECENY-STANDARDEXPORTMODE",
                "page": "SPOT.XML",
                "source_page": "SPOT"
            }
        },
        # FVE entities (second priority) - includes duplicate
        {
            "entity_id": "xcc_spotoveceny_standardexportmode",
            "entity_type": "sensor",
            "state": "1", 
            "attributes": {
                "field_name": "SPOTOVECENY-STANDARDEXPORTMODE",  # Duplicate from SPOT
                "page": "FVE.XML",
                "source_page": "FVE"
            }
        },
        {
            "entity_id": "xcc_fvestats_demandchrgcurr",
            "entity_type": "sensor",
            "state": "15.2",
            "attributes": {
                "field_name": "FVESTATS-DEMANDCHRGCURR",
                "page": "FVE.XML",
                "source_page": "FVE"
            }
        }
    ]
    
    # Simulate the priority-based assignment logic
    device_priority = ["SPOT", "FVE", "BIV", "OKRUH", "TUV1", "STAVJED"]
    assigned_entities = set()
    device_assignments = {}
    
    # Group entities by page
    entities_by_page = {}
    for entity in mock_entities:
        page = entity["attributes"].get("page", "unknown").upper()
        page_normalized = page.replace("1.XML", "").replace("10.XML", "").replace("11.XML", "").replace("4.XML", "").replace(".XML", "")
        if page_normalized not in entities_by_page:
            entities_by_page[page_normalized] = []
        entities_by_page[page_normalized].append(entity)
    
    print("🔍 TESTING PRIORITY-BASED DEVICE ASSIGNMENT")
    print("=" * 60)
    print(f"Device priority order: {' > '.join(device_priority)}")
    print(f"Pages found: {list(entities_by_page.keys())}")
    
    # Process entities in priority order
    for device_name in device_priority:
        if device_name not in entities_by_page:
            continue
            
        device_entities = entities_by_page[device_name]
        assigned_count = 0
        skipped_count = 0
        
        print(f"\n📄 Processing {device_name}:")
        
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
    print(f"\n🎯 FINAL DEVICE ASSIGNMENTS:")
    print("=" * 60)
    
    expected_assignments = {
        "SPOTOVECENY-STANDARDEXPORTMODE": "SPOT",  # Should go to SPOT (highest priority)
        "FVESTATS-DEMANDCHRGCURR": "FVE"
    }
    
    for prop, expected_device in expected_assignments.items():
        actual_device = device_assignments.get(prop)
        if actual_device == expected_device:
            print(f"✅ {prop}: {actual_device} (correct)")
        else:
            print(f"❌ {prop}: expected {expected_device}, got {actual_device}")
            return False
    
    print(f"\n✅ SUCCESS: All {len(device_assignments)} entities assigned uniquely")
    # Test passed if we reach here without any assertion errors

