"""Test XCC integration import paths and dependencies."""

import pytest
import sys
from pathlib import Path
import ast
import inspect

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def test_xcc_client_exists():
    """Test that xcc_client.py exists in the integration package."""
    xcc_client_path = project_root / "custom_components" / "xcc" / "xcc_client.py"
    assert xcc_client_path.exists(), "xcc_client.py must exist in the integration package"


def test_config_flow_imports():
    """Test that config_flow.py uses correct relative imports."""
    config_flow_path = project_root / "custom_components" / "xcc" / "config_flow.py"
    
    with open(config_flow_path, 'r') as f:
        content = f.read()
    
    # Parse the AST to check imports
    tree = ast.parse(content)
    
    # Check for problematic absolute imports
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module == "xcc_client":
                pytest.fail(
                    "config_flow.py should use relative import '.xcc_client' not 'xcc_client'"
                )
    
    # Verify correct relative import exists
    assert "from .xcc_client import" in content, \
        "config_flow.py must use relative import 'from .xcc_client import'"


def test_coordinator_imports():
    """Test that coordinator.py uses correct relative imports."""
    coordinator_path = project_root / "custom_components" / "xcc" / "coordinator.py"
    
    with open(coordinator_path, 'r') as f:
        content = f.read()
    
    # Parse the AST to check imports
    tree = ast.parse(content)
    
    # Check for problematic absolute imports
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module == "xcc_client":
                pytest.fail(
                    "coordinator.py should use relative import '.xcc_client' not 'xcc_client'"
                )
    
    # Verify correct relative import exists
    assert "from .xcc_client import" in content, \
        "coordinator.py must use relative import 'from .xcc_client import'"


def test_all_integration_files_importable():
    """Test that all integration files can be imported without errors."""
    integration_files = [
        "const",
        "config_flow", 
        "coordinator",
        "entity",
        "sensor",
        "binary_sensor",
        "switch",
        "number",
        "select",
        "mqtt_discovery",
        "xcc_client"
    ]
    
    for module_name in integration_files:
        try:
            module = __import__(f"custom_components.xcc.{module_name}", fromlist=[module_name])
            assert module is not None, f"Failed to import {module_name}"
        except ImportError as e:
            pytest.fail(f"Failed to import custom_components.xcc.{module_name}: {e}")


def test_xcc_client_has_required_classes():
    """Test that xcc_client.py has the required classes and functions."""
    from custom_components.xcc.xcc_client import XCCClient, parse_xml_entities
    
    # Check XCCClient class exists and has required methods
    assert hasattr(XCCClient, '__init__'), "XCCClient must have __init__ method"
    assert hasattr(XCCClient, 'fetch_page'), "XCCClient must have fetch_page method"
    assert hasattr(XCCClient, 'fetch_pages'), "XCCClient must have fetch_pages method"
    
    # Check parse_xml_entities function exists
    assert callable(parse_xml_entities), "parse_xml_entities must be callable"


def test_config_flow_validate_function():
    """Test that config flow validate_input function works correctly."""
    from custom_components.xcc.config_flow import validate_input
    
    # Check function signature
    sig = inspect.signature(validate_input)
    params = list(sig.parameters.keys())
    
    assert 'hass' in params, "validate_input must accept 'hass' parameter"
    assert 'data' in params, "validate_input must accept 'data' parameter"
    
    # Check it's an async function
    assert inspect.iscoroutinefunction(validate_input), \
        "validate_input must be an async function"


def test_coordinator_class_structure():
    """Test that coordinator has the required structure."""
    from custom_components.xcc.coordinator import XCCDataUpdateCoordinator
    
    # Check required methods exist
    required_methods = [
        '__init__',
        '_async_update_data',
        'async_set_value'
    ]
    
    for method in required_methods:
        assert hasattr(XCCDataUpdateCoordinator, method), \
            f"XCCDataUpdateCoordinator must have {method} method"


def test_no_global_xcc_client_imports():
    """Test that no files import xcc_client from global scope."""
    integration_dir = project_root / "custom_components" / "xcc"
    python_files = list(integration_dir.glob("*.py"))
    
    problematic_files = []
    
    for py_file in python_files:
        if py_file.name == "xcc_client.py":
            continue  # Skip the xcc_client.py file itself
            
        with open(py_file, 'r') as f:
            content = f.read()
        
        # Check for problematic imports
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if (line.startswith('from xcc_client import') or 
                line.startswith('import xcc_client')):
                problematic_files.append(f"{py_file.name}:{line_num} - {line}")
    
    if problematic_files:
        pytest.fail(
            f"Found global xcc_client imports (should be relative '.xcc_client'):\n" +
            "\n".join(problematic_files)
        )


def test_manifest_structure():
    """Test that manifest.json has correct structure."""
    import json
    
    manifest_path = project_root / "custom_components" / "xcc" / "manifest.json"
    
    with open(manifest_path) as f:
        manifest = json.load(f)
    
    # Check required fields
    required_fields = ["domain", "name", "config_flow", "documentation_url", "version"]
    for field in required_fields:
        assert field in manifest, f"manifest.json must have '{field}' field"
    
    # Check domain matches
    assert manifest["domain"] == "xcc", "Domain must be 'xcc'"
    
    # Check config_flow is enabled
    assert manifest["config_flow"] is True, "config_flow must be enabled"


@pytest.mark.asyncio
async def test_integration_setup_imports():
    """Test that integration setup can import all required modules."""
    # This simulates what happens when Home Assistant loads the integration
    try:
        # Import main integration module
        from custom_components.xcc import async_setup_entry, async_unload_entry
        
        # Import config flow
        from custom_components.xcc.config_flow import XCCConfigFlow
        
        # Import coordinator
        from custom_components.xcc.coordinator import XCCDataUpdateCoordinator
        
        # Import all platform modules
        from custom_components.xcc import sensor, binary_sensor, switch, number, select
        
        # All imports successful
        assert True
        
    except ImportError as e:
        pytest.fail(f"Integration setup import failed: {e}")


def test_homeassistant_version_imports():
    """Test that homeassistant/components/xcc version also has correct imports."""
    ha_coordinator_path = project_root / "homeassistant" / "components" / "xcc" / "coordinator.py"
    ha_config_flow_path = project_root / "homeassistant" / "components" / "xcc" / "config_flow.py"
    
    if ha_coordinator_path.exists():
        with open(ha_coordinator_path, 'r') as f:
            content = f.read()
        
        # Check for problematic absolute imports
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module == "xcc_client":
                    pytest.fail(
                        "homeassistant/components/xcc/coordinator.py should use relative import"
                    )
    
    if ha_config_flow_path.exists():
        with open(ha_config_flow_path, 'r') as f:
            content = f.read()
        
        # Check for problematic absolute imports  
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module == "xcc_client":
                    pytest.fail(
                        "homeassistant/components/xcc/config_flow.py should use relative import"
                    )
