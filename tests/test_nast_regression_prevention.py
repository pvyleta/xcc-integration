#!/usr/bin/env python3
"""
NAST Regression Prevention Tests

This test suite ensures that NAST parsing functionality doesn't regress
in future updates. It validates parsing logic, entity creation, and
attribute handling for NAST-style descriptor pages.
"""

import pytest
import sys
from pathlib import Path
import re
from unittest.mock import MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import XCC client for testing
try:
    from custom_components.xcc.xcc_client import parse_xml_entities
except ImportError:
    pytest.skip("XCC client not available", allow_module_level=True)


class TestNASTParsingRegression:
    """Test class for NAST parsing regression prevention."""
    
    @pytest.fixture
    def nast_sample_content(self):
        """Load NAST sample content."""
        sample_file = project_root / "tests" / "sample_data" / "nast.xml"
        if not sample_file.exists():
            pytest.skip("NAST sample data not available")
        
        with open(sample_file, 'r', encoding='utf-8') as f:
            return f.read()
    
    def test_nast_parsing_logic_exists(self):
        """Test that NAST parsing logic exists in XCC client."""
        xcc_client_file = project_root / "custom_components" / "xcc" / "xcc_client.py"
        
        with open(xcc_client_file, 'r', encoding='utf-8') as f:
            client_content = f.read()
        
        # Check for NAST-specific parsing logic
        nast_indicators = [
            "nast_elements = root.xpath",
            "Processing NAST-style elements",
            'elem.tag == "number"',
            'elem.tag == "choice"',
            'elem.tag == "button"',
            'elem.tag == "text"',
            "NAST processing complete",
        ]
        
        for indicator in nast_indicators:
            assert indicator in client_content, f"NAST parsing logic missing: {indicator}"
    
    def test_nast_element_detection(self, nast_sample_content):
        """Test that NAST elements are properly detected."""
        # Count elements in raw XML
        number_count = len(re.findall(r'<number[^>]*prop="[^"]*"', nast_sample_content))
        choice_count = len(re.findall(r'<choice[^>]*prop="[^"]*"', nast_sample_content))
        button_count = len(re.findall(r'<button[^>]*prop="[^"]*"', nast_sample_content))
        text_count = len(re.findall(r'<text[^>]*prop="[^"]*"', nast_sample_content))
        
        # Verify expected counts (regression baseline)
        assert number_count >= 100, f"Number elements regression: expected >=100, got {number_count}"
        assert choice_count >= 30, f"Choice elements regression: expected >=30, got {choice_count}"
        assert button_count >= 8, f"Button elements regression: expected >=8, got {button_count}"
        assert text_count >= 3, f"Text elements regression: expected >=3, got {text_count}"
    
    def test_nast_entity_creation_regression(self, nast_sample_content):
        """Test that NAST entity creation doesn't regress."""
        entities = parse_xml_entities(nast_sample_content, "nast.xml")
        
        # Baseline entity counts (from v1.12.4)
        baseline_counts = {
            "number": 100,
            "select": 32,
            "button": 2,
            "text": 3,
        }
        
        actual_counts = {}
        for entity in entities:
            entity_type = entity["entity_type"]
            actual_counts[entity_type] = actual_counts.get(entity_type, 0) + 1
        
        # Check for regressions
        for entity_type, baseline in baseline_counts.items():
            actual = actual_counts.get(entity_type, 0)
            # Allow some flexibility but catch major regressions
            min_acceptable = int(baseline * 0.9)  # 10% tolerance
            assert actual >= min_acceptable, f"Major regression in {entity_type}: expected >={min_acceptable}, got {actual}"
    
    def test_nast_critical_entities_regression(self, nast_sample_content):
        """Test that critical NAST entities are always created."""
        entities = parse_xml_entities(nast_sample_content, "nast.xml")
        entity_ids = {e["entity_id"] for e in entities}
        
        # Critical entities that must never regress
        critical_entities = {
            # Sensor corrections
            "xcc_b0_i": "Sensor B0 temperature correction",
            "xcc_b4_i": "Sensor B4 temperature correction",
            
            # Multi-zone offsets
            "xcc_mzo_zona0_offset": "Multi-zone offset 0",
            "xcc_mzo_zona1_offset": "Multi-zone offset 1",
            
            # Power restrictions
            "xcc_omezenivykonuglobalni": "Global power restriction",
            "xcc_ovppovoleni": "Time-based power restriction enable",
            
            # Heat pump controls
            "xcc_tcodstaveni0": "Heat pump I control",
            "xcc_tcodstaveni1": "Heat pump II control",
            
            # System backup
            "xcc_flash_readwrite": "System backup button",
            "xcc_flash_header0_name": "Configuration slot 0 name",
        }
        
        missing_entities = []
        for entity_id, description in critical_entities.items():
            if entity_id not in entity_ids:
                missing_entities.append(f"{entity_id} ({description})")
        
        assert not missing_entities, f"Critical entities missing: {', '.join(missing_entities)}"
    
    def test_nast_attribute_quality_regression(self, nast_sample_content):
        """Test that entity attribute quality doesn't regress."""
        entities = parse_xml_entities(nast_sample_content, "nast.xml")
        
        # Quality metrics that shouldn't regress
        entities_with_min_max = 0
        entities_with_units = 0
        entities_with_options = 0
        entities_with_friendly_names = 0
        
        for entity in entities:
            attrs = entity["attributes"]
            
            # Count quality indicators
            if "min_value" in attrs or "max_value" in attrs:
                entities_with_min_max += 1
            if "unit_of_measurement" in attrs:
                entities_with_units += 1
            if "options" in attrs:
                entities_with_options += 1
            if "friendly_name" in attrs and len(attrs["friendly_name"]) > 0:
                entities_with_friendly_names += 1
        
        # Quality regression checks
        assert entities_with_min_max >= 50, f"Min/max attributes regression: {entities_with_min_max}"
        assert entities_with_units >= 20, f"Unit attributes regression: {entities_with_units}"
        assert entities_with_options >= 25, f"Options attributes regression: {entities_with_options}"
        assert entities_with_friendly_names >= 130, f"Friendly names regression: {entities_with_friendly_names}"
    
    def test_nast_parsing_performance_regression(self, nast_sample_content):
        """Test that NAST parsing performance doesn't regress."""
        import time
        
        # Measure parsing time
        start_time = time.time()
        entities = parse_xml_entities(nast_sample_content, "nast.xml")
        end_time = time.time()
        
        parsing_time = end_time - start_time
        
        # Performance regression check (should parse in under 1 second)
        assert parsing_time < 1.0, f"Performance regression: parsing took {parsing_time:.3f}s"
        assert len(entities) > 0, "Parsing should produce entities"
    
    def test_nast_error_handling_regression(self):
        """Test that NAST error handling doesn't regress."""
        # Test with malformed XML
        malformed_xml = '<?xml version="1.0"?><page><number prop="test"'  # Missing closing
        
        # Should not crash, should return empty list
        entities = parse_xml_entities(malformed_xml, "test.xml")
        assert isinstance(entities, list), "Should return list even for malformed XML"
        
        # Test with empty XML
        empty_xml = ""
        entities = parse_xml_entities(empty_xml, "empty.xml")
        assert isinstance(entities, list), "Should return list for empty XML"
        assert len(entities) == 0, "Should return empty list for empty XML"
    
    def test_nast_entity_id_format_regression(self, nast_sample_content):
        """Test that entity ID format doesn't regress."""
        entities = parse_xml_entities(nast_sample_content, "nast.xml")
        
        for entity in entities:
            entity_id = entity["entity_id"]
            
            # Entity ID format requirements
            assert entity_id.startswith("xcc_"), f"Entity ID should start with xcc_: {entity_id}"
            assert "_" in entity_id, f"Entity ID should contain underscore: {entity_id}"
            assert entity_id.islower() or "_" in entity_id, f"Entity ID should be lowercase or contain underscores: {entity_id}"
            assert len(entity_id) > 4, f"Entity ID should be substantial: {entity_id}"
            assert len(entity_id) < 100, f"Entity ID should not be too long: {entity_id}"
            
            # Should not contain invalid characters
            invalid_chars = [" ", ".", "-", "(", ")", "[", "]"]
            for char in invalid_chars:
                if char == "-":
                    # Hyphens should be converted to underscores
                    assert char not in entity_id, f"Entity ID should not contain hyphens: {entity_id}"
                else:
                    assert char not in entity_id, f"Entity ID should not contain '{char}': {entity_id}"
    
    def test_nast_state_handling_regression(self, nast_sample_content):
        """Test that entity state handling doesn't regress."""
        entities = parse_xml_entities(nast_sample_content, "nast.xml")
        
        state_counts = {}
        for entity in entities:
            state = entity["state"]
            entity_type = entity["entity_type"]
            
            # Track state types
            state_type = type(state).__name__
            key = f"{entity_type}_{state_type}"
            state_counts[key] = state_counts.get(key, 0) + 1
            
            # State validation by entity type
            if entity_type == "number":
                assert isinstance(state, (int, float, type(None))), f"Number entity should have numeric or None state: {entity['entity_id']}"
            elif entity_type == "select":
                assert isinstance(state, (str, type(None))), f"Select entity should have string or None state: {entity['entity_id']}"
            elif entity_type == "button":
                assert isinstance(state, (str, type(None))), f"Button entity should have string or None state: {entity['entity_id']}"
            elif entity_type == "text":
                assert isinstance(state, (str, type(None))), f"Text entity should have string or None state: {entity['entity_id']}"
        
        # Should have reasonable distribution of states
        assert len(state_counts) > 0, "Should have various state types"


class TestNASTSpecificFeatures:
    """Test NAST-specific features that shouldn't regress."""
    
    @pytest.fixture
    def nast_entities(self):
        """Get parsed NAST entities."""
        sample_file = project_root / "tests" / "sample_data" / "nast.xml"
        if not sample_file.exists():
            pytest.skip("NAST sample data not available")
        
        with open(sample_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return parse_xml_entities(content, "nast.xml")
    
    def test_sensor_correction_entities(self, nast_entities):
        """Test sensor correction entities don't regress."""
        sensor_corrections = [e for e in nast_entities if e["entity_id"].endswith("_i")]
        
        assert len(sensor_corrections) >= 12, f"Sensor corrections regression: {len(sensor_corrections)}"
        
        # Check specific sensor corrections
        expected_sensors = ["b0_i", "b4_i", "b8_i", "b9_i", "b10_i"]
        found_sensors = [e["entity_id"].split("_")[-1] for e in sensor_corrections]
        
        for sensor in expected_sensors:
            assert sensor in found_sensors, f"Missing sensor correction: {sensor}"
    
    def test_multi_zone_offset_entities(self, nast_entities):
        """Test multi-zone offset entities don't regress."""
        mzo_entities = [e for e in nast_entities if "mzo_zona" in e["entity_id"] and "offset" in e["entity_id"]]
        
        assert len(mzo_entities) >= 16, f"Multi-zone offset regression: {len(mzo_entities)}"
        
        # Check zone range
        zone_numbers = []
        for entity in mzo_entities:
            match = re.search(r'mzo_zona(\d+)_offset', entity["entity_id"])
            if match:
                zone_numbers.append(int(match.group(1)))
        
        assert min(zone_numbers) == 0, "Should start from zone 0"
        assert max(zone_numbers) >= 15, "Should go up to at least zone 15"
    
    def test_heat_pump_control_entities(self, nast_entities):
        """Test heat pump control entities don't regress."""
        hp_controls = [e for e in nast_entities if "tcodstaveni" in e["entity_id"]]
        
        assert len(hp_controls) >= 10, f"Heat pump controls regression: {len(hp_controls)}"
        
        # Check heat pump range
        hp_numbers = []
        for entity in hp_controls:
            match = re.search(r'tcodstaveni(\d+)', entity["entity_id"])
            if match:
                hp_numbers.append(int(match.group(1)))
        
        assert min(hp_numbers) == 0, "Should start from heat pump 0"
        assert max(hp_numbers) >= 9, "Should go up to at least heat pump 9"
    
    def test_power_restriction_entities(self, nast_entities):
        """Test power restriction entities don't regress."""
        power_entities = [e for e in nast_entities if "omezen" in e["entity_id"] or "ovp" in e["entity_id"]]
        
        assert len(power_entities) >= 10, f"Power restriction regression: {len(power_entities)}"
        
        # Check for specific power restriction types
        global_power = [e for e in power_entities if "omezenivykonuglobalni" in e["entity_id"]]
        assert len(global_power) >= 1, "Should have global power restriction"
        
        time_based = [e for e in power_entities if "ovp" in e["entity_id"]]
        assert len(time_based) >= 2, "Should have time-based power restrictions"
    
    def test_system_backup_entities(self, nast_entities):
        """Test system backup entities don't regress."""
        backup_entities = [e for e in nast_entities if "flash" in e["entity_id"]]
        
        assert len(backup_entities) >= 4, f"System backup regression: {len(backup_entities)}"
        
        # Check for specific backup functions
        readwrite_buttons = [e for e in backup_entities if "readwrite" in e["entity_id"]]
        assert len(readwrite_buttons) >= 1, "Should have read/write buttons"
        
        header_names = [e for e in backup_entities if "header" in e["entity_id"] and "name" in e["entity_id"]]
        assert len(header_names) >= 3, "Should have header name fields"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
