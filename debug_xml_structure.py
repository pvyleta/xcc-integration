#!/usr/bin/env python3
"""Debug XML structure to understand the TO-FVEPRETOPENI-POVOLENI issue."""

import xml.etree.ElementTree as ET

def debug_xml_structure():
    """Debug the XML structure around TO-FVEPRETOPENI-POVOLENI."""
    
    with open('sample_data/OKRUH.XML', 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    root = ET.fromstring(content)
    
    print("🔍 Debugging TO-FVEPRETOPENI-POVOLENI XML Structure")
    print("=" * 70)
    
    # Find the element
    target_element = None
    target_row = None
    
    for element in root.iter():
        if element.get('prop') == 'TO-FVEPRETOPENI-POVOLENI':
            target_element = element
            print(f"Found target element: <{element.tag}>")
            print(f"  prop: '{element.get('prop', '')}'")
            print(f"  text: '{element.get('text', '')}'")
            print(f"  text_en: '{element.get('text_en', '')}'")
            
            # Find immediate parent row
            for row in root.iter('row'):
                for child in row.iter():
                    if child is element:
                        target_row = row
                        print(f"\nImmediate parent row:")
                        print(f"  text: '{row.get('text', '')}'")
                        print(f"  text_en: '{row.get('text_en', '')}'")
                        print(f"  prop: '{row.get('prop', '')}'")
                        print(f"  prop2: '{row.get('prop2', '')}'")
                        break
                if target_row is not None:
                    break
            break
    
    if target_element is None:
        print("❌ TO-FVEPRETOPENI-POVOLENI not found!")
        return
    
    # Look for nearby rows with text
    print(f"\n🔍 Looking for nearby rows with text...")
    
    # Find all rows in the same block
    current_block = None
    for block in root.iter('block'):
        for element in block.iter():
            if element.get('prop') == 'TO-FVEPRETOPENI-POVOLENI':
                current_block = block
                break
        if current_block is not None:
            break
    
    if current_block is not None:
        print(f"\nFound containing block:")
        print(f"  name: '{current_block.get('name', '')}'")
        print(f"  name_en: '{current_block.get('name_en', '')}'")
        
        print(f"\nAll rows in this block:")
        for i, row in enumerate(current_block.iter('row')):
            row_text = row.get('text', '')
            row_text_en = row.get('text_en', '')
            row_prop = row.get('prop', '')
            
            # Check if this row contains our target element
            contains_target = False
            for child in row.iter():
                if child.get('prop') == 'TO-FVEPRETOPENI-POVOLENI':
                    contains_target = True
                    break
            
            marker = " ⭐ TARGET ROW" if contains_target else ""
            print(f"  Row {i+1}{marker}:")
            print(f"    text: '{row_text}'")
            print(f"    text_en: '{row_text_en}'")
            print(f"    prop: '{row_prop}'")
            
            if contains_target:
                print(f"    Children in this row:")
                for child in row:
                    child_prop = child.get('prop', '')
                    child_text = child.get('text', '')
                    child_text_en = child.get('text_en', '')
                    print(f"      <{child.tag}> prop='{child_prop}' text='{child_text}' text_en='{child_text_en}'")
    
    # Look for header rows or label rows that might provide context
    print(f"\n🔍 Looking for header/label rows that might provide context...")

    # Check Row 7 (the header row) for labels
    if current_block is not None:
        rows = list(current_block.iter('row'))
        if len(rows) >= 7:
            header_row = rows[6]  # Row 7 (0-indexed)
            print(f"\nChecking Row 7 (header row) for labels:")
            print(f"  Row text: '{header_row.get('text', '')}'")
            print(f"  Row text_en: '{header_row.get('text_en', '')}'")

            for label in header_row.iter('label'):
                label_text = label.get('text', '')
                label_text_en = label.get('text_en', '')
                print(f"  Label: text='{label_text}' text_en='{label_text_en}'")

    # Check if there are any label elements with relevant text in target row
    if target_row is not None:
        print(f"\nChecking labels in the target row:")
        for label in target_row.iter('label'):
            label_text = label.get('text', '')
            label_text_en = label.get('text_en', '')
            print(f"  Label: text='{label_text}' text_en='{label_text_en}'")

if __name__ == "__main__":
    debug_xml_structure()
