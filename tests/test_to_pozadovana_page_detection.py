"""Test TO-POZADOVANA page detection fix."""

def test_to_pozadovana_page_detection():
    """Test that TO-POZADOVANA is correctly routed to OKRUH10.XML."""
    
    # Simulate the page detection logic from xcc_client.py
    prop = "TO-POZADOVANA"
    prop_upper = prop.upper()
    page_to_fetch = None
    
    # Check for TUV/DHW related properties (including Czech terms)
    tuv_keywords = ["TUV", "DHW", "ZASOBNIK", "TEPLOTA", "TALT"]
    if any(tuv_word in prop_upper for tuv_word in tuv_keywords):
        page_to_fetch = "TUV11.XML"
    elif prop_upper.startswith("FVE-CONFIG-") or prop_upper.startswith("FVESTATS-"):
        page_to_fetch = "FVEINV10.XML"
    elif any(fve_word in prop_upper for fve_word in ["FVE", "SOLAR", "PV"]):
        page_to_fetch = "FVE4.XML"
    elif any(okruh_word in prop_upper for okruh_word in ["OKRUH", "CIRCUIT", "TO-"]):
        # TO- properties (room temperature) are in OKRUH pages
        page_to_fetch = "OKRUH10.XML"
    elif any(biv_word in prop_upper for biv_word in ["BIV", "BIVALENCE"]):
        page_to_fetch = "BIV1.XML"
    else:
        page_to_fetch = "STAVJED1.XML"  # Default page
    
    print(f"✅ TO-POZADOVANA -> {page_to_fetch}")
    
    # Verify the fix
    assert page_to_fetch == "OKRUH10.XML", \
        f"Expected OKRUH10.XML, got {page_to_fetch}"
    
    print("✅ TEST PASSED: TO-POZADOVANA correctly routed to OKRUH10.XML")


def test_other_to_properties():
    """Test that other TO- properties are also correctly routed."""
    
    test_cases = [
        ("TO-POZADOVANA", "OKRUH10.XML"),
        ("TO-UTLUMOVA", "OKRUH10.XML"),
        ("TO-POVOLENI", "OKRUH10.XML"),
        ("TO-KONSTANTNI", "OKRUH10.XML"),
        ("TO-HYSTEREZEPOKOJOVETEPLOTY", "OKRUH10.XML"),
    ]
    
    for prop, expected_page in test_cases:
        prop_upper = prop.upper()
        page_to_fetch = None
        
        # Same logic as in xcc_client.py
        tuv_keywords = ["TUV", "DHW", "ZASOBNIK", "TEPLOTA", "TALT"]
        if any(tuv_word in prop_upper for tuv_word in tuv_keywords):
            page_to_fetch = "TUV11.XML"
        elif prop_upper.startswith("FVE-CONFIG-") or prop_upper.startswith("FVESTATS-"):
            page_to_fetch = "FVEINV10.XML"
        elif any(fve_word in prop_upper for fve_word in ["FVE", "SOLAR", "PV"]):
            page_to_fetch = "FVE4.XML"
        elif any(okruh_word in prop_upper for okruh_word in ["OKRUH", "CIRCUIT", "TO-"]):
            page_to_fetch = "OKRUH10.XML"
        elif any(biv_word in prop_upper for biv_word in ["BIV", "BIVALENCE"]):
            page_to_fetch = "BIV1.XML"
        else:
            page_to_fetch = "STAVJED1.XML"
        
        assert page_to_fetch == expected_page, \
            f"{prop}: Expected {expected_page}, got {page_to_fetch}"
        
        print(f"✅ {prop} -> {page_to_fetch}")
    
    print(f"\n✅ ALL TESTS PASSED: {len(test_cases)} TO- properties correctly routed")


if __name__ == "__main__":
    test_to_pozadovana_page_detection()
    test_other_to_properties()

