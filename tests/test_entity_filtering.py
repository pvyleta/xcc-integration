"""Test entity filtering to only create entities with both descriptor and data."""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_entity_filtering_removes_data_only_entities():
    """Test that entities with data but no descriptor are filtered out."""
    
    try:
        sys.path.insert(0, str(project_root / "custom_components" / "xcc"))
        from descriptor_parser import XCCDescriptorParser
    except ImportError as e:
        pytest.skip(f"Cannot import XCCDescriptorParser: {e}")
    
    # Load TUV1.XML and TUV11.XML specifically
    tuv1_path = project_root / "sample_data" / "TUV1.XML"
    tuv11_path = project_root / "sample_data" / "TUV11.XML"
    
    if not tuv1_path.exists() or not tuv11_path.exists():
        pytest.skip("TUV sample files not found")
    
    # Parse descriptor
    with open(tuv1_path, 'r', encoding='utf-8') as f:
        tuv1_content = f.read()
    
    parser = XCCDescriptorParser()
    entity_configs = parser._parse_single_descriptor(tuv1_content, 'TUV1.XML')
    
    # Parse data
    try:
        with open(tuv11_path, 'r', encoding='utf-8') as f:
            tuv11_content = f.read()
    except UnicodeDecodeError:
        with open(tuv11_path, 'r', encoding='windows-1250') as f:
            tuv11_content = f.read()
    
    import xml.etree.ElementTree as ET
    root = ET.fromstring(tuv11_content)
    data_props = set()
    for input_elem in root.findall(".//INPUT"):
        prop = input_elem.get("P")
        if prop:
            data_props.add(prop)
    
    print(f"\n🔍 Entity Filtering Analysis")
    print("=" * 30)
    print(f"📊 Descriptors found: {len(entity_configs)}")
    print(f"📊 Data values found: {len(data_props)}")
    
    # Find entities with both descriptor and data
    both_descriptor_and_data = []
    descriptor_only = []
    data_only = []
    
    # Check descriptor entities
    for prop in entity_configs:
        if prop in data_props:
            both_descriptor_and_data.append(prop)
        else:
            descriptor_only.append(prop)
    
    # Check data entities
    for prop in data_props:
        if prop not in entity_configs:
            data_only.append(prop)
    
    print(f"\n✅ Both descriptor + data: {len(both_descriptor_and_data)}")
    print(f"🚫 Descriptor only: {len(descriptor_only)}")
    print(f"🚫 Data only: {len(data_only)}")
    
    # Show some examples
    if both_descriptor_and_data:
        print(f"\n🎉 Examples with both (should be created):")
        for prop in both_descriptor_and_data[:5]:
            config = entity_configs[prop]
            entity_type = config.get('entity_type', 'unknown')
            friendly_name = config.get('friendly_name_en', prop)
            print(f"   ✅ {prop} ({entity_type}): {friendly_name}")
    
    if descriptor_only:
        print(f"\n⚠️  Examples with descriptor only (should be filtered out):")
        for prop in descriptor_only[:5]:
            config = entity_configs[prop]
            entity_type = config.get('entity_type', 'unknown')
            friendly_name = config.get('friendly_name_en', prop)
            print(f"   🚫 {prop} ({entity_type}): {friendly_name}")
    
    if data_only:
        print(f"\n⚠️  Examples with data only (should be filtered out):")
        for prop in data_only[:5]:
            print(f"   🚫 {prop} (data only)")
    
    # Calculate filtering efficiency
    total_potential = len(entity_configs) + len(data_only)
    filtered_out = len(descriptor_only) + len(data_only)
    efficiency = (filtered_out / total_potential * 100) if total_potential > 0 else 0
    
    print(f"\n📈 Filtering Efficiency:")
    print(f"   Total potential entities: {total_potential}")
    print(f"   Entities with both: {len(both_descriptor_and_data)}")
    print(f"   Filtered out: {filtered_out}")
    print(f"   Efficiency: {efficiency:.1f}% filtered out")
    
    # Assertions
    assert len(both_descriptor_and_data) > 0, "Should have some entities with both descriptor and data"
    assert len(descriptor_only) > 0, "Should have some descriptor-only entities to filter"
    assert len(data_only) > 0, "Should have some data-only entities to filter"
    
    # Should filter out a significant portion
    assert efficiency > 50, f"Should filter out >50% of entities, got {efficiency:.1f}%"
    
    return {
        'both': both_descriptor_and_data,
        'descriptor_only': descriptor_only,
        'data_only': data_only,
        'efficiency': efficiency
    }


def test_filtering_preserves_important_entities():
    """Test that filtering preserves important entities like TUVPOZADOVANA."""
    
    try:
        sys.path.insert(0, str(project_root / "custom_components" / "xcc"))
        from descriptor_parser import XCCDescriptorParser
    except ImportError as e:
        pytest.skip(f"Cannot import XCCDescriptorParser: {e}")
    
    # Load TUV files
    tuv1_path = project_root / "sample_data" / "TUV1.XML"
    tuv11_path = project_root / "sample_data" / "TUV11.XML"
    
    if not tuv1_path.exists() or not tuv11_path.exists():
        pytest.skip("TUV sample files not found")
    
    # Parse descriptor
    with open(tuv1_path, 'r', encoding='utf-8') as f:
        tuv1_content = f.read()
    
    parser = XCCDescriptorParser()
    entity_configs = parser._parse_single_descriptor(tuv1_content, 'TUV1.XML')
    
    # Parse data
    try:
        with open(tuv11_path, 'r', encoding='utf-8') as f:
            tuv11_content = f.read()
    except UnicodeDecodeError:
        with open(tuv11_path, 'r', encoding='windows-1250') as f:
            tuv11_content = f.read()
    
    import xml.etree.ElementTree as ET
    root = ET.fromstring(tuv11_content)
    data_props = set()
    for input_elem in root.findall(".//INPUT"):
        prop = input_elem.get("P")
        if prop:
            data_props.add(prop)
    
    # Important entities that should be preserved
    important_entities = [
        "TUVPOZADOVANA",      # Requested temperature
        "TUVMINIMALNI",       # Minimum temperature  
        "TUVPOZADOVANA2",     # Requested temperature 2
        "TUVUTLUM",           # Attenuation temperature
        "TSC-TEPLOTA",        # Sanitation temperature
        "TSC-INTERVALSANITACE", # Sanitation interval
    ]
    
    print(f"\n🎯 Testing Important Entity Preservation")
    print("=" * 40)
    
    preserved_count = 0
    for prop in important_entities:
        has_descriptor = prop in entity_configs
        has_data = prop in data_props
        will_be_preserved = has_descriptor and has_data
        
        status = "✅ PRESERVED" if will_be_preserved else "❌ FILTERED"
        print(f"{status}: {prop} (desc: {has_descriptor}, data: {has_data})")
        
        if will_be_preserved:
            preserved_count += 1
    
    preservation_rate = (preserved_count / len(important_entities) * 100)
    print(f"\n📊 Preservation Rate: {preservation_rate:.1f}% ({preserved_count}/{len(important_entities)})")
    
    # Should preserve most important entities
    assert preservation_rate >= 75, f"Should preserve >=75% of important entities, got {preservation_rate:.1f}%"
    
    # Specifically check TUVPOZADOVANA
    assert "TUVPOZADOVANA" in entity_configs, "TUVPOZADOVANA should have descriptor"
    assert "TUVPOZADOVANA" in data_props, "TUVPOZADOVANA should have data"
    
    return preserved_count, len(important_entities)


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v", "-s"])
