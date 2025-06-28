#!/usr/bin/env python3
"""Validation script for XCC Home Assistant integration."""

import json
import os
import ast
from pathlib import Path

def validate_python_syntax(file_path):
    """Validate Python file syntax."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        ast.parse(content)
        return True, None
    except SyntaxError as e:
        return False, f"Syntax error: {e}"
    except Exception as e:
        return False, f"Error: {e}"

def validate_json_syntax(file_path):
    """Validate JSON file syntax."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            json.load(f)
        return True, None
    except json.JSONDecodeError as e:
        return False, f"JSON error: {e}"
    except Exception as e:
        return False, f"Error: {e}"

def main():
    """Run validation."""
    print("🔍 Validating XCC Home Assistant Integration\n")
    
    base_path = Path("homeassistant/components/xcc")
    
    # Python files to validate
    python_files = [
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
        "mqtt_discovery.py",
        "xcc_client.py",
    ]
    
    # JSON files to validate
    json_files = [
        "manifest.json",
        "strings.json",
        "translations/cs.json",
    ]
    
    errors = []
    
    print("📝 Validating Python files...")
    for file_name in python_files:
        file_path = base_path / file_name
        if file_path.exists():
            valid, error = validate_python_syntax(file_path)
            if valid:
                print(f"  ✓ {file_name}")
            else:
                print(f"  ❌ {file_name}: {error}")
                errors.append(f"{file_name}: {error}")
        else:
            print(f"  ❌ {file_name}: File not found")
            errors.append(f"{file_name}: File not found")
    
    print("\n📋 Validating JSON files...")
    for file_name in json_files:
        file_path = base_path / file_name
        if file_path.exists():
            valid, error = validate_json_syntax(file_path)
            if valid:
                print(f"  ✓ {file_name}")
            else:
                print(f"  ❌ {file_name}: {error}")
                errors.append(f"{file_name}: {error}")
        else:
            print(f"  ❌ {file_name}: File not found")
            errors.append(f"{file_name}: File not found")
    
    # Validate manifest structure
    print("\n🔧 Validating manifest structure...")
    manifest_path = base_path / "manifest.json"
    try:
        with open(manifest_path) as f:
            manifest = json.load(f)
        
        required_fields = {
            "domain": str,
            "name": str,
            "config_flow": bool,
            "integration_type": str,
            "iot_class": str,
            "requirements": list,
        }
        
        for field, expected_type in required_fields.items():
            if field not in manifest:
                error = f"Missing required field: {field}"
                print(f"  ❌ {error}")
                errors.append(error)
            elif not isinstance(manifest[field], expected_type):
                error = f"Field {field} should be {expected_type.__name__}, got {type(manifest[field]).__name__}"
                print(f"  ❌ {error}")
                errors.append(error)
            else:
                print(f"  ✓ {field}: {manifest[field]}")
                
    except Exception as e:
        error = f"Error validating manifest: {e}"
        print(f"  ❌ {error}")
        errors.append(error)
    
    # Summary
    print(f"\n📊 Validation Summary:")
    if errors:
        print(f"❌ Found {len(errors)} errors:")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print("✅ All validations passed!")
        print("\n🎉 The XCC integration structure is valid and ready for Home Assistant!")
        print("\n📋 Next steps:")
        print("  1. Copy the homeassistant/components/xcc directory to your Home Assistant custom_components folder")
        print("  2. Restart Home Assistant")
        print("  3. Go to Settings > Devices & Services > Add Integration")
        print("  4. Search for 'XCC Heat Pump Controller'")
        print("  5. Configure with your XCC controller IP and credentials")
        return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
