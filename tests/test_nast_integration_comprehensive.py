#!/usr/bin/env python3
"""
Comprehensive NAST Integration Tests

This test suite validates the complete NAST integration flow from
XML parsing through entity creation to Home Assistant integration.
"""

import pytest
import sys
from pathlib import Path
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import components for testing
try:
    from custom_components.xcc.xcc_client import parse_xml_entities
    from custom_components.xcc.const import PLATFORMS_TO_SETUP
except ImportError:
    pytest.skip("XCC components not available", allow_module_level=True)


class TestNASTIntegrationFlow:
    """Test the complete NAST integration flow."""
    
    @pytest.fixture
    def nast_sample_data(self):
        """Load NAST sample data."""
        sample_file = project_root / "tests" / "sample_data" / "nast.xml"
        if not sample_file.exists():
            pytest.skip("NAST sample data not available")
        
        with open(sample_file, 'r', encoding='utf-8') as f:
            return f.read()
    
    @pytest.fixture
    def mock_coordinator(self):
        """Create a mock coordinator for testing."""
        coordinator = MagicMock()
        coordinator.data = {}
        coordinator.async_request_refresh = AsyncMock()
        return coordinator
    
    def test_nast_page_discovery_integration(self):
        """Test NAST page discovery in integration constants."""
        # Check that NAST pages can be discovered dynamically
        const_file = project_root / "custom_components" / "xcc" / "const.py"
        
        with open(const_file, 'r', encoding='utf-8') as f:
            const_content = f.read()
        
        # NAST should not be in static constants (dynamic discovery)
        assert '"nast.xml"' not in const_content, "NAST should not be in static descriptor constants"
        assert '"NAST.XML"' not in const_content, "NAST should not be in static data constants"
        
        # Should have dynamic discovery comments
        assert "dynamically" in const_content, "Should mention dynamic discovery"
    
    def test_nast_coordinator_integration(self, nast_sample_data):
        """Test NAST integration with coordinator."""
        # Parse NAST entities
        entities = parse_xml_entities(nast_sample_data, "nast.xml")
        
        # Simulate coordinator data structure
        coordinator_data = {}
        for entity in entities:
            coordinator_data[entity["entity_id"]] = {
                "state": entity["state"],
                "attributes": entity["attributes"]
            }
        
        # Validate coordinator data structure
        assert len(coordinator_data) >= 130, "Coordinator should have many NAST entities"
        
        # Check specific entity types in coordinator
        number_entities = [k for k, v in coordinator_data.items() if v["attributes"].get("entity_type") == "number"]
        select_entities = [k for k, v in coordinator_data.items() if v["attributes"].get("entity_type") == "select"]
        
        # Should have substantial entities of each type
        assert len([k for k in coordinator_data.keys() if "offset" in k]) >= 15, "Should have offset entities"
        assert len([k for k in coordinator_data.keys() if "tcodstaveni" in k]) >= 5, "Should have heat pump controls"
    
    def test_nast_platform_integration(self):
        """Test NAST platform integration."""
        # Check that all required platforms are configured
        platforms = [p.value for p in PLATFORMS_TO_SETUP]
        
        required_for_nast = ["number", "select", "button", "text"]
        for platform in required_for_nast:
            assert platform in platforms, f"Platform {platform} required for NAST not configured"
    
    def test_nast_entity_creation_simulation(self, nast_sample_data, mock_coordinator):
        """Test simulated NAST entity creation."""
        entities = parse_xml_entities(nast_sample_data, "nast.xml")
        
        # Simulate entity creation for each platform
        created_entities = {
            "number": [],
            "select": [],
            "button": [],
            "text": []
        }
        
        for entity in entities:
            entity_type = entity["entity_type"]
            if entity_type in created_entities:
                created_entities[entity_type].append({
                    "entity_id": entity["entity_id"],
                    "state": entity["state"],
                    "attributes": entity["attributes"]
                })
        
        # Validate entity creation
        assert len(created_entities["number"]) >= 90, f"Should create many number entities: {len(created_entities['number'])}"
        assert len(created_entities["select"]) >= 25, f"Should create many select entities: {len(created_entities['select'])}"
        assert len(created_entities["button"]) >= 1, f"Should create button entities: {len(created_entities['button'])}"
        assert len(created_entities["text"]) >= 2, f"Should create text entities: {len(created_entities['text'])}"
        
        # Test entity attributes
        for entity_type, entity_list in created_entities.items():
            for entity in entity_list[:3]:  # Test first 3 of each type
                assert "entity_id" in entity, f"{entity_type} entity missing entity_id"
                assert "attributes" in entity, f"{entity_type} entity missing attributes"
                assert entity["attributes"]["source_page"] == "nast.xml", f"{entity_type} entity wrong source page"
    
    def test_nast_error_handling_integration(self):
        """Test NAST error handling in integration."""
        # Test with invalid XML
        invalid_xml = "<?xml version='1.0'?><invalid>test</invalid>"
        entities = parse_xml_entities(invalid_xml, "nast.xml")
        
        # Should handle gracefully
        assert isinstance(entities, list), "Should return list for invalid XML"
        assert len(entities) == 0, "Should return empty list for invalid XML"
    
    def test_nast_visibility_handling(self, nast_sample_data):
        """Test NAST visibility condition handling."""
        entities = parse_xml_entities(nast_sample_data, "nast.xml")
        
        # NAST entities should be created regardless of visibility
        # (integration loads all entities, ignoring visibility conditions)
        visible_entities = [e for e in entities if "visib" not in str(e)]
        all_entities = entities
        
        # Should have many entities (visibility ignored)
        assert len(all_entities) >= 130, "Should create entities regardless of visibility"
        
        # Check that entities with visibility conditions are included
        mzo_entities = [e for e in entities if "mzo_zona" in e["entity_id"]]
        assert len(mzo_entities) >= 16, "Should include MZO entities despite visibility conditions"
    
    def test_nast_device_assignment_integration(self, nast_sample_data):
        """Test NAST device assignment integration."""
        entities = parse_xml_entities(nast_sample_data, "nast.xml")
        
        # All NAST entities should be assigned to appropriate devices
        for entity in entities[:10]:  # Test first 10 entities
            attrs = entity["attributes"]
            
            # Should have source page for device assignment
            assert "source_page" in attrs, f"Entity {entity['entity_id']} missing source_page"
            assert attrs["source_page"] == "nast.xml", f"Entity {entity['entity_id']} wrong source page"
            
            # Should have field name for device grouping
            assert "field_name" in attrs, f"Entity {entity['entity_id']} missing field_name"
    
    def test_nast_translation_integration(self, nast_sample_data):
        """Test NAST translation integration."""
        entities = parse_xml_entities(nast_sample_data, "nast.xml")
        
        # Check that entities have reasonable friendly names
        for entity in entities[:20]:  # Test first 20 entities
            attrs = entity["attributes"]
            friendly_name = attrs.get("friendly_name", "")
            
            assert len(friendly_name) > 0, f"Entity {entity['entity_id']} has empty friendly name"
            assert len(friendly_name) < 100, f"Entity {entity['entity_id']} has overly long friendly name"
            
            # Should not have raw technical names
            assert not friendly_name.isupper(), f"Entity {entity['entity_id']} has raw technical name: {friendly_name}"
    
    def test_nast_state_management_integration(self, nast_sample_data):
        """Test NAST state management integration."""
        entities = parse_xml_entities(nast_sample_data, "nast.xml")
        
        # Test state handling for different entity types
        state_validation = {
            "number": lambda s: s is None or isinstance(s, (int, float)),
            "select": lambda s: s is None or isinstance(s, str),
            "button": lambda s: s is None or isinstance(s, str),
            "text": lambda s: s is None or isinstance(s, str),
        }
        
        for entity in entities:
            entity_type = entity["entity_type"]
            state = entity["state"]
            
            if entity_type in state_validation:
                validator = state_validation[entity_type]
                assert validator(state), f"Invalid state for {entity_type} entity {entity['entity_id']}: {state}"
    
    def test_nast_performance_integration(self, nast_sample_data):
        """Test NAST performance in integration context."""
        import time
        
        # Measure parsing performance
        start_time = time.time()
        entities = parse_xml_entities(nast_sample_data, "nast.xml")
        parsing_time = time.time() - start_time
        
        # Should parse quickly
        assert parsing_time < 0.5, f"NAST parsing too slow: {parsing_time:.3f}s"
        assert len(entities) >= 130, "Should parse substantial entities quickly"
        
        # Measure entity processing performance
        start_time = time.time()
        processed_entities = []
        for entity in entities:
            # Simulate entity processing
            processed_entity = {
                "id": entity["entity_id"],
                "type": entity["entity_type"],
                "state": entity["state"],
                "attrs": len(entity["attributes"])
            }
            processed_entities.append(processed_entity)
        processing_time = time.time() - start_time
        
        assert processing_time < 0.1, f"Entity processing too slow: {processing_time:.3f}s"


class TestNASTRealWorldScenarios:
    """Test NAST integration in real-world scenarios."""
    
    @pytest.fixture
    def nast_entities(self):
        """Get parsed NAST entities."""
        sample_file = project_root / "tests" / "sample_data" / "nast.xml"
        if not sample_file.exists():
            pytest.skip("NAST sample data not available")
        
        with open(sample_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return parse_xml_entities(content, "nast.xml")
    
    def test_sensor_calibration_scenario(self, nast_entities):
        """Test sensor calibration scenario."""
        # Find sensor correction entities
        sensor_corrections = [e for e in nast_entities if e["entity_id"].endswith("_i")]
        
        assert len(sensor_corrections) >= 12, "Should have sensor corrections for calibration"
        
        # Test sensor correction attributes
        for sensor in sensor_corrections[:5]:
            attrs = sensor["attributes"]
            
            # Should have min/max for calibration range
            if "min_value" in attrs:
                assert attrs["min_value"] <= 0, "Sensor correction should allow negative values"
            
            # Should be number entities
            assert sensor["entity_type"] == "number", "Sensor corrections should be number entities"
    
    def test_power_management_scenario(self, nast_entities):
        """Test power management scenario."""
        # Find power restriction entities
        power_entities = [e for e in nast_entities if "omezen" in e["entity_id"] or "ovp" in e["entity_id"]]
        
        assert len(power_entities) >= 10, "Should have power management entities"
        
        # Test power management features
        global_power = [e for e in power_entities if "omezenivykonuglobalni" in e["entity_id"]]
        assert len(global_power) >= 1, "Should have global power restriction"
        
        # Check for percentage units
        percentage_entities = [e for e in power_entities if e["attributes"].get("unit_of_measurement") == "%"]
        assert len(percentage_entities) >= 5, "Should have percentage-based power controls"
    
    def test_multi_zone_control_scenario(self, nast_entities):
        """Test multi-zone control scenario."""
        # Find multi-zone offset entities
        mzo_entities = [e for e in nast_entities if "mzo_zona" in e["entity_id"] and "offset" in e["entity_id"]]
        
        assert len(mzo_entities) >= 16, "Should have multi-zone offset controls"
        
        # Test zone numbering
        zone_numbers = set()
        for entity in mzo_entities:
            import re
            match = re.search(r'mzo_zona(\d+)_offset', entity["entity_id"])
            if match:
                zone_numbers.add(int(match.group(1)))
        
        assert 0 in zone_numbers, "Should have zone 0"
        assert len(zone_numbers) >= 16, "Should have at least 16 zones"
        assert max(zone_numbers) >= 15, "Should go up to zone 15"
    
    def test_heat_pump_management_scenario(self, nast_entities):
        """Test heat pump management scenario."""
        # Find heat pump control entities
        hp_controls = [e for e in nast_entities if "tcodstaveni" in e["entity_id"]]
        
        assert len(hp_controls) >= 10, "Should have heat pump controls"
        
        # Test heat pump controls
        for hp_control in hp_controls[:5]:
            assert hp_control["entity_type"] == "select", "Heat pump controls should be select entities"
            
            attrs = hp_control["attributes"]
            if "options" in attrs:
                options = attrs["options"]
                assert len(options) >= 2, "Heat pump control should have on/off options"
    
    def test_system_administration_scenario(self, nast_entities):
        """Test system administration scenario."""
        # Find system backup entities
        backup_entities = [e for e in nast_entities if "flash" in e["entity_id"]]
        
        assert len(backup_entities) >= 4, "Should have system backup entities"
        
        # Test backup functionality
        readwrite_buttons = [e for e in backup_entities if "readwrite" in e["entity_id"]]
        assert len(readwrite_buttons) >= 1, "Should have read/write buttons"
        
        config_names = [e for e in backup_entities if "name" in e["entity_id"]]
        assert len(config_names) >= 3, "Should have configuration name fields"
        
        # Test entity types
        for entity in backup_entities:
            assert entity["entity_type"] in ["button", "text"], "Backup entities should be buttons or text"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
