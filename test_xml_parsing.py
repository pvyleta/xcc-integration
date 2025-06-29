#!/usr/bin/env python3
"""Test XML parsing with sample data to debug the integration."""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from custom_components.xcc.xcc_client import parse_xml_entities


def test_sample_xml_files():
    """Test XML parsing with sample files."""
    print("🧪 Testing XML Parsing with Sample Files")
    print("=" * 50)
    
    # Test files to check
    test_files = [
        ("mock_data/stavjed.xml", "Mock data format"),
        ("xcc_data/STAVJED.XML", "Real XCC format"),
        ("xcc_data/STAVJED1.XML", "Real XCC values format"),
    ]
    
    for file_path, description in test_files:
        print(f"\n📄 Testing: {file_path} ({description})")
        print("-" * 40)
        
        try:
            # Try different encodings
            encodings = ['utf-8', 'windows-1250', 'iso-8859-1']
            xml_content = None

            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        xml_content = f.read()
                    break
                except UnicodeDecodeError:
                    continue

            if xml_content is None:
                print(f"❌ Could not decode file with any encoding")
                continue
            
            print(f"📊 File size: {len(xml_content)} bytes")
            print(f"📝 First 200 chars: {xml_content[:200]}...")
            
            # Parse entities
            entities = parse_xml_entities(xml_content, file_path)
            print(f"📈 Parsed entities: {len(entities)}")
            
            if entities:
                print("✅ Sample entities found:")
                for i, entity in enumerate(entities[:5]):  # Show first 5
                    print(f"  {i+1}. {entity.get('field_name', 'Unknown')}: {entity.get('value', 'N/A')} ({entity.get('type', 'unknown')})")
                if len(entities) > 5:
                    print(f"  ... and {len(entities) - 5} more entities")
            else:
                print("❌ No entities parsed - analyzing why...")
                
                # Check for XML structure
                if "<" in xml_content and ">" in xml_content:
                    print("✅ Contains XML tags")
                    
                    # Check for prop attributes (what parser looks for)
                    if 'prop="' in xml_content:
                        print("✅ Contains 'prop' attributes")
                        
                        # Count prop attributes
                        prop_count = xml_content.count('prop="')
                        print(f"📊 Found {prop_count} 'prop' attributes")
                        
                        # Show some prop examples
                        import re
                        props = re.findall(r'prop="([^"]*)"', xml_content)
                        if props:
                            print(f"📋 Sample props: {props[:5]}")
                    else:
                        print("❌ No 'prop' attributes found")
                        
                        # Check for other patterns
                        patterns = ["<P>", "<ITEM>", "<NAME>", "<VALUE>"]
                        found = [p for p in patterns if p in xml_content]
                        if found:
                            print(f"📋 Found other patterns: {found}")
                else:
                    print("❌ Not valid XML format")
                    
        except FileNotFoundError:
            print(f"❌ File not found: {file_path}")
        except Exception as e:
            print(f"❌ Error processing file: {e}")


def test_empty_xml():
    """Test what happens with empty or minimal XML."""
    print(f"\n🧪 Testing Edge Cases")
    print("=" * 30)
    
    test_cases = [
        ("", "Empty string"),
        ("<?xml version='1.0'?><root></root>", "Empty XML"),
        ("<?xml version='1.0'?><root><item prop='test'>value</item></root>", "Simple XML with prop"),
        ("Not XML at all", "Non-XML content"),
        ("Error: 404 Not Found", "Error response"),
    ]
    
    for xml_content, description in test_cases:
        print(f"\n📝 Testing: {description}")
        entities = parse_xml_entities(xml_content, "test.xml")
        print(f"📈 Result: {len(entities)} entities")
        
        if entities:
            for entity in entities:
                print(f"  - {entity.get('field_name')}: {entity.get('value')}")


def analyze_xcc_data_format():
    """Analyze the XCC data format in detail."""
    print(f"\n🔍 Analyzing XCC Data Format")
    print("=" * 40)
    
    try:
        with open("xcc_data/STAVJED.XML", 'r', encoding='utf-8') as f:
            xml_content = f.read()
        
        print(f"📊 Total length: {len(xml_content)} bytes")
        
        # Count different elements
        import re
        
        # Count prop attributes
        props = re.findall(r'prop="([^"]*)"', xml_content)
        print(f"📋 Total prop attributes: {len(props)}")
        
        # Show unique prop names
        unique_props = list(set(props))[:10]  # First 10 unique
        print(f"📋 Sample prop names: {unique_props}")
        
        # Count different element types
        elements = re.findall(r'<(\w+)', xml_content)
        element_counts = {}
        for elem in elements:
            element_counts[elem] = element_counts.get(elem, 0) + 1
        
        print(f"📊 Element counts: {element_counts}")
        
        # Look for text content in elements with props
        prop_elements = re.findall(r'<\w+[^>]*prop="([^"]*)"[^>]*>([^<]*)</\w+>', xml_content)
        print(f"📋 Elements with prop and text content: {len(prop_elements)}")
        
        if prop_elements:
            print("📝 Sample prop elements with content:")
            for prop, content in prop_elements[:5]:
                print(f"  - {prop}: '{content.strip()}'")
        
    except Exception as e:
        print(f"❌ Error analyzing XCC data: {e}")


if __name__ == "__main__":
    test_sample_xml_files()
    test_empty_xml()
    analyze_xcc_data_format()
