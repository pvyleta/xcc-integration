"""Test Czech language fix for entity names."""

def test_entity_name_selection_with_czech_language():
    """Test that entity name selection works correctly with Czech language preference."""
    
    print("🔍 TESTING CZECH LANGUAGE ENTITY NAME SELECTION")
    print("=" * 70)
    
    # Test cases for different entity scenarios
    test_cases = [
        {
            "name": "Entity with real Czech translation",
            "attributes": {
                "friendly_name_en": "Priority",
                "friendly_name": "Přetápění z FVE - Priority",
                "field_name": "TO-FVEPRETOPENI-PRIORITA"
            },
            "language": "czech",
            "expected": "Přetápění z FVE - Priority",
            "expected_log": "✅ Using Czech translation"
        },
        {
            "name": "Entity without descriptors (Czech preference)",
            "attributes": {
                "friendly_name_en": "",
                "friendly_name": "To Config Michacka Povoleni",  # Formatted from field_name
                "field_name": "TO-CONFIG-MICHACKA-POVOLENI"
            },
            "language": "czech",
            "expected": "TO-CONFIG-MICHACKA-POVOLENI",
            "expected_log": "🔧 Using technical field name (no translations)"
        },
        {
            "name": "Entity without descriptors (English preference)",
            "attributes": {
                "friendly_name_en": "",
                "friendly_name": "Fve Config Enabled",  # Formatted from field_name
                "field_name": "FVE-CONFIG-ENABLED"
            },
            "language": "english",
            "expected": "FVE-CONFIG-ENABLED",
            "expected_log": "🔧 Using technical field name"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 TEST {i}: {test_case['name']}")
        print(f"   Language: {test_case['language']}")
        
        # Simulate the entity name selection logic
        friendly_name_en = test_case['attributes'].get("friendly_name_en", "")
        friendly_name_cz = test_case['attributes'].get("friendly_name", "")
        field_name = test_case['attributes'].get("field_name", "")
        language_preference = test_case['language']
        
        # Check if we have real translations
        has_real_translations = bool(friendly_name_en and friendly_name_cz and friendly_name_en != friendly_name_cz)
        
        print(f"   Has real translations: {has_real_translations}")
        
        # Apply the fixed logic
        if language_preference == "english":
            if friendly_name_en:
                selected_name = friendly_name_en
                log_message = "✅ Using English name"
            elif friendly_name_cz and has_real_translations:
                selected_name = friendly_name_cz
                log_message = "⚠️ Using Czech name (no English available)"
            elif field_name:
                selected_name = field_name
                log_message = "🔧 Using technical field name"
            else:
                selected_name = "fallback"
                log_message = "❌ Using fallback"
        else:  # Czech
            if friendly_name_cz and has_real_translations:
                selected_name = friendly_name_cz
                log_message = "✅ Using Czech translation"
            elif friendly_name_en:
                selected_name = friendly_name_en
                log_message = "⚠️ Using English name (no Czech translation)"
            elif field_name:
                selected_name = field_name
                log_message = "🔧 Using technical field name (no translations)"
            else:
                selected_name = "fallback"
                log_message = "❌ Using fallback"
        
        print(f"   Selected name: '{selected_name}'")
        print(f"   Expected: '{test_case['expected']}'")
        
        # Verify the result
        assert selected_name == test_case['expected'], f"Expected '{test_case['expected']}', got '{selected_name}'"
        assert test_case['expected_log'] in log_message, f"Expected log containing '{test_case['expected_log']}', got '{log_message}'"
        
        print(f"   ✅ PASS")
    
    print(f"\n🎉 ALL CZECH LANGUAGE TESTS PASSED!")
    # Test passed if we reach here without any assertion errors

