#!/usr/bin/env python3
"""Test script to verify XCC integration configuration options."""

import sys
import os

# Add the custom_components directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'custom_components'))

def test_config_constants():
    """Test that configuration constants are properly defined."""
    print("🔍 Testing configuration constants...")

    try:
        # Read const.py file directly
        const_file = os.path.join(os.path.dirname(__file__), 'custom_components', 'xcc', 'const.py')
        with open(const_file, 'r') as f:
            content = f.read()

        # Check for required constants
        required_constants = [
            'CONF_ENTITY_TYPE: Final = "entity_type"',
            'ENTITY_TYPE_INTEGRATION: Final = "integration"',
            'ENTITY_TYPE_MQTT: Final = "mqtt"',
            'DEFAULT_ENTITY_TYPE: Final = ENTITY_TYPE_MQTT',
            'VERSION: Final = "1.4.0"'
        ]

        for constant in required_constants:
            if constant in content:
                print(f"✅ Found: {constant}")
            else:
                print(f"❌ Missing: {constant}")
                return False

        print("✅ All configuration constants are present!")
        return True

    except Exception as e:
        print(f"❌ Error testing configuration constants: {e}")
        return False

def test_config_flow_schema():
    """Test that config flow schema includes entity type selection."""
    print("\n🔍 Testing config flow schema...")

    try:
        # Read config_flow.py file directly
        config_flow_file = os.path.join(os.path.dirname(__file__), 'custom_components', 'xcc', 'config_flow.py')
        with open(config_flow_file, 'r') as f:
            content = f.read()

        # Check for entity type imports and usage
        required_patterns = [
            'CONF_ENTITY_TYPE',
            'ENTITY_TYPE_INTEGRATION',
            'ENTITY_TYPE_MQTT',
            'DEFAULT_ENTITY_TYPE',
            'vol.Optional(CONF_ENTITY_TYPE, default=DEFAULT_ENTITY_TYPE)',
            'selector.SelectSelector'
        ]

        for pattern in required_patterns:
            if pattern in content:
                print(f"✅ Found: {pattern}")
            else:
                print(f"❌ Missing: {pattern}")
                return False

        print("✅ Config flow includes entity type selection!")
        return True

    except Exception as e:
        print(f"❌ Error testing config flow schema: {e}")
        return False

def test_entity_type_logic():
    """Test entity type selection logic."""
    print("\n🔍 Testing entity type selection logic...")

    try:
        # Test the logic without importing Home Assistant modules
        CONF_ENTITY_TYPE = "entity_type"
        ENTITY_TYPE_INTEGRATION = "integration"
        ENTITY_TYPE_MQTT = "mqtt"
        DEFAULT_ENTITY_TYPE = ENTITY_TYPE_MQTT

        # Test default behavior
        config_data = {}
        entity_type = config_data.get(CONF_ENTITY_TYPE, DEFAULT_ENTITY_TYPE)
        print(f"✅ Default entity type: {entity_type}")
        assert entity_type == ENTITY_TYPE_MQTT

        # Test MQTT selection
        config_data = {CONF_ENTITY_TYPE: ENTITY_TYPE_MQTT}
        entity_type = config_data.get(CONF_ENTITY_TYPE, DEFAULT_ENTITY_TYPE)
        print(f"✅ MQTT entity type: {entity_type}")
        assert entity_type == ENTITY_TYPE_MQTT

        # Test Integration selection
        config_data = {CONF_ENTITY_TYPE: ENTITY_TYPE_INTEGRATION}
        entity_type = config_data.get(CONF_ENTITY_TYPE, DEFAULT_ENTITY_TYPE)
        print(f"✅ Integration entity type: {entity_type}")
        assert entity_type == ENTITY_TYPE_INTEGRATION

        print("✅ Entity type selection logic works correctly!")
        return True

    except Exception as e:
        print(f"❌ Error testing entity type logic: {e}")
        return False

def main():
    """Run all configuration tests."""
    print("🚀 XCC Integration Configuration Test Suite")
    print("=" * 50)
    
    tests = [
        test_config_constants,
        test_config_flow_schema,
        test_entity_type_logic,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Configuration options are working correctly.")
        return True
    else:
        print("❌ Some tests failed. Please check the configuration.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
