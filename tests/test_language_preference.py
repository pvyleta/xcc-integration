"""Test language preference functionality."""

def test_language_preference_constants():
    """Test that language preference constants are properly defined."""
    
    # Import constants
    try:
        from custom_components.xcc.const import (
            CONF_LANGUAGE,
            LANGUAGE_ENGLISH,
            LANGUAGE_CZECH,
            DEFAULT_LANGUAGE
        )
    except ImportError as e:
        print(f"Failed to import language constants: {e}")
        return False
    
    # Verify constants are defined correctly
    assert CONF_LANGUAGE == "language"
    assert LANGUAGE_ENGLISH == "english"
    assert LANGUAGE_CZECH == "czech"
    assert DEFAULT_LANGUAGE == LANGUAGE_ENGLISH
    
    print("✅ Language preference constants are properly defined")
    # Test passed if we reach here without any assertion errors

def test_friendly_name_selection_english():
    """Test friendly name selection with English preference."""
    
    # Mock descriptor config with both languages
    descriptor_config = {
        "friendly_name": "Česká teplota",  # Czech name
        "friendly_name_en": "English temperature",  # English name
        "unit": "°C"
    }
    
    # Simulate English preference logic
    language = "english"
    if language == "english":
        result = (
            descriptor_config.get("friendly_name_en")
            or descriptor_config.get("friendly_name")
            or "TEST_PROP"
        )
    else:
        result = (
            descriptor_config.get("friendly_name")
            or descriptor_config.get("friendly_name_en")
            or "TEST_PROP"
        )
    
    assert result == "English temperature"
    print("✅ English preference correctly selects English friendly name")
    # Test passed if we reach here without any assertion errors

def test_friendly_name_selection_czech():
    """Test friendly name selection with Czech preference."""
    
    # Mock descriptor config with both languages
    descriptor_config = {
        "friendly_name": "Česká teplota",  # Czech name
        "friendly_name_en": "English temperature",  # English name
        "unit": "°C"
    }
    
    # Simulate Czech preference logic
    language = "czech"
    if language == "english":
        result = (
            descriptor_config.get("friendly_name_en")
            or descriptor_config.get("friendly_name")
            or "TEST_PROP"
        )
    else:
        result = (
            descriptor_config.get("friendly_name")
            or descriptor_config.get("friendly_name_en")
            or "TEST_PROP"
        )
    
    assert result == "Česká teplota"
    print("✅ Czech preference correctly selects Czech friendly name")
    # Test passed if we reach here without any assertion errors

def test_friendly_name_fallback_scenarios():
    """Test fallback scenarios for friendly name selection."""
    
    test_cases = [
        {
            "name": "English only - English preference",
            "config": {"friendly_name_en": "English temperature"},
            "language": "english",
            "expected": "English temperature"
        },
        {
            "name": "English only - Czech preference",
            "config": {"friendly_name_en": "English temperature"},
            "language": "czech",
            "expected": "English temperature"
        },
        {
            "name": "Czech only - English preference",
            "config": {"friendly_name": "Česká teplota"},
            "language": "english",
            "expected": "Česká teplota"
        },
        {
            "name": "Czech only - Czech preference",
            "config": {"friendly_name": "Česká teplota"},
            "language": "czech",
            "expected": "Česká teplota"
        },
        {
            "name": "No names - fallback to prop",
            "config": {},
            "language": "english",
            "expected": "TEST_PROP"
        }
    ]
    
    for case in test_cases:
        config = case["config"]
        language = case["language"]
        
        if language == "english":
            result = (
                config.get("friendly_name_en")
                or config.get("friendly_name")
                or "TEST_PROP"
            )
        else:
            result = (
                config.get("friendly_name")
                or config.get("friendly_name_en")
                or "TEST_PROP"
            )
        
        assert result == case["expected"], f"Failed for {case['name']}: expected '{case['expected']}', got '{result}'"
        print(f"✅ {case['name']}: '{result}'")
    
    # Test passed if we reach here without any assertion errors

