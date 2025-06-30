#!/usr/bin/env python3
"""
Fix trailing whitespace in Python files.
"""

from pathlib import Path


def fix_trailing_whitespace(file_path):
    """Remove trailing whitespace from a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Remove trailing whitespace from each line
        fixed_lines = []
        changes = 0
        
        for line_num, line in enumerate(lines, 1):
            original_line = line
            # Remove trailing whitespace but keep newlines
            if line.endswith('\n'):
                fixed_line = line.rstrip() + '\n'
            else:
                fixed_line = line.rstrip()
            
            if original_line != fixed_line:
                changes += 1
                print(f"  Fixed line {line_num}")
            
            fixed_lines.append(fixed_line)
        
        if changes > 0:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(fixed_lines)
            print(f"✓ Fixed {changes} lines in {file_path.name}")
        else:
            print(f"✓ No changes needed in {file_path.name}")
            
        return changes
        
    except Exception as e:
        print(f"❌ Error fixing {file_path}: {e}")
        return 0


def main():
    """Fix trailing whitespace in all Python files."""
    print("🔧 Fixing trailing whitespace in Python files...")
    
    xcc_dir = Path(__file__).parent / "custom_components" / "xcc"
    python_files = list(xcc_dir.glob("*.py"))
    
    total_changes = 0
    
    for py_file in python_files:
        changes = fix_trailing_whitespace(py_file)
        total_changes += changes
    
    print(f"\n✅ Fixed {total_changes} total lines across {len(python_files)} files")


if __name__ == "__main__":
    main()
