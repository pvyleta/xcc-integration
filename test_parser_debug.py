#!/usr/bin/env python3
"""Debug the XML parser with specific test cases."""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from custom_components.xcc.xcc_client import parse_xml_entities


def test_input_format():
    """Test the INPUT format parsing."""
    print("🧪 Testing INPUT Format Parsing")
    print("=" * 40)
    
    # Test with simple INPUT format
    test_xml = '''<?xml version="1.0" encoding="windows-1250" ?>
<PAGE>
<INPUT P="SVENKU" NAME="__R3254_REAL_.1f" VALUE="29.0"/>
<INPUT P="TCSTAV0-FANH" NAME="__R1830_INT_d" VALUE="0"/>
<INPUT P="SZAPNUTO" NAME="__R38578.0_BOOL_i" VALUE="1"/>
</PAGE>'''
    
    print("📝 Test XML:")
    print(test_xml)
    
    entities = parse_xml_entities(test_xml, "test.xml")
    print(f"\n📈 Parsed {len(entities)} entities:")
    
    for entity in entities:
        print(f"  - {entity.get('field_name')}: {entity.get('value')} ({entity.get('type')})")
        print(f"    ID: {entity.get('entity_id')}")
        if entity.get('unit_of_measurement'):
            print(f"    Unit: {entity.get('unit_of_measurement')}")


def test_real_stavjed1():
    """Test with real STAVJED1.XML file."""
    print(f"\n🧪 Testing Real STAVJED1.XML")
    print("=" * 40)
    
    try:
        # Try different encodings
        encodings = ['windows-1250', 'utf-8', 'iso-8859-1']
        xml_content = None
        
        for encoding in encodings:
            try:
                with open("xcc_data/STAVJED1.XML", 'r', encoding=encoding) as f:
                    xml_content = f.read()
                print(f"✅ Successfully read with {encoding} encoding")
                break
            except UnicodeDecodeError:
                continue
        
        if xml_content is None:
            print("❌ Could not read file")
            return
        
        print(f"📊 File length: {len(xml_content)} bytes")
        
        # Count INPUT elements
        input_count = xml_content.count('<INPUT')
        print(f"📋 Found {input_count} INPUT elements")
        
        # Parse entities
        entities = parse_xml_entities(xml_content, "STAVJED1.XML")
        print(f"📈 Parsed {len(entities)} entities")
        
        if entities:
            print("✅ Sample entities:")
            for i, entity in enumerate(entities[:10]):  # Show first 10
                print(f"  {i+1}. {entity.get('field_name')}: {entity.get('value')} ({entity.get('type')})")
        else:
            print("❌ No entities parsed - debugging...")
            
            # Check XML structure
            from lxml import etree
            try:
                root = etree.fromstring(xml_content.encode())
                print("✅ XML is valid")
                
                # Check for INPUT elements
                input_elements = root.xpath(".//INPUT[@P and @VALUE]")
                print(f"📋 XPath found {len(input_elements)} INPUT elements with P and VALUE")
                
                if input_elements:
                    print("📝 Sample INPUT elements:")
                    for i, elem in enumerate(input_elements[:5]):
                        p_val = elem.get("P")
                        value_val = elem.get("VALUE")
                        print(f"  {i+1}. P='{p_val}' VALUE='{value_val}'")
                
            except Exception as e:
                print(f"❌ XML parsing error: {e}")
        
    except Exception as e:
        print(f"❌ Error: {e}")


def test_xpath_directly():
    """Test XPath expressions directly."""
    print(f"\n🧪 Testing XPath Expressions")
    print("=" * 40)
    
    test_xml = '''<?xml version="1.0" encoding="windows-1250" ?>
<PAGE>
<INPUT P="TEST1" NAME="test" VALUE="123"/>
<INPUT P="TEST2" VALUE="456"/>
<INPUT P="TEST3" NAME="test"/>
</PAGE>'''
    
    from lxml import etree
    
    try:
        root = etree.fromstring(test_xml.encode())
        
        # Test different XPath expressions
        xpath_tests = [
            ".//INPUT",
            ".//INPUT[@P]",
            ".//INPUT[@VALUE]", 
            ".//INPUT[@P and @VALUE]",
        ]
        
        for xpath in xpath_tests:
            elements = root.xpath(xpath)
            print(f"📋 XPath '{xpath}': {len(elements)} elements")
            
            for elem in elements:
                p_val = elem.get("P", "None")
                value_val = elem.get("VALUE", "None")
                print(f"    P='{p_val}' VALUE='{value_val}'")
    
    except Exception as e:
        print(f"❌ XPath test error: {e}")


if __name__ == "__main__":
    test_input_format()
    test_real_stavjed1()
    test_xpath_directly()
