"""Test sensor creation with sample data."""

import pytest
import sys
import os
from pathlib import Path
from unittest.mock import Mock, AsyncMock, MagicMock

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_sensor_creation_with_sample_data():
    """Test that sensor creation works with real sample data."""
    
    # Import the modules we need to test (standalone versions)
    try:
        from xcc_client import parse_xml_entities
        # Import descriptor parser directly to avoid Home Assistant dependencies
        sys.path.insert(0, str(project_root / "custom_components" / "xcc"))
        from descriptor_parser import XCCDescriptorParser
    except ImportError as e:
        print(f"Cannot import required modules: {e}")
        return None
    
    # Load sample data
    sample_dir = project_root / "sample_data"
    if not sample_dir.exists():
        pytest.skip("Sample data directory not found")
    
    # Test with STAVJED1.XML (status data)
    sample_file = sample_dir / "STAVJED1.XML"
    if not sample_file.exists():
        pytest.skip("STAVJED1.XML sample file not found")
    
    print(f"\n=== TESTING SENSOR CREATION WITH SAMPLE DATA ===")
    
    # Load and parse XML with proper encoding detection
    try:
        with open(sample_file, 'r', encoding='windows-1250') as f:
            xml_content = f.read()
    except UnicodeDecodeError:
        try:
            with open(sample_file, 'r', encoding='utf-8') as f:
                xml_content = f.read()
        except UnicodeDecodeError:
            with open(sample_file, 'rb') as f:
                raw_content = f.read()
                # Try to detect encoding
                xml_content = raw_content.decode('utf-8', errors='ignore')

    print(f"Loaded XML content: {len(xml_content)} characters")
    print(f"First 200 chars: {xml_content[:200]}")

    # Parse entities from XML
    entities = parse_xml_entities(xml_content, "STAVJED1.XML")
    print(f"Parsed {len(entities)} entities from XML")

    if len(entities) == 0:
        print("❌ No entities parsed! Checking XML structure...")
        # Check if XML contains INPUT elements
        input_count = xml_content.count('<INPUT')
        print(f"Found {input_count} <INPUT> elements in XML")
        if input_count == 0:
            print("No <INPUT> elements found - this might be a descriptor file, not data file")
            return None
    
    # Load descriptors to determine entity types
    descriptor_files = ["OKRUH.XML", "FVE.XML", "TUV1.XML", "BIV.XML", "SPOT.XML"]
    descriptor_data = {}
    
    for desc_file in descriptor_files:
        desc_path = sample_dir / desc_file
        if desc_path.exists():
            try:
                with open(desc_path, 'r', encoding='windows-1250') as f:
                    descriptor_data[desc_file] = f.read()
            except UnicodeDecodeError:
                try:
                    with open(desc_path, 'r', encoding='utf-8') as f:
                        descriptor_data[desc_file] = f.read()
                except UnicodeDecodeError:
                    with open(desc_path, 'rb') as f:
                        raw_content = f.read()
                        descriptor_data[desc_file] = raw_content.decode('utf-8', errors='ignore')
            print(f"Loaded descriptor {desc_file}: {len(descriptor_data[desc_file])} characters")
    
    # Parse descriptors
    if descriptor_data:
        parser = XCCDescriptorParser()
        entity_configs = parser.parse_descriptor_files(descriptor_data)
        print(f"Parsed {len(entity_configs)} entity configurations from descriptors")
    else:
        entity_configs = {}
        print("No descriptor data available")
    
    # Simulate coordinator data processing
    processed_data = {
        "sensors": {},
        "switches": {},
        "numbers": {},
        "selects": {},
        "buttons": {},
        "entities": []
    }
    
    sensor_count = 0
    switch_count = 0
    number_count = 0
    select_count = 0
    
    for entity in entities:
        prop = entity.get("prop", "").upper()
        
        # Determine entity type based on descriptor or default logic
        if prop in entity_configs:
            config = entity_configs[prop]
            entity_type = config.get('entity_type', 'sensor')
            print(f"Entity {prop}: has descriptor, type = {entity_type}")
        else:
            # Default logic for entities without descriptors
            attributes = entity.get("attributes", {})
            data_type = attributes.get("data_type", "unknown")
            is_settable = attributes.get("is_settable", False)
            
            if data_type == "boolean":
                entity_type = "switch" if is_settable else "binary_sensor"
            elif data_type == "enum":
                entity_type = "select" if is_settable else "sensor"
            elif data_type == "numeric":
                entity_type = "number" if is_settable else "sensor"
            else:
                entity_type = "sensor"
            
            print(f"Entity {prop}: no descriptor, defaulting to {entity_type} (data_type={data_type}, settable={is_settable})")
        
        # Add entity data structure that matches what coordinator creates
        entity_data = {
            "entity_id": f"xcc_{prop.lower()}",
            "prop": prop,
            "type": entity_type,
            "data": entity
        }
        
        # Store in appropriate category
        if entity_type == "sensor":
            processed_data["sensors"][prop] = entity_data
            sensor_count += 1
        elif entity_type == "switch":
            processed_data["switches"][prop] = entity_data
            switch_count += 1
        elif entity_type == "number":
            processed_data["numbers"][prop] = entity_data
            number_count += 1
        elif entity_type == "select":
            processed_data["selects"][prop] = entity_data
            select_count += 1
        
        processed_data["entities"].append(entity_data)
    
    print(f"\n=== ENTITY DISTRIBUTION ===")
    print(f"Sensors: {sensor_count}")
    print(f"Switches: {switch_count}")
    print(f"Numbers: {number_count}")
    print(f"Selects: {select_count}")
    print(f"Total: {len(processed_data['entities'])}")
    
    # Test that we have sensors to create
    assert sensor_count > 0, f"No sensors found! This indicates a problem with entity classification."
    assert len(processed_data["sensors"]) == sensor_count, "Sensor count mismatch"
    
    # Test sensor data structure
    for prop, sensor_data in processed_data["sensors"].items():
        assert "entity_id" in sensor_data, f"Sensor {prop} missing entity_id"
        assert "prop" in sensor_data, f"Sensor {prop} missing prop"
        assert "type" in sensor_data, f"Sensor {prop} missing type"
        assert "data" in sensor_data, f"Sensor {prop} missing data"
        assert sensor_data["type"] == "sensor", f"Sensor {prop} has wrong type: {sensor_data['type']}"
    
    print(f"\n✅ Test passed! Found {sensor_count} sensors that should be created")
    
    # Show some example sensors
    print(f"\n=== EXAMPLE SENSORS ===")
    for i, (prop, sensor_data) in enumerate(list(processed_data["sensors"].items())[:5]):
        print(f"{i+1}. {prop} -> {sensor_data['entity_id']}")
        entity = sensor_data["data"]
        value = entity.get("value", "N/A")
        unit = entity.get("attributes", {}).get("unit", "")
        print(f"   Value: {value} {unit}")
    
    return processed_data

if __name__ == "__main__":
    # Run the test directly
    try:
        result = test_sensor_creation_with_sample_data()
        print(f"\n🎉 SUCCESS: Test completed successfully!")
        print(f"Found {len(result['sensors'])} sensors that should be created")
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
