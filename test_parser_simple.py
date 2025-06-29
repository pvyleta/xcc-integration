#!/usr/bin/env python3
"""
Simple test runner for XCC XML parser using real sample data.
No external dependencies required.
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from custom_components.xcc.xcc_client import parse_xml_entities


def load_sample_file(filename):
    """Load a sample XML file with proper encoding detection."""
    file_path = project_root / "sample_data" / filename
    
    if not file_path.exists():
        raise FileNotFoundError(f"Sample file not found: {file_path}")
    
    # Try different encodings like the real parser
    encodings = ['windows-1250', 'utf-8', 'iso-8859-1']
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    
    raise ValueError(f"Could not decode {filename} with any encoding")


def test_file_parsing(filename, expected_min_entities=50):
    """Test parsing of a specific XML file."""
    print(f"\n📄 Testing: {filename}")
    print("-" * 40)
    
    try:
        # Load and parse the file
        xml_content = load_sample_file(filename)
        entities = parse_xml_entities(xml_content, filename)
        
        print(f"📊 File size: {len(xml_content)} bytes")
        print(f"📈 Entities found: {len(entities)}")
        
        # Basic validation
        if len(entities) < expected_min_entities:
            print(f"⚠️  Warning: Expected at least {expected_min_entities} entities, got {len(entities)}")
        
        if len(entities) == 0:
            print("❌ No entities found - this indicates a parsing problem")
            return False
        
        # Validate entity structure
        sample_entity = entities[0]
        required_keys = ["entity_id", "entity_type", "state", "attributes"]
        
        for key in required_keys:
            if key not in sample_entity:
                print(f"❌ Missing required key '{key}' in entity structure")
                return False
        
        # Show sample entities
        print("📝 Sample entities:")
        for i, entity in enumerate(entities[:3]):
            entity_id = entity["entity_id"]
            entity_type = entity["entity_type"]
            state = entity["state"]
            print(f"  {i+1}. {entity_id} ({entity_type}): {state}")
        
        # Count entity types
        type_counts = {}
        for entity in entities:
            entity_type = entity["entity_type"]
            type_counts[entity_type] = type_counts.get(entity_type, 0) + 1
        
        print(f"📊 Entity types: {type_counts}")
        
        print(f"✅ {filename} parsed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error parsing {filename}: {e}")
        return False


def test_specific_entities():
    """Test for specific known entities."""
    print(f"\n🔍 Testing Specific Known Entities")
    print("-" * 40)
    
    try:
        xml_content = load_sample_file("STAVJED1.XML")
        entities = parse_xml_entities(xml_content, "STAVJED1.XML")
        
        # Create lookup by entity_id
        entity_lookup = {e["entity_id"]: e for e in entities}
        
        # Test outdoor temperature sensor
        if "xcc_svenku" in entity_lookup:
            svenku = entity_lookup["xcc_svenku"]
            print(f"✅ Found outdoor temperature: {svenku['state']}°C")
            
            # Validate temperature sensor
            if svenku["entity_type"] != "sensor":
                print(f"⚠️  Expected sensor, got {svenku['entity_type']}")
            
            try:
                temp_value = float(svenku["state"])
                if -50 <= temp_value <= 50:
                    print(f"✅ Temperature value {temp_value}°C is reasonable")
                else:
                    print(f"⚠️  Temperature value {temp_value}°C seems out of range")
            except ValueError:
                print(f"⚠️  Temperature value '{svenku['state']}' is not numeric")
        else:
            print("❌ Outdoor temperature sensor (xcc_svenku) not found")
        
        # Test device model
        if "xcc_snazev1" in entity_lookup:
            model = entity_lookup["xcc_snazev1"]
            print(f"✅ Found device model: {model['state']}")
        else:
            print("❌ Device model (xcc_snazev1) not found")
        
        # Test device location
        if "xcc_snazev2" in entity_lookup:
            location = entity_lookup["xcc_snazev2"]
            print(f"✅ Found device location: {location['state']}")
        else:
            print("❌ Device location (xcc_snazev2) not found")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing specific entities: {e}")
        return False


def test_entity_id_format():
    """Test entity ID format compliance."""
    print(f"\n🔤 Testing Entity ID Format")
    print("-" * 40)
    
    try:
        xml_content = load_sample_file("STAVJED1.XML")
        entities = parse_xml_entities(xml_content, "STAVJED1.XML")
        
        issues = []
        
        for entity in entities[:10]:  # Check first 10
            entity_id = entity["entity_id"]
            
            # Check prefix
            if not entity_id.startswith("xcc_"):
                issues.append(f"Missing 'xcc_' prefix: {entity_id}")
            
            # Check lowercase
            if not entity_id.islower():
                issues.append(f"Not lowercase: {entity_id}")
            
            # Check for invalid characters
            invalid_chars = [" ", "-", ".", "/", "\\", "(", ")"]
            for char in invalid_chars:
                if char in entity_id:
                    issues.append(f"Contains invalid char '{char}': {entity_id}")
        
        if issues:
            print("⚠️  Entity ID format issues found:")
            for issue in issues[:5]:  # Show first 5
                print(f"   - {issue}")
        else:
            print("✅ All entity IDs follow correct format")
        
        return len(issues) == 0
        
    except Exception as e:
        print(f"❌ Error testing entity ID format: {e}")
        return False


def main():
    """Run all parser tests."""
    print("🧪 XCC XML Parser Test Suite")
    print("=" * 50)
    
    # Test individual files
    test_files = [
        ("STAVJED1.XML", 100),  # Main heat pump data
        ("OKRUH10.XML", 80),    # Heating circuit
        ("TUV11.XML", 80),      # Hot water
        ("BIV1.XML", 80),       # Auxiliary source
        ("FVE4.XML", 70),       # Photovoltaic
        ("SPOT1.XML", 50),      # Spot prices
    ]
    
    passed_tests = 0
    total_tests = 0
    total_entities = 0
    
    # Test each file
    for filename, min_entities in test_files:
        total_tests += 1
        if test_file_parsing(filename, min_entities):
            passed_tests += 1
            
            # Count entities for total
            try:
                xml_content = load_sample_file(filename)
                entities = parse_xml_entities(xml_content, filename)
                total_entities += len(entities)
            except:
                pass
    
    # Test specific functionality
    print(f"\n🔧 Testing Parser Functionality")
    print("=" * 40)
    
    functionality_tests = [
        ("Specific entities", test_specific_entities),
        ("Entity ID format", test_entity_id_format),
    ]
    
    for test_name, test_func in functionality_tests:
        total_tests += 1
        print(f"\n📋 {test_name}:")
        if test_func():
            passed_tests += 1
    
    # Summary
    print(f"\n📊 Test Summary")
    print("=" * 30)
    print(f"Tests passed: {passed_tests}/{total_tests}")
    print(f"Total entities found: {total_entities}")
    
    if total_entities >= 600:
        print(f"✅ Entity count matches expected (~601)")
    else:
        print(f"⚠️  Entity count lower than expected (601)")
    
    if passed_tests == total_tests:
        print(f"\n🎉 All tests passed! Parser is working correctly.")
        return True
    else:
        print(f"\n⚠️  {total_tests - passed_tests} test(s) failed. Check parser implementation.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
