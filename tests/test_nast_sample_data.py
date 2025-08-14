#!/usr/bin/env python3
"""
Test NAST parsing using sample data to prevent regressions.

This test suite validates that NAST XML parsing works correctly
with the sample data files and prevents future regressions.
"""

import pytest
import sys
from pathlib import Path
import asyncio
from unittest.mock import AsyncMock, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import XCC client for testing
try:
    from custom_components.xcc.xcc_client import parse_xml_entities
except ImportError:
    pytest.skip("XCC client not available", allow_module_level=True)


@pytest.fixture
def sample_nast_descriptor():
    """Load sample NAST descriptor data."""
    sample_file = project_root / "tests" / "sample_data" / "nast.xml"
    if not sample_file.exists():
        pytest.skip("NAST sample data not available")
    
    with open(sample_file, 'r', encoding='utf-8') as f:
        return f.read()


@pytest.fixture
def sample_nast_data():
    """Load sample NAST data (same as descriptor for NAST)."""
    sample_file = project_root / "tests" / "sample_data" / "NAST.XML"
    if not sample_file.exists():
        pytest.skip("NAST sample data not available")
    
    with open(sample_file, 'r', encoding='utf-8') as f:
        return f.read()


def test_nast_sample_data_exists():
    """Test that NAST sample data files exist."""
    descriptor_file = project_root / "tests" / "sample_data" / "nast.xml"
    data_file = project_root / "tests" / "sample_data" / "NAST.XML"
    
    assert descriptor_file.exists(), "NAST descriptor sample file should exist"
    assert data_file.exists(), "NAST data sample file should exist"
    
    # Verify files have content
    with open(descriptor_file, 'r', encoding='utf-8') as f:
        descriptor_content = f.read()
    with open(data_file, 'r', encoding='utf-8') as f:
        data_content = f.read()
    
    assert len(descriptor_content) > 1000, "NAST descriptor should have substantial content"
    assert len(data_content) > 1000, "NAST data should have substantial content"
    assert descriptor_content == data_content, "NAST descriptor and data should be identical (descriptor-only page)"


def test_nast_xml_structure_validation(sample_nast_descriptor):
    """Test that NAST XML has expected structure."""
    content = sample_nast_descriptor
    
    # Basic XML structure
    assert '<?xml version="1.0"' in content, "Should have XML declaration"
    assert '<page' in content, "Should have page element"
    assert 'name="Nastavení TČ"' in content, "Should have Czech page name"
    assert 'name_en="HP settings"' in content, "Should have English page name"
    
    # Block structure
    assert '<block data="NAST1"' in content, "Should have sensor corrections block"
    assert '<block data="NAST2"' in content, "Should have power restrictions block"
    assert '<block data="NAST3"' in content, "Should have heat pump control block"
    
    # Element types
    assert '<number' in content, "Should contain number elements"
    assert '<choice' in content, "Should contain choice elements"
    assert '<button' in content, "Should contain button elements"
    assert '<text' in content, "Should contain text elements"
    
    # Key attributes
    assert 'prop=' in content, "Should have prop attributes"
    assert 'min=' in content, "Should have min attributes"
    assert 'max=' in content, "Should have max attributes"
    assert 'unit=' in content, "Should have unit attributes"


def test_nast_entity_parsing(sample_nast_descriptor):
    """Test parsing NAST entities from sample data."""
    entities = parse_xml_entities(sample_nast_descriptor, "nast.xml")
    
    # Basic parsing validation
    assert isinstance(entities, list), "Should return list of entities"
    assert len(entities) >= 130, f"Should parse many entities, got {len(entities)}"
    
    # Entity structure validation
    for entity in entities[:5]:  # Check first 5 entities
        assert "entity_id" in entity, "Entity should have entity_id"
        assert "entity_type" in entity, "Entity should have entity_type"
        assert "state" in entity, "Entity should have state"
        assert "attributes" in entity, "Entity should have attributes"
        
        # Validate entity_id format
        assert entity["entity_id"].startswith("xcc_"), "Entity ID should start with xcc_"
        assert entity["entity_type"] in ["number", "select", "button", "text", "sensor"], "Should have valid entity type"


def test_nast_number_entities(sample_nast_descriptor):
    """Test parsing of NAST number entities."""
    entities = parse_xml_entities(sample_nast_descriptor, "nast.xml")
    
    number_entities = [e for e in entities if e["entity_type"] == "number"]
    assert len(number_entities) >= 90, f"Should have many number entities, got {len(number_entities)}"
    
    # Test specific number entities
    sensor_corrections = [e for e in number_entities if e["entity_id"].endswith("_i")]
    assert len(sensor_corrections) >= 10, f"Should have sensor corrections, got {len(sensor_corrections)}"
    
    mzo_offsets = [e for e in number_entities if "mzo_zona" in e["entity_id"] and "offset" in e["entity_id"]]
    assert len(mzo_offsets) >= 15, f"Should have multi-zone offsets, got {len(mzo_offsets)}"
    
    power_limits = [e for e in number_entities if "omezen" in e["entity_id"]]
    assert len(power_limits) >= 5, f"Should have power limits, got {len(power_limits)}"
    
    # Validate number entity attributes
    for entity in number_entities[:3]:
        attrs = entity["attributes"]
        assert "source_page" in attrs, "Should have source_page"
        assert attrs["source_page"] == "nast.xml", "Should reference correct page"
        
        # Check for number-specific attributes
        if "min_value" in attrs:
            assert isinstance(attrs["min_value"], (int, float)), "min_value should be numeric"
        if "max_value" in attrs:
            assert isinstance(attrs["max_value"], (int, float)), "max_value should be numeric"
        if "step" in attrs:
            assert isinstance(attrs["step"], (int, float)), "step should be numeric"


def test_nast_select_entities(sample_nast_descriptor):
    """Test parsing of NAST select entities."""
    entities = parse_xml_entities(sample_nast_descriptor, "nast.xml")
    
    select_entities = [e for e in entities if e["entity_type"] == "select"]
    assert len(select_entities) >= 25, f"Should have many select entities, got {len(select_entities)}"
    
    # Test specific select entities
    hp_controls = [e for e in select_entities if "tcodstaveni" in e["entity_id"]]
    assert len(hp_controls) >= 5, f"Should have heat pump controls, got {len(hp_controls)}"
    
    enable_disable = [e for e in select_entities if "povoleni" in e["entity_id"]]
    assert len(enable_disable) >= 10, f"Should have enable/disable controls, got {len(enable_disable)}"
    
    # Validate select entity attributes
    for entity in select_entities[:3]:
        attrs = entity["attributes"]
        assert "source_page" in attrs, "Should have source_page"
        
        # Check for select-specific attributes
        if "options" in attrs:
            assert isinstance(attrs["options"], list), "options should be a list"
            assert len(attrs["options"]) >= 2, "Should have at least 2 options"


def test_nast_button_entities(sample_nast_descriptor):
    """Test parsing of NAST button entities."""
    entities = parse_xml_entities(sample_nast_descriptor, "nast.xml")
    
    button_entities = [e for e in entities if e["entity_type"] == "button"]
    assert len(button_entities) >= 1, f"Should have button entities, got {len(button_entities)}"
    
    # Test specific button entities
    flash_buttons = [e for e in button_entities if "flash" in e["entity_id"]]
    assert len(flash_buttons) >= 1, f"Should have flash buttons, got {len(flash_buttons)}"
    
    # Validate button entity attributes
    for entity in button_entities:
        attrs = entity["attributes"]
        assert "source_page" in attrs, "Should have source_page"
        
        # Check for button-specific attributes
        if "button_value" in attrs:
            assert attrs["button_value"], "button_value should not be empty"


def test_nast_text_entities(sample_nast_descriptor):
    """Test parsing of NAST text entities."""
    entities = parse_xml_entities(sample_nast_descriptor, "nast.xml")
    
    text_entities = [e for e in entities if e["entity_type"] == "text"]
    assert len(text_entities) >= 2, f"Should have text entities, got {len(text_entities)}"
    
    # Test specific text entities
    header_names = [e for e in text_entities if "header" in e["entity_id"] and "name" in e["entity_id"]]
    assert len(header_names) >= 2, f"Should have header name entities, got {len(header_names)}"
    
    # Validate text entity attributes
    for entity in text_entities:
        attrs = entity["attributes"]
        assert "source_page" in attrs, "Should have source_page"


def test_nast_entity_regression_counts(sample_nast_descriptor):
    """Test that entity counts don't regress."""
    entities = parse_xml_entities(sample_nast_descriptor, "nast.xml")
    
    # Count entities by type
    entity_counts = {}
    for entity in entities:
        entity_type = entity["entity_type"]
        entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1
    
    # Regression thresholds (based on current parsing)
    expected_minimums = {
        "number": 90,   # Should have at least 90 number entities
        "select": 25,   # Should have at least 25 select entities
        "button": 1,    # Should have at least 1 button entity
        "text": 2,      # Should have at least 2 text entities
    }
    
    for entity_type, minimum in expected_minimums.items():
        actual = entity_counts.get(entity_type, 0)
        assert actual >= minimum, f"Regression detected: {entity_type} entities dropped from {minimum} to {actual}"
    
    # Total entity count regression check
    total_entities = len(entities)
    assert total_entities >= 130, f"Total entity regression: expected >=130, got {total_entities}"


def test_nast_specific_entities_exist(sample_nast_descriptor):
    """Test that specific important NAST entities exist."""
    entities = parse_xml_entities(sample_nast_descriptor, "nast.xml")
    
    entity_ids = {e["entity_id"] for e in entities}
    
    # Critical entities that should always exist
    critical_entities = [
        "xcc_b0_i",                          # Sensor B0 correction
        "xcc_mzo_zona0_offset",              # Multi-zone offset 0
        "xcc_omezenivykonuglobalni",         # Global power restriction
        "xcc_tcodstaveni0",                  # Heat pump I control
        "xcc_flash_readwrite",               # System backup button
        "xcc_flash_header0_name",            # Configuration name
    ]
    
    for entity_id in critical_entities:
        assert entity_id in entity_ids, f"Critical entity missing: {entity_id}"


def test_nast_entity_attributes_quality(sample_nast_descriptor):
    """Test quality of entity attributes."""
    entities = parse_xml_entities(sample_nast_descriptor, "nast.xml")
    
    # Test attribute quality for different entity types
    for entity in entities:
        attrs = entity["attributes"]
        
        # All entities should have these
        assert "source_page" in attrs, f"Entity {entity['entity_id']} missing source_page"
        assert "field_name" in attrs, f"Entity {entity['entity_id']} missing field_name"
        assert "friendly_name" in attrs, f"Entity {entity['entity_id']} missing friendly_name"
        
        # Friendly name should be reasonable
        friendly_name = attrs["friendly_name"]
        assert len(friendly_name) > 0, f"Entity {entity['entity_id']} has empty friendly_name"
        assert len(friendly_name) < 100, f"Entity {entity['entity_id']} has overly long friendly_name"
        
        # Type-specific attribute validation
        if entity["entity_type"] == "number":
            # Number entities should have step
            assert "step" in attrs, f"Number entity {entity['entity_id']} missing step"
            
        elif entity["entity_type"] == "select":
            # Select entities should have options if available
            if "options" in attrs:
                options = attrs["options"]
                assert len(options) >= 2, f"Select entity {entity['entity_id']} has too few options"
                for option in options:
                    assert isinstance(option, str), f"Select entity {entity['entity_id']} has non-string option"
                    assert len(option) > 0, f"Select entity {entity['entity_id']} has empty option"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
