"""Basic tests for XCC integration."""

import pytest
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def test_import_custom_components():
    """Test that we can import the custom components."""
    try:
        from custom_components.xcc.const import DOMAIN
        assert DOMAIN == "xcc"
    except ImportError as e:
        pytest.fail(f"Failed to import custom_components.xcc.const: {e}")


def test_import_manifest():
    """Test that manifest.json exists and is valid."""
    import json
    
    manifest_path = project_root / "custom_components" / "xcc" / "manifest.json"
    assert manifest_path.exists(), "manifest.json not found"
    
    with open(manifest_path) as f:
        manifest = json.load(f)
    
    assert manifest["domain"] == "xcc"
    assert manifest["name"] == "XCC Heat Pump Controller"
    assert "config_flow" in manifest
    assert manifest["config_flow"] is True


def test_import_config_flow():
    """Test that config flow can be imported."""
    try:
        from custom_components.xcc.config_flow import XCCConfigFlow
        assert XCCConfigFlow is not None
    except ImportError as e:
        pytest.fail(f"Failed to import config flow: {e}")


def test_import_coordinator():
    """Test that coordinator can be imported."""
    try:
        from custom_components.xcc.coordinator import XCCDataUpdateCoordinator
        assert XCCDataUpdateCoordinator is not None
    except ImportError as e:
        pytest.fail(f"Failed to import coordinator: {e}")


def test_import_entities():
    """Test that entity modules can be imported."""
    try:
        from custom_components.xcc import sensor, binary_sensor, switch, number, select
        assert sensor is not None
        assert binary_sensor is not None
        assert switch is not None
        assert number is not None
        assert select is not None
    except ImportError as e:
        pytest.fail(f"Failed to import entity modules: {e}")


@pytest.mark.asyncio
async def test_basic_async():
    """Test basic async functionality."""
    import asyncio
    await asyncio.sleep(0.001)  # Basic async test
    assert True
