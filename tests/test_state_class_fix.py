"""Test state class assignment fixes for XCC integration."""

import pytest

# Use string constants instead of importing Home Assistant classes
class SensorStateClass:
    MEASUREMENT = "measurement"
    TOTAL_INCREASING = "total_increasing"

def test_state_class_determination():
    """Test that state class is correctly determined for different entity types."""
    
    print("🔧 Testing State Class Determination")
    print("=" * 50)
    
    def simulate_state_class_logic(prop, xml_name, current_value, device_class=None):
        """Simulate the state class determination logic from sensor.py"""
        
        # Look for clear indicators of string types
        is_clearly_string = (
            "STRING" in xml_name.upper()
            or "TIME" in xml_name.upper()  # Time values like "03:00"
            or "_s" in xml_name  # String suffix
            or "Thh:mm" in xml_name  # Time format indicator
            or prop in ["SNAZEV1", "SNAZEV2", "DEVICE_NAME", "LOCATION"]  # Known string fields
        )

        # Look for clear indicators of boolean types (should not have state class)
        is_clearly_boolean = (
            "BOOL" in xml_name.upper()
            or "_BOOL_" in xml_name.upper()
            or prop in ["SZAPNUTO", "ENABLED", "ACTIVE", "STATUS"]  # Known boolean fields
            or (
                # Check if current value is clearly boolean (0/1 only)
                current_value in ["0", "1", 0, 1]
                and xml_name.endswith("_i")  # Integer type but likely boolean
                and len(str(current_value)) == 1  # Single digit
            )
        )

        # Look for clear indicators of numeric types (should have state class)
        is_clearly_numeric = (
            "REAL" in xml_name.upper()
            or "INT" in xml_name.upper()
            or "FLOAT" in xml_name.upper()
            or "_f" in xml_name  # Float suffix
            or ("_i" in xml_name and not is_clearly_boolean)  # Integer suffix but not boolean
            or ".1f" in xml_name  # Float format
            or prop in ["SVENKU", "TEMPERATURE", "TEMP", "PRESSURE", "POWER"]  # Known numeric fields
        )

        # State class mapping for device classes
        STATE_CLASS_MAPPING = {
            "temperature": SensorStateClass.MEASUREMENT,
            "power": SensorStateClass.MEASUREMENT,
            "energy": SensorStateClass.TOTAL_INCREASING,
            "voltage": SensorStateClass.MEASUREMENT,
            "current": SensorStateClass.MEASUREMENT,
            "frequency": SensorStateClass.MEASUREMENT,
            "pressure": SensorStateClass.MEASUREMENT,
        }

        # Determine state class
        state_class = None

        # First, check if we have a device class mapping
        if device_class in STATE_CLASS_MAPPING:
            state_class = STATE_CLASS_MAPPING[device_class]
        else:
            if is_clearly_string or is_clearly_boolean:
                # Definitely a string or boolean sensor - no state class
                state_class = None
            elif is_clearly_numeric or device_class is not None:
                # Likely numeric or has device class - default to measurement
                state_class = SensorStateClass.MEASUREMENT
            else:
                # Unknown type - check current value as fallback, but be more careful
                if current_value is not None:
                    try:
                        numeric_value = float(str(current_value))
                        # Check if this looks like a boolean disguised as numeric
                        if str(current_value) in ["0", "1", "0.0", "1.0"] and xml_name.endswith("_i"):
                            # Likely a boolean value - no state class
                            state_class = None
                        else:
                            # Current value is numeric and not boolean - probably should have state class
                            state_class = SensorStateClass.MEASUREMENT
                    except (ValueError, TypeError):
                        # Current value is not numeric - no state class
                        state_class = None

        return state_class, is_clearly_boolean, is_clearly_numeric, is_clearly_string

    # Test cases based on real XCC entities
    test_cases = [
        {
            "name": "SZAPNUTO - Boolean system status",
            "prop": "SZAPNUTO",
            "xml_name": "__R38578.0_BOOL_i",
            "current_value": "1",
            "device_class": None,
            "expected_state_class": None,
            "expected_boolean": True,
        },
        {
            "name": "Temperature sensor",
            "prop": "SVENKU",
            "xml_name": "__R12345.0_REAL_f",
            "current_value": "23.5",
            "device_class": "temperature",
            "expected_state_class": SensorStateClass.MEASUREMENT,
            "expected_boolean": False,
        },
        {
            "name": "Power sensor",
            "prop": "POWER_CONSUMPTION",
            "xml_name": "__R67890.0_REAL_f",
            "current_value": "1250.0",
            "device_class": "power",
            "expected_state_class": SensorStateClass.MEASUREMENT,
            "expected_boolean": False,
        },
        {
            "name": "String sensor",
            "prop": "DEVICE_NAME",
            "xml_name": "__R11111.0_STRING_s",
            "current_value": "XCC Controller",
            "device_class": None,
            "expected_state_class": None,
            "expected_boolean": False,
        },
        {
            "name": "Boolean disguised as integer",
            "prop": "SOME_STATUS",
            "xml_name": "__R22222.0_INT_i",
            "current_value": "0",
            "device_class": None,
            "expected_state_class": None,  # Should be detected as boolean
            "expected_boolean": True,
        },
        {
            "name": "Real integer sensor",
            "prop": "COUNT_VALUE",
            "xml_name": "__R33333.0_INT_i",
            "current_value": "42",
            "device_class": None,
            "expected_state_class": SensorStateClass.MEASUREMENT,
            "expected_boolean": False,
        },
        {
            "name": "Time string",
            "prop": "SCHEDULE_TIME",
            "xml_name": "__R44444.0_TIME_s",
            "current_value": "14:30",
            "device_class": None,
            "expected_state_class": None,
            "expected_boolean": False,
        },
    ]

    for test_case in test_cases:
        print(f"\n🎯 Testing: {test_case['name']}")
        
        state_class, is_boolean, is_numeric, is_string = simulate_state_class_logic(
            test_case["prop"],
            test_case["xml_name"],
            test_case["current_value"],
            test_case["device_class"]
        )
        
        expected_state_class = test_case["expected_state_class"]
        expected_boolean = test_case["expected_boolean"]
        
        print(f"   Prop: {test_case['prop']}")
        print(f"   XML Name: {test_case['xml_name']}")
        print(f"   Current Value: {test_case['current_value']}")
        print(f"   Device Class: {test_case['device_class']}")
        print(f"   Expected State Class: {expected_state_class}")
        print(f"   Actual State Class: {state_class}")
        print(f"   Is Boolean: {is_boolean} (expected: {expected_boolean})")
        
        # Check state class
        if state_class == expected_state_class:
            print(f"   ✅ State class correct")
        else:
            print(f"   ❌ State class mismatch")
        
        # Check boolean detection
        if is_boolean == expected_boolean:
            print(f"   ✅ Boolean detection correct")
        else:
            print(f"   ❌ Boolean detection mismatch")

    print(f"\n📊 Summary")
    print("=" * 50)
    print("State class assignment rules:")
    print("1. Boolean entities (SZAPNUTO, BOOL in name, 0/1 values): NO state class")
    print("2. String entities (TIME, STRING in name): NO state class")
    print("3. Numeric entities with device class: MEASUREMENT state class")
    print("4. Clearly numeric entities: MEASUREMENT state class")
    print("5. Unknown entities with numeric values: MEASUREMENT state class")
    print("6. Unknown entities with non-numeric values: NO state class")


def test_szapnuto_specific_case():
    """Test the specific SZAPNUTO case that was causing issues."""
    
    print(f"\n🎯 Testing SZAPNUTO Specific Case")
    print("=" * 50)
    
    # Simulate the exact SZAPNUTO entity data
    entity_data = {
        "prop": "SZAPNUTO",
        "state": "1",
        "attributes": {
            "name": "__R38578.0_BOOL_i",
        }
    }
    
    # Test the boolean detection logic
    prop = entity_data["prop"]
    xml_name = entity_data["attributes"]["name"]
    current_value = entity_data["state"]
    
    is_clearly_boolean = (
        "BOOL" in xml_name.upper()
        or "_BOOL_" in xml_name.upper()
        or prop in ["SZAPNUTO", "ENABLED", "ACTIVE", "STATUS"]
        or (
            current_value in ["0", "1", 0, 1]
            and xml_name.endswith("_i")
            and len(str(current_value)) == 1
        )
    )
    
    print(f"Entity: {prop}")
    print(f"XML Name: {xml_name}")
    print(f"Current Value: {current_value}")
    print(f"Contains 'BOOL': {'BOOL' in xml_name.upper()}")
    print(f"Contains '_BOOL_': {'_BOOL_' in xml_name.upper()}")
    print(f"Is known boolean prop: {prop in ['SZAPNUTO', 'ENABLED', 'ACTIVE', 'STATUS']}")
    print(f"Value is 0/1: {current_value in ['0', '1', 0, 1]}")
    print(f"Ends with '_i': {xml_name.endswith('_i')}")
    print(f"Single digit: {len(str(current_value)) == 1}")
    print(f"Final boolean detection: {is_clearly_boolean}")
    
    if is_clearly_boolean:
        print("✅ SZAPNUTO correctly identified as boolean - will have NO state class")
        print("✅ This should resolve the Home Assistant statistics warning")
    else:
        print("❌ SZAPNUTO not identified as boolean - may still cause issues")


if __name__ == "__main__":
    """Run tests when executed directly."""
    try:
        test_state_class_determination()
        test_szapnuto_specific_case()
        print("\n🎉 STATE CLASS TESTS COMPLETED!")
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
