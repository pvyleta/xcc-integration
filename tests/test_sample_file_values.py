"""Test entity value updates using real sample files from XCC controller."""

import pytest
import sys
import os
from pathlib import Path
import logging

# Set up logging for tests
logging.basicConfig(level=logging.INFO)
_LOGGER = logging.getLogger(__name__)

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_entity_values_from_sample_files():
    """Test that entity values are correctly extracted from real XCC sample files."""
    
    # Import the modules we need to test
    try:
        from xcc_client import parse_xml_entities
        sys.path.insert(0, str(project_root / "custom_components" / "xcc"))
        from descriptor_parser import XCCDescriptorParser
    except ImportError as e:
        pytest.skip(f"Cannot import required modules: {e}")
    
    # Find sample data directory
    sample_dirs = [
        project_root / "sample_data",
        project_root / "tests" / "sample_data"
    ]
    
    sample_dir = None
    for dir_path in sample_dirs:
        if dir_path.exists():
            sample_dir = dir_path
            break
    
    if not sample_dir:
        pytest.skip("Sample data directory not found")
    
    print(f"\n=== TESTING ENTITY VALUES FROM SAMPLE FILES ===")
    print(f"Using sample directory: {sample_dir}")
    
    # Test with STAVJED1.XML (status data with actual values)
    sample_file = sample_dir / "STAVJED1.XML"
    if not sample_file.exists():
        pytest.skip("STAVJED1.XML sample file not found")
    
    # Load and parse XML
    xml_content = _load_xml_file(sample_file)
    print(f"Loaded XML content: {len(xml_content)} characters")
    
    # Parse entities from XML
    entities = parse_xml_entities(xml_content, "STAVJED1.XML")
    print(f"Parsed {len(entities)} entities from XML")
    
    assert len(entities) > 0, "Should parse at least some entities from sample file"
    
    # Test that entities have state values
    entities_with_values = []
    entities_without_values = []
    
    for entity in entities:
        # IMPORTANT: Standalone xcc_client.py uses "value" field, integration uses "state" field
        state_value = entity.get("value", "") or entity.get("state", "")
        entity_id = entity.get("entity_id", entity.get("prop", "unknown"))

        if state_value is not None and str(state_value).strip():
            entities_with_values.append({
                "entity_id": entity_id,
                "state": state_value,
                "attributes": entity.get("attributes", {})
            })
        else:
            entities_without_values.append(entity_id)
    
    print(f"\n=== ENTITY VALUE ANALYSIS ===")
    print(f"Entities with values: {len(entities_with_values)}")
    print(f"Entities without values: {len(entities_without_values)}")
    
    # Show first 10 entities with values
    print(f"\n=== FIRST 10 ENTITIES WITH VALUES ===")
    for i, entity in enumerate(entities_with_values[:10]):
        state = entity["state"]
        entity_id = entity["entity_id"]
        unit = entity["attributes"].get("unit", "")
        # Handle both standalone and integration entity formats
        field_name = entity["attributes"].get("field_name", entity.get("prop", "unknown"))
        
        value_display = f"{state} {unit}".strip()
        print(f"{i+1:2d}. {field_name:<20} = {value_display:<15} ({entity_id})")
    
    # Test that we have a reasonable number of entities with values
    assert len(entities_with_values) > 10, f"Expected at least 10 entities with values, got {len(entities_with_values)}"
    
    # Test specific value types
    numeric_values = []
    boolean_values = []
    string_values = []
    
    for entity in entities_with_values:
        state = entity["state"]
        
        # Try to classify the value type
        try:
            float(state)
            numeric_values.append(entity)
        except ValueError:
            if state.lower() in ["0", "1", "true", "false", "on", "off"]:
                boolean_values.append(entity)
            else:
                string_values.append(entity)
    
    print(f"\n=== VALUE TYPE ANALYSIS ===")
    print(f"Numeric values: {len(numeric_values)}")
    print(f"Boolean values: {len(boolean_values)}")
    print(f"String values: {len(string_values)}")
    
    # Show examples of each type
    if numeric_values:
        print(f"\n=== NUMERIC VALUE EXAMPLES ===")
        for i, entity in enumerate(numeric_values[:5]):
            field_name = entity["attributes"].get("field_name", "unknown")
            state = entity["state"]
            unit = entity["attributes"].get("unit", "")
            print(f"{i+1}. {field_name}: {state} {unit}".strip())
    
    if boolean_values:
        print(f"\n=== BOOLEAN VALUE EXAMPLES ===")
        for i, entity in enumerate(boolean_values[:5]):
            field_name = entity["attributes"].get("field_name", "unknown")
            state = entity["state"]
            print(f"{i+1}. {field_name}: {state}")
    
    # Test that values are reasonable (not all empty or all the same)
    unique_values = set(entity["state"] for entity in entities_with_values)
    assert len(unique_values) > 1, f"All entities have the same value, expected variety. Values: {unique_values}"
    
    print(f"\n✅ Entity value test passed!")
    print(f"Found {len(entities_with_values)} entities with valid values")
    print(f"Value variety: {len(unique_values)} unique values")
    
    # Test passed if we reach here without any assertion errors


def test_coordinator_value_processing_with_sample_files():
    """Test that the coordinator properly processes values from sample files."""
    
    # Import the modules we need to test
    try:
        from xcc_client import parse_xml_entities
    except ImportError as e:
        pytest.skip(f"Cannot import required modules: {e}")
    
    # Find sample data directory
    sample_dirs = [
        project_root / "sample_data",
        project_root / "tests" / "sample_data"
    ]
    
    sample_dir = None
    for dir_path in sample_dirs:
        if dir_path.exists():
            sample_dir = dir_path
            break
    
    if not sample_dir:
        pytest.skip("Sample data directory not found")
    
    # Test with STAVJED1.XML
    sample_file = sample_dir / "STAVJED1.XML"
    if not sample_file.exists():
        pytest.skip("STAVJED1.XML sample file not found")
    
    print(f"\n=== TESTING COORDINATOR VALUE PROCESSING ===")
    
    # Load and parse XML
    xml_content = _load_xml_file(sample_file)
    entities = parse_xml_entities(xml_content, "STAVJED1.XML")
    
    # Simulate coordinator processing (like in coordinator.py)
    processed_data = {
        "sensors": {},
        "switches": {},
        "numbers": {},
        "selects": {},
        "buttons": {},
        "entities": []
    }
    
    for entity in entities:
        # Extract values - handle both standalone and integration formats
        state_value = entity.get("value", "") or entity.get("state", "")
        entity_id = entity.get("entity_id", entity.get("prop", "unknown"))
        attributes = entity.get("attributes", {})
        field_name = attributes.get("field_name", entity.get("prop", "unknown"))
        
        # Create state data structure like coordinator does
        state_data = {
            "state": state_value,
            "attributes": attributes,
            "entity_id": entity_id,
            "prop": field_name,
            "name": field_name,
            "unit": attributes.get("unit", ""),
            "page": "STAVJED1.XML"
        }
        
        # Classify entity type (simplified)
        entity_type = entity.get("entity_type", "sensor")
        
        if entity_type == "sensor":
            processed_data["sensors"][entity_id] = state_data
        elif entity_type == "binary_sensor":
            processed_data["switches"][entity_id] = state_data
        
        processed_data["entities"].append(state_data)
    
    # Test that processed data has the correct structure
    assert len(processed_data["sensors"]) > 0, "Should have at least some sensors"
    
    # Test that sensor data has state values
    sensors_with_values = 0
    for entity_id, sensor_data in processed_data["sensors"].items():
        state = sensor_data.get("state", "")
        if state is not None and str(state).strip():
            sensors_with_values += 1
    
    print(f"Sensors with values: {sensors_with_values} / {len(processed_data['sensors'])}")
    
    # Show first few sensors with their values
    print(f"\n=== PROCESSED SENSOR VALUES ===")
    for i, (entity_id, sensor_data) in enumerate(list(processed_data["sensors"].items())[:10]):
        state = sensor_data.get("state", "N/A")
        unit = sensor_data.get("unit", "")
        prop = sensor_data.get("prop", "unknown")
        
        value_display = f"{state} {unit}".strip()
        print(f"{i+1:2d}. {prop:<20} = {value_display}")
    
    assert sensors_with_values > 0, f"Expected sensors with values, got {sensors_with_values}"
    
    print(f"\n✅ Coordinator processing test passed!")
    print(f"Processed {len(processed_data['sensors'])} sensors with {sensors_with_values} having values")
    
    # Test passed if we reach here without any assertion errors


def _load_xml_file(file_path: Path) -> str:
    """Load XML file with proper encoding detection."""
    encodings = ['windows-1250', 'utf-8', 'iso-8859-1']
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    
    # Last resort: read as binary and decode with error handling
    with open(file_path, 'rb') as f:
        raw_content = f.read()
        return raw_content.decode('utf-8', errors='ignore')


if __name__ == "__main__":
    # Run tests directly
    try:
        print("Running entity values test...")
        entities = test_entity_values_from_sample_files()
        
        print("\nRunning coordinator processing test...")
        processed = test_coordinator_value_processing_with_sample_files()
        
        print(f"\n🎉 All tests passed!")
        print(f"Found {len(entities)} entities with values")
        print(f"Processed {len(processed['sensors'])} sensors")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
