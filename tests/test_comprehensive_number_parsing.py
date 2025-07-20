"""Comprehensive test for number entity parsing from sample data."""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_comprehensive_number_entity_parsing():
    """Test comprehensive number entity parsing from all sample descriptor and data files."""
    
    try:
        sys.path.insert(0, str(project_root / "custom_components" / "xcc"))
        from descriptor_parser import XCCDescriptorParser
    except ImportError as e:
        pytest.skip(f"Cannot import XCCDescriptorParser: {e}")
    
    # Define the descriptor-data file pairs (like in XCC CLI)
    file_pairs = [
        ("TUV1.XML", "TUV11.XML"),
        ("STAVJED.XML", "STAVJED1.XML"),
        ("OKRUH.XML", "OKRUH10.XML"),
        ("BIV.XML", "BIV1.XML"),
        ("FVE.XML", "FVE4.XML"),
        ("SPOT.XML", "SPOT1.XML")
    ]
    
    parser = XCCDescriptorParser()
    all_number_entities = {}
    all_data_values = {}
    
    print("\n🔍 Comprehensive Number Entity Analysis")
    print("=" * 50)
    
    # Parse all descriptor files for number entities
    for desc_file, data_file in file_pairs:
        desc_path = project_root / "tests" / "sample_data" / desc_file
        data_path = project_root / "tests" / "sample_data" / data_file
        
        if not desc_path.exists():
            print(f"⚠️  Descriptor file not found: {desc_file}")
            continue
            
        if not data_path.exists():
            print(f"⚠️  Data file not found: {data_file}")
            continue
        
        # Parse descriptor file
        try:
            with open(desc_path, 'r', encoding='utf-8') as f:
                desc_content = f.read()
        except UnicodeDecodeError:
            try:
                with open(desc_path, 'r', encoding='windows-1250') as f:
                    desc_content = f.read()
            except Exception as e:
                print(f"❌ Error reading {desc_file}: {e}")
                continue
        
        entity_configs = parser._parse_single_descriptor(desc_content, desc_file)
        
        # Filter for number entities
        number_entities = {prop: config for prop, config in entity_configs.items() 
                          if config.get('entity_type') == 'number'}
        
        print(f"\n📋 {desc_file}: Found {len(number_entities)} number entities")
        for prop, config in number_entities.items():
            writable = "✏️ " if config.get('writable') else "👁️ "
            friendly_name = config.get('friendly_name_en', prop)
            unit = config.get('unit', 'no unit')
            print(f"  {writable}{prop}: {friendly_name} ({unit})")
            all_number_entities[prop] = {
                'config': config,
                'source_file': desc_file,
                'friendly_name': friendly_name,
                'unit': unit,
                'writable': config.get('writable', False)
            }
        
        # Parse data file for values
        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                data_content = f.read()
        except UnicodeDecodeError:
            try:
                with open(data_path, 'r', encoding='windows-1250') as f:
                    data_content = f.read()
            except Exception as e:
                print(f"❌ Error reading {data_file}: {e}")
                continue
        
        # Parse INPUT elements manually (like XCC CLI does)
        import xml.etree.ElementTree as ET
        try:
            root = ET.fromstring(data_content)
            for input_elem in root.findall(".//INPUT"):
                prop = input_elem.get("P")
                value = input_elem.get("VALUE")
                name = input_elem.get("NAME", "")
                
                if prop and value is not None:
                    all_data_values[prop] = {
                        'value': value,
                        'name': name,
                        'source_file': data_file
                    }
        except ET.ParseError as e:
            print(f"❌ Error parsing XML in {data_file}: {e}")
    
    # Analysis: Match descriptors with data values
    print(f"\n🎯 Analysis Results")
    print("=" * 30)
    print(f"📊 Total number entities in descriptors: {len(all_number_entities)}")
    print(f"📊 Total data values available: {len(all_data_values)}")
    
    # Find matches
    matched_entities = []
    unmatched_descriptors = []
    unmatched_data = []
    
    for prop, entity_info in all_number_entities.items():
        if prop in all_data_values:
            data_info = all_data_values[prop]
            matched_entities.append({
                'prop': prop,
                'friendly_name': entity_info['friendly_name'],
                'unit': entity_info['unit'],
                'writable': entity_info['writable'],
                'value': data_info['value'],
                'data_type': data_info['name'],
                'desc_file': entity_info['source_file'],
                'data_file': data_info['source_file']
            })
        else:
            unmatched_descriptors.append(prop)
    
    # Find data without descriptors
    for prop in all_data_values:
        if prop not in all_number_entities:
            unmatched_data.append(prop)
    
    print(f"\n✅ Successfully matched: {len(matched_entities)} number entities")
    print(f"❌ Descriptors without data: {len(unmatched_descriptors)}")
    print(f"❓ Data without number descriptors: {len(unmatched_data)}")
    
    # Show successful matches
    if matched_entities:
        print(f"\n🎉 Successfully Matched Number Entities:")
        print("-" * 60)
        for entity in matched_entities[:10]:  # Show first 10
            writable_icon = "✏️ " if entity['writable'] else "👁️ "
            print(f"{writable_icon}{entity['prop']}")
            print(f"   Name: {entity['friendly_name']}")
            print(f"   Value: {entity['value']} {entity['unit']}")
            print(f"   Type: {entity['data_type']}")
            print(f"   Files: {entity['desc_file']} + {entity['data_file']}")
            print()
        
        if len(matched_entities) > 10:
            print(f"   ... and {len(matched_entities) - 10} more")
    
    # Show problematic cases
    if unmatched_descriptors:
        print(f"\n⚠️  Number entities without data values:")
        for prop in unmatched_descriptors[:5]:
            entity_info = all_number_entities[prop]
            print(f"   {prop} ({entity_info['source_file']}) - {entity_info['friendly_name']}")
        if len(unmatched_descriptors) > 5:
            print(f"   ... and {len(unmatched_descriptors) - 5} more")
    
    if unmatched_data:
        print(f"\n🔍 Data values that could be number entities:")
        for prop in unmatched_data[:10]:
            data_info = all_data_values[prop]
            # Check if it looks like a number
            if 'REAL' in data_info['name'] or 'INT' in data_info['name']:
                print(f"   {prop} = {data_info['value']} ({data_info['name']}) from {data_info['source_file']}")
    
    # Assertions for the test
    assert len(all_number_entities) > 0, "Should find at least some number entities in descriptors"
    assert len(all_data_values) > 0, "Should find at least some data values"
    assert len(matched_entities) > 0, "Should successfully match at least some number entities with data"
    
    # Success rate should be reasonable
    success_rate = len(matched_entities) / len(all_number_entities) if all_number_entities else 0
    print(f"\n📈 Success Rate: {success_rate:.1%} ({len(matched_entities)}/{len(all_number_entities)})")
    
    # We should have a reasonable success rate (lowered expectation due to conditional entities)
    assert success_rate > 0.2, f"Success rate too low: {success_rate:.1%}. Expected > 20%"
    
    # Test passed if we reach here without any assertion errors
    print(f"\n✅ Test completed successfully with {success_rate:.1%} success rate")


def test_specific_tuv_number_entities():
    """Test specific TUV number entities that should work."""
    
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
    data_values = {}
    for input_elem in root.findall(".//INPUT"):
        prop = input_elem.get("P")
        value = input_elem.get("VALUE")
        if prop and value is not None:
            data_values[prop] = value
    
    # Test specific entities that should be numbers
    expected_number_entities = [
        "TUVPOZADOVANA",      # Requested temperature
        "TUVMINIMALNI",       # Minimum temperature  
        "TUVPOZADOVANA2",     # Requested temperature 2
        "TUVUTLUM",           # Attenuation temperature
        "TUVUTLUMMIN",        # Attenuation minimum
        "TCR-TEPLOTAVYPNUTI", # Turnoff temperature
        "TSC-TEPLOTA",        # Sanitation temperature
        "TSC-INTERVALSANITACE", # Sanitation interval
    ]
    
    print(f"\n🎯 Testing Specific TUV Number Entities")
    print("=" * 40)
    
    successful = []
    failed = []
    
    for prop in expected_number_entities:
        # Check if it's in descriptor as number
        if prop in entity_configs and entity_configs[prop].get('entity_type') == 'number':
            # Check if it has data value
            if prop in data_values:
                config = entity_configs[prop]
                friendly_name = config.get('friendly_name_en', prop)
                value = data_values[prop]
                writable = config.get('writable', False)
                
                print(f"✅ {prop}: {friendly_name} = {value} ({'writable' if writable else 'readonly'})")
                successful.append(prop)
            else:
                print(f"❌ {prop}: Found in descriptor but no data value")
                failed.append(prop)
        else:
            print(f"❌ {prop}: Not found as number in descriptor")
            failed.append(prop)
    
    print(f"\n📊 Results: {len(successful)} successful, {len(failed)} failed")
    
    # Should have most of these working
    assert len(successful) >= len(expected_number_entities) // 2, \
        f"Should have at least half of expected entities working. Got {len(successful)}/{len(expected_number_entities)}"
    
    # Test passed if we reach here without any assertion errors


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v", "-s"])
