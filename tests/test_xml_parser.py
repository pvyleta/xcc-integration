#!/usr/bin/env python3
"""
Comprehensive tests for XCC XML parser using real sample data.

Tests ensure correct parsing of all XCC XML formats and entity creation.
"""

import pytest
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from custom_components.xcc.xcc_client import parse_xml_entities


class TestXCCXMLParser:
    """Test XCC XML parser with real sample data."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.sample_data_dir = project_root / "sample_data"
        assert self.sample_data_dir.exists(), "sample_data directory not found"
    
    def load_sample_file(self, filename):
        """Load a sample XML file with proper encoding detection."""
        file_path = self.sample_data_dir / filename
        
        # Try different encodings like the real parser
        encodings = ['windows-1250', 'utf-8', 'iso-8859-1']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        
        raise ValueError(f"Could not decode {filename} with any encoding")
    
    def test_stavjed1_xml_parsing(self):
        """Test parsing of STAVJED1.XML (main heat pump data)."""
        xml_content = self.load_sample_file("STAVJED1.XML")
        entities = parse_xml_entities(xml_content, "STAVJED1.XML")
        
        # Should find significant number of entities
        assert len(entities) > 100, f"Expected >100 entities, got {len(entities)}"
        
        # Check for key entities we know should exist
        entity_ids = [e["entity_id"] for e in entities]
        
        # Outdoor temperature sensor
        assert "xcc_svenku" in entity_ids, "Missing outdoor temperature sensor"
        
        # Device information
        assert "xcc_snazev1" in entity_ids, "Missing device model"
        assert "xcc_snazev2" in entity_ids, "Missing device location"
        
        # Find and validate outdoor temperature entity
        svenku_entity = next(e for e in entities if e["entity_id"] == "xcc_svenku")
        assert svenku_entity["entity_type"] == "sensor"
        assert svenku_entity["attributes"]["device_class"] == "temperature"
        assert svenku_entity["attributes"]["unit_of_measurement"] == "°C"
        assert float(svenku_entity["state"]) > -50  # Reasonable temperature range
        assert float(svenku_entity["state"]) < 50
        
        # Validate entity structure
        for entity in entities[:5]:  # Check first 5 entities
            assert "entity_id" in entity
            assert "entity_type" in entity
            assert "state" in entity
            assert "attributes" in entity
            assert isinstance(entity["attributes"], dict)
    
    def test_okruh10_xml_parsing(self):
        """Test parsing of OKRUH10.XML (heating circuit data)."""
        xml_content = self.load_sample_file("OKRUH10.XML")
        entities = parse_xml_entities(xml_content, "OKRUH10.XML")
        
        # Should find entities
        assert len(entities) > 50, f"Expected >50 entities, got {len(entities)}"
        
        # Validate entity structure
        for entity in entities[:3]:
            assert "entity_id" in entity
            assert "entity_type" in entity
            assert "state" in entity
            assert "attributes" in entity
            assert entity["attributes"]["source_page"] == "OKRUH10.XML"
    
    def test_tuv11_xml_parsing(self):
        """Test parsing of TUV11.XML (hot water data)."""
        xml_content = self.load_sample_file("TUV11.XML")
        entities = parse_xml_entities(xml_content, "TUV11.XML")
        
        # Should find entities
        assert len(entities) > 50, f"Expected >50 entities, got {len(entities)}"
        
        # Validate entity structure
        for entity in entities[:3]:
            assert "entity_id" in entity
            assert "entity_type" in entity
            assert "state" in entity
            assert "attributes" in entity
    
    def test_biv1_xml_parsing(self):
        """Test parsing of BIV1.XML (auxiliary source data)."""
        xml_content = self.load_sample_file("BIV1.XML")
        entities = parse_xml_entities(xml_content, "BIV1.XML")
        
        # Should find entities
        assert len(entities) > 50, f"Expected >50 entities, got {len(entities)}"
    
    def test_fve4_xml_parsing(self):
        """Test parsing of FVE4.XML (photovoltaic data)."""
        xml_content = self.load_sample_file("FVE4.XML")
        entities = parse_xml_entities(xml_content, "FVE4.XML")
        
        # Should find entities
        assert len(entities) > 50, f"Expected >50 entities, got {len(entities)}"
    
    def test_spot1_xml_parsing(self):
        """Test parsing of SPOT1.XML (spot price data)."""
        xml_content = self.load_sample_file("SPOT1.XML")
        entities = parse_xml_entities(xml_content, "SPOT1.XML")
        
        # Should find entities
        assert len(entities) > 30, f"Expected >30 entities, got {len(entities)}"
    
    def test_entity_types_detection(self):
        """Test that different entity types are correctly detected."""
        xml_content = self.load_sample_file("STAVJED1.XML")
        entities = parse_xml_entities(xml_content, "STAVJED1.XML")
        
        # Group entities by type
        entity_types = {}
        for entity in entities:
            entity_type = entity["entity_type"]
            entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
        
        # Should have sensors (most common)
        assert "sensor" in entity_types
        assert entity_types["sensor"] > 50
        
        # Should have binary sensors for boolean values
        assert "binary_sensor" in entity_types
        assert entity_types["binary_sensor"] > 0
        
        print(f"Entity types found: {entity_types}")
    
    def test_temperature_sensors(self):
        """Test that temperature sensors are properly identified."""
        xml_content = self.load_sample_file("STAVJED1.XML")
        entities = parse_xml_entities(xml_content, "STAVJED1.XML")
        
        # Find temperature sensors
        temp_sensors = [
            e for e in entities 
            if e["attributes"].get("device_class") == "temperature"
        ]
        
        assert len(temp_sensors) > 0, "No temperature sensors found"
        
        # Validate temperature sensors
        for sensor in temp_sensors:
            assert sensor["entity_type"] == "sensor"
            assert sensor["attributes"]["unit_of_measurement"] == "°C"
            # Temperature values should be numeric
            try:
                temp_value = float(sensor["state"])
                assert -50 <= temp_value <= 100, f"Temperature {temp_value} out of range"
            except ValueError:
                pytest.fail(f"Temperature sensor has non-numeric value: {sensor['state']}")
    
    def test_boolean_sensors(self):
        """Test that boolean sensors are properly identified."""
        xml_content = self.load_sample_file("STAVJED1.XML")
        entities = parse_xml_entities(xml_content, "STAVJED1.XML")
        
        # Find binary sensors
        binary_sensors = [
            e for e in entities 
            if e["entity_type"] == "binary_sensor"
        ]
        
        assert len(binary_sensors) > 0, "No binary sensors found"
        
        # Validate binary sensors
        for sensor in binary_sensors:
            assert sensor["state"] in ["0", "1"], f"Binary sensor has invalid state: {sensor['state']}"
    
    def test_entity_id_generation(self):
        """Test that entity IDs are properly generated."""
        xml_content = self.load_sample_file("STAVJED1.XML")
        entities = parse_xml_entities(xml_content, "STAVJED1.XML")
        
        # Check entity ID format
        for entity in entities:
            entity_id = entity["entity_id"]
            
            # Should start with xcc_
            assert entity_id.startswith("xcc_"), f"Entity ID doesn't start with xcc_: {entity_id}"
            
            # Should be lowercase
            assert entity_id.islower(), f"Entity ID not lowercase: {entity_id}"
            
            # Should not contain invalid characters
            invalid_chars = [" ", "-", ".", "/", "\\"]
            for char in invalid_chars:
                assert char not in entity_id, f"Entity ID contains invalid char '{char}': {entity_id}"
    
    def test_all_sample_files_total_count(self):
        """Test total entity count across all sample files."""
        sample_files = [
            "STAVJED1.XML",
            "OKRUH10.XML", 
            "TUV11.XML",
            "BIV1.XML",
            "FVE4.XML",
            "SPOT1.XML"
        ]
        
        total_entities = 0
        file_counts = {}
        
        for filename in sample_files:
            xml_content = self.load_sample_file(filename)
            entities = parse_xml_entities(xml_content, filename)
            count = len(entities)
            total_entities += count
            file_counts[filename] = count
            
            print(f"{filename}: {count} entities")
        
        print(f"Total entities across all files: {total_entities}")
        
        # Should match the expected total from logs (601 entities)
        assert total_entities >= 600, f"Expected >=600 total entities, got {total_entities}"
        assert total_entities <= 650, f"Expected <=650 total entities, got {total_entities}"
        
        # Each file should contribute entities
        for filename, count in file_counts.items():
            assert count > 0, f"No entities found in {filename}"


if __name__ == "__main__":
    # Run tests directly
    test_instance = TestXCCXMLParser()
    test_instance.setup_method()
    
    print("🧪 Running XCC XML Parser Tests")
    print("=" * 50)
    
    # Run individual tests
    tests = [
        ("STAVJED1.XML parsing", test_instance.test_stavjed1_xml_parsing),
        ("OKRUH10.XML parsing", test_instance.test_okruh10_xml_parsing),
        ("TUV11.XML parsing", test_instance.test_tuv11_xml_parsing),
        ("BIV1.XML parsing", test_instance.test_biv1_xml_parsing),
        ("FVE4.XML parsing", test_instance.test_fve4_xml_parsing),
        ("SPOT1.XML parsing", test_instance.test_spot1_xml_parsing),
        ("Entity types detection", test_instance.test_entity_types_detection),
        ("Temperature sensors", test_instance.test_temperature_sensors),
        ("Boolean sensors", test_instance.test_boolean_sensors),
        ("Entity ID generation", test_instance.test_entity_id_generation),
        ("Total entity count", test_instance.test_all_sample_files_total_count),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            print(f"\n📋 Testing: {test_name}")
            test_func()
            print(f"✅ PASSED: {test_name}")
            passed += 1
        except Exception as e:
            print(f"❌ FAILED: {test_name}")
            print(f"   Error: {e}")
            failed += 1
    
    print(f"\n📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed - check the parser implementation")
