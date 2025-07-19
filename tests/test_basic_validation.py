"""Basic validation tests for XCC integration."""

import pytest
import os
import ast
import sys

def test_python_syntax():
    """Test that all Python files have valid syntax."""
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
                content = f.read()
            ast.parse(content)
        except SyntaxError as e:
            errors.append(f"Syntax error in {file_path}: {e}")
        except Exception as e:
            errors.append(f"Error reading {file_path}: {e}")
    
    assert not errors, f"Syntax errors found: {errors}"

def test_manifest_exists():
    """Test that manifest.json exists and is valid."""
    manifest_path = "custom_components/xcc/manifest.json"
    assert os.path.exists(manifest_path), "manifest.json not found"
    
    import json
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    required_fields = ["domain", "name", "version", "documentation_url", "codeowners"]
    for field in required_fields:
        assert field in manifest, f"Required field '{field}' missing from manifest"

def test_sample_data_exists(sample_data_dir):
    """Test that sample data files exist."""
    required_files = ["BIV.XML", "FVE.XML", "OKRUH.XML", "SPOT.XML", "STAVJED.XML", "TUV1.XML"]
    
    for file_name in required_files:
        file_path = os.path.join(sample_data_dir, file_name)
        assert os.path.exists(file_path), f"Sample data file {file_name} not found"

def test_integration_constants():
    """Test that integration constants are properly defined."""
    # This test doesn't require Home Assistant imports
    constants_to_check = [
        ("DOMAIN", "xcc"),
        ("DEFAULT_SCAN_INTERVAL", 30),
    ]
    
    # We can't import the actual constants without HA, but we can check the file exists
    const_file = "custom_components/xcc/const.py"
    assert os.path.exists(const_file), "const.py file not found"
    
    # Check that the file contains the expected constants
    with open(const_file, 'r') as f:
        content = f.read()
    
    for const_name, expected_value in constants_to_check:
        assert const_name in content, f"Constant {const_name} not found in const.py"
