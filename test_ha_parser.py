#!/usr/bin/env python3
"""Test if Home Assistant has the updated parser."""

import sys
import os

# Add Home Assistant custom components path
ha_custom_path = "/config/custom_components"
if os.path.exists(ha_custom_path):
    sys.path.insert(0, ha_custom_path)

def test_ha_parser():
    """Test if HA has the updated parser."""
    print("🔍 Testing Home Assistant Parser")
    print("=" * 40)
    
    try:
        # Try to import from HA custom components
        from xcc.xcc_client import parse_xml_entities
        
        # Test with sample INPUT format
        test_xml = '''<?xml version="1.0" encoding="windows-1250" ?>
<PAGE>
<INPUT P="SVENKU" NAME="__R3254_REAL_.1f" VALUE="13.0"/>
<INPUT P="SZAPNUTO" NAME="__R38578.0_BOOL_i" VALUE="1"/>
</PAGE>'''
        
        print("📝 Testing with sample XML...")
        entities = parse_xml_entities(test_xml, "test.xml")
        
        print(f"📈 Result: {len(entities)} entities")
        
        if entities:
            print("✅ Parser is working! Found entities:")
            for entity in entities:
                print(f"  - {entity.get('field_name')}: {entity.get('value')} ({entity.get('type')})")
            print("\n🎉 The fix is applied in Home Assistant!")
        else:
            print("❌ Parser still returns 0 entities")
            print("💡 The updated code is not loaded in Home Assistant")
            
            # Check if the file has the fix
            try:
                import inspect
                source = inspect.getsource(parse_xml_entities)
                if "windows-1250" in source:
                    print("✅ Source code contains the encoding fix")
                    print("⚠️  But parser still fails - there might be another issue")
                else:
                    print("❌ Source code does not contain the encoding fix")
                    print("💡 Home Assistant is using old version")
            except:
                print("❓ Could not check source code")
        
    except ImportError as e:
        print(f"❌ Could not import parser: {e}")
        print("💡 Make sure you're running this from Home Assistant environment")
    except Exception as e:
        print(f"❌ Test failed: {e}")


def check_file_version():
    """Check if the file has been updated."""
    print(f"\n🔍 Checking File Version")
    print("=" * 30)
    
    file_path = "/config/custom_components/xcc/xcc_client.py"
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check for the encoding fix
        if "windows-1250" in content:
            print("✅ File contains encoding fix")
        else:
            print("❌ File does not contain encoding fix")
            print("💡 Need to update the file manually")
        
        # Check for INPUT parsing
        if "INPUT[@P and @VALUE]" in content:
            print("✅ File contains INPUT format parsing")
        else:
            print("❌ File does not contain INPUT format parsing")
        
        # Show file modification time
        import os
        mtime = os.path.getmtime(file_path)
        import datetime
        mod_time = datetime.datetime.fromtimestamp(mtime)
        print(f"📅 File last modified: {mod_time}")
        
    except Exception as e:
        print(f"❌ Could not check file: {e}")


if __name__ == "__main__":
    test_ha_parser()
    check_file_version()
