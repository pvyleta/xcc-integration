"""Test the real descriptor parser with the date element fix."""
import pytest
import xml.etree.ElementTree as ET
import sys
import importlib.util
import logging
from pathlib import Path


def test_real_descriptor_parser_date_fix():
    """Test the real descriptor parser with the date element fix."""
    
    # Import the descriptor parser module directly
    repo_root = Path(__file__).parent.parent
    parser_path = repo_root / "custom_components" / "xcc" / "descriptor_parser.py"
    
    spec = importlib.util.spec_from_file_location("descriptor_parser", parser_path)
    descriptor_parser = importlib.util.module_from_spec(spec)
    
    # Mock the logger
    descriptor_parser._LOGGER = logging.getLogger('test')
    
    # Execute the module
    spec.loader.exec_module(descriptor_parser)
    
    # Create parser instance
    parser = descriptor_parser.XCCDescriptorParser()
    
    # Test the problematic XML that was causing ValueError
    xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
    <page>
        <block>
            <row text="Hodina" text_en="Hour">
                <date config="readonly" prop="SPOTOVECENYSTATS-DATA0-TIMESTAMP" unit="date"/>
            </row>
            <row text="Hodina" text_en="Hour">
                <date config="readonly" prop="SPOTOVECENYSTATS-DATA1-TIMESTAMP" unit="date"/>
            </row>
        </block>
    </page>
    '''
    
    # Parse the descriptor content using the private method
    entity_configs = parser._parse_single_descriptor(xml_content, "test_page")

    # Convert to list format for easier testing
    entities = list(entity_configs.values())
    
    # Find the timestamp entities
    timestamp_entities = [
        e for e in entities 
        if e["prop"] in ["SPOTOVECENYSTATS-DATA0-TIMESTAMP", "SPOTOVECENYSTATS-DATA1-TIMESTAMP"]
    ]
    
    # Verify we found the entities
    assert len(timestamp_entities) == 2, f"Expected 2 timestamp entities, found {len(timestamp_entities)}"
    
    # Verify each timestamp entity is configured correctly
    for entity in timestamp_entities:
        print(f"Testing entity: {entity['prop']}")
        
        # Critical assertions to prevent ValueError
        assert entity["entity_type"] == "sensor", f"Entity {entity['prop']} should be sensor, got {entity['entity_type']}"
        assert entity["data_type"] == "string", f"Entity {entity['prop']} should have string data_type, got {entity['data_type']}"
        assert entity["unit"] is None, f"Entity {entity['prop']} should have unit=None, got {entity['unit']}"
        assert entity["device_class"] == "timestamp", f"Entity {entity['prop']} should have timestamp device_class, got {entity['device_class']}"
        assert entity["state_class"] is None, f"Entity {entity['prop']} should have state_class=None, got {entity['state_class']}"
        
        print(f"✅ Entity {entity['prop']} configured correctly")
    
    print("✅ Real descriptor parser date fix test passed!")


def test_real_descriptor_parser_other_elements():
    """Test that other elements still work correctly."""
    
    # Import the descriptor parser module directly
    repo_root = Path(__file__).parent.parent
    parser_path = repo_root / "custom_components" / "xcc" / "descriptor_parser.py"
    
    spec = importlib.util.spec_from_file_location("descriptor_parser", parser_path)
    descriptor_parser = importlib.util.module_from_spec(spec)
    
    # Mock the logger
    descriptor_parser._LOGGER = logging.getLogger('test')
    
    # Execute the module
    spec.loader.exec_module(descriptor_parser)
    
    # Create parser instance
    parser = descriptor_parser.XCCDescriptorParser()
    
    # Test XML with various element types
    xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
    <page>
        <block>
            <row text="Temperature" text_en="Temperature">
                <number prop="TUVPOZADOVANA" unit="°C" min="10" max="80" digits="1"/>
            </row>
            <row text="Switch" text_en="Switch">
                <switch prop="TEST_SWITCH"/>
            </row>
            <row text="Time" text_en="Time">
                <time prop="BIVALENCECASODPOJENI"/>
            </row>
        </block>
    </page>
    '''
    
    # Parse the descriptor content using the private method
    entity_configs = parser._parse_single_descriptor(xml_content, "test_page")

    # Convert to list format for easier testing
    entities = list(entity_configs.values())
    
    # Verify we got entities
    assert len(entities) > 0, "Should have found some entities"
    
    # Find specific entities
    number_entity = next((e for e in entities if e["prop"] == "TUVPOZADOVANA"), None)
    switch_entity = next((e for e in entities if e["prop"] == "TEST_SWITCH"), None)
    time_entity = next((e for e in entities if e["prop"] == "BIVALENCECASODPOJENI"), None)
    
    # Verify number entity
    if number_entity:
        assert number_entity["entity_type"] == "number"
        assert number_entity["data_type"] == "real"  # Numbers use "real" data type
        assert number_entity["unit"] == "°C"
        print("✅ Number entity configured correctly")
    
    # Verify switch entity
    if switch_entity:
        assert switch_entity["entity_type"] == "switch"
        assert switch_entity["data_type"] == "bool"
        print("✅ Switch entity configured correctly")
    
    # Verify time entity
    if time_entity:
        assert time_entity["entity_type"] == "sensor"
        assert time_entity["data_type"] == "time"  # Time elements use "time" data type
        assert time_entity["unit"] == ""  # Time elements should have empty unit
        assert time_entity["state_class"] is None
        print("✅ Time entity configured correctly")
    
    print("✅ Real descriptor parser other elements test passed!")


def _load_descriptor_parser():
    """Helper: load the descriptor_parser module by file path (mirrors other tests)."""
    repo_root = Path(__file__).parent.parent
    parser_path = repo_root / "custom_components" / "xcc" / "descriptor_parser.py"
    spec = importlib.util.spec_from_file_location("descriptor_parser", parser_path)
    module = importlib.util.module_from_spec(spec)
    module._LOGGER = logging.getLogger("test")
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    "prop",
    [
        "POCASI-NAZEVMESTA",
        "POCASI-STARI",
        "POCASI-PREDPOVEDI0-DOBAPLATNOSTI",
        "POCASI-PREDPOVEDI11-DOBAPLATNOSTI",
        "POCASI-PREDPOVEDILOCAL0-OBRAZEK",
        "POCASICONFIG-LOKALITA",
        "POCASICONFIG-STAT",
    ],
)
def test_pocasi_props_do_not_get_hour_unit(prop):
    """POCASI* props must not be tagged with unit='h' via the CAS heuristic.

    Regression for the ValueError observed in production where
    sensor.xcc_pocasi_predpovedi0_dobaplatnosti was assigned unit='h' and HA
    rejected its non-numeric value '25.04.2026 23:00', poisoning coordinator
    refresh and blocking unrelated number writes.
    """
    descriptor_parser = _load_descriptor_parser()
    parser = descriptor_parser.XCCDescriptorParser()

    inferred = parser._infer_unit_from_context(prop, None, None)
    assert inferred != "h", (
        f"{prop} must not be inferred as duration/hours; "
        f"'POCASI' (Czech for 'weather') contains 'CAS' but is not time-related."
    )


@pytest.mark.parametrize(
    "prop",
    [
        "BIVALENCECASODPOJENI",
        "BIVALENCECASSPUSTENI",
        "BLOKYSPOTREBYOMEZENICASU1",
        "BLOKYSPOTREBYOMEZENICASU7",
        "BAZENPROGRAMCASY1",
        "FVE-MAXPOCETODLOZENYCHHODIN",
    ],
)
def test_legitimate_time_props_still_get_hour_unit(prop):
    """Genuine CAS/HODIN time props must keep unit='h' (no regression from the POCASI fix)."""
    descriptor_parser = _load_descriptor_parser()
    parser = descriptor_parser.XCCDescriptorParser()

    assert parser._infer_unit_from_context(prop, None, None) == "h"


def test_pocasi_dobaplatnosti_row_prop_end_to_end():
    """End-to-end: parsing a POCASI row prop must not yield unit='h' on the sensor config."""
    descriptor_parser = _load_descriptor_parser()
    parser = descriptor_parser.XCCDescriptorParser()

    # Mirrors the structure of fresh_tuv_data/descriptors/pocasi.xml: a row whose
    # own prop is the date string, with typed children (number/icon) for sub-fields.
    xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
    <page>
        <block>
            <row prop="POCASI-PREDPOVEDI0-DOBAPLATNOSTI" text="Datum" text_en="Date">
                <number config="readonly" prop="POCASI-PREDPOVEDI0-VLHKOST" unit="%"/>
                <number config="readonly" prop="POCASI-PREDPOVEDI0-TEPLOTA" unit="°C"/>
            </row>
            <row text="Lokalita" text_en="Chosen location">
                <label prop="POCASI-NAZEVMESTA"/>
            </row>
        </block>
    </page>
    '''

    entity_configs = parser._parse_single_descriptor(xml_content, "pocasi.xml")

    doba = entity_configs.get("POCASI-PREDPOVEDI0-DOBAPLATNOSTI")
    assert doba is not None, "row-prop entity should be extracted"
    assert doba["unit"] != "h", (
        f"DOBAPLATNOSTI must not get unit='h' (got {doba['unit']!r}); "
        f"would cause ValueError on the date-string state."
    )
    assert doba["device_class"] != "duration"

    nazev = entity_configs.get("POCASI-NAZEVMESTA")
    assert nazev is not None
    assert nazev["unit"] != "h"
    assert nazev["device_class"] != "duration"


if __name__ == "__main__":
    test_real_descriptor_parser_date_fix()
    test_real_descriptor_parser_other_elements()
    print("🎉 All real descriptor parser tests passed!")
