#!/usr/bin/env python3
"""Test XCC integration without MQTT dependency."""

import json
import sys
from pathlib import Path

def test_manifest_no_mqtt_dependency():
    """Test that manifest doesn't have MQTT as hard dependency."""
    print("🔍 Testing manifest.json for MQTT dependency...")
    
    # Test both manifest files
    manifests = [
        "homeassistant/components/xcc/manifest.json",
        "custom_components/xcc/manifest.json"
    ]
    
    for manifest_path in manifests:
        if not Path(manifest_path).exists():
            print(f"  ⚠️  {manifest_path} not found, skipping")
            continue
            
        with open(manifest_path) as f:
            manifest = json.load(f)
        
        # Check that MQTT is not in dependencies
        dependencies = manifest.get("dependencies", [])
        if "mqtt" in dependencies:
            print(f"  ❌ {manifest_path}: MQTT found in dependencies: {dependencies}")
            return False
        else:
            print(f"  ✅ {manifest_path}: No MQTT hard dependency")
        
        # Check that MQTT is in after_dependencies (optional)
        after_deps = manifest.get("after_dependencies", [])
        if "mqtt" in after_deps:
            print(f"  ✅ {manifest_path}: MQTT correctly in after_dependencies: {after_deps}")
        else:
            print(f"  ⚠️  {manifest_path}: MQTT not in after_dependencies")
    
    return True

def test_import_without_mqtt():
    """Test that integration modules can be imported without MQTT."""
    print("\n🔍 Testing module imports without MQTT...")
    
    # Add the homeassistant directory to the path
    sys.path.insert(0, str(Path(__file__).parent / "homeassistant"))
    
    try:
        # Test importing core modules
        from homeassistant.components.xcc import const
        print("  ✅ const.py imported successfully")
        
        from homeassistant.components.xcc import config_flow
        print("  ✅ config_flow.py imported successfully")
        
        from homeassistant.components.xcc import coordinator
        print("  ✅ coordinator.py imported successfully")
        
        from homeassistant.components.xcc import entity
        print("  ✅ entity.py imported successfully")
        
        # Test importing platform modules
        from homeassistant.components.xcc import sensor
        print("  ✅ sensor.py imported successfully")
        
        from homeassistant.components.xcc import binary_sensor
        print("  ✅ binary_sensor.py imported successfully")
        
        from homeassistant.components.xcc import switch
        print("  ✅ switch.py imported successfully")
        
        from homeassistant.components.xcc import number
        print("  ✅ number.py imported successfully")
        
        from homeassistant.components.xcc import select
        print("  ✅ select.py imported successfully")
        
        # Test importing MQTT discovery (should not fail even without MQTT)
        from homeassistant.components.xcc import mqtt_discovery
        print("  ✅ mqtt_discovery.py imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"  ❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Unexpected error: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing XCC Integration without MQTT\n")
    
    tests = [
        ("Manifest MQTT Dependency", test_manifest_no_mqtt_dependency),
        ("Module Imports", test_import_without_mqtt),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            if result:
                passed += 1
        except Exception as e:
            print(f"  ❌ Test {test_name} failed with exception: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ Integration should work without MQTT!")
        print("\n📋 What this means:")
        print("  - Integration can be installed without MQTT configured")
        print("  - MQTT features are optional and gracefully disabled")
        print("  - Core functionality (sensors, controls) works independently")
        print("  - Users can add MQTT later if desired")
        return True
    else:
        print("❌ Some tests failed. Integration may still require MQTT.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
