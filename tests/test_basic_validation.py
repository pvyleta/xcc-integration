"""Basic validation tests that don't require external dependencies."""

import ast
import os
import sys
import pytest
from pathlib import Path

# Add the custom_components directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "custom_components"))


def test_python_syntax():
    """Test that all Python files have valid syntax."""
    python_files = []
    
    # Find all Python files in custom_components/xcc
    xcc_dir = Path(__file__).parent.parent / "custom_components" / "xcc"
    for file_path in xcc_dir.rglob("*.py"):
        python_files.append(file_path)
    
    assert len(python_files) > 0, "No Python files found to test"
    
    for file_path in python_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        try:
            ast.parse(source, filename=str(file_path))
        except SyntaxError as e:
            pytest.fail(f"Syntax error in {file_path}: {e}")


def test_basic_imports():
    """Test that basic imports work without external dependencies."""
    try:
        from xcc import const
        assert hasattr(const, 'DOMAIN'), "const.DOMAIN should be defined"
    except ImportError as e:
        # Skip if it's due to missing external dependencies
        if any(dep in str(e) for dep in ['aiohttp', 'homeassistant', 'voluptuous']):
            pytest.skip(f"Skipping due to missing external dependency: {e}")
        else:
            pytest.fail(f"Import error: {e}")


def test_no_critical_undefined_variables():
    """Test for undefined variable patterns that cause runtime errors.
    
    This test specifically catches the type of error that caused the v1.7.5 regression
    where entity_id was used in logging before being defined.
    """
    python_files = []
    
    # Find all Python files in custom_components/xcc
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
            # This is the exact pattern that caused the v1.7.5 regression
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
                        f"CRITICAL: entity_id used in logging before definition in {file_path.name}:{line_num}\n"
                        f"  Line: {line_stripped}\n"
                        f"  This will cause UnboundLocalError at runtime!"
                    )
    
    if critical_errors:
        error_msg = "Critical undefined variable errors found that will cause runtime failures:\n\n" + "\n\n".join(critical_errors)
        pytest.fail(error_msg)


def test_entity_data_structure_consistency():
    """Test that entity data structures are consistent across the codebase."""
    # This test ensures that entity_id is properly handled in data structures
    
    # Check coordinator.py for proper entity_id handling
    coordinator_file = Path(__file__).parent.parent / "custom_components" / "xcc" / "coordinator.py"
    if coordinator_file.exists():
        with open(coordinator_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Ensure state_data includes entity_id
        if 'state_data = {' in content:
            # Find the state_data definition
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
                        pytest.fail("state_data structure missing entity_id field in coordinator.py")
