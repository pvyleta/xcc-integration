#!/usr/bin/env python3
"""Find hidden switches in XCC controller.

Scans all data pages for _BOOL_i fields that should be writable switches
but have no matching <switch> or <choice> control in the descriptor files.

These are typically:
- Service technician settings
- Installation-time configuration
- Hardware capability flags
- Hidden features not exposed in the web UI
"""

import sys
from pathlib import Path
from lxml import etree
from collections import defaultdict


def parse_data_page_simple(content: str) -> list:
    """Simplified parser for data pages - extract INPUT elements only."""
    try:
        root = etree.fromstring(content.encode("utf-8"))
    except:
        # Try with XML declaration
        if '<?xml' not in content:
            content = '<?xml version="1.0" encoding="utf-8"?>\n' + content
        root = etree.fromstring(content.encode("utf-8"))

    entities = []

    for elem in root.xpath(".//INPUT[@P and @NAME and @VALUE]"):
        prop = elem.get("P")
        name_attr = elem.get("NAME", "")
        value = elem.get("VALUE", "")

        # Determine data type from NAME attribute
        data_type = "unknown"
        if "_BOOL_" in name_attr:
            data_type = "boolean"
        elif "_REAL_" in name_attr or "_INT_" in name_attr:
            data_type = "numeric"
        elif "_STRING" in name_attr:
            data_type = "string"

        entities.append({
            "prop": prop,
            "internal_name": name_attr,
            "value": value,
            "data_type": data_type,
        })

    return entities


def load_descriptor_controls(descriptor_dir: Path) -> dict:
    """Load all prop values that have actual control elements in descriptors.
    
    Returns dict: {prop_name: control_type} where control_type is 'switch', 'choice', 'number', etc.
    """
    controls = {}
    
    for desc_file in descriptor_dir.glob("*.xml"):
        try:
            content = desc_file.read_text(encoding="utf-8")
            root = etree.fromstring(content.encode("utf-8"))
            
            # Find all control elements with prop attributes
            for elem in root.xpath(".//*[@prop]"):
                prop = elem.get("prop")
                control_type = elem.tag.lower()
                
                if control_type in ["switch", "choice", "number", "time", "button"]:
                    controls[prop] = control_type
                    
        except Exception as e:
            print(f"Warning: Could not parse {desc_file.name}: {e}", file=sys.stderr)
    
    return controls


def find_hidden_switches(data_dir: Path, descriptor_dir: Path):
    """Find all _BOOL_i fields in data pages that have no control in descriptors."""
    
    # Load all known controls from descriptors
    known_controls = load_descriptor_controls(descriptor_dir)
    
    print(f"📋 Found {len(known_controls)} controls in descriptor files\n")
    
    # Scan all data pages
    hidden_switches = defaultdict(list)
    all_bool_fields = {}
    
    for data_file in sorted(data_dir.glob("*.XML")):
        try:
            content = data_file.read_text(encoding="utf-8")
            entities = parse_data_page_simple(content)

            for entity in entities:
                field_name = entity["prop"]
                internal_name = entity["internal_name"]
                data_type = entity["data_type"]
                value = entity["value"]

                # Check if it's a boolean field
                if "_BOOL_" in internal_name and data_type == "boolean":
                    all_bool_fields[field_name] = {
                        "page": data_file.name,
                        "internal_name": internal_name,
                        "value": value,
                    }

                    # Check if it's missing from descriptors
                    if field_name not in known_controls:
                        hidden_switches[data_file.name].append({
                            "prop": field_name,
                            "internal_name": internal_name,
                            "value": value,
                        })
                        
        except Exception as e:
            print(f"Warning: Could not parse {data_file.name}: {e}", file=sys.stderr)
    
    return hidden_switches, all_bool_fields, known_controls


def main():
    # Use fresh_tuv_data if available, otherwise tests/sample_data
    data_dir = Path("fresh_tuv_data/data")
    descriptor_dir = Path("fresh_tuv_data/descriptors")
    
    if not data_dir.exists():
        data_dir = Path("tests/sample_data")
        descriptor_dir = Path("tests/sample_data")
    
    if not data_dir.exists():
        print("❌ No data directory found (fresh_tuv_data/data or tests/sample_data)")
        sys.exit(1)
    
    print(f"🔍 Scanning data pages in: {data_dir}")
    print(f"📖 Loading descriptors from: {descriptor_dir}\n")
    
    hidden, all_bool, controls = find_hidden_switches(data_dir, descriptor_dir)
    
    # Report
    print("=" * 80)
    print("🔒 HIDDEN SWITCHES (writable _BOOL_i fields with no UI control)")
    print("=" * 80)
    print()
    
    total_hidden = sum(len(switches) for switches in hidden.values())
    
    if total_hidden == 0:
        print("✅ No hidden switches found")
    else:
        for page, switches in sorted(hidden.items()):
            print(f"\n📄 {page} ({len(switches)} hidden switches)")
            print("-" * 80)
            for sw in switches:
                print(f"  • {sw['prop']}")
                print(f"      Internal: {sw['internal_name']}")
                print(f"      Value: {sw['value']}")
    
    print(f"\n\n📊 Summary:")
    print(f"  Total boolean fields in data: {len(all_bool)}")
    print(f"  With UI controls: {len([p for p in all_bool if p in controls])}")
    print(f"  Hidden (no UI): {total_hidden}")
    
    # Save detailed report
    report_file = Path("hidden_switches_report.txt")
    with open(report_file, "w", encoding="utf-8") as f:
        f.write("HIDDEN SWITCHES IN XCC CONTROLLER\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Data directory: {data_dir.absolute()}\n")
        f.write(f"Descriptor directory: {descriptor_dir.absolute()}\n\n")
        
        for page, switches in sorted(hidden.items()):
            f.write(f"\n{page}\n")
            f.write("-" * 80 + "\n")
            for sw in switches:
                f.write(f"prop={sw['prop']}\n")
                f.write(f"  NAME={sw['internal_name']}\n")
                f.write(f"  VALUE={sw['value']}\n")
                f.write("\n")
    
    print(f"\n💾 Detailed report saved to: {report_file}")


if __name__ == "__main__":
    main()
