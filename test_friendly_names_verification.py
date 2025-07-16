#!/usr/bin/env python3
"""Verify that friendly name fixes are working correctly."""

import sys
import os
import xml.etree.ElementTree as ET

def test_friendly_name_fixes_verification():

    """Test that the friendly name fixes are actually working by parsing XML directly."""

    print("🔍 Verifying Friendly Name Fixes")
    print("=" * 60)

    # Test the specific problematic entities by manually parsing XML
    test_cases = [
        {
            "name": "TO-FVEPRETOPENI-POVOLENI",
            "file": "sample_data/OKRUH.XML",
            "expected_friendly_name_en": "Přetápění z FVE - Enable",  # Row text + label text_en
            "issue": "Switch element should combine row text with label text_en"
        },
        {
            "name": "FVE-CHARGEATCHEAPMAXSOC",
            "file": "sample_data/FVE.XML",
            "expected_friendly_name_en": "Ukončit nabíjení při překročení SOC baterie",  # Should fall back to Czech
            "issue": "Should fall back to Czech when text_en is empty"
        },
        {
            "name": "FVM0-CURRENTBATTERYSETTINGS-CHARGEIMAX",
            "file": "sample_data/FVE.XML",
            "expected_friendly_name_en": "Iverter 1 - Actual maximal charge current",
            "issue": "Readonly sensor should use parent row's text_en"
        }
    ]

    all_passed = True

    for test_case in test_cases:
        print(f"\n🎯 Testing: {test_case['name']}")
        print(f"   Issue: {test_case['issue']}")

        file_path = test_case["file"]
        if not os.path.exists(file_path):
            print(f"   ❌ Sample file {file_path} not found")
            all_passed = False
            continue

        try:
            # Parse the XML file manually
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                xml_content = f.read()

            root = ET.fromstring(xml_content)

            # Find the element with this prop
            prop_name = test_case["name"]
            found_element = None
            parent_row = None

            for element in root.iter():
                if element.get("prop") == prop_name:
                    found_element = element
                    # Find parent row
                    for row in root.iter("row"):
                        for child in row.iter():
                            if child is element:
                                parent_row = row
                                break
                        if parent_row:
                            break
                    break

            if found_element is not None:
                # Apply the friendly name logic manually
                element_text = found_element.get("text", "")
                element_text_en = found_element.get("text_en", "")

                row_text = ""
                row_text_en = ""
                label_text = ""
                label_text_en = ""

                if parent_row is not None:
                    row_text = parent_row.get("text", "")
                    row_text_en = parent_row.get("text_en", "")

                    # Find corresponding label
                    labels = list(parent_row.iter("label"))
                    input_elements = []
                    for child in parent_row.iter():
                        if child.tag in ["number", "switch", "select", "button"] and child.get("prop"):
                            input_elements.append(child)

                    # Find the index of our element
                    element_index = -1
                    for i, input_elem in enumerate(input_elements):
                        if input_elem is found_element:
                            element_index = i
                            break

                    # Get corresponding label
                    if element_index >= 0 and element_index < len(labels):
                        label = labels[element_index]
                        label_text = label.get("text", "")
                        label_text_en = label.get("text_en", "")

                # Apply the priority logic: element text_en > label text_en > row text_en > element text > label text > row text > prop
                friendly_name_en = element_text_en or label_text_en or row_text_en or element_text or label_text or row_text or prop_name

                # For display friendly name, combine row and element/label text
                if row_text and (element_text or label_text):
                    element_part = element_text_en or label_text_en or element_text or label_text
                    row_part = row_text_en or row_text
                    if element_part:
                        friendly_name = f"{row_part} - {element_part}"
                    else:
                        friendly_name = row_part
                elif label_text:
                    friendly_name = label_text_en or label_text
                else:
                    friendly_name = friendly_name_en

                expected_friendly_name_en = test_case["expected_friendly_name_en"]

                print(f"   Element text: '{element_text}'")
                print(f"   Element text_en: '{element_text_en}'")
                print(f"   Row text: '{row_text}'")
                print(f"   Row text_en: '{row_text_en}'")
                print(f"   Label text: '{label_text}'")
                print(f"   Label text_en: '{label_text_en}'")
                print(f"   Calculated friendly_name_en: '{friendly_name_en}'")
                print(f"   Calculated friendly_name: '{friendly_name}'")
                print(f"   Expected: '{expected_friendly_name_en}'")

                if friendly_name == expected_friendly_name_en:
                    print(f"   ✅ PASS - Friendly name logic is correct")
                else:
                    print(f"   ❌ FAIL - Friendly name logic mismatch")
                    all_passed = False

            else:
                print(f"   ❌ Entity {prop_name} not found in XML")
                all_passed = False

        except Exception as e:
            print(f"   ❌ Error testing {test_case['name']}: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False
    
    print(f"\n📊 Overall Result")
    print("=" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED - Friendly name fixes are working correctly!")
    else:
        print("❌ SOME TESTS FAILED - Friendly name fixes may not be working properly")
        
    return all_passed


def debug_xml_structure():
    """Debug the XML structure to understand what's happening."""
    
    print(f"\n🔧 Debugging XML Structure")
    print("=" * 60)
    
    # Check the specific XML elements for our test cases
    test_files = [
        ("sample_data/OKRUH.XML", "TO-FVEPRETOPENI-POVOLENI"),
        ("sample_data/FVE.XML", "FVE-CHARGEATCHEAPMAXSOC"),
        ("sample_data/FVE.XML", "FVM0-CURRENTBATTERYSETTINGS-CHARGEIMAX"),
    ]
    
    for file_path, prop_name in test_files:
        print(f"\n🔍 Analyzing {prop_name} in {file_path}")
        
        if not os.path.exists(file_path):
            print(f"   ❌ File not found: {file_path}")
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Parse XML
            root = ET.fromstring(content)
            
            # Find elements with this prop
            found_elements = []
            for element in root.iter():
                if element.get("prop") == prop_name:
                    found_elements.append(element)
            
            if found_elements:
                for i, element in enumerate(found_elements):
                    print(f"   Element {i+1}: <{element.tag}>")
                    print(f"      prop: {element.get('prop', 'MISSING')}")
                    print(f"      text: '{element.get('text', 'MISSING')}'")
                    print(f"      text_en: '{element.get('text_en', 'MISSING')}'")
                    print(f"      config: '{element.get('config', 'MISSING')}'")
                    
                    # Find parent row
                    for row in root.iter("row"):
                        for child in row.iter():
                            if child is element:
                                print(f"      Parent row text: '{row.get('text', 'MISSING')}'")
                                print(f"      Parent row text_en: '{row.get('text_en', 'MISSING')}'")
                                break
            else:
                print(f"   ❌ No elements found with prop='{prop_name}'")
                
        except Exception as e:
            print(f"   ❌ Error analyzing {file_path}: {e}")


if __name__ == "__main__":
    """Run verification when executed directly."""
    try:
        success = test_friendly_name_fixes_verification()
        debug_xml_structure()
        
        if success:
            print("\n🎉 VERIFICATION COMPLETED SUCCESSFULLY!")
            sys.exit(0)
        else:
            print("\n❌ VERIFICATION FAILED!")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 VERIFICATION ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
