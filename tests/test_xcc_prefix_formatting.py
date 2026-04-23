"""Test XCC entity ID prefix and formatting."""

def test_entity_id_formatting():
    """Test that entity IDs are properly formatted with xcc_ prefix."""
    
    print("🔍 TESTING XCC ENTITY ID FORMATTING")
    print("=" * 70)
    
    # Test cases with various XCC property names and expected entity IDs
    test_cases = [
        {
            "prop": "TOPNEOKRUHYIN3-FVEPRETOPENI-PRIORITA",
            "expected": "xcc_topneokruhyin3_fvepretopeni_priorita",
            "description": "Standard property with hyphens"
        },
        {
            "prop": "VARIANTAZOBRAZCERPADLA7",
            "expected": "xcc_variantazobrazcerpadla7",
            "description": "Simple property name"
        },
        {
            "prop": "WEB-OKRUHYODKAZPOCASI",
            "expected": "xcc_web_okruhyodkazpocasi",
            "description": "Property with hyphen"
        },
        {
            "prop": "FVE.ENABLED",
            "expected": "xcc_fve_enabled",
            "description": "Property with dot separator"
        }
    ]
    
    # Use the real helper from the integration so this test exercises production code.
    # Load the helper file directly rather than through ``xcc.entity_helpers`` to
    # avoid pulling in the whole package (which imports homeassistant.*).
    import importlib.util
    from pathlib import Path

    helper_path = Path(__file__).parent.parent / "custom_components" / "xcc" / "entity_helpers.py"
    spec = importlib.util.spec_from_file_location("_xcc_entity_helpers", helper_path)
    helpers = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helpers)

    def format_entity_id(prop: str) -> str:
        return f"xcc_{helpers.format_entity_id_suffix(prop)}"
    
    print("�� ENTITY ID FORMATTING TESTS:")
    
    for i, case in enumerate(test_cases, 1):
        prop = case["prop"]
        expected = case["expected"]
        description = case["description"]
        
        actual = format_entity_id(prop)
        
        print(f"\n{i}. {description}")
        print(f"   Input:    '{prop}'")
        print(f"   Expected: '{expected}'")
        print(f"   Actual:   '{actual}'")
        
        assert actual == expected, f"Entity ID formatting failed for '{prop}'"
        assert actual.startswith("xcc_"), f"Entity ID '{actual}' should start with 'xcc_'"
        
        print(f"   ✅ PASS")
    
    print(f"\n✅ All {len(test_cases)} entity ID formatting tests passed")

if __name__ == "__main__":
    test_entity_id_formatting()
    print("\n🎉 XCC PREFIX AND FORMATTING TESTS PASSED!")
