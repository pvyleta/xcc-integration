"""Test descriptor parsing debug."""

import xml.etree.ElementTree as ET
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from custom_components.xcc.descriptor_parser import DescriptorParser
except ImportError:
    # Skip this test if Home Assistant dependencies are not available
    import pytest
    pytest.skip("Home Assistant dependencies not available", allow_module_level=True)

def test_descriptor_parsing_debug():
    """Test descriptor parsing with debug output for specific entities."""
    
    print("🔍 TESTING DESCRIPTOR PARSING DEBUG")
    print("=" * 70)
    
    # Test entities that should have Czech translations
    test_entities = [
        ("TCSTAV4-PROUD", "sample_data/STAVJED.XML"),
        ("TCSTAV7-PRIKON", "sample_data/STAVJED.XML"),
        ("TO-SPOT-STOPENABLED", "sample_data/OKRUH.XML"),
    ]
    
    parser = DescriptorParser()
    
    for prop, xml_file in test_entities:
        print(f"\n📋 TESTING: {prop} from {xml_file}")
        
        try:
            # Parse the XML file
            with open(xml_file, 'r', encoding='utf-8') as f:
                xml_content = f.read()
            
            root = ET.fromstring(xml_content)
            page_name = xml_file.split('/')[-1].replace('.XML', '').lower()
            
            # Find the element with this prop
            element = None
            for elem in root.iter():
                if elem.get("prop") == prop:
                    element = elem
                    break
            
            if element is None:
                print(f"   ❌ Element with prop='{prop}' not found in {xml_file}")
                continue
            
            print(f"   Found element: <{element.tag} prop='{prop}' ...>")
            
            # Get the entity config
            entity_config = parser._determine_entity_config(element, page_name)
            
            if entity_config:
                print(f"   ✅ Entity config created:")
                print(f"      friendly_name: '{entity_config['friendly_name']}'")
                print(f"      friendly_name_en: '{entity_config['friendly_name_en']}'")
                print(f"      page: '{entity_config['page']}'")
                print(f"      writable: {entity_config['writable']}")
            else:
                print(f"   ❌ No entity config created")
                
        except Exception as e:
            print(f"   ❌ Error processing {prop}: {e}")
    
    print(f"\n🎉 DESCRIPTOR PARSING DEBUG TEST COMPLETED!")

if __name__ == "__main__":
    test_descriptor_parsing_debug()
