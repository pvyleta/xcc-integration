"""Test parent row detection logic."""

import xml.etree.ElementTree as ET

def find_parent_row(element, root):
    """Find the parent row element for context (mimicking the descriptor parser logic)."""
    # Find the element in the tree and get its parent row
    immediate_parent = None
    for row in root.iter("row"):
        for child in row.iter():
            if child is element:
                immediate_parent = row
                break
        if immediate_parent is not None:
            break

    # If the immediate parent has no text, look for the previous row with text
    if immediate_parent is not None:
        row_text = immediate_parent.get("text", "")
        row_text_en = immediate_parent.get("text_en", "")

        if not row_text and not row_text_en:
            # Look for the previous row with text in the same block
            for block in root.iter("block"):
                rows = list(block.iter("row"))
                for i, row in enumerate(rows):
                    if row is immediate_parent and i > 0:
                        # Look backwards for a row with text
                        for j in range(i - 1, -1, -1):
                            prev_row = rows[j]
                            prev_text = prev_row.get("text", "")
                            prev_text_en = prev_row.get("text_en", "")
                            if prev_text or prev_text_en:
                                return prev_row
                        break

    return immediate_parent

def test_parent_row_detection():
    """Test parent row detection for specific entities."""
    
    print("🔍 TESTING PARENT ROW DETECTION")
    print("=" * 70)
    
    # Test entities that should have Czech translations
    test_entities = [
        ("TCSTAV8-VYKON", "sample_data/STAVJED.XML"),
        ("TCSTAV5-FANH", "sample_data/STAVJED.XML"),
        ("TCSTAV3-TCJ", "sample_data/STAVJED.XML"),
        ("TO-EK50", "sample_data/OKRUH.XML"),
        ("TO-ADAPTACE-ROZPTYLEKV", "sample_data/OKRUH.XML"),
        ("TO-PR-VITR-POSUN", "sample_data/OKRUH.XML"),
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
            print(f"   Element attributes: {dict(element.attrib)}")
            
            # Find parent row using the same logic as descriptor parser
            parent_row = find_parent_row(element, root)
            
            if parent_row is None:
                print(f"   ❌ No parent row found")
                continue
            
            print(f"   Found parent row")
            print(f"   Parent row attributes: {dict(parent_row.attrib)}")
            
            # Extract text values
            text = element.get("text", "")
            text_en = element.get("text_en", "")
            row_text = parent_row.get("text", "")
            row_text_en = parent_row.get("text_en", "")
            
            print(f"   Text extraction:")
            print(f"     element text='{text}', text_en='{text_en}'")
            print(f"     row text='{row_text}', text_en='{row_text_en}'")
            
            # Apply the descriptor parsing logic
            # English friendly name - prioritize English text
            friendly_name_en = text_en or row_text_en or text or row_text or prop

            # Czech friendly name - prioritize Czech text
            friendly_name_cz = text or row_text or text_en or row_text_en or prop
            
            print(f"   Fallback logic results:")
            print(f"     friendly_name_cz='{friendly_name_cz}'")
            print(f"     friendly_name_en='{friendly_name_en}'")
            
            # Check if they're different
            if friendly_name_cz != friendly_name_en:
                print(f"   ✅ Different Czech and English names - GOOD!")
            else:
                print(f"   ❌ Same Czech and English names - BAD!")
                print(f"      Both are: '{friendly_name_cz}'")
                
        except Exception as e:
            print(f"   ❌ Error processing {prop}: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n🎉 PARENT ROW DETECTION TEST COMPLETED!")

if __name__ == "__main__":
    test_parent_row_detection()
