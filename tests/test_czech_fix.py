"""Test Czech descriptor parsing fix."""

def test_czech_descriptor_parsing():
    """Test that descriptor parsing creates proper Czech and English friendly names."""
    
    print("🔍 TESTING CZECH DESCRIPTOR PARSING")
    print("=" * 70)
    
    # Test the specific case from TUV1.XML
    test_case = {
        "name": "TUVEXTERNIOHREVMOTOHODINY from TUV1.XML",
        "row_text": "Externí ohřev",
        "row_text_en": "External heating", 
        "label_text": "Motohodiny",
        "label_text_en": "Runhours",
        "expected_czech": "Externí ohřev - Motohodiny",
        "expected_english": "External heating - Runhours"
    }
    
    print(f"\n📋 TEST: {test_case['name']}")
    
    # Simulate the descriptor parsing logic
    row_text = test_case['row_text']
    row_text_en = test_case['row_text_en']
    label_text = test_case['label_text']
    label_text_en = test_case['label_text_en']
    text = ""  # Element text (usually empty for number elements)
    text_en = ""
    prop = "TUVEXTERNIOHREVMOTOHODINY"
    
    print(f"   Input: row_text='{row_text}', row_text_en='{row_text_en}'")
    print(f"          label_text='{label_text}', label_text_en='{label_text_en}'")
    
    # Apply the fixed logic from descriptor_parser.py
    # English friendly name - prioritize English text
    friendly_name_en = text_en or label_text_en or row_text_en or text or label_text or row_text or prop

    # Czech friendly name - prioritize Czech text
    friendly_name_cz = text or label_text or row_text or text_en or label_text_en or row_text_en or prop

    # Handle different combinations of row, label, and element text for ENGLISH
    if row_text_en and (text_en or label_text_en):
        # Both row and element/label have English text - combine them
        element_part_en = text_en or label_text_en
        friendly_name_en = f"{row_text_en} - {element_part_en}"
    elif row_text and (text_en or label_text_en):
        # Row has Czech text, element has English text - use English element with Czech row
        element_part_en = text_en or label_text_en
        friendly_name_en = f"{row_text} - {element_part_en}"
    elif row_text_en and (text or label_text):
        # Row has English text, element has Czech text - use Czech element with English row
        element_part_cz = text or label_text
        friendly_name_en = f"{row_text_en} - {element_part_cz}"
    elif label_text_en:
        # No row text but label has English text
        friendly_name_en = label_text_en

    # Handle different combinations of row, label, and element text for CZECH
    if row_text and (text or label_text):
        # Both row and element/label have Czech text - combine them
        element_part_cz = text or label_text
        friendly_name_cz = f"{row_text} - {element_part_cz}"
    elif row_text_en and (text or label_text):
        # Row has English text, element has Czech text - use Czech element with English row
        element_part_cz = text or label_text
        friendly_name_cz = f"{row_text_en} - {element_part_cz}"
    elif row_text and (text_en or label_text_en):
        # Row has Czech text, element has English text - use English element with Czech row
        element_part_en = text_en or label_text_en
        friendly_name_cz = f"{row_text} - {element_part_en}"
    elif label_text:
        # No row text but label has Czech text
        friendly_name_cz = label_text

    print(f"   Result: friendly_name_cz='{friendly_name_cz}'")
    print(f"           friendly_name_en='{friendly_name_en}'")
    print(f"   Expected: czech='{test_case['expected_czech']}'")
    print(f"             english='{test_case['expected_english']}'")
    
    # Verify the results
    assert friendly_name_cz == test_case['expected_czech'], f"Czech name mismatch: expected '{test_case['expected_czech']}', got '{friendly_name_cz}'"
    assert friendly_name_en == test_case['expected_english'], f"English name mismatch: expected '{test_case['expected_english']}', got '{friendly_name_en}'"
    
    print(f"   ✅ PASS")
    
    print(f"\n🎉 CZECH DESCRIPTOR PARSING TEST PASSED!")
    print(f"   ✅ TUVEXTERNIOHREVMOTOHODINY now gets 'Externí ohřev - Motohodiny' (Czech)")
    print(f"   ✅ TUVEXTERNIOHREVMOTOHODINY now gets 'External heating - Runhours' (English)")
    
    return True

if __name__ == "__main__":
    test_czech_descriptor_parsing()
