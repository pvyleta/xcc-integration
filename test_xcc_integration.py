#!/usr/bin/env python3
"""Test script for XCC Home Assistant integration."""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add the homeassistant directory to the path
sys.path.insert(0, str(Path(__file__).parent / "homeassistant"))

def test_integration_structure():
    """Test that all required files exist."""
    print("🔍 Testing integration structure...")
    
    base_path = Path("homeassistant/components/xcc")
    required_files = [
        "manifest.json",
        "const.py",
        "config_flow.py",
        "coordinator.py",
        "__init__.py",
        "entity.py",
        "sensor.py",
        "binary_sensor.py",
        "switch.py",
        "number.py",
        "select.py",
        "strings.json",
        "mqtt_discovery.py",
        "xcc_client.py",
        "translations/cs.json",
    ]
    
    missing_files = []
    for file_path in required_files:
        full_path = base_path / file_path
        if not full_path.exists():
            missing_files.append(str(full_path))
        else:
            print(f"  ✓ {file_path}")
    
    if missing_files:
        print(f"  ❌ Missing files: {missing_files}")
        return False
    
    print("  ✅ All required files present")
    return True

def test_manifest():
    """Test manifest.json structure."""
    print("\n🔍 Testing manifest.json...")
    
    manifest_path = Path("homeassistant/components/xcc/manifest.json")
    try:
        with open(manifest_path) as f:
            manifest = json.load(f)
        
        required_keys = ["domain", "name", "config_flow", "integration_type", "iot_class"]
        for key in required_keys:
            if key not in manifest:
                print(f"  ❌ Missing required key: {key}")
                return False
            print(f"  ✓ {key}: {manifest[key]}")
        
        print("  ✅ Manifest structure valid")
        return True
        
    except Exception as e:
        print(f"  ❌ Error reading manifest: {e}")
        return False

def test_imports():
    """Test that modules can be imported."""
    print("\n🔍 Testing module imports...")
    
    try:
        # Test XCC client import
        from homeassistant.components.xcc import xcc_client
        print("  ✓ xcc_client imported")
        
        # Test const import
        from homeassistant.components.xcc import const
        print("  ✓ const imported")
        
        # Test coordinator import
        from homeassistant.components.xcc import coordinator
        print("  ✓ coordinator imported")
        
        # Test entity import
        from homeassistant.components.xcc import entity
        print("  ✓ entity imported")
        
        print("  ✅ All modules imported successfully")
        return True
        
    except Exception as e:
        print(f"  ❌ Import error: {e}")
        return False

def test_translations():
    """Test translation files."""
    print("\n🔍 Testing translations...")
    
    try:
        # Test English strings
        strings_path = Path("homeassistant/components/xcc/strings.json")
        with open(strings_path) as f:
            en_strings = json.load(f)
        print("  ✓ English strings loaded")
        
        # Test Czech translations
        cs_path = Path("homeassistant/components/xcc/translations/cs.json")
        with open(cs_path) as f:
            cs_strings = json.load(f)
        print("  ✓ Czech translations loaded")
        
        # Check that both have config section
        if "config" not in en_strings or "config" not in cs_strings:
            print("  ❌ Missing config section in translations")
            return False
        
        print("  ✅ Translation files valid")
        return True
        
    except Exception as e:
        print(f"  ❌ Translation error: {e}")
        return False

async def test_xcc_client():
    """Test XCC client functionality."""
    print("\n🔍 Testing XCC client...")
    
    try:
        from homeassistant.components.xcc.xcc_client import XCCClient, parse_xml_entities
        
        # Test client creation
        client = XCCClient(ip="192.168.1.100", username="test", password="test")
        print("  ✓ XCC client created")
        
        # Test XML parsing with sample data
        sample_xml = '''<?xml version="1.0" encoding="UTF-8"?>
        <root>
            <INPUT P="TEST_PARAM" VALUE="123" />
        </root>'''
        
        entities = parse_xml_entities(sample_xml, "test.xml")
        print(f"  ✓ XML parsing works, found {len(entities)} entities")
        
        print("  ✅ XCC client functionality verified")
        return True
        
    except Exception as e:
        print(f"  ❌ XCC client error: {e}")
        return False

def test_config_flow():
    """Test config flow structure."""
    print("\n🔍 Testing config flow...")
    
    try:
        from homeassistant.components.xcc.config_flow import XCCConfigFlow
        
        # Check that config flow has required methods
        required_methods = ["async_step_user"]
        for method in required_methods:
            if not hasattr(XCCConfigFlow, method):
                print(f"  ❌ Missing method: {method}")
                return False
            print(f"  ✓ {method} method exists")
        
        print("  ✅ Config flow structure valid")
        return True
        
    except Exception as e:
        print(f"  ❌ Config flow error: {e}")
        return False

async def main():
    """Run all tests."""
    print("🚀 Starting XCC Home Assistant Integration Tests\n")
    
    tests = [
        ("Integration Structure", test_integration_structure),
        ("Manifest", test_manifest),
        ("Module Imports", test_imports),
        ("Translations", test_translations),
        ("XCC Client", test_xcc_client),
        ("Config Flow", test_config_flow),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            if result:
                passed += 1
        except Exception as e:
            print(f"  ❌ Test {test_name} failed with exception: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The XCC integration is ready for testing.")
        return True
    else:
        print("❌ Some tests failed. Please fix the issues before proceeding.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
