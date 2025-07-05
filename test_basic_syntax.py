#!/usr/bin/env python3
"""
Basic syntax and import tests that don't require external dependencies.
These tests should catch basic coding errors like undefined variables.
"""

import ast
import os
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
_LOGGER = logging.getLogger(__name__)

def test_python_syntax():
    """Test that all Python files have valid syntax."""
    _LOGGER.info("Testing Python syntax...")
    
    errors = []
    python_files = []
    
    # Find all Python files in custom_components/xcc
    for root, dirs, files in os.walk("custom_components/xcc"):
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))
    
    _LOGGER.info(f"Found {len(python_files)} Python files to check")
    
    for file_path in python_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            # Parse the AST to check syntax
            ast.parse(source, filename=file_path)
            _LOGGER.debug(f"✅ Syntax OK: {file_path}")
            
        except SyntaxError as e:
            error_msg = f"❌ Syntax Error in {file_path}: {e}"
            _LOGGER.error(error_msg)
            errors.append(error_msg)
        except Exception as e:
            error_msg = f"❌ Error reading {file_path}: {e}"
            _LOGGER.error(error_msg)
            errors.append(error_msg)
    
    return errors

def test_basic_imports():
    """Test that basic imports work without external dependencies."""
    _LOGGER.info("Testing basic imports...")
    
    errors = []
    
    # Test imports that should work without external dependencies
    test_imports = [
        "custom_components.xcc.const",
    ]
    
    for module_name in test_imports:
        try:
            # Add the current directory to path
            if os.getcwd() not in sys.path:
                sys.path.insert(0, os.getcwd())
            
            __import__(module_name)
            _LOGGER.debug(f"✅ Import OK: {module_name}")
            
        except ImportError as e:
            # Skip if it's due to missing external dependencies
            if any(dep in str(e) for dep in ['aiohttp', 'homeassistant', 'voluptuous']):
                _LOGGER.debug(f"⚠️  Skipping {module_name} due to missing external dependency: {e}")
            else:
                error_msg = f"❌ Import Error in {module_name}: {e}"
                _LOGGER.error(error_msg)
                errors.append(error_msg)
        except Exception as e:
            error_msg = f"❌ Unexpected error importing {module_name}: {e}"
            _LOGGER.error(error_msg)
            errors.append(error_msg)
    
    return errors

def test_undefined_variables():
    """Test for common undefined variable patterns - STRICT VERSION."""
    _LOGGER.info("Testing for undefined variable patterns...")

    errors = []
    python_files = []

    # Find all Python files in custom_components/xcc
    for root, dirs, files in os.walk("custom_components/xcc"):
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))

    for file_path in python_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Look for critical undefined variable patterns that cause runtime errors
            for line_num, line in enumerate(lines, 1):
                line_stripped = line.strip()

                # Skip comments and empty lines
                if not line_stripped or line_stripped.startswith('#'):
                    continue

                # CRITICAL: Check for entity_id used in logging before definition
                # This is the exact pattern that caused the v1.7.5 regression
                if ('_LOGGER' in line_stripped and 'entity_id' in line_stripped and
                    ('info' in line_stripped or 'error' in line_stripped or 'warning' in line_stripped or 'debug' in line_stripped)):

                    # Look backwards in the same function to see if entity_id was defined
                    defined_in_function = False
                    function_start = line_num

                    # Find the start of the current function
                    for search_line_num in range(line_num - 1, max(0, line_num - 50), -1):
                        search_line = lines[search_line_num - 1].strip()
                        if search_line.startswith('def ') or search_line.startswith('class '):
                            function_start = search_line_num
                            break

                    # Check if entity_id is defined between function start and current line
                    for check_line_num in range(function_start, line_num):
                        check_line = lines[check_line_num - 1].strip()
                        if ('entity_id =' in check_line or 'entity_id=' in check_line) and not check_line.startswith('#'):
                            defined_in_function = True
                            break

                    if not defined_in_function:
                        # This is a critical error that will cause runtime failures
                        error_msg = f"❌ CRITICAL: entity_id used in logging before definition in {file_path}:{line_num}: {line_stripped}"
                        _LOGGER.error(error_msg)
                        errors.append(error_msg)

        except Exception as e:
            error_msg = f"❌ Error checking {file_path}: {e}"
            _LOGGER.error(error_msg)
            errors.append(error_msg)

    return errors

def main():
    """Main test function."""
    _LOGGER.info("=== Basic Syntax and Import Tests ===")
    
    all_errors = []
    
    # Test syntax
    syntax_errors = test_python_syntax()
    all_errors.extend(syntax_errors)
    
    # Test imports
    import_errors = test_basic_imports()
    all_errors.extend(import_errors)
    
    # Test for undefined variables
    undefined_errors = test_undefined_variables()
    all_errors.extend(undefined_errors)
    
    if all_errors:
        _LOGGER.error(f"❌ Found {len(all_errors)} errors:")
        for error in all_errors:
            _LOGGER.error(f"  {error}")
        return False
    else:
        _LOGGER.info("✅ All basic tests passed!")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
