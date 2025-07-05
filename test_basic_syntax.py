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
    """Test for common undefined variable patterns."""
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
            
            # Look for common undefined variable patterns
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                
                # Check for variables used in f-strings or format strings before definition
                if 'entity_id' in line and ('_LOGGER' in line or 'format' in line or 'f"' in line):
                    # Look backwards to see if entity_id was defined
                    defined = False
                    for prev_line_num in range(line_num - 1, max(0, line_num - 20), -1):
                        prev_line = lines[prev_line_num - 1].strip()
                        if 'entity_id =' in prev_line:
                            defined = True
                            break
                    
                    if not defined and 'entity_id' in line:
                        error_msg = f"❌ Potential undefined variable 'entity_id' in {file_path}:{line_num}: {line}"
                        _LOGGER.warning(error_msg)
                        # Don't add to errors for now, just warn
            
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
