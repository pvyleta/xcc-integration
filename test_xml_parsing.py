"""Test XML parsing to understand the structure."""

import xml.etree.ElementTree as ET

def test_xml_structure():
    """Test XML structure to understand how entities are organized."""
    
    print("🔍 TESTING XML STRUCTURE")
    print("=" * 70)
    
    # Test entities that should have Czech translations
    test_entities = [
        ("TCSTAV4-PROUD", "sample_data/STAVJED.XML"),
        ("TCSTAV7-PRIKON", "sample_data/STAVJED.XML"),
        ("TO-SPOT-STOPENABLED", "sample_data/OKRUH.XML"),
    ]
    
    for prop, xml_file in test_entities:
        print(f"\n📋 TESTING: {prop} from {xml_file}")
        
        try:
            # Parse the XML file
            with open(xml_file, 'r', encoding='utf-8') as f:
                xml_content = f.read()
            
            root = ET.fromstring(xml_content)
            
            # Find the element with this prop
            element = None
            for elem in root.iter():
                if elem.get("prop") == prop:
                    element = elem
                    break
            
            if element is None:
                print(f"   ❌ Element with prop='{prop}' not found in {xml_file}")
                continue
            
            print(f"   Found element: <{element.tag} prop='{prop}'>")
            print(f"   Element attributes: {dict(element.attrib)}")
            
            # Find parent row
            parent_row = None
            for row in root.iter("row"):
                if element in list(row.iter()):
                    parent_row = row
                    break
            
            if parent_row is not None:
                print(f"   Parent row attributes: {dict(parent_row.attrib)}")
                row_text = parent_row.get("text", "")
                row_text_en = parent_row.get("text_en", "")
                print(f"   Row text: '{row_text}'")
                print(f"   Row text_en: '{row_text_en}'")
                
                # Look for labels in the row
                labels = list(parent_row.iter("label"))
                if labels:
                    print(f"   Found {len(labels)} labels in row:")
                    for i, label in enumerate(labels):
                        label_text = label.get("text", "")
                        label_text_en = label.get("text_en", "")
                        print(f"     Label {i+1}: text='{label_text}', text_en='{label_text_en}'")
            else:
                print(f"   ❌ No parent row found")
                
        except Exception as e:
            print(f"   ❌ Error processing {prop}: {e}")
    
    print(f"\n🎉 XML STRUCTURE TEST COMPLETED!")

if __name__ == "__main__":
    test_xml_structure()
