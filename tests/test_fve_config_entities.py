"""Test FVE-CONFIG entities parsing in FVEINV descriptor."""

import pytest
from pathlib import Path

# Get the project root directory
project_root = Path(__file__).parent.parent


def test_fve_config_meniceconfig_readonly_discovery():
    """Test that FVE-CONFIG-MENICECONFIG-READONLY is discovered correctly."""
    try:
        from custom_components.xcc.descriptor_parser import XCCDescriptorParser
    except ImportError:
        pytest.skip("XCC descriptor parser not available (Home Assistant dependencies missing)")

    # Load the FVEINV descriptor
    sample_dir = project_root / "tests" / "sample_data"
    fveinv_desc_file = sample_dir / "FVEINV.XML"
    
    if not fveinv_desc_file.exists():
        pytest.skip("FVEINV.XML sample file not found")

    with open(fveinv_desc_file, 'r', encoding='utf-8') as f:
        content = f.read()

    parser = XCCDescriptorParser()
    configs = parser._parse_single_descriptor(content, 'fveinv.xml')

    # Check if our target entity is found
    target = 'FVE-CONFIG-MENICECONFIG-READONLY'
    assert target in configs, f"Entity {target} should be discovered"
    
    # Verify the configuration
    config = configs[target]
    assert config['entity_type'] == 'switch', "Should be a switch entity (controls read-only mode)"
    assert config['friendly_name'] == 'Read-only Mode', "Should have correct friendly name"
    assert config['icon'] == 'mdi:lock', "Should have lock icon"
    assert config['page'] == 'pv_inverter', "Should be on pv_inverter page"
    assert config.get('writable', False) == True, "Should be writable (can be toggled)"

    print(f"✅ Successfully found {target} with config: {config}")


def test_all_fve_config_entities_discovered():
    """Test that all FVE-CONFIG entities are discovered."""
    try:
        from custom_components.xcc.descriptor_parser import XCCDescriptorParser
    except ImportError:
        pytest.skip("XCC descriptor parser not available (Home Assistant dependencies missing)")

    # Load the FVEINV descriptor
    sample_dir = project_root / "tests" / "sample_data"
    fveinv_desc_file = sample_dir / "FVEINV.XML"
    
    if not fveinv_desc_file.exists():
        pytest.skip("FVEINV.XML sample file not found")

    with open(fveinv_desc_file, 'r', encoding='utf-8') as f:
        content = f.read()

    parser = XCCDescriptorParser()
    configs = parser._parse_single_descriptor(content, 'fveinv.xml')

    # Find all FVE-CONFIG entities
    fve_config_entities = [key for key in configs.keys() if key.startswith('FVE-CONFIG-')]
    
    print(f"Found {len(fve_config_entities)} FVE-CONFIG entities:")
    for entity in sorted(fve_config_entities):
        config = configs[entity]
        print(f"  - {entity}: {config['friendly_name']} ({config['entity_type']})")

    # Expected FVE-CONFIG entities based on the FVEINV.XML file
    expected_entities = [
        'FVE-CONFIG-MENICECONFIG-READONLY',
        'FVE-CONFIG-MENICECONFIG-KOMUNIKOVAT',
    ]

    for expected in expected_entities:
        assert expected in fve_config_entities, f"Expected entity {expected} not found"

    # Should have at least the expected entities
    assert len(fve_config_entities) >= len(expected_entities), f"Should have at least {len(expected_entities)} FVE-CONFIG entities"


def test_fve_config_vs_fvestats_entities():
    """Test that both FVE-CONFIG and FVESTATS entities are discovered."""
    try:
        from custom_components.xcc.descriptor_parser import XCCDescriptorParser
    except ImportError:
        pytest.skip("XCC descriptor parser not available (Home Assistant dependencies missing)")

    # Load the FVEINV descriptor
    sample_dir = project_root / "tests" / "sample_data"
    fveinv_desc_file = sample_dir / "FVEINV.XML"
    
    if not fveinv_desc_file.exists():
        pytest.skip("FVEINV.XML sample file not found")

    with open(fveinv_desc_file, 'r', encoding='utf-8') as f:
        content = f.read()

    parser = XCCDescriptorParser()
    configs = parser._parse_single_descriptor(content, 'fveinv.xml')

    # Count different entity types
    fve_config_entities = [key for key in configs.keys() if key.startswith('FVE-CONFIG-')]
    fvestats_entities = [key for key in configs.keys() if key.startswith('FVESTATS-')]
    
    print(f"Entity breakdown:")
    print(f"  FVE-CONFIG entities: {len(fve_config_entities)}")
    print(f"  FVESTATS entities: {len(fvestats_entities)}")
    print(f"  Total entities: {len(configs)}")

    # Should have both types
    assert len(fve_config_entities) > 0, "Should have FVE-CONFIG entities"
    assert len(fvestats_entities) > 0, "Should have FVESTATS entities"
    
    # FVESTATS should be the majority (status/measurement entities)
    assert len(fvestats_entities) > len(fve_config_entities), "Should have more FVESTATS than FVE-CONFIG entities"


def test_fve_config_entity_properties():
    """Test that FVE-CONFIG entities have appropriate properties."""
    try:
        from custom_components.xcc.descriptor_parser import XCCDescriptorParser
    except ImportError:
        pytest.skip("XCC descriptor parser not available (Home Assistant dependencies missing)")

    # Load the FVEINV descriptor
    sample_dir = project_root / "tests" / "sample_data"
    fveinv_desc_file = sample_dir / "FVEINV.XML"
    
    if not fveinv_desc_file.exists():
        pytest.skip("FVEINV.XML sample file not found")

    with open(fveinv_desc_file, 'r', encoding='utf-8') as f:
        content = f.read()

    parser = XCCDescriptorParser()
    configs = parser._parse_single_descriptor(content, 'fveinv.xml')

    # Test specific FVE-CONFIG entities
    test_cases = {
        'FVE-CONFIG-MENICECONFIG-READONLY': {
            'friendly_name': 'Read-only Mode',
            'icon': 'mdi:lock',
            'entity_type': 'switch',  # This is a switch to control read-only mode
            'writable': True,
        },
        'FVE-CONFIG-MENICECONFIG-KOMUNIKOVAT': {
            'friendly_name': 'Communication Enabled',
            'icon': 'mdi:network',
            'entity_type': 'switch',  # This is a switch to enable/disable communication
            'writable': True,
        }
    }

    for entity_name, expected_props in test_cases.items():
        if entity_name in configs:
            config = configs[entity_name]
            for prop, expected_value in expected_props.items():
                actual_value = config.get(prop)
                assert actual_value == expected_value, f"Entity {entity_name} property {prop}: expected {expected_value}, got {actual_value}"
            print(f"✅ {entity_name}: {config['friendly_name']} ({config['entity_type']}) - writable: {config.get('writable', False)}")
        else:
            print(f"⚠️  {entity_name} not found in configs")
