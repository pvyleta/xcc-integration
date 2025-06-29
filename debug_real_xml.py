#!/usr/bin/env python3
"""Debug real XML structure to find why parsing fails."""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def debug_xml_structure():
    """Debug the XML structure of real files."""
    print("🔍 Debugging Real XML Structure")
    print("=" * 40)
    
    try:
        with open("sample_data/STAVJED1.XML", 'r', encoding='windows-1250') as f:
            xml_content = f.read()
        
        print(f"📊 File length: {len(xml_content)} bytes")
        
        # Test XML parsing
        from lxml import etree
        
        try:
            root = etree.fromstring(xml_content.encode('windows-1250'))
            print("✅ XML parsing successful")
            
            # Test different XPath expressions
            xpath_tests = [
                (".//INPUT", "All INPUT elements"),
                (".//INPUT[@P]", "INPUT with P attribute"),
                (".//INPUT[@VALUE]", "INPUT with VALUE attribute"),
                (".//INPUT[@P and @VALUE]", "INPUT with both P and VALUE"),
            ]
            
            for xpath, description in xpath_tests:
                elements = root.xpath(xpath)
                print(f"📋 {description}: {len(elements)} elements")
                
                if elements and len(elements) <= 3:
                    for i, elem in enumerate(elements):
                        p_val = elem.get("P", "None")
                        value_val = elem.get("VALUE", "None")
                        name_val = elem.get("NAME", "None")
                        print(f"    {i+1}. P='{p_val}' VALUE='{value_val}' NAME='{name_val}'")
                elif elements:
                    # Show first 3
                    for i, elem in enumerate(elements[:3]):
                        p_val = elem.get("P", "None")
                        value_val = elem.get("VALUE", "None")
                        print(f"    {i+1}. P='{p_val}' VALUE='{value_val}'")
                    print(f"    ... and {len(elements) - 3} more")
            
            # Test the exact parser logic
            print(f"\n🔧 Testing Parser Logic Step by Step")
            
            # Get INPUT elements with P and VALUE
            input_elements = root.xpath(".//INPUT[@P and @VALUE]")
            print(f"📋 Found {len(input_elements)} INPUT elements with P and VALUE")
            
            if input_elements:
                print("🔍 Processing first few elements:")
                
                for i, elem in enumerate(input_elements[:5]):
                    prop = elem.get("P")
                    value = elem.get("VALUE")
                    
                    print(f"  Element {i+1}:")
                    print(f"    P attribute: '{prop}'")
                    print(f"    VALUE attribute: '{value}'")
                    print(f"    prop is None: {prop is None}")
                    print(f"    value is None: {value is None}")
                    print(f"    prop empty: {not prop if prop is not None else 'N/A'}")
                    print(f"    value empty: {not value if value is not None else 'N/A'}")
                    
                    # Check the conditions in the parser
                    if not prop:
                        print(f"    ❌ Skipped: prop is empty")
                        continue
                    if not value:
                        print(f"    ❌ Skipped: value is empty")
                        continue
                    
                    print(f"    ✅ Should be processed")
                    
                    # Generate entity_id like the parser does
                    entity_id = f"xcc_{prop.lower().replace('-', '_')}"
                    print(f"    Entity ID: {entity_id}")
            
        except Exception as e:
            print(f"❌ XML parsing failed: {e}")
            
            # Show raw content around first INPUT
            lines = xml_content.split('\n')
            input_line_idx = None
            for i, line in enumerate(lines):
                if '<INPUT' in line:
                    input_line_idx = i
                    break
            
            if input_line_idx is not None:
                print(f"\n📝 Raw content around first INPUT (line {input_line_idx + 1}):")
                start = max(0, input_line_idx - 2)
                end = min(len(lines), input_line_idx + 3)
                for i in range(start, end):
                    marker = ">>> " if i == input_line_idx else "    "
                    print(f"{marker}{i+1:3d}: {lines[i]}")
        
    except Exception as e:
        print(f"❌ Error reading file: {e}")


def test_parser_directly():
    """Test the parser function directly with real data."""
    print(f"\n🧪 Testing Parser Function Directly")
    print("=" * 40)
    
    try:
        from custom_components.xcc.xcc_client import parse_xml_entities
        
        with open("sample_data/STAVJED1.XML", 'r', encoding='windows-1250') as f:
            xml_content = f.read()
        
        print("📝 Calling parse_xml_entities...")
        
        # Add some debug prints to see what happens
        entities = parse_xml_entities(xml_content, "STAVJED1.XML")
        
        print(f"📈 Result: {len(entities)} entities")
        
        if entities:
            for entity in entities:
                print(f"  - {entity}")
        else:
            print("❌ No entities returned")
            
            # Let's manually step through the parser logic
            print("\n🔍 Manual parser debugging:")
            
            from lxml import etree
            
            try:
                root = etree.fromstring(xml_content.encode())
                print("✅ XML root parsed")
                
                # Check Format 1: XCC Values format
                input_elements = root.xpath(".//INPUT[@P and @VALUE]")
                print(f"📋 Format 1 (INPUT): Found {len(input_elements)} elements")
                
                if input_elements:
                    print("🔍 Processing INPUT elements:")
                    processed = 0
                    
                    for i, elem in enumerate(input_elements[:3]):  # Check first 3
                        prop = elem.get("P")
                        value = elem.get("VALUE")
                        
                        print(f"  Element {i+1}: P='{prop}' VALUE='{value}'")
                        
                        if not prop:
                            print(f"    ❌ Skipped: no prop")
                            continue
                        if not value:
                            print(f"    ❌ Skipped: no value")
                            continue
                        
                        print(f"    ✅ Would process this element")
                        processed += 1
                    
                    print(f"📊 Should have processed {processed} elements")
                    
                    if processed > 0:
                        print("⚠️  Parser should have found entities but didn't!")
                        print("🔍 There might be an exception in the parser")
                
                # Check Format 2: prop attributes
                prop_elements = root.xpath(".//*[@prop and text()]")
                print(f"📋 Format 2 (prop): Found {len(prop_elements)} elements")
                
            except Exception as e:
                print(f"❌ Manual debugging failed: {e}")
        
    except Exception as e:
        print(f"❌ Parser test failed: {e}")


if __name__ == "__main__":
    debug_xml_structure()
    test_parser_directly()
