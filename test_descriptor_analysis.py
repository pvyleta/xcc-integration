#!/usr/bin/env python3
"""
Test script to analyze XCC descriptor files and identify changeable entities.
"""

import sys
import os
from pathlib import Path

# Add the custom_components directory to the path
sys.path.insert(0, str(Path(__file__).parent / "custom_components" / "xcc"))

from descriptor_parser import XCCDescriptorParser
from xcc_client import parse_xml_entities


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
            with open(file_path, 'r', encoding='utf-8') as f:
                data_content[page_name] = f.read()
            print(f"✓ Loaded {page_name} ({len(data_content[page_name])} bytes)")
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
    parser = XCCDescriptorParser()
    entity_configs = parser.parse_descriptor_files(descriptor_content)
    
    # Parse data files to get current values
    print("\n📊 Parsing data files for current values...")
    all_entities = []
    for page_name, xml_content in data_content.items():
        entities = parse_xml_entities(xml_content, page_name)
        all_entities.extend(entities)
        print(f"✓ Parsed {len(entities)} entities from {page_name}")
    
    # Create lookup of current values by prop
    current_values = {}
    for entity in all_entities:
        # Extract prop from entity_id (remove xcc_ prefix)
        entity_id = entity.get('entity_id', '')
        if entity_id.startswith('xcc_'):
            prop = entity_id[4:].upper()  # Remove xcc_ and convert to uppercase
            current_values[prop] = entity.get('state', 'Unknown')
    
    # Analyze and display results
    print(f"\n🎛️  CHANGEABLE ENTITIES ANALYSIS")
    print("=" * 80)
    print(f"Found {len(entity_configs)} changeable entities in descriptor files")
    print(f"Found {len(all_entities)} total entities in data files")
    print()
    
    # Group by entity type
    by_type = {}
    for prop, config in entity_configs.items():
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
            current_value = current_values.get(prop, 'N/A')
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
    
    print(f"\nTotal changeable entities: {len(entity_configs)}")
    print(f"Total read-only entities: {len(all_entities) - len(entity_configs)}")
    
    # Show some examples of entities that could be changed
    print(f"\n💡 EXAMPLES OF CHANGEABLE ENTITIES")
    print("=" * 50)
    
    # Find some interesting examples
    examples = []
    for prop, config in entity_configs.items():
        friendly_name = config.get('friendly_name', '')
        if any(keyword in friendly_name.lower() for keyword in ['temperature', 'teplota', 'switch', 'mode']):
            examples.append((prop, config))
    
    for prop, config in examples[:5]:
        entity_type = config.get('entity_type', 'unknown')
        friendly_name = config.get('friendly_name', prop)
        current_value = current_values.get(prop, 'N/A')
        
        print(f"🎯 {prop} ({entity_type})")
        print(f"   {friendly_name}")
        print(f"   Current value: {current_value}")
        print()


if __name__ == "__main__":
    analyze_descriptors()
