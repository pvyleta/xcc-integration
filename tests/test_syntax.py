#!/usr/bin/env python3
"""
Test syntax validation for all Python files to catch syntax errors before release.
"""

import ast
import sys
import os
from pathlib import Path


def test_python_syntax(file_path):
    """Test that a Python file has valid syntax."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        # Parse the AST to check for syntax errors
        ast.parse(source, filename=str(file_path))
        return True, None
        
    except SyntaxError as e:
        return False, f"Syntax error in {file_path}:{e.lineno}: {e.msg}"
    except Exception as e:
        return False, f"Error reading {file_path}: {e}"


def test_all_python_files():
    """Test syntax of all Python files in the integration."""
    
    # Get the custom_components/xcc directory
    xcc_dir = Path(__file__).parent.parent / "custom_components" / "xcc"
    
    if not xcc_dir.exists():
        raise FileNotFoundError(f"XCC directory not found: {xcc_dir}")
    
    # Find all Python files
    python_files = list(xcc_dir.glob("*.py"))
    
    if not python_files:
        raise FileNotFoundError(f"No Python files found in {xcc_dir}")
    
    print(f"🔍 Testing syntax of {len(python_files)} Python files...")
    
    failed_files = []
    
    for py_file in python_files:
        print(f"  Testing {py_file.name}...", end=" ")
        
        success, error = test_python_syntax(py_file)
        
        if success:
            print("✓")
        else:
            print("❌")
            failed_files.append((py_file, error))
    
    if failed_files:
        print(f"\n❌ {len(failed_files)} files have syntax errors:")
        for file_path, error in failed_files:
            print(f"  • {error}")
        return False
    else:
        print(f"\n✅ All {len(python_files)} Python files have valid syntax!")
        return True


def test_import_statements():
    """Test that import statements are valid."""
    
    xcc_dir = Path(__file__).parent.parent / "custom_components" / "xcc"
    python_files = list(xcc_dir.glob("*.py"))
    
    print(f"🔍 Testing import statements in {len(python_files)} files...")
    
    issues = []
    
    for py_file in python_files:
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                source = f.read()
            
            # Parse AST and check imports
            tree = ast.parse(source, filename=str(py_file))
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        # Check for common problematic imports
                        if alias.name in ['xml_parser', 'nonexistent_module']:
                            issues.append(f"{py_file.name}: Suspicious import '{alias.name}'")
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        # Check for relative imports that might not exist
                        if node.module.startswith('.') and 'xml_parser' in node.module:
                            issues.append(f"{py_file.name}: Suspicious relative import '{node.module}'")
                        
                        # Check for specific problematic imports
                        for alias in node.names:
                            if alias.name == 'parse_xml_entities' and node.module and 'xml_parser' in node.module:
                                issues.append(f"{py_file.name}: parse_xml_entities should be imported from xcc_client, not xml_parser")
        
        except Exception as e:
            issues.append(f"{py_file.name}: Error analyzing imports: {e}")
    
    if issues:
        print(f"\n❌ Found {len(issues)} import issues:")
        for issue in issues:
            print(f"  • {issue}")
        return False
    else:
        print("✅ All import statements look good!")
        return True


def test_indentation():
    """Test for common indentation issues."""
    
    xcc_dir = Path(__file__).parent.parent / "custom_components" / "xcc"
    python_files = list(xcc_dir.glob("*.py"))
    
    print(f"🔍 Testing indentation in {len(python_files)} files...")
    
    issues = []
    
    for py_file in python_files:
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for line_num, line in enumerate(lines, 1):
                # Check for mixed tabs and spaces
                if '\t' in line and '    ' in line:
                    issues.append(f"{py_file.name}:{line_num}: Mixed tabs and spaces")
                
                # Check for trailing whitespace
                if line.rstrip() != line.rstrip('\n'):
                    issues.append(f"{py_file.name}:{line_num}: Trailing whitespace")
        
        except Exception as e:
            issues.append(f"{py_file.name}: Error checking indentation: {e}")
    
    if issues:
        print(f"\n⚠️  Found {len(issues)} indentation issues:")
        for issue in issues[:10]:  # Show first 10
            print(f"  • {issue}")
        if len(issues) > 10:
            print(f"  ... and {len(issues) - 10} more")
        return False
    else:
        print("✅ Indentation looks good!")
        return True


if __name__ == "__main__":
    """Run syntax tests directly."""
    print("🧪 Running XCC Integration Syntax Tests")
    print("=" * 50)
    
    all_passed = True
    
    try:
        if not test_all_python_files():
            all_passed = False
        
        print()
        if not test_import_statements():
            all_passed = False
        
        print()
        if not test_indentation():
            all_passed = False
        
        print("\n" + "=" * 50)
        if all_passed:
            print("✅ ALL SYNTAX TESTS PASSED! Code is ready for release.")
        else:
            print("❌ SYNTAX TESTS FAILED! Fix issues before release.")
            sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ TEST RUNNER FAILED: {e}")
        sys.exit(1)
