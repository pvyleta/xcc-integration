"""Test XML parsing directly to debug the issue."""

import xml.etree.ElementTree as ET

def find_parent_row(element, root):
    """Find the parent row element."""
    for row in root.iter("row"):
        if element in list(row.iter()):
            return row
    return None

def test_xml_direct():
    """Test XML parsing directly to see what's happening."""
    
    print("🔍 TESTING XML PARSING DIRECTLY")
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
                print(f"   ❌ Element with prop='{prop}' not found")
                continue
            
            print(f"   Found element: <{element.tag} prop='{prop}'>")
            
            # Find parent row
            parent_row = find_parent_row(element, root)
            
            if parent_row is None:
                print(f"   ❌ No parent row found")
                continue
            
            print(f"   Found parent row")
            
            # Extract text values
            text = element.get("text", "")
            text_en = element.get("text_en", "")
            row_text = parent_row.get("text", "")
            row_text_en = parent_row.get("text_en", "")
            label_text = ""
            label_text_en = ""
            
            print(f"   Text extraction:")
            print(f"     element text='{text}', text_en='{text_en}'")
            print(f"     row text='{row_text}', text_en='{row_text_en}'")
            print(f"     label text='{label_text}', text_en='{label_text_en}'")
            
            # Apply the descriptor parsing logic
            # English friendly name - prioritize English text
            friendly_name_en = text_en or label_text_en or row_text_en or text or label_text or row_text or prop

            # Czech friendly name - prioritize Czech text
            friendly_name_cz = text or label_text or row_text or text_en or label_text_en or row_text_en or prop
            
            print(f"   Fallback logic results:")
            print(f"     friendly_name_cz='{friendly_name_cz}'")
            print(f"     friendly_name_en='{friendly_name_en}'")

            # Handle different combinations of row, label, and element text for ENGLISH
            if row_text_en and (text_en or label_text_en):
                # Both row and element/label have English text - combine them
                element_part_en = text_en or label_text_en
                friendly_name_en = f"{row_text_en} - {element_part_en}"
                print(f"   English combination applied: row_text_en + element_part_en")
            elif row_text and (text_en or label_text_en):
                # Row has Czech text, element has English text - use English element with Czech row
                element_part_en = text_en or label_text_en
                friendly_name_en = f"{row_text} - {element_part_en}"
                print(f"   English combination applied: row_text + element_part_en")
            elif row_text_en and (text or label_text):
                # Row has English text, element has Czech text - use Czech element with English row
                element_part_cz = text or label_text
                friendly_name_en = f"{row_text_en} - {element_part_cz}"
                print(f"   English combination applied: row_text_en + element_part_cz")
            elif label_text_en:
                # No row text but label has English text
                friendly_name_en = label_text_en
                print(f"   English combination applied: label_text_en only")
            else:
                print(f"   English combination: No combination applied")

            # Handle different combinations of row, label, and element text for CZECH
            if row_text and (text or label_text):
                # Both row and element/label have Czech text - combine them
                element_part_cz = text or label_text
                friendly_name_cz = f"{row_text} - {element_part_cz}"
                print(f"   Czech combination applied: row_text + element_part_cz")
            elif row_text_en and (text or label_text):
                # Row has English text, element has Czech text - use Czech element with English row
                element_part_cz = text or label_text
                friendly_name_cz = f"{row_text_en} - {element_part_cz}"
                print(f"   Czech combination applied: row_text_en + element_part_cz")
            elif row_text and (text_en or label_text_en):
                # Row has Czech text, element has English text - use English element with Czech row
                element_part_en = text_en or label_text_en
                friendly_name_cz = f"{row_text} - {element_part_en}"
                print(f"   Czech combination applied: row_text + element_part_en")
            elif label_text:
                # No row text but label has Czech text
                friendly_name_cz = label_text
                print(f"   Czech combination applied: label_text only")
            else:
                print(f"   Czech combination: No combination applied")

            # For backward compatibility, set friendly_name to the Czech version
            friendly_name = friendly_name_cz

            print(f"   Final results:")
            print(f"     friendly_name='{friendly_name}' (Czech)")
            print(f"     friendly_name_en='{friendly_name_en}' (English)")
            
            # Check if they're different
            if friendly_name != friendly_name_en:
                print(f"   ✅ Different Czech and English names - GOOD!")
            else:
                print(f"   ❌ Same Czech and English names - BAD!")
                
        except Exception as e:
            print(f"   ❌ Error processing {prop}: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n🎉 XML DIRECT PARSING TEST COMPLETED!")

if __name__ == "__main__":
    test_xml_direct()
