"""Tests for XCC descriptor parser."""
import pytest
import xml.etree.ElementTree as ET
from custom_components.xcc.descriptor_parser import DescriptorParser


class TestDescriptorParser:
    """Test the descriptor parser functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = DescriptorParser()

    def test_date_element_parsing(self):
        """Test that date elements are parsed correctly without numeric units."""
        # Create a sample date element like the one causing issues
        xml_content = '''
        <page>
            <block>
                <row>
                    <date config="readonly" prop="SPOTOVECENYSTATS-DATA0-TIMESTAMP" unit="date"/>
                </row>
            </block>
        </page>
        '''
        root = ET.fromstring(xml_content)
        date_element = root.find(".//date")
        
        # Parse the date element
        entity_config = self.parser._parse_element(date_element, "SPOTOVECENYSTATS-DATA0-TIMESTAMP")
        
        # Verify it's configured correctly
        assert entity_config is not None
        assert entity_config["entity_type"] == "sensor"
        assert entity_config["data_type"] == "string"
        assert entity_config["unit"] is None  # Should not have numeric unit
        assert entity_config["device_class"] == "timestamp"  # Should detect timestamp
        assert entity_config["state_class"] is None  # No state class for strings

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

    def test_unit_inference_from_context(self):
        """Test that units are inferred from context when missing."""
        xml_content = '''
        <page>
            <block>
                <row text="Temperature" text_en="Temperature">
                    <number prop="TEMP_VALUE"/>
                </row>
            </block>
        </page>
        '''
        root = ET.fromstring(xml_content)
        number_element = root.find(".//number")
        
        entity_config = self.parser._parse_element(number_element, "TEMP_VALUE")
        
        assert entity_config is not None
        # Should infer temperature unit from context
        assert entity_config["unit"] in ["°C", "temperature"]

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

    def test_device_class_inference(self):
        """Test that device classes are inferred correctly."""
        test_cases = [
            ("TEMPERATURE", "temperature"),
            ("HUMIDITY", "humidity"),
            ("PRESSURE", "pressure"),
            ("POWER", "power"),
            ("ENERGY", "energy"),
            ("VOLTAGE", "voltage"),
            ("CURRENT", "current"),
            ("TIMESTAMP", "timestamp"),
        ]
        
        for prop_name, expected_device_class in test_cases:
            xml_content = f'''
            <page>
                <block>
                    <row>
                        <number prop="{prop_name}" unit="test"/>
                    </row>
                </block>
            </page>
            '''
            root = ET.fromstring(xml_content)
            number_element = root.find(".//number")
            
            entity_config = self.parser._parse_element(number_element, prop_name)
            
            assert entity_config is not None
            assert entity_config["device_class"] == expected_device_class

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

    def test_regression_date_unit_issue(self):
        """Regression test for the date unit issue that caused ValueError."""
        # This is the exact case that was causing problems
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
        
        entity_config = self.parser._parse_element(date_element, "SPOTOVECENYSTATS-DATA0-TIMESTAMP")
        
        # This should NOT have a numeric unit that would cause ValueError
        assert entity_config is not None
        assert entity_config["entity_type"] == "sensor"
        assert entity_config["data_type"] == "string"
        assert entity_config["unit"] is None  # Critical: no numeric unit
        assert entity_config["device_class"] == "timestamp"
        assert entity_config["state_class"] is None  # Critical: no state class for strings


class TestDescriptorParserIntegration:
    """Integration tests for descriptor parser with real sample data."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = DescriptorParser()

    def test_parse_sample_spot_descriptor(self):
        """Test parsing the actual SPOT.XML descriptor file."""
        # This tests the real descriptor that was causing issues
        try:
            from pathlib import Path
            sample_file = Path(__file__).parent.parent / "sample_data" / "SPOT.XML"
            if sample_file.exists():
                entities = self.parser.parse_descriptor_file(str(sample_file))

                # Should find the problematic timestamp entities
                timestamp_entities = [
                    e for e in entities
                    if e["prop"] in ["SPOTOVECENYSTATS-DATA0-TIMESTAMP", "SPOTOVECENYSTATS-DATA1-TIMESTAMP"]
                ]

                assert len(timestamp_entities) == 2
                for entity in timestamp_entities:
                    # These should be sensors without numeric units
                    assert entity["entity_type"] == "sensor"
                    assert entity["data_type"] == "string"
                    assert entity["unit"] is None
                    assert entity["device_class"] == "timestamp"
                    assert entity["state_class"] is None
        except ImportError:
            pytest.skip("Sample data not available")

    def test_no_duplicate_entity_configs(self):
        """Test that no duplicate entity configurations are created."""
        # Create a descriptor with potential duplicates
        xml_content = '''
        <page>
            <block>
                <row>
                    <switch prop="TEST_SWITCH"/>
                </row>
                <row>
                    <switch prop="TEST_SWITCH"/>
                </row>
            </block>
        </page>
        '''

        entities = self.parser.parse_descriptor_content(xml_content)

        # Should only have one entity even if defined multiple times
        switch_entities = [e for e in entities if e["prop"] == "TEST_SWITCH"]
        assert len(switch_entities) == 1
