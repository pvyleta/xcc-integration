#!/usr/bin/env python3
"""
Run basic validation tests without requiring pytest.
This is a simple test runner that can catch critical issues.
"""

import ast
import sys
from pathlib import Path

def test_python_syntax():
    """Test that all Python files have valid syntax."""
    print("Testing Python syntax...")
    
    python_files = []
    xcc_dir = Path(__file__).parent.parent / "custom_components" / "xcc"
    for file_path in xcc_dir.rglob("*.py"):
        python_files.append(file_path)
    
    if len(python_files) == 0:
        print("❌ FAIL: No Python files found to test")
        return False
    
    print(f"Found {len(python_files)} Python files to check")
    
    for file_path in python_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        try:
            ast.parse(source, filename=str(file_path))
            print(f"✅ Syntax OK: {file_path.name}")
        except SyntaxError as e:
            print(f"❌ FAIL: Syntax error in {file_path}: {e}")
            return False
    
    return True


def test_no_critical_undefined_variables():
    """Test for undefined variable patterns that cause runtime errors."""
    print("\nTesting for critical undefined variables...")
    
    python_files = []
    xcc_dir = Path(__file__).parent.parent / "custom_components" / "xcc"
    for file_path in xcc_dir.rglob("*.py"):
        python_files.append(file_path)
    
    critical_errors = []
    
    for file_path in python_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Look for critical undefined variable patterns
        for line_num, line in enumerate(lines, 1):
            line_stripped = line.strip()
            
            # Skip comments and empty lines
            if not line_stripped or line_stripped.startswith('#'):
                continue
            
            # CRITICAL PATTERN: entity_id used in logging before definition
            if ('_LOGGER' in line_stripped and 'entity_id' in line_stripped and 
                ('info(' in line_stripped or 'error(' in line_stripped or 'warning(' in line_stripped or 'debug(' in line_stripped)):
                
                # Look backwards in the same function to see if entity_id was defined
                defined_in_function = False
                function_start = line_num
                
                # Find the start of the current function/method
                for search_line_num in range(line_num - 1, max(0, line_num - 100), -1):
                    search_line = lines[search_line_num - 1].strip()
                    if (search_line.startswith('def ') or search_line.startswith('class ') or 
                        search_line.startswith('async def ')):
                        function_start = search_line_num
                        break
                
                # Check if entity_id is defined between function start and current line
                for check_line_num in range(function_start, line_num):
                    check_line = lines[check_line_num - 1].strip()
                    # Look for entity_id assignment (but not in comments)
                    if (('entity_id =' in check_line or 'entity_id=' in check_line) and 
                        not check_line.startswith('#') and 
                        not 'self.entity_id' in check_line):  # Exclude self.entity_id assignments
                        defined_in_function = True
                        break
                
                # Also check for entity_id as a parameter
                if not defined_in_function:
                    for check_line_num in range(function_start, min(function_start + 5, len(lines))):
                        check_line = lines[check_line_num - 1].strip()
                        if 'def ' in check_line and 'entity_id' in check_line:
                            defined_in_function = True
                            break
                
                if not defined_in_function:
                    # This is a critical error that will cause UnboundLocalError at runtime
                    critical_errors.append(
                        f"❌ CRITICAL: entity_id used before definition in {file_path.name}:{line_num}\n"
                        f"   Line: {line_stripped}\n"
                        f"   This will cause UnboundLocalError at runtime!"
                    )
    
    if critical_errors:
        print("❌ FAIL: Critical undefined variable errors found:")
        for error in critical_errors:
            print(f"  {error}")
        return False
    else:
        print("✅ No critical undefined variable issues found")
        return True


def test_entity_data_structure():
    """Test that entity data structures are consistent."""
    print("\nTesting entity data structure consistency...")
    
    coordinator_file = Path(__file__).parent.parent / "custom_components" / "xcc" / "coordinator.py"
    if not coordinator_file.exists():
        print("❌ FAIL: coordinator.py not found")
        return False
    
    with open(coordinator_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Ensure state_data includes entity_id
    if 'state_data = {' in content:
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'state_data = {' in line:
                # Check the next few lines for entity_id
                found_entity_id = False
                for j in range(i, min(i + 10, len(lines))):
                    if '"entity_id"' in lines[j]:
                        found_entity_id = True
                        break
                
                if not found_entity_id:
                    print("❌ FAIL: state_data structure missing entity_id field in coordinator.py")
                    return False
                else:
                    print("✅ state_data structure includes entity_id field")
                    break
    else:
        print("⚠️  WARNING: state_data structure not found in coordinator.py")
    
    return True


def main():
    """Run all tests."""
    print("=== XCC Integration Basic Validation Tests ===")
    
    all_passed = True
    
    # Run syntax test
    if not test_python_syntax():
        all_passed = False
    
    # Run undefined variable test
    if not test_no_critical_undefined_variables():
        all_passed = False
    
    # Run entity data structure test
    if not test_entity_data_structure():
        all_passed = False
    
    print("\n=== Test Results ===")
    if all_passed:
        print("✅ ALL TESTS PASSED")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
