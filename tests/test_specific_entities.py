"""Test specific entities that are showing wrong names."""

import sys
import os
import logging

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Set up logging to see debug messages
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(name)s - %(message)s')

try:
    from custom_components.xcc.descriptor_parser import DescriptorParser
except ImportError:
    # Skip this test if Home Assistant dependencies are not available
    import pytest
    pytest.skip("Home Assistant dependencies not available", allow_module_level=True)

def test_specific_entities():
    """Test specific entities that should have Czech translations."""
    
    print("🔍 TESTING SPECIFIC ENTITIES WITH DEBUG LOGGING")
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
            # Parse the descriptor file
            with open(xml_file, 'r', encoding='utf-8') as f:
                xml_content = f.read()
            
            page_name = xml_file.split('/')[-1].replace('.XML', '').lower()
            
            # Parse the XML and get entity configs
            entity_configs = parser.parse_descriptor_xml(xml_content, page_name)
            
            # Find the specific entity
            entity_config = None
            for config in entity_configs:
                if config['prop'] == prop:
                    entity_config = config
                    break
            
            if entity_config:
                print(f"   ✅ Entity config found:")
                print(f"      prop: '{entity_config['prop']}'")
                print(f"      friendly_name: '{entity_config['friendly_name']}'")
                print(f"      friendly_name_en: '{entity_config['friendly_name_en']}'")
                print(f"      page: '{entity_config['page']}'")
                print(f"      writable: {entity_config['writable']}")
                
                # Check if the names are correct
                if entity_config['friendly_name'] != entity_config['friendly_name_en']:
                    print(f"   ✅ Different Czech and English names - GOOD!")
                else:
                    print(f"   ❌ Same Czech and English names - BAD!")
                    print(f"      Both are: '{entity_config['friendly_name']}'")
            else:
                print(f"   ❌ No entity config found for {prop}")
                
        except Exception as e:
            print(f"   ❌ Error processing {prop}: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n🎉 SPECIFIC ENTITIES TEST COMPLETED!")

if __name__ == "__main__":
    test_specific_entities()
