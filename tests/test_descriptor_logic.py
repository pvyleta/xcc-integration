"""Test descriptor parsing logic directly."""

def test_descriptor_logic():
    """Test the descriptor parsing logic with the actual values from XML."""
    
    print("🔍 TESTING DESCRIPTOR PARSING LOGIC")
    print("=" * 70)
    
    # Test cases based on actual XML data
    test_cases = [
        {
            "name": "TCSTAV4-PROUD",
            "text": "",
            "text_en": "",
            "row_text": "Odebíraný proud TČ",
            "row_text_en": "Current draw by HP",
            "label_text": "",
            "label_text_en": "",
            "expected_czech": "Odebíraný proud TČ",
            "expected_english": "Current draw by HP"
        },
        {
            "name": "TCSTAV7-PRIKON",
            "text": "",
            "text_en": "",
            "row_text": "Příkon TČ",
            "row_text_en": "Power consumption by HP",
            "label_text": "",
            "label_text_en": "",
            "expected_czech": "Příkon TČ",
            "expected_english": "Power consumption by HP"
        },
        {
            "name": "TO-SPOT-STOPENABLED",
            "text": "",
            "text_en": "",
            "row_text": "Vypínat okruh při drahé elektrické energie na spotovém trhu",
            "row_text_en": "Switch off the circuit when electricity is expensive on the spot market",
            "label_text": "",
            "label_text_en": "",
            "expected_czech": "Vypínat okruh při drahé elektrické energie na spotovém trhu",
            "expected_english": "Switch off the circuit when electricity is expensive on the spot market"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 TEST {i}: {test_case['name']}")
        
        # Extract values
        text = test_case['text']
        text_en = test_case['text_en']
        row_text = test_case['row_text']
        row_text_en = test_case['row_text_en']
        label_text = test_case['label_text']
        label_text_en = test_case['label_text_en']
        prop = test_case['name']
        
        print(f"   Input values:")
        print(f"     text='{text}', text_en='{text_en}'")
        print(f"     row_text='{row_text}', row_text_en='{row_text_en}'")
        print(f"     label_text='{label_text}', label_text_en='{label_text_en}'")
        
        # Apply the fixed logic from descriptor_parser.py
        # English friendly name - prioritize English text
        friendly_name_en = text_en or label_text_en or row_text_en or text or label_text or row_text or prop

        # Czech friendly name - prioritize Czech text
        friendly_name_cz = text or label_text or row_text or text_en or label_text_en or row_text_en or prop
        
        print(f"   Fallback results:")
        print(f"     friendly_name_cz='{friendly_name_cz}'")
        print(f"     friendly_name_en='{friendly_name_en}'")

        # Handle different combinations of row, label, and element text for ENGLISH
        if row_text_en and (text_en or label_text_en):
            # Both row and element/label have English text - combine them
            element_part_en = text_en or label_text_en
            friendly_name_en = f"{row_text_en} - {element_part_en}"
            print(f"   English combination: row_text_en + element_part_en")
        elif row_text and (text_en or label_text_en):
            # Row has Czech text, element has English text - use English element with Czech row
            element_part_en = text_en or label_text_en
            friendly_name_en = f"{row_text} - {element_part_en}"
            print(f"   English combination: row_text + element_part_en")
        elif row_text_en and (text or label_text):
            # Row has English text, element has Czech text - use Czech element with English row
            element_part_cz = text or label_text
            friendly_name_en = f"{row_text_en} - {element_part_cz}"
            print(f"   English combination: row_text_en + element_part_cz")
        elif label_text_en:
            # No row text but label has English text
            friendly_name_en = label_text_en
            print(f"   English combination: label_text_en only")
        else:
            print(f"   English combination: No combination applied, using fallback")

        # Handle different combinations of row, label, and element text for CZECH
        if row_text and (text or label_text):
            # Both row and element/label have Czech text - combine them
            element_part_cz = text or label_text
            friendly_name_cz = f"{row_text} - {element_part_cz}"
            print(f"   Czech combination: row_text + element_part_cz")
        elif row_text_en and (text or label_text):
            # Row has English text, element has Czech text - use Czech element with English row
            element_part_cz = text or label_text
            friendly_name_cz = f"{row_text_en} - {element_part_cz}"
            print(f"   Czech combination: row_text_en + element_part_cz")
        elif row_text and (text_en or label_text_en):
            # Row has Czech text, element has English text - use English element with Czech row
            element_part_en = text_en or label_text_en
            friendly_name_cz = f"{row_text} - {element_part_en}"
            print(f"   Czech combination: row_text + element_part_en")
        elif label_text:
            # No row text but label has Czech text
            friendly_name_cz = label_text
            print(f"   Czech combination: label_text only")
        else:
            print(f"   Czech combination: No combination applied, using fallback")

        # For backward compatibility, set friendly_name to the Czech version
        friendly_name = friendly_name_cz

        print(f"   Final results:")
        print(f"     friendly_name='{friendly_name}' (Czech)")
        print(f"     friendly_name_en='{friendly_name_en}' (English)")
        print(f"   Expected:")
        print(f"     czech='{test_case['expected_czech']}'")
        print(f"     english='{test_case['expected_english']}'")
        
        # Verify the results
        czech_ok = friendly_name_cz == test_case['expected_czech']
        english_ok = friendly_name_en == test_case['expected_english']
        
        if czech_ok and english_ok:
            print(f"   ✅ PASS")
        else:
            print(f"   ❌ FAIL")
            if not czech_ok:
                print(f"      Czech mismatch: expected '{test_case['expected_czech']}', got '{friendly_name_cz}'")
            if not english_ok:
                print(f"      English mismatch: expected '{test_case['expected_english']}', got '{friendly_name_en}'")
    
    print(f"\n🎉 DESCRIPTOR PARSING LOGIC TEST COMPLETED!")

if __name__ == "__main__":
    test_descriptor_logic()
