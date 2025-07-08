"""Standalone tests for XCC descriptor parser (no Home Assistant dependencies)."""
import pytest
import xml.etree.ElementTree as ET
import sys
from pathlib import Path

# Add the custom_components directory to the Python path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

# Import just the descriptor parser module directly
from custom_components.xcc.descriptor_parser import DescriptorParser


class TestDescriptorParserStandalone:
    """Test the descriptor parser functionality without Home Assistant dependencies."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = DescriptorParser()

    def test_date_element_parsing_regression(self):
        """Regression test for date elements that caused ValueError."""
        # Create a sample date element like the one causing issues
        xml_content = '''
        <page>
            <block>
                <row text="Hodina" text_en="Hour">
                    <date config="readonly" prop="SPOTOVECENYSTATS-DATA0-TIMESTAMP" unit="date"/>
                </row>
            </block>
        </page>
        '''
        root = ET.fromstring(xml_content)
        date_element = root.find(".//date")
        
        # Parse the date element
        entity_config = self.parser._parse_element(date_element, "SPOTOVECENYSTATS-DATA0-TIMESTAMP")
        
        # Verify it's configured correctly to prevent ValueError
        assert entity_config is not None
        assert entity_config["entity_type"] == "sensor"
        assert entity_config["data_type"] == "string"
        assert entity_config["unit"] is None  # Critical: should not have numeric unit
        assert entity_config["device_class"] == "timestamp"
        assert entity_config["state_class"] is None  # Critical: no state class for strings

    def test_date_element_with_timestamp_prop(self):
        """Test date element with timestamp in property name."""
        xml_content = '''
        <page>
            <block>
                <row>
                    <date prop="SPOTOVECENYSTATS-DATA1-TIMESTAMP" unit="date"/>
                </row>
            </block>
        </page>
        '''
        root = ET.fromstring(xml_content)
        date_element = root.find(".//date")
        
        entity_config = self.parser._parse_element(date_element, "SPOTOVECENYSTATS-DATA1-TIMESTAMP")
        
        assert entity_config is not None
        assert entity_config["entity_type"] == "sensor"
        assert entity_config["data_type"] == "string"
        assert entity_config["unit"] is None
        assert entity_config["device_class"] == "timestamp"
        assert entity_config["state_class"] is None

    def test_time_element_parsing(self):
        """Test that time elements are parsed correctly."""
        xml_content = '''
        <page>
            <block>
                <row>
                    <time prop="BIVALENCECASODPOJENI"/>
                </row>
            </block>
        </page>
        '''
        root = ET.fromstring(xml_content)
        time_element = root.find(".//time")
        
        entity_config = self.parser._parse_element(time_element, "BIVALENCECASODPOJENI")
        
        assert entity_config is not None
        assert entity_config["entity_type"] == "sensor"
        assert entity_config["data_type"] == "string"
        assert entity_config["unit"] is None
        assert entity_config["state_class"] is None

    def test_number_element_parsing(self):
        """Test that number elements are parsed correctly."""
        xml_content = '''
        <page>
            <block>
                <row>
                    <number prop="TUVPOZADOVANA" unit="°C" min="10" max="80" digits="1"/>
                </row>
            </block>
        </page>
        '''
        root = ET.fromstring(xml_content)
        number_element = root.find(".//number")
        
        entity_config = self.parser._parse_element(number_element, "TUVPOZADOVANA")
        
        assert entity_config is not None
        assert entity_config["entity_type"] == "number"
        assert entity_config["data_type"] == "float"
        assert entity_config["unit"] == "°C"
        assert entity_config["min_value"] == 10.0
        assert entity_config["max_value"] == 80.0
        assert entity_config["step"] == 0.1

    def test_switch_element_parsing(self):
        """Test that switch elements are parsed correctly."""
        xml_content = '''
        <page>
            <block>
                <row>
                    <switch prop="SPOTOVECENY-FEEDTOGRIDLIMIT"/>
                </row>
            </block>
        </page>
        '''
        root = ET.fromstring(xml_content)
        switch_element = root.find(".//switch")
        
        entity_config = self.parser._parse_element(switch_element, "SPOTOVECENY-FEEDTOGRIDLIMIT")
        
        assert entity_config is not None
        assert entity_config["entity_type"] == "switch"
        assert entity_config["data_type"] == "bool"

    def test_choice_element_parsing(self):
        """Test that choice elements are parsed correctly."""
        xml_content = '''
        <page>
            <block>
                <row>
                    <choice prop="SPOTOVECENY-DSMODE">
                        <option text="Standard" text_en="Standard" value="0"/>
                        <option text="Virt. baterie" text_en="Virt. battery" value="1"/>
                        <option text="SPOT" text_en="SPOT" value="2"/>
                    </choice>
                </row>
            </block>
        </page>
        '''
        root = ET.fromstring(xml_content)
        choice_element = root.find(".//choice")
        
        entity_config = self.parser._parse_element(choice_element, "SPOTOVECENY-DSMODE")
        
        assert entity_config is not None
        assert entity_config["entity_type"] == "select"
        assert entity_config["data_type"] == "string"
        assert "options" in entity_config
        assert len(entity_config["options"]) == 3
        assert entity_config["options"]["0"] == "Standard"
        assert entity_config["options"]["1"] == "Virt. battery"
        assert entity_config["options"]["2"] == "SPOT"

    def test_unknown_element_returns_none(self):
        """Test that unknown elements return None."""
        xml_content = '''
        <page>
            <block>
                <row>
                    <unknown_element prop="TEST"/>
                </row>
            </block>
        </page>
        '''
        root = ET.fromstring(xml_content)
        unknown_element = root.find(".//unknown_element")
        
        entity_config = self.parser._parse_element(unknown_element, "TEST")
        
        assert entity_config is None

    def test_friendly_name_extraction(self):
        """Test that friendly names are extracted correctly."""
        xml_content = '''
        <page>
            <block>
                <row text="Teplota TUV" text_en="DHW Temperature">
                    <number prop="TUVPOZADOVANA" unit="°C"/>
                </row>
            </block>
        </page>
        '''
        root = ET.fromstring(xml_content)
        number_element = root.find(".//number")
        
        entity_config = self.parser._parse_element(number_element, "TUVPOZADOVANA")
        
        assert entity_config is not None
        # Should prefer English text
        assert entity_config["friendly_name"] == "DHW Temperature"

    def test_readonly_config_detection(self):
        """Test that readonly configuration is detected."""
        xml_content = '''
        <page>
            <block>
                <row>
                    <number config="readonly" prop="READONLY_VALUE" unit="°C"/>
                </row>
            </block>
        </page>
        '''
        root = ET.fromstring(xml_content)
        number_element = root.find(".//number")
        
        entity_config = self.parser._parse_element(number_element, "READONLY_VALUE")
        
        assert entity_config is not None
        # Readonly numbers should become sensors
        assert entity_config["entity_type"] == "sensor"
        assert entity_config["data_type"] == "float"

    def test_multiple_date_elements_regression(self):
        """Test multiple date elements like those causing the original issue."""
        xml_content = '''
        <page>
            <block>
                <row text="Hodina" text_en="Hour">
                    <date config="readonly" prop="SPOTOVECENYSTATS-DATA0-TIMESTAMP" unit="date"/>
                    <date config="readonly" prop="SPOTOVECENYSTATS-DATA1-TIMESTAMP" unit="date"/>
                </row>
            </block>
        </page>
        '''
        root = ET.fromstring(xml_content)
        date_elements = root.findall(".//date")
        
        assert len(date_elements) == 2
        
        for i, date_element in enumerate(date_elements):
            prop = date_element.get("prop")
            entity_config = self.parser._parse_element(date_element, prop)
            
            # Both should be configured as string sensors without numeric units
            assert entity_config is not None
            assert entity_config["entity_type"] == "sensor"
            assert entity_config["data_type"] == "string"
            assert entity_config["unit"] is None  # Critical: prevents ValueError
            assert entity_config["device_class"] == "timestamp"
            assert entity_config["state_class"] is None  # Critical: prevents ValueError

    def test_parse_descriptor_content_with_dates(self):
        """Test parsing full descriptor content with date elements."""
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
        <page>
            <block>
                <row text="Data received" text_en="Data received">
                    <date config="readonly" prop="SPOTOVECENYSTATS-RECEIVED"/>
                </row>
                <row text="Hodina" text_en="Hour">
                    <date config="readonly" prop="SPOTOVECENYSTATS-DATA0-TIMESTAMP" unit="date"/>
                </row>
                <row text="Hodina" text_en="Hour">
                    <date config="readonly" prop="SPOTOVECENYSTATS-DATA1-TIMESTAMP" unit="date"/>
                </row>
            </block>
        </page>
        '''
        
        entities = self.parser.parse_descriptor_content(xml_content)
        
        # Should find all date entities
        date_entities = [e for e in entities if "TIMESTAMP" in e["prop"] or "RECEIVED" in e["prop"]]
        assert len(date_entities) == 3
        
        # All should be configured correctly
        for entity in date_entities:
            assert entity["entity_type"] == "sensor"
            assert entity["data_type"] == "string"
            assert entity["unit"] is None
            assert entity["state_class"] is None
