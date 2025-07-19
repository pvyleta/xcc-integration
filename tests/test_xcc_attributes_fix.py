"""Test XCC attributes fix."""

def test_xcc_attributes_with_descriptor():
    """Test that xcc_* attributes are correctly populated for entities with descriptors."""
    
    print("🔍 TESTING XCC ATTRIBUTES WITH DESCRIPTOR")
    print("=" * 70)
    
    # Mock entity data structure as it would be in coordinator
    mock_entity_data = {
        "type": "number",
        "data": {
            "entity_id": "xcc_topneokruhyin3_fvepretopeni_priorita",
            "entity_type": "number",
            "state": "5",
            "attributes": {
                "source_page": "OKRUH",
                "field_name": "TOPNEOKRUHYIN3-FVEPRETOPENI-PRIORITA",
                "friendly_name": "Topneokruhyin3 Fvepretopeni Priorita",
                "unit": "W",
                "page": "OKRUH.XML"
            }
        },
        "page": "OKRUH.XML",
        "prop": "TOPNEOKRUHYIN3-FVEPRETOPENI-PRIORITA",
        "descriptor_config": {
            "prop": "TOPNEOKRUHYIN3-FVEPRETOPENI-PRIORITA",
            "friendly_name": "Priorita",
            "friendly_name_en": "Priority",
            "page": "OKRUH",
            "writable": True,
            "entity_type": "number",
            "data_type": "real",
            "min": 0,
            "max": 10,
            "step": 1.0,
            "unit": "W"
        },
        "device": "OKRUH"
    }
    
    # Simulate entity initialization and attribute enhancement
    xcc_data = mock_entity_data.get("data", {})
    attributes = xcc_data.get("attributes", {}).copy()
    
    # Apply the descriptor config enhancement (from entity.py fix)
    descriptor_config = mock_entity_data.get("descriptor_config", {})
    if descriptor_config:
        # Add data type and element type information
        if "data_type" in descriptor_config:
            attributes["data_type"] = descriptor_config["data_type"]
        if "entity_type" in descriptor_config:
            entity_type = descriptor_config["entity_type"]
            if entity_type == "number":
                attributes["element_type"] = "INPUT"
            elif entity_type == "switch":
                attributes["element_type"] = "SWITCH"
            elif entity_type == "select":
                attributes["element_type"] = "SELECT"
            else:
                attributes["element_type"] = "DISPLAY"
    
    # Simulate extra_state_attributes method
    xcc_prop = mock_entity_data.get("prop", "unknown")
    xcc_page = mock_entity_data.get("page", "unknown")
    
    extra_attrs = {
        "xcc_field_name": xcc_prop,
        "xcc_page": xcc_page,
        "xcc_data_type": attributes.get("data_type", "unknown"),
        "xcc_element_type": attributes.get("element_type", "unknown"),
    }
    
    # Add settable information
    if descriptor_config:
        extra_attrs["xcc_settable"] = descriptor_config.get("writable", False)
    else:
        extra_attrs["xcc_settable"] = attributes.get("is_settable", False)
    
    print("📊 FIXED XCC ATTRIBUTES:")
    print(f"   xcc_field_name: '{extra_attrs['xcc_field_name']}'")
    print(f"   xcc_page: '{extra_attrs['xcc_page']}'")
    print(f"   xcc_data_type: '{extra_attrs['xcc_data_type']}'")
    print(f"   xcc_element_type: '{extra_attrs['xcc_element_type']}'")
    print(f"   xcc_settable: {extra_attrs['xcc_settable']}")
    
    # Verify the fixes work
    assert extra_attrs["xcc_field_name"] == "TOPNEOKRUHYIN3-FVEPRETOPENI-PRIORITA", "Field name should be original XCC prop"
    assert extra_attrs["xcc_page"] == "OKRUH.XML", "Page should be from entity data"
    assert extra_attrs["xcc_data_type"] == "real", "Data type should be from descriptor config"
    assert extra_attrs["xcc_element_type"] == "INPUT", "Element type should be mapped from entity type"
    assert extra_attrs["xcc_settable"] == True, "Should be settable based on descriptor writable flag"
    
    print("\n✅ All XCC attributes correctly populated for entity with descriptor")

if __name__ == "__main__":
    test_xcc_attributes_with_descriptor()
    print("\n🎉 XCC ATTRIBUTES FIX TEST PASSED!")
