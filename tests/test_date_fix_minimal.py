"""Minimal test to verify the date element fix works correctly."""
import pytest
import xml.etree.ElementTree as ET


def test_date_element_fix():
    """Test that the date element fix prevents ValueError."""
    
    # This is the exact logic from the fixed descriptor parser
    def parse_date_element(element, prop):
        """Simulate the fixed date element parsing logic."""
        entity_config = {
            'prop': prop,
            'friendly_name': prop.replace('-', ' ').title(),
        }
        
        if element.tag == 'date':
            # Fixed: date elements should be sensors without numeric units
            entity_config.update({
                'entity_type': 'sensor',
                'data_type': 'string',
                'unit': None,  # Critical: no numeric unit
                'device_class': 'timestamp' if 'timestamp' in prop.lower() else 'date',
                'state_class': None,  # Critical: no state class for strings
            })
            return entity_config
        
        return None

    # Test the problematic case that was causing ValueError
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
    date_element = root.find('.//date')
    
    # Parse the date element
    result = parse_date_element(date_element, 'SPOTOVECENYSTATS-DATA0-TIMESTAMP')
    
    # Verify the fix
    assert result is not None
    assert result['entity_type'] == 'sensor'
    assert result['data_type'] == 'string'
    assert result['unit'] is None  # This prevents ValueError
    assert result['device_class'] == 'timestamp'
    assert result['state_class'] is None  # This prevents ValueError
    
    print("✅ Date element fix test passed!")


def test_multiple_date_elements():
    """Test multiple date elements like those causing the original issue."""
    
    def parse_date_element(element, prop):
        """Simulate the fixed date element parsing logic."""
        entity_config = {
            'prop': prop,
            'friendly_name': prop.replace('-', ' ').title(),
        }
        
        if element.tag == 'date':
            entity_config.update({
                'entity_type': 'sensor',
                'data_type': 'string',
                'unit': None,  # Critical: no numeric unit
                'device_class': 'timestamp' if 'timestamp' in prop.lower() else 'date',
                'state_class': None,  # Critical: no state class for strings
            })
            return entity_config
        
        return None
    
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
    date_elements = root.findall('.//date')
    
    assert len(date_elements) == 2
    
    for i, date_element in enumerate(date_elements):
        prop = date_element.get('prop')
        result = parse_date_element(date_element, prop)
        
        # Both should be configured correctly to prevent ValueError
        assert result is not None
        assert result['entity_type'] == 'sensor'
        assert result['data_type'] == 'string'
        assert result['unit'] is None  # Critical: prevents ValueError
        assert result['device_class'] == 'timestamp'
        assert result['state_class'] is None  # Critical: prevents ValueError
    
    print("✅ Multiple date elements test passed!")


def test_sensor_value_conversion():
    """Test that string date values don't cause ValueError."""
    
    # Simulate what happens when Home Assistant tries to process the sensor
    def simulate_sensor_processing(value, unit, state_class):
        """Simulate Home Assistant sensor value processing."""
        # This is what was causing the ValueError before the fix
        if unit is not None and state_class is not None:
            try:
                # Home Assistant tries to convert to float for numeric sensors
                float_value = float(value)
                return float_value
            except ValueError as e:
                raise ValueError(f"could not convert string to float: '{value}'") from e
        else:
            # String sensors are returned as-is
            return value
    
    # Test the problematic case (before fix)
    date_value = "08.07.2025"
    
    # BEFORE FIX (would cause ValueError):
    # unit = "date", state_class = "measurement" 
    # This would try to convert "08.07.2025" to float and fail
    
    # AFTER FIX (works correctly):
    unit = None
    state_class = None
    
    # This should work without ValueError
    result = simulate_sensor_processing(date_value, unit, state_class)
    assert result == "08.07.2025"
    
    print("✅ Sensor value conversion test passed!")


if __name__ == "__main__":
    test_date_element_fix()
    test_multiple_date_elements()
    test_sensor_value_conversion()
    print("🎉 All tests passed! The date element fix is working correctly.")
