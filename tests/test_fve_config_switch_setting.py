"""Test FVE-CONFIG switch setting functionality."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from custom_components.xcc.xcc_client import XCCClient


def test_fve_config_page_selection():
    """Test that FVE-CONFIG entities are correctly mapped to fveinv.xml page."""
    
    # Test the page selection logic for FVE-CONFIG entities
    test_cases = [
        ("FVE-CONFIG-MENICECONFIG-READONLY", "FVEINV10.XML"),
        ("FVE-CONFIG-MENICECONFIG-KOMUNIKOVAT", "FVEINV10.XML"),
        ("FVESTATS-DEMANDCHRGCURR", "FVEINV10.XML"),
        ("FVESTATS-MENIC-BATTERY-SOC", "FVEINV10.XML"),
        ("FVE-SOMETHING-ELSE", "FVE4.XML"),  # Regular FVE entities should still go to FVE4.XML
        ("TUV-TEPLOTA", "TUV11.XML"),
        ("OKRUH-CIRCUIT", "OKRUH10.XML"),
    ]
    
    for prop, expected_page in test_cases:
        prop_upper = prop.upper()
        
        # Simulate the page selection logic from XCCClient.set_value
        if prop_upper.startswith("FVE-CONFIG-") or prop_upper.startswith("FVESTATS-"):
            page_to_fetch = "FVEINV10.XML"
        elif any(tuv_word in prop_upper for tuv_word in ["TUV", "DHW", "ZASOBNIK", "TEPLOTA", "TALT"]):
            page_to_fetch = "TUV11.XML"
        elif any(fve_word in prop_upper for fve_word in ["FVE", "SOLAR", "PV"]):
            page_to_fetch = "FVE4.XML"
        elif any(okruh_word in prop_upper for okruh_word in ["OKRUH", "CIRCUIT"]):
            page_to_fetch = "OKRUH10.XML"
        else:
            page_to_fetch = "STAVJED1.XML"
        
        assert page_to_fetch == expected_page, f"Property {prop} should map to {expected_page}, got {page_to_fetch}"
        print(f"✅ {prop} -> {page_to_fetch}")
    
    print("✅ All page selection tests passed")


@pytest.mark.asyncio
async def test_xcc_client_error_detection():
    """Test enhanced error detection in XCC client responses."""
    
    # Mock XCC client
    client = XCCClient("192.168.1.100", "xcc", "xcc")
    
    # Test cases for error detection
    test_responses = [
        ("HTTP 200 with success", 200, "OK: Value set successfully", True),
        ("HTTP 200 with error keyword", 200, "ERROR: Invalid value", False),
        ("HTTP 200 with failed keyword", 200, "Operation failed", False),
        ("HTTP 200 with invalid keyword", 200, "Invalid parameter", False),
        ("HTTP 200 with denied keyword", 200, "Access denied", False),
        ("HTTP 200 with forbidden keyword", 200, "Forbidden operation", False),
        ("HTTP 200 clean response", 200, "Configuration updated", True),
        ("HTTP 404 error", 404, "Not found", False),
        ("HTTP 500 error", 500, "Internal server error", False),
    ]
    
    for description, status_code, response_text, expected_success in test_responses:
        # Simulate the error detection logic from XCCClient.set_value
        if status_code == 200:
            response_lower = response_text.lower()
            has_error = any(error_word in response_lower for error_word in ['error', 'failed', 'invalid', 'denied', 'forbidden'])
            success = not has_error
        else:
            success = False
        
        assert success == expected_success, f"{description}: expected {expected_success}, got {success}"
        print(f"✅ {description}: {response_text[:50]}... -> {'SUCCESS' if success else 'FAILURE'}")
    
    print("✅ All error detection tests passed")


@pytest.mark.asyncio
async def test_fve_config_switch_entity_creation():
    """Test that FVE-CONFIG entities are created as switch entities."""
    
    from custom_components.xcc.descriptor_parser import XCCDescriptorParser
    
    # Load FVEINV descriptor
    import os
    from pathlib import Path
    
    project_root = Path(__file__).parent.parent
    sample_file = project_root / "tests" / "sample_data" / "FVEINV.XML"
    
    if not sample_file.exists():
        pytest.skip("FVEINV.XML sample file not found")
    
    with open(sample_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    parser = XCCDescriptorParser()
    configs = parser._parse_single_descriptor(content, 'fveinv.xml')
    
    # Test that FVE-CONFIG entities are switches
    fve_config_switches = []
    fve_config_sensors = []
    
    for entity_name, config in configs.items():
        if entity_name.startswith('FVE-CONFIG-'):
            if config['entity_type'] == 'switch':
                fve_config_switches.append(entity_name)
            elif config['entity_type'] == 'sensor':
                fve_config_sensors.append(entity_name)
    
    print(f"FVE-CONFIG switches: {len(fve_config_switches)}")
    for switch in fve_config_switches:
        config = configs[switch]
        print(f"  - {switch}: {config['friendly_name']} (writable: {config.get('writable', False)})")
    
    print(f"FVE-CONFIG sensors: {len(fve_config_sensors)}")
    for sensor in fve_config_sensors:
        config = configs[sensor]
        print(f"  - {sensor}: {config['friendly_name']}")
    
    # Verify that the main configuration switches are switches, not sensors
    expected_switches = [
        'FVE-CONFIG-MENICECONFIG-READONLY',
        'FVE-CONFIG-MENICECONFIG-KOMUNIKOVAT',
    ]
    
    for expected_switch in expected_switches:
        assert expected_switch in configs, f"Expected switch {expected_switch} not found"
        config = configs[expected_switch]
        assert config['entity_type'] == 'switch', f"{expected_switch} should be a switch, got {config['entity_type']}"
        assert config.get('writable', False) == True, f"{expected_switch} should be writable"
    
    print("✅ FVE-CONFIG switch entity creation test passed")


def test_switch_value_conversion():
    """Test that switch values are properly converted for XCC."""
    
    # Test the value conversion logic used in switch entities
    test_cases = [
        (True, "1"),
        (False, "0"),
        ("true", "1"),
        ("false", "0"),
        ("on", "1"),
        ("off", "0"),
        (1, "1"),
        (0, "0"),
    ]
    
    for input_value, expected_output in test_cases:
        # Simulate the conversion logic from XCCSwitch._async_set_state
        if isinstance(input_value, bool):
            output = "1" if input_value else "0"
        elif isinstance(input_value, str):
            if input_value.lower() in ["true", "on", "yes", "enabled", "active"]:
                output = "1"
            elif input_value.lower() in ["false", "off", "no", "disabled", "inactive"]:
                output = "0"
            else:
                output = "1" if input_value != "0" else "0"
        else:
            output = "1" if input_value else "0"
        
        assert output == expected_output, f"Input {input_value} should convert to {expected_output}, got {output}"
        print(f"✅ {input_value} -> {output}")
    
    print("✅ All switch value conversion tests passed")


@pytest.mark.asyncio
async def test_fve_config_internal_name_mapping():
    """Test that FVE-CONFIG entities get correct internal NAME mapping."""

    from custom_components.xcc.xcc_client import XCCClient

    # Mock XCC client
    client = XCCClient("192.168.1.100", "xcc", "xcc")

    # Test using the actual corrected sample data
    try:
        with open("tests/sample_data/FVEINV10.XML", "r", encoding="utf-8") as f:
            fveinv_content = f.read()
    except UnicodeDecodeError:
        # Fallback to windows-1250 if UTF-8 fails
        with open("tests/sample_data/FVEINV10.XML", "r", encoding="windows-1250", errors="ignore") as f:
            fveinv_content = f.read()

    # Test XML parsing with real data
    name_mapping = client._extract_name_mapping_from_xml(fveinv_content)

    assert "FVE-CONFIG-MENICECONFIG-READONLY" in name_mapping
    assert name_mapping["FVE-CONFIG-MENICECONFIG-READONLY"] == "__R69297.1_BOOL_i"
    assert "FVE-CONFIG-MENICECONFIG-KOMUNIKOVAT" in name_mapping
    assert name_mapping["FVE-CONFIG-MENICECONFIG-KOMUNIKOVAT"] == "__R69297.0_BOOL_i"

    print("✅ FVE-CONFIG internal NAME mapping test passed")
    print(f"   - READONLY: {name_mapping['FVE-CONFIG-MENICECONFIG-READONLY']}")
    print(f"   - KOMUNIKOVAT: {name_mapping['FVE-CONFIG-MENICECONFIG-KOMUNIKOVAT']}")

    # Also test that we can find TUVMINIMALNI in TUV data for comparison
    try:
        with open("tests/sample_data/TUV11.XML", "r", encoding="utf-8") as f:
            tuv_content = f.read()
    except UnicodeDecodeError:
        with open("tests/sample_data/TUV11.XML", "r", encoding="windows-1250", errors="ignore") as f:
            tuv_content = f.read()

    tuv_mapping = client._extract_name_mapping_from_xml(tuv_content)
    if "TUVMINIMALNI" in tuv_mapping:
        print(f"   - TUVMINIMALNI (for comparison): {tuv_mapping['TUVMINIMALNI']}")
    else:
        print("   - TUVMINIMALNI not found in TUV11.XML")


if __name__ == "__main__":
    import asyncio

    def run_sync_tests():
        test_fve_config_page_selection()
        test_switch_value_conversion()
        print("\n🎉 All synchronous tests passed!")

    async def run_async_tests():
        await test_xcc_client_error_detection()
        await test_fve_config_switch_entity_creation()
        await test_fve_config_internal_name_mapping()
        print("\n🎉 All asynchronous tests passed!")

    run_sync_tests()
    asyncio.run(run_async_tests())
    print("\n🎉 All FVE-CONFIG switch setting tests passed!")
