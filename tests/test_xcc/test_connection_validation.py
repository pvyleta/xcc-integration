"""Test XCC connection validation - focused on preventing 'cannot_connect' errors."""

import pytest
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def test_xcc_client_can_be_imported():
    """Test that XCC client can be imported from the integration package."""
    # This should not raise ImportError
    from custom_components.xcc.xcc_client import XCCClient
    assert XCCClient is not None


def test_config_flow_can_import_xcc_client():
    """Test that config flow can import XCC client without errors."""
    # This should not raise ImportError during import
    from custom_components.xcc.config_flow import validate_input
    assert validate_input is not None


def test_coordinator_can_import_xcc_client():
    """Test that coordinator can import XCC client without errors."""
    # This should not raise ImportError during import
    from custom_components.xcc.coordinator import XCCDataUpdateCoordinator
    assert XCCDataUpdateCoordinator is not None


def test_no_absolute_xcc_client_imports():
    """Test that no files use absolute 'xcc_client' imports."""
    integration_dir = project_root / "custom_components" / "xcc"
    python_files = list(integration_dir.glob("*.py"))
    
    problematic_imports = []
    
    for py_file in python_files:
        if py_file.name == "xcc_client.py":
            continue  # Skip the xcc_client.py file itself
            
        with open(py_file, 'r') as f:
            content = f.read()
        
        # Check for problematic imports in the actual file content
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            # Look for imports that would cause the original error
            if ('from xcc_client import' in line and 
                not line.startswith('#') and 
                'from .xcc_client import' not in line):
                problematic_imports.append(f"{py_file.name}:{line_num} - {line}")
    
    assert len(problematic_imports) == 0, \
        f"Found absolute xcc_client imports that could cause 'cannot_connect' errors:\n" + \
        "\n".join(problematic_imports)


def test_validate_input_function_exists():
    """Test that validate_input function exists and is callable."""
    from custom_components.xcc.config_flow import validate_input
    
    # Check it's callable
    assert callable(validate_input), "validate_input must be callable"
    
    # Check it's async (this is what caused the original issue)
    import inspect
    assert inspect.iscoroutinefunction(validate_input), \
        "validate_input must be an async function"


def test_integration_structure_intact():
    """Test that integration has all required files for connection validation."""
    integration_dir = project_root / "custom_components" / "xcc"
    
    required_files = [
        "xcc_client.py",
        "config_flow.py", 
        "coordinator.py",
        "manifest.json"
    ]
    
    for required_file in required_files:
        file_path = integration_dir / required_file
        assert file_path.exists(), f"Required file {required_file} is missing"


def test_xcc_client_has_required_methods():
    """Test that XCC client has the methods used by config flow."""
    from custom_components.xcc.xcc_client import XCCClient
    
    # Check required methods exist
    required_methods = ["__init__", "fetch_page", "__aenter__", "__aexit__"]
    
    for method in required_methods:
        assert hasattr(XCCClient, method), \
            f"XCCClient must have {method} method for config flow to work"


def test_config_flow_imports_are_relative():
    """Test that config_flow.py uses relative imports for xcc_client."""
    config_flow_path = project_root / "custom_components" / "xcc" / "config_flow.py"
    
    with open(config_flow_path, 'r') as f:
        content = f.read()
    
    # Should have relative import
    assert "from .xcc_client import" in content, \
        "config_flow.py must use relative import 'from .xcc_client import'"
    
    # Should NOT have absolute import
    assert "from xcc_client import" not in content, \
        "config_flow.py must not use absolute import 'from xcc_client import'"


def test_coordinator_imports_are_relative():
    """Test that coordinator.py uses relative imports for xcc_client."""
    coordinator_path = project_root / "custom_components" / "xcc" / "coordinator.py"
    
    with open(coordinator_path, 'r') as f:
        content = f.read()
    
    # Should have relative import
    assert "from .xcc_client import" in content, \
        "coordinator.py must use relative import 'from .xcc_client import'"
    
    # Should NOT have absolute import  
    assert "from xcc_client import" not in content, \
        "coordinator.py must not use absolute import 'from xcc_client import'"


def test_manifest_has_required_fields():
    """Test that manifest.json has all required fields."""
    import json
    
    manifest_path = project_root / "custom_components" / "xcc" / "manifest.json"
    
    with open(manifest_path) as f:
        manifest = json.load(f)
    
    # Check required fields for Home Assistant integration
    required_fields = ["domain", "name", "config_flow", "version"]
    for field in required_fields:
        assert field in manifest, f"manifest.json must have '{field}' field"
    
    # Check domain matches
    assert manifest["domain"] == "xcc", "Domain must be 'xcc'"
    
    # Check config_flow is enabled (required for connection validation)
    assert manifest["config_flow"] is True, "config_flow must be enabled"


@pytest.mark.asyncio
async def test_validate_input_can_be_called():
    """Test that validate_input function can be called without import errors."""
    from custom_components.xcc.config_flow import validate_input
    from homeassistant.const import CONF_IP_ADDRESS, CONF_USERNAME, CONF_PASSWORD
    from custom_components.xcc.const import CONF_SCAN_INTERVAL
    
    # This test just verifies the function can be called without ImportError
    # We don't test actual connection since that requires mocking
    test_data = {
        CONF_IP_ADDRESS: "192.168.1.100",
        CONF_USERNAME: "test",
        CONF_PASSWORD: "test", 
        CONF_SCAN_INTERVAL: 30,
    }
    
    # The function should be callable (even if it fails due to no real XCC)
    # The important thing is that it doesn't fail with ImportError
    try:
        await validate_input(None, test_data)
    except Exception as e:
        # Any exception is fine except ImportError
        assert not isinstance(e, ImportError), \
            f"validate_input should not fail with ImportError: {e}"
        # We expect it to fail with connection error since no real XCC exists
        # "Unexpected error" is also acceptable as it means connection failed (not ImportError)
        assert ("Connection" in str(e) or "Cannot" in str(e) or "Unexpected" in str(e)), \
            f"Expected connection-related error, got: {e}"


def test_integration_can_be_imported_completely():
    """Test that the entire integration can be imported without errors."""
    try:
        # Import main integration components
        from custom_components.xcc import async_setup_entry, async_unload_entry
        from custom_components.xcc.config_flow import XCCConfigFlow
        from custom_components.xcc.coordinator import XCCDataUpdateCoordinator
        from custom_components.xcc.xcc_client import XCCClient
        
        # All imports successful
        assert True
        
    except ImportError as e:
        pytest.fail(f"Integration import failed with ImportError: {e}")
    except Exception as e:
        # Other exceptions are OK, ImportError is the critical one
        pass
