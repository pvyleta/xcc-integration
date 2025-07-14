#!/usr/bin/env python3
"""Debug script to analyze friendly name issues in XCC integration."""

import os
import xml.etree.ElementTree as ET
import re

def analyze_friendly_names():
    """Analyze friendly name issues with specific entities."""

    print("🔍 Analyzing Friendly Name Issues")
    print("=" * 50)

    # Test entities mentioned by user
    test_entities = [
        "TO-FVEPRETOPENI-POVOLENI",
        "FVE-CHARGEATCHEAPMAXSOC",
        "FVM0-CURRENTBATTERYSETTINGS-CHARGEIMAX"
    ]
    # Manual XML analysis for the problematic entities
    print(f"\n🔍 Manual XML Analysis for Missing English Names")
    print("=" * 50)

    # Analyze each test entity
    for entity_prop in test_entities:
        print(f"\n🎯 Analyzing {entity_prop}")
        print("-" * 40)

        # Search in all sample files
        found_in_files = []
        for file_path in ["sample_data/OKRUH.XML", "sample_data/FVE.XML", "sample_data/FVE4.XML"]:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                if entity_prop in content:
                    found_in_files.append(file_path)
                    print(f"   ✅ Found in {file_path}")

                    # Extract context around the entity
                    start_pos = max(0, content.find(entity_prop) - 300)
                    end_pos = content.find(entity_prop) + 300
                    context = content[start_pos:end_pos]

                    # Look for text and text_en attributes in the context
                    text_match = re.search(r'text="([^"]*)"', context)
                    text_en_match = re.search(r'text_en="([^"]*)"', context)

                    if text_match:
                        print(f"      text (Czech): '{text_match.group(1)}'")
                    else:
                        print(f"      text (Czech): MISSING")

                    if text_en_match:
                        print(f"      text_en (English): '{text_en_match.group(1)}'")
                    else:
                        print(f"      text_en (English): MISSING")

                    # Look for unit attribute
                    unit_match = re.search(r'unit="([^"]*)"', context)
                    if unit_match:
                        print(f"      unit: '{unit_match.group(1)}'")

                    # Show a snippet of the context for debugging
                    print(f"      Context snippet:")
                    lines = context.split('\n')
                    for line in lines:
                        if entity_prop in line:
                            print(f"        {line.strip()}")
                            break

        if not found_in_files:
            print(f"   ❌ {entity_prop} not found in any sample files")

    print(f"\n📊 Summary of Issues")
    print("=" * 50)
    print("1. TO-FVEPRETOPENI-POVOLENI: Missing English friendly name")
    print("2. FVE-CHARGEATCHEAPMAXSOC: Uses Czech translation instead of English")
    print("3. FVM0-CURRENTBATTERYSETTINGS-CHARGEIMAX: No friendly name (sensor)")
    print("\nRoot causes:")
    print("- Some entities have text but no text_en attribute")
    print("- Some entities are read-only sensors without descriptive text")
    print("- Entity generation logic may not be handling missing text_en properly")

if __name__ == "__main__":
    analyze_friendly_names()
