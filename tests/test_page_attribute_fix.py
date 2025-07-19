"""Test page attribute fix."""

def test_page_attribute_in_parse_xml_entities():
    """Test that parse_xml_entities sets the correct page attribute."""
    
    print("🔍 TESTING PAGE ATTRIBUTE IN PARSE_XML_ENTITIES")
    print("=" * 70)
    
    try:
        # Import the function
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'custom_components', 'xcc'))
        
        from xcc_client import parse_xml_entities
        
        # Mock XML content with INPUT elements
        mock_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<root>
    <INPUT P="SVENKU" VALUE="24.5" NAME="SVENKU_REAL_"/>
    <INPUT P="FVE-CONFIG-ENABLED" VALUE="1" NAME="FVE_CONFIG_ENABLED"/>
</root>'''
        
        # Test different page names
        test_cases = [
            ("STAVJED1.XML", "STAVJED"),
            ("FVE4.XML", "FVE"),
            ("OKRUH10.XML", "OKRUH"),
        ]
        
        for page_name, expected_device in test_cases:
            print(f"\n📄 Testing page: {page_name}")
            
            # Parse entities
            entities = parse_xml_entities(mock_xml, page_name, "xcc")
            
            print(f"   Found {len(entities)} entities")
            
            # Check that all entities have the correct page attribute
            for entity in entities:
                prop = entity["attributes"]["field_name"]
                page_attr = entity["attributes"].get("page")
                
                print(f"   Entity {prop}: page='{page_attr}'")
                
                # Verify page attribute is set correctly
                assert page_attr == page_name, f"Entity {prop} has wrong page: expected '{page_name}', got '{page_attr}'"
        
        print(f"\n✅ All entities have correct page attributes")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_page_attribute_in_parse_xml_entities()
    
    if success:
        print("\n🎉 PAGE ATTRIBUTE TEST PASSED!")
    else:
        print("\n❌ PAGE ATTRIBUTE TEST FAILED!")
        exit(1)
