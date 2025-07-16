#!/usr/bin/env python3
"""Test the actual descriptor parser with the new friendly name logic."""

import sys
import os
import importlib.util
import logging
from pathlib import Path

def test_actual_parser():
    """Test the actual descriptor parser with the new friendly name logic."""

    print("🔧 Testing Actual Descriptor Parser")
    print("=" * 60)

    # Import the descriptor parser module directly
    repo_root = Path(__file__).parent
    parser_path = repo_root / "custom_components" / "xcc" / "descriptor_parser.py"

    spec = importlib.util.spec_from_file_location("descriptor_parser", parser_path)
    descriptor_parser = importlib.util.module_from_spec(spec)

    # Mock the logger with debug level
    logger = logging.getLogger('test')
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    descriptor_parser._LOGGER = logger

    # Execute the module
    spec.loader.exec_module(descriptor_parser)

    # Create parser instance
    parser = descriptor_parser.XCCDescriptorParser()
    
    # Test TO-FVEPRETOPENI-POVOLENI
    print(f"\n🎯 Testing TO-FVEPRETOPENI-POVOLENI")
    
    with open('sample_data/OKRUH.XML', 'r', encoding='utf-8', errors='ignore') as f:
        xml_content = f.read()
    
    page_name = "OKRUH"
    entity_configs = parser._parse_single_descriptor(xml_content, page_name)
    
    prop_name = "TO-FVEPRETOPENI-POVOLENI"
    if prop_name in entity_configs:
        config = entity_configs[prop_name]
        print(f"   Found entity config:")
        print(f"   friendly_name: '{config.get('friendly_name', 'MISSING')}'")
        print(f"   friendly_name_en: '{config.get('friendly_name_en', 'MISSING')}'")
        print(f"   entity_type: '{config.get('entity_type', 'MISSING')}'")
        print(f"   writable: {config.get('writable', 'MISSING')}")
        
        # Check if it contains the expected text
        friendly_name = config.get('friendly_name', '')
        if 'Enable' in friendly_name or 'Povolit' in friendly_name:
            print(f"   ✅ Contains expected label text")
        else:
            print(f"   ❌ Missing expected label text")
            
        if 'FVE' in friendly_name or 'Přetápění' in friendly_name:
            print(f"   ✅ Contains expected row context")
        else:
            print(f"   ❌ Missing expected row context")
    else:
        print(f"   ❌ Entity not found")
        print(f"   Available entities: {list(entity_configs.keys())[:10]}...")

if __name__ == "__main__":
    test_actual_parser()
