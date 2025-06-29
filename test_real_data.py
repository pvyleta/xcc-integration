#!/usr/bin/env python3
"""Test XML parsing with real XCC data from sample_data folder."""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from custom_components.xcc.xcc_client import parse_xml_entities


def test_real_xcc_data():
    """Test XML parsing with real XCC data."""
    print("🧪 Testing Real XCC Data from sample_data/")
    print("=" * 50)
    
    # Test files from your real XCC controller
    test_files = [
        "sample_data/STAVJED1.XML",
        "sample_data/OKRUH10.XML", 
        "sample_data/TUV11.XML",
        "sample_data/BIV1.XML",
        "sample_data/FVE4.XML",
        "sample_data/SPOT1.XML"
    ]
    
    total_entities = 0
    
    for file_path in test_files:
        print(f"\n📄 Testing: {file_path}")
        print("-" * 40)
        
        try:
            # Try different encodings for your real data
            encodings = ['windows-1250', 'utf-8', 'iso-8859-1']
            xml_content = None
            used_encoding = None
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        xml_content = f.read()
                    used_encoding = encoding
                    break
                except UnicodeDecodeError:
                    continue
            
            if xml_content is None:
                print(f"❌ Could not decode file with any encoding")
                continue
            
            print(f"✅ Read with {used_encoding} encoding")
            print(f"📊 File size: {len(xml_content)} bytes")
            
            # Count INPUT elements
            input_count = xml_content.count('<INPUT')
            print(f"📋 Found {input_count} INPUT elements")
            
            # Parse entities
            entities = parse_xml_entities(xml_content, file_path)
            print(f"📈 Parsed {len(entities)} entities")
            total_entities += len(entities)
            
            if entities:
                print("✅ Sample entities:")
                for i, entity in enumerate(entities[:5]):  # Show first 5
                    field_name = entity.get('field_name', 'Unknown')
                    value = entity.get('value', 'N/A')
                    entity_type = entity.get('type', 'unknown')
                    unit = entity.get('unit_of_measurement', '')
                    unit_str = f" {unit}" if unit else ""
                    print(f"  {i+1}. {field_name}: {value}{unit_str} ({entity_type})")
                
                if len(entities) > 5:
                    print(f"  ... and {len(entities) - 5} more entities")
            else:
                print("❌ No entities parsed")
                
                # Debug why no entities were found
                if input_count > 0:
                    print("🔍 Debugging: Found INPUT elements but no entities parsed")
                    
                    # Check first few INPUT elements manually
                    lines = xml_content.split('\n')
                    input_lines = [line for line in lines if '<INPUT' in line][:3]
                    
                    print("📝 Sample INPUT lines:")
                    for line in input_lines:
                        print(f"    {line.strip()}")
                        
        except FileNotFoundError:
            print(f"❌ File not found: {file_path}")
        except Exception as e:
            print(f"❌ Error processing {file_path}: {e}")
    
    print(f"\n📊 Summary: Found {total_entities} total entities across all files")
    
    if total_entities == 0:
        print("\n❌ No entities found in any file - this explains why your integration shows no devices!")
        print("🔍 Let's debug the parser...")
        debug_parser()
    else:
        print(f"\n✅ Parser is working! Your integration should show {total_entities} entities")


def debug_parser():
    """Debug the parser with a simple test case."""
    print(f"\n🔧 Debugging Parser")
    print("=" * 30)
    
    # Test with a simple case from your real data
    test_xml = '''<?xml version="1.0" encoding="windows-1250" ?>
<PAGE>
<INPUT P="SVENKU" NAME="__R3254_REAL_.1f" VALUE="13.0"/>
<INPUT P="SZAPNUTO" NAME="__R38578.0_BOOL_i" VALUE="1"/>
</PAGE>'''
    
    print("📝 Testing with simplified real data format:")
    print(test_xml)
    
    entities = parse_xml_entities(test_xml, "debug.xml")
    print(f"\n📈 Result: {len(entities)} entities")
    
    if entities:
        for entity in entities:
            print(f"  - {entity}")
    else:
        print("❌ Still no entities - there's a bug in the parser")
        
        # Test XPath manually
        from lxml import etree
        try:
            root = etree.fromstring(test_xml.encode())
            input_elements = root.xpath(".//INPUT[@P and @VALUE]")
            print(f"🔍 XPath found {len(input_elements)} INPUT elements")
            
            for elem in input_elements:
                p_val = elem.get("P")
                value_val = elem.get("VALUE")
                print(f"    P='{p_val}' VALUE='{value_val}'")
                
        except Exception as e:
            print(f"❌ XPath test failed: {e}")


def test_cli_with_real_data():
    """Test CLI tool with real data."""
    print(f"\n🔧 Testing CLI Tool with Real Data")
    print("=" * 40)
    
    # Test CLI parsing function directly
    try:
        from xcc_client import parse_xml_entities as cli_parse_xml_entities
        
        # Test with your real STAVJED1.XML
        with open("sample_data/STAVJED1.XML", 'r', encoding='windows-1250') as f:
            xml_content = f.read()
        
        cli_entities = cli_parse_xml_entities(xml_content, "STAVJED1.XML")
        print(f"📈 CLI parser found {len(cli_entities)} entities")
        
        if cli_entities:
            print("✅ CLI parser sample entities:")
            for i, entity in enumerate(cli_entities[:5]):
                print(f"  {i+1}. {entity}")
        
        # Compare with integration parser
        from custom_components.xcc.xcc_client import parse_xml_entities as integration_parse_xml_entities
        integration_entities = integration_parse_xml_entities(xml_content, "STAVJED1.XML")
        
        print(f"\n📊 Comparison:")
        print(f"  CLI parser: {len(cli_entities)} entities")
        print(f"  Integration parser: {len(integration_entities)} entities")
        
        if len(cli_entities) != len(integration_entities):
            print("⚠️  Parsers return different results!")
        else:
            print("✅ Both parsers return same number of entities")
            
    except ImportError:
        print("❌ Could not import CLI parser")
    except Exception as e:
        print(f"❌ CLI test error: {e}")


if __name__ == "__main__":
    test_real_xcc_data()
    test_cli_with_real_data()
