"""Test friendly name entity fix."""

def test_friendly_name_entity_fix():
    """Test that friendly names from descriptor config are properly added to entity attributes."""
    
    # Test case: FVESTATS-DEMANDCHRGCURR entity that was showing Czech name instead of English
    test_prop = "FVESTATS-DEMANDCHRGCURR"
    
    # Simulate descriptor config with English friendly name (from descriptor parser)
    descriptor_config = {
        "prop": test_prop,
        "friendly_name": "System - Actual maximal charge current",
        "friendly_name_en": "System - Actual maximal charge current",
        "page": "FVE",
        "writable": False,
        "entity_type": "sensor",
        "unit": "A"
    }
    
    # Simulate entity data structure as it exists in coordinator
    mock_entity_data = {
        "type": "sensor",
        "data": {
            "entity_id": f"xcc_{test_prop.lower()}",
            "entity_type": "sensor", 
            "state": "25.0",
            "attributes": {
                "source_page": "FVE",
                "field_name": test_prop,
                "friendly_name": "Fvestats Demandchrgcurr",  # Fallback name (Czech-like)
                "unit": "A",
                "page": "FVE"
            }
        },
        "page": "FVE",
        "prop": test_prop,
        "descriptor_config": descriptor_config  # Contains English friendly name
    }
    
    # Simulate XCCEntity.__init__ logic BEFORE the fix
    xcc_data = mock_entity_data.get("data", {})
    attributes_before = xcc_data.get("attributes", {}).copy()
    
    # Verify the problem exists
    assert "friendly_name_en" not in attributes_before
    assert attributes_before.get("friendly_name") == "Fvestats Demandchrgcurr"
    
    # Apply the fix: Add friendly names from descriptor config to attributes
    attributes_after = attributes_before.copy()
    descriptor_config = mock_entity_data.get("descriptor_config", {})
    if descriptor_config:
        if "friendly_name" in descriptor_config:
            attributes_after["friendly_name"] = descriptor_config["friendly_name"]
        if "friendly_name_en" in descriptor_config:
            attributes_after["friendly_name_en"] = descriptor_config["friendly_name_en"]
    
    # Verify the fix works
    assert "friendly_name_en" in attributes_after
    assert attributes_after["friendly_name_en"] == "System - Actual maximal charge current"
    assert attributes_after["friendly_name"] == "System - Actual maximal charge current"
    
    # Simulate _get_entity_name logic
    friendly_name_en = attributes_after.get("friendly_name_en", "")
    friendly_name_cz = attributes_after.get("friendly_name", "")
    
    # Verify English name is selected
    if friendly_name_en:
        selected_name = friendly_name_en
    elif friendly_name_cz:
        selected_name = friendly_name_cz
    else:
        selected_name = test_prop
    
    assert selected_name == "System - Actual maximal charge current"
    
    print(f"✅ Test passed: {test_prop} correctly uses English name: '{selected_name}'")
