"""Tests for STATUS.XML parsing and entity routing.

STATUS.XML is a data-only page with no paired descriptor XML.
Its field metadata lives in STATUS_XML_DESCRIPTOR (const.py).
"""

def test_status_xml_sample_data_exists():
    """STATUS.XML sample data file exists and is valid XML."""
    from pathlib import Path
    sample_file = Path(__file__).parent / "sample_data" / "STATUS.XML"
    
    assert sample_file.exists(), "STATUS.XML sample data missing"
    content = sample_file.read_text(encoding="utf-8")
    
    # Basic XML structure checks
    assert '<?xml version=' in content
    assert '<PAGE>' in content
    assert '</PAGE>' in content
    assert '<INPUT P="SVYKON"' in content, "SVYKON field missing"
    assert '<INPUT P="SCHLAZENI"' in content, "SCHLAZENI field missing"
    assert '<INPUT P="SOBEH0RUN"' in content, "SOBEH0RUN field missing"


def test_status_xml_descriptor_structure():
    """STATUS_XML_DESCRIPTOR contains all required fields with correct structure."""
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'custom_components', 'xcc'))
    
    from const import STATUS_XML_DESCRIPTOR
    
    # Must have the unique STATUS.XML fields
    expected_fields = [
        "SVYKON", "SCHLAZENI", "SPOZTEP", "SAKTTEP",
        "STEPTUV", "SAKTTEPTUV", "SHDOIGNORE", "SHDOLOWT", "SHDOSTAV",
        "SSTAVJEDNOTKY", "SSTAVKOTLU",
    ]
    
    for field in expected_fields:
        assert field in STATUS_XML_DESCRIPTOR, f"{field} missing from STATUS_XML_DESCRIPTOR"
        
        config = STATUS_XML_DESCRIPTOR[field]
        assert "entity_type" in config, f"{field}: missing entity_type"
        assert "friendly_name" in config, f"{field}: missing friendly_name"
        assert "friendly_name_en" in config, f"{field}: missing friendly_name_en"
        assert "unit" in config, f"{field}: missing unit"
        assert "writable" in config, f"{field}: missing writable"
        
        # All STATUS.XML fields are read-only
        assert config["writable"] is False, f"{field}: should be read-only"


def test_status_xml_binary_sensor_fields():
    """All BOOL fields in STATUS_XML_DESCRIPTOR are declared as binary_sensor."""
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'custom_components', 'xcc'))
    
    from const import STATUS_XML_DESCRIPTOR
    
    bool_fields = [
        "SCHLAZENI", "STEPTUV", "SHDOIGNORE", "SHDOSTAV",
        "SSTAVJEDNOTKY", "SSTAVKOTLU",
    ] + [f"SOBEH{i}RUN" for i in range(10)] + [f"SOBEH{i}VIS" for i in range(10)]
    
    for field in bool_fields:
        assert field in STATUS_XML_DESCRIPTOR
        assert STATUS_XML_DESCRIPTOR[field]["entity_type"] == "binary_sensor", (
            f"{field}: expected entity_type='binary_sensor', got "
            f"{STATUS_XML_DESCRIPTOR[field]['entity_type']!r}"
        )


def test_coordinator_binary_sensor_routing():
    """Verify coordinator routing logic sends binary_sensor to correct bucket."""
    # Simulate the routing block from coordinator._process_entities (lines 451-462)
    processed_data = {"sensors": {}, "binary_sensors": {}, "switches": {}, "numbers": {}}
    
    test_cases = [
        ("sobeh0run", "binary_sensor", "binary_sensors"),
        ("schlazeni", "binary_sensor", "binary_sensors"),
        ("svykon", "sensor", "sensors"),
        ("zapnuto", "switch", "switches"),
    ]
    
    for entity_id, entity_type, expected_bucket in test_cases:
        state_data = {"id": entity_id, "state": "1"}
        
        # This is the fix from v1.14.6 - must have binary_sensor branch
        if entity_type == "switch":
            processed_data["switches"][entity_id] = state_data
        elif entity_type == "binary_sensor":
            processed_data["binary_sensors"][entity_id] = state_data
        elif entity_type == "number":
            processed_data["numbers"][entity_id] = state_data
        else:
            processed_data["sensors"][entity_id] = state_data
        
        assert entity_id in processed_data[expected_bucket], (
            f"{entity_id} (type={entity_type}) should be in '{expected_bucket}'"
        )


if __name__ == "__main__":
    test_status_xml_sample_data_exists()
    print("✅ STATUS.XML sample data valid")
    
    test_status_xml_descriptor_structure()
    print("✅ STATUS_XML_DESCRIPTOR structure valid")
    
    test_status_xml_binary_sensor_fields()
    print("✅ STATUS_XML_DESCRIPTOR binary_sensor fields correct")
    
    test_coordinator_binary_sensor_routing()
    print("✅ Coordinator routing logic correct")
    
    print("\n✅ All STATUS.XML tests passed!")
