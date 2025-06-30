#!/usr/bin/env python3
"""
Simple script to analyze XCC descriptor files and identify changeable entities.
"""

import sys
import os
from pathlib import Path
from xml.etree import ElementTree as ET


def parse_descriptor_file(xml_content, page_name):
    """Parse a single descriptor XML file to find changeable entities."""
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as err:
        print(f"Failed to parse XML for {page_name}: {err}")
        return {}
        
    entity_configs = {}
    
    # Find all interactive elements that can be changed
    for element in root.iter():
        if element.tag in ['number', 'switch', 'choice', 'option', 'button']:
            prop = element.get('prop')
            if not prop:
                continue
                
            # Check if element is readonly
            config_attr = element.get('config', '')
            if 'readonly' in config_attr:
                continue  # Skip readonly elements
                
            # Get friendly names
            text = element.get('text', '')
            text_en = element.get('text_en', text)
            
            # Determine entity type and configuration
            entity_config = {
                'prop': prop,
                'friendly_name': text_en or text or prop,
                'page': page_name,
                'writable': True,
            }
            
            if element.tag == 'switch':
                entity_config.update({
                    'entity_type': 'switch',
                    'data_type': 'bool',
                })
                
            elif element.tag == 'number':
                min_val = element.get('min')
                max_val = element.get('max')
                entity_config.update({
                    'entity_type': 'number',
                    'data_type': 'real',
                    'min': float(min_val) if min_val else None,
                    'max': float(max_val) if max_val else None,
                    'unit': element.get('unit', ''),
                    'unit_en': element.get('unit_en', element.get('unit', '')),
                })
                
            elif element.tag == 'choice':
                # Get available options
                options = []
                for option in element.findall('option'):
                    option_data = {
                        'value': option.get('value', ''),
                        'text': option.get('text', ''),
                        'text_en': option.get('text_en', option.get('text', '')),
                    }
                    options.append(option_data)
                    
                entity_config.update({
                    'entity_type': 'select',
                    'data_type': 'enum',
                    'options': options,
                })
                
            elif element.tag == 'button':
                entity_config.update({
                    'entity_type': 'button',
                    'data_type': 'action',
                })
                
            else:
                continue  # Unknown element type
                
            entity_configs[prop] = entity_config
                
    return entity_configs


def parse_data_file(xml_content, page_name):
    """Parse a data XML file to get current values."""
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as err:
        print(f"Failed to parse XML for {page_name}: {err}")
        return {}
        
    current_values = {}
    
    # Find all INPUT elements with P and VALUE attributes
    for element in root.findall('.//INPUT'):
        prop = element.get('P')
        value = element.get('VALUE')
        if prop and value:
            current_values[prop] = value
            
    return current_values


def analyze_descriptors():
    """Analyze descriptor files to identify changeable entities."""
    
    # Use sample data from xcc_data directory
    data_files = {
        "STAVJED1.XML": "xcc_data/STAVJED1.XML",
        "OKRUH10.XML": "xcc_data/OKRUH10.XML", 
        "TUV11.XML": "xcc_data/TUV11.XML",
        "BIV1.XML": "xcc_data/BIV1.XML",
        "FVE4.XML": "xcc_data/FVE4.XML",
        "SPOT1.XML": "xcc_data/SPOT1.XML",
    }
    
    descriptor_files = {
        "STAVJED.XML": "xcc_data/STAVJED.XML",
        "OKRUH.XML": "xcc_data/OKRUH.XML",
        "TUV1.XML": "xcc_data/TUV1.XML", 
        "BIV.XML": "xcc_data/BIV.XML",
        "FVE.XML": "xcc_data/FVE.XML",
        "SPOT.XML": "xcc_data/SPOT.XML",
    }
    
    # Load sample data
    data_content = {}
    descriptor_content = {}
    
    print("📁 Loading sample data files...")
    for page_name, file_path in data_files.items():
        try:
            # Try different encodings for data files
            for encoding in ['windows-1250', 'iso-8859-1', 'utf-8']:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        data_content[page_name] = f.read()
                    print(f"✓ Loaded {page_name} ({len(data_content[page_name])} bytes) with {encoding}")
                    break
                except UnicodeDecodeError:
                    continue
            else:
                print(f"✗ Failed to load {page_name}: Could not decode with any encoding")
        except Exception as e:
            print(f"✗ Failed to load {page_name}: {e}")
    
    print("\n📋 Loading descriptor files...")
    for page_name, file_path in descriptor_files.items():
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                descriptor_content[page_name] = f.read()
            print(f"✓ Loaded {page_name} ({len(descriptor_content[page_name])} bytes)")
        except Exception as e:
            print(f"✗ Failed to load {page_name}: {e}")
    
    # Parse descriptors to find changeable entities
    print("\n🔍 Analyzing descriptor files for changeable entities...")
    all_entity_configs = {}
    for page_name, xml_content in descriptor_content.items():
        entity_configs = parse_descriptor_file(xml_content, page_name)
        all_entity_configs.update(entity_configs)
        print(f"✓ Found {len(entity_configs)} changeable entities in {page_name}")
    
    # Parse data files to get current values
    print("\n📊 Parsing data files for current values...")
    all_current_values = {}
    for page_name, xml_content in data_content.items():
        current_values = parse_data_file(xml_content, page_name)
        all_current_values.update(current_values)
        print(f"✓ Found {len(current_values)} current values in {page_name}")
    
    # Analyze and display results
    print(f"\n🎛️  CHANGEABLE ENTITIES ANALYSIS")
    print("=" * 80)
    print(f"Found {len(all_entity_configs)} changeable entities in descriptor files")
    print(f"Found {len(all_current_values)} total current values in data files")
    print()
    
    # Group by entity type
    by_type = {}
    for prop, config in all_entity_configs.items():
        entity_type = config.get('entity_type', 'unknown')
        if entity_type not in by_type:
            by_type[entity_type] = []
        by_type[entity_type].append((prop, config))
    
    # Display by type
    for entity_type, entities in by_type.items():
        print(f"\n🔧 {entity_type.upper()} ENTITIES ({len(entities)} found)")
        print("-" * 60)
        
        for prop, config in entities[:10]:  # Show first 10 of each type
            friendly_name = config.get('friendly_name', prop)
            current_value = all_current_values.get(prop, 'N/A')
            page = config.get('page', 'Unknown')
            
            print(f"  • {prop}")
            print(f"    Name: {friendly_name}")
            print(f"    Current: {current_value}")
            print(f"    Page: {page}")
            
            if entity_type == 'number':
                min_val = config.get('min')
                max_val = config.get('max')
                unit = config.get('unit', '')
                if min_val is not None or max_val is not None:
                    print(f"    Range: {min_val} to {max_val} {unit}")
                    
            elif entity_type == 'select':
                options = config.get('options', [])
                if options:
                    option_texts = [opt.get('text_en', opt.get('text', '')) for opt in options[:3]]
                    print(f"    Options: {', '.join(option_texts)}{'...' if len(options) > 3 else ''}")
            
            print()
        
        if len(entities) > 10:
            print(f"    ... and {len(entities) - 10} more {entity_type} entities")
            print()
    
    # Summary
    print(f"\n📈 SUMMARY")
    print("=" * 40)
    for entity_type, entities in by_type.items():
        print(f"{entity_type.capitalize()}: {len(entities)} entities")
    
    print(f"\nTotal changeable entities: {len(all_entity_configs)}")
    print(f"Total read-only entities: {len(all_current_values) - len(all_entity_configs)}")
    
    # Show some examples of entities that could be changed
    print(f"\n💡 EXAMPLES OF CHANGEABLE ENTITIES")
    print("=" * 50)
    
    # Find some interesting examples
    examples = []
    for prop, config in all_entity_configs.items():
        friendly_name = config.get('friendly_name', '')
        if any(keyword in friendly_name.lower() for keyword in ['temperature', 'teplota', 'switch', 'mode', 'enable']):
            examples.append((prop, config))
    
    for prop, config in examples[:5]:
        entity_type = config.get('entity_type', 'unknown')
        friendly_name = config.get('friendly_name', prop)
        current_value = all_current_values.get(prop, 'N/A')
        
        print(f"🎯 {prop} ({entity_type})")
        print(f"   {friendly_name}")
        print(f"   Current value: {current_value}")
        print()


if __name__ == "__main__":
    analyze_descriptors()
