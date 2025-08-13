#!/usr/bin/env python3
"""
Test NAST.XML integration and entity creation.

This test verifies that the NAST page (Heat Pump Settings) is properly
integrated and creates the expected entities.
"""

import pytest
import sys
from pathlib import Path
import re

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_nast_page_added_to_constants():
    """Test that nast.xml is properly added to the integration constants."""
    
    print(f"\n=== TESTING NAST PAGE CONSTANTS ===")
    
    # Load constants file
    const_file = project_root / "custom_components" / "xcc" / "const.py"
    
    if not const_file.exists():
        pytest.skip("const.py not found")
    
    with open(const_file, 'r', encoding='utf-8') as f:
        const_content = f.read()
    
    # Check if nast.xml is in descriptor pages
    descriptor_pages_match = re.search(r'XCC_DESCRIPTOR_PAGES.*?\[(.*?)\]', const_content, re.DOTALL)
    descriptor_pages = descriptor_pages_match.group(1) if descriptor_pages_match else ""
    
    nast_in_descriptors = "nast.xml" in descriptor_pages
    
    # Check if NAST.XML is in data pages
    data_pages_match = re.search(r'XCC_DATA_PAGES.*?\[(.*?)\]', const_content, re.DOTALL)
    data_pages = data_pages_match.group(1) if data_pages_match else ""
    
    nast_in_data = "NAST.XML" in data_pages
    
    print(f"🔍 CONSTANTS VERIFICATION:")
    print(f"  nast.xml in XCC_DESCRIPTOR_PAGES: {nast_in_descriptors}")
    print(f"  NAST.XML in XCC_DATA_PAGES: {nast_in_data}")
    
    # Test assertions
    assert nast_in_descriptors, "nast.xml should be added to XCC_DESCRIPTOR_PAGES"
    assert nast_in_data, "NAST.XML should be added to XCC_DATA_PAGES"
    
    print(f"✅ NAST page constants test PASSED!")


def test_nast_descriptor_analysis():
    """Test analysis of the NAST descriptor content."""
    
    print(f"\n=== TESTING NAST DESCRIPTOR ANALYSIS ===")
    
    # Load the NAST descriptor we discovered
    nast_file = project_root / "nast_data_nast_xml"
    
    if not nast_file.exists():
        pytest.skip("NAST descriptor file not found")
    
    with open(nast_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"📄 NAST descriptor: {len(content)} characters")
    
    # Parse the structure
    page_match = re.search(r'<page[^>]*name="([^"]*)"[^>]*name_en="([^"]*)"', content)
    if page_match:
        print(f"   Name (CZ): {page_match.group(1)}")
        print(f"   Name (EN): {page_match.group(2)}")
    
    # Find all blocks
    blocks = re.findall(r'<block[^>]*data="([^"]*)"[^>]*name="([^"]*)"[^>]*name_en="([^"]*)"', content)
    print(f"\n📦 BLOCKS FOUND ({len(blocks)}):")
    for i, (data_ref, name_cz, name_en) in enumerate(blocks, 1):
        print(f"   {i}. {data_ref} - {name_en} ({name_cz})")
    
    # Count entity types
    number_props = re.findall(r'<number[^>]*prop="([^"]*)"', content)
    choice_props = re.findall(r'<choice[^>]*prop="([^"]*)"', content)
    button_props = re.findall(r'<button[^>]*prop="([^"]*)"', content)
    text_props = re.findall(r'<text[^>]*prop="([^"]*)"', content)
    label_props = re.findall(r'<label[^>]*prop="([^"]*)"', content)
    
    print(f"\n🏷️  ENTITY TYPES:")
    print(f"   Numbers: {len(number_props)}")
    print(f"   Choices: {len(choice_props)}")
    print(f"   Buttons: {len(button_props)}")
    print(f"   Text: {len(text_props)}")
    print(f"   Labels: {len(label_props)}")
    
    total_entities = len(number_props) + len(choice_props) + len(button_props) + len(text_props)
    print(f"   📊 Total interactive entities: {total_entities}")
    
    # Show interesting entities
    print(f"\n🎯 INTERESTING ENTITIES:")
    
    # Sensor corrections
    sensor_corrections = [p for p in number_props if re.match(r'B\d+-I$', p)]
    print(f"   Sensor corrections: {len(sensor_corrections)} ({', '.join(sensor_corrections[:5])}...)")
    
    # Multi-zone offsets
    mzo_offsets = [p for p in number_props if 'MZO-ZONA' in p and 'OFFSET' in p]
    print(f"   Multi-zone offsets: {len(mzo_offsets)} ({', '.join(mzo_offsets[:3])}...)")
    
    # Power restrictions
    power_restrictions = [p for p in number_props if 'OMEZENI' in p or p.startswith('E')]
    print(f"   Power restrictions: {len(power_restrictions)} ({', '.join(power_restrictions[:3])}...)")
    
    # Heat pump controls
    hp_controls = [p for p in choice_props if 'TCODSTAVENI' in p]
    print(f"   Heat pump controls: {len(hp_controls)} ({', '.join(hp_controls[:3])}...)")
    
    # Test assertions
    assert len(blocks) >= 3, f"Should find at least 3 blocks, found {len(blocks)}"
    assert len(number_props) >= 50, f"Should find many number entities, found {len(number_props)}"
    assert len(choice_props) >= 20, f"Should find many choice entities, found {len(choice_props)}"
    assert len(sensor_corrections) >= 10, f"Should find sensor corrections, found {len(sensor_corrections)}"
    assert len(hp_controls) >= 1, f"Should find heat pump controls, found {len(hp_controls)}"
    
    print(f"✅ NAST descriptor analysis test PASSED!")
    
    return total_entities


def test_nast_integration_impact():
    """Test the expected impact of adding NAST page to the integration."""
    
    print(f"\n=== TESTING NAST INTEGRATION IMPACT ===")
    
    # Analyze current entity counts from logs
    log_file = project_root / "homeassistant.log"
    
    current_entities = 0
    if log_file.exists():
        with open(log_file, 'r', encoding='utf-8') as f:
            log_content = f.read()
        
        # Find current entity distribution
        distribution_match = re.search(r"Final entity distribution:.*'total': (\d+)", log_content)
        if distribution_match:
            current_entities = int(distribution_match.group(1))
    
    # Estimate NAST entities from descriptor analysis
    nast_entities = test_nast_descriptor_analysis()
    
    print(f"📊 INTEGRATION IMPACT:")
    print(f"   Current entities: {current_entities}")
    print(f"   NAST entities: {nast_entities}")
    print(f"   New total: {current_entities + nast_entities}")
    print(f"   Improvement: +{nast_entities} entities ({nast_entities/current_entities*100:.1f}% increase)")
    
    print(f"\n🎯 NEW CAPABILITIES:")
    print(f"   🌡️  Sensor temperature corrections (B0-I, B4-I, etc.)")
    print(f"   🏠 Multi-zone temperature offsets (16 zones)")
    print(f"   🔧 Power restriction controls (global, time-based, external, thermal)")
    print(f"   🔄 Heat pump on/off switches (up to 10 heat pumps)")
    print(f"   💾 System backup/restore functionality")
    print(f"   📋 Circuit priority settings")
    
    print(f"\n🚀 USER BENEFITS:")
    print(f"   ✅ Fine-tune sensor accuracy with correction offsets")
    print(f"   ✅ Control power consumption limits")
    print(f"   ✅ Manage multiple heat pump units")
    print(f"   ✅ Backup and restore system configurations")
    print(f"   ✅ Adjust multi-zone heating priorities")
    
    # Test assertions
    assert nast_entities > 50, f"NAST should provide significant entities, found {nast_entities}"
    
    print(f"✅ NAST integration impact test PASSED!")


def test_nast_entity_examples():
    """Test specific examples of entities that will be created from NAST page."""
    
    print(f"\n=== TESTING NAST ENTITY EXAMPLES ===")
    
    # Load the NAST descriptor
    nast_file = project_root / "nast_data_nast_xml"
    
    if not nast_file.exists():
        pytest.skip("NAST descriptor file not found")
    
    with open(nast_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Test specific entity examples
    examples = [
        ("B0-I", "number", "Sensor B0 temperature correction"),
        ("OFFSETBAZ", "number", "Pool temperature offset"),
        ("MZO-ZONA0-OFFSET", "number", "Multi-zone 0 temperature offset"),
        ("OMEZENIVYKONUGLOBALNI", "number", "Global power restriction percentage"),
        ("TCODSTAVENI0", "select", "Heat pump I on/off control"),
        ("FLASH-READWRITE", "button", "System backup/restore button"),
        ("OVPPOVOLENI", "select", "Time-based power restriction enable/disable"),
    ]
    
    print(f"🔍 ENTITY EXAMPLES:")
    
    found_examples = []
    for prop, expected_type, description in examples:
        # Check if entity exists in descriptor
        if expected_type == "number":
            pattern = rf'<number[^>]*prop="{re.escape(prop)}"'
        elif expected_type == "select":
            pattern = rf'<choice[^>]*prop="{re.escape(prop)}"'
        elif expected_type == "button":
            pattern = rf'<button[^>]*prop="{re.escape(prop)}"'
        else:
            continue
        
        match = re.search(pattern, content)
        if match:
            found_examples.append((prop, expected_type, description))
            print(f"   ✅ {prop} ({expected_type}) - {description}")
        else:
            print(f"   ❌ {prop} ({expected_type}) - NOT FOUND")
    
    print(f"\n📊 EXAMPLE VERIFICATION:")
    print(f"   Found: {len(found_examples)}/{len(examples)} expected entities")
    
    # Test assertions
    assert len(found_examples) >= len(examples) * 0.7, f"Should find most example entities"
    
    print(f"✅ NAST entity examples test PASSED!")


if __name__ == "__main__":
    """Run tests directly for debugging."""
    print("🧪 Running NAST Integration Tests")
    print("=" * 60)
    
    try:
        test_nast_page_added_to_constants()
        total_entities = test_nast_descriptor_analysis()
        test_nast_integration_impact()
        test_nast_entity_examples()
        
        print("\n" + "=" * 60)
        print("🎉 ALL NAST INTEGRATION TESTS PASSED!")
        print(f"✅ NAST page successfully added to integration")
        print(f"📊 Expected additional entities: ~{total_entities}")
        print(f"🔧 Restart Home Assistant to see new NAST entities")
        print(f"🎯 Look for sensor corrections, power controls, and HP switches")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
