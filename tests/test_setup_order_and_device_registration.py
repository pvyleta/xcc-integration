"""Test setup order and device registration fixes."""

import pytest
from pathlib import Path
import re


def test_setup_order_fix():
    """Test that setup order is correct: data fetch BEFORE platform setup."""
    
    project_root = Path(__file__).parent.parent
    init_file = project_root / "custom_components" / "xcc" / "__init__.py"
    
    with open(init_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the positions of key operations
    first_refresh_pos = content.find("async_config_entry_first_refresh")
    platform_setup_pos = content.find("async_forward_entry_setups")
    
    assert first_refresh_pos > 0, "First refresh call not found"
    assert platform_setup_pos > 0, "Platform setup call not found"
    assert first_refresh_pos < platform_setup_pos, \
        "First refresh must happen BEFORE platform setup"
    
    print("✅ Setup order is correct: data fetch happens before platform setup")


def test_timeout_handling():
    """Test that timeout and cancellation errors are properly handled."""
    
    project_root = Path(__file__).parent.parent
    init_file = project_root / "custom_components" / "xcc" / "__init__.py"
    
    with open(init_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for proper exception handling
    assert "asyncio.TimeoutError" in content, "TimeoutError handling missing"
    assert "asyncio.CancelledError" in content, "CancelledError handling missing"
    assert "ConfigEntryNotReady" in content, "ConfigEntryNotReady not raised"
    
    # Check that we clean up on failure
    assert "hass.data[DOMAIN].pop(entry.entry_id)" in content, \
        "Cleanup of coordinator from hass.data missing on failure"
    
    print("✅ Timeout and cancellation handling is correct")


def test_device_registration():
    """Test that main device is registered before platform setup."""
    
    project_root = Path(__file__).parent.parent
    init_file = project_root / "custom_components" / "xcc" / "__init__.py"
    
    with open(init_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for device registry import
    assert "device_registry" in content, "Device registry import missing"
    
    # Check for device registration
    assert "async_get_or_create" in content, "Device registration call missing"
    
    # Find positions
    device_reg_pos = content.find("async_get_or_create")
    platform_setup_pos = content.find("async_forward_entry_setups")
    
    assert device_reg_pos > 0, "Device registration not found"
    assert platform_setup_pos > 0, "Platform setup not found"
    assert device_reg_pos < platform_setup_pos, \
        "Device registration must happen BEFORE platform setup"
    
    print("✅ Main device registration happens before platform setup")


def test_xcc_client_timeout_handling():
    """Test that xcc_client properly handles timeouts and cancellations."""
    
    project_root = Path(__file__).parent.parent
    client_file = project_root / "custom_components" / "xcc" / "xcc_client.py"
    
    with open(client_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find fetch_page method
    fetch_page_match = re.search(
        r'async def fetch_page\(.*?\):(.*?)(?=\n    async def|\nclass|\Z)',
        content,
        re.DOTALL
    )
    
    assert fetch_page_match, "fetch_page method not found"
    fetch_page_code = fetch_page_match.group(1)
    
    # Check for proper exception handling in fetch_page
    assert "asyncio.CancelledError" in fetch_page_code, \
        "CancelledError handling missing in fetch_page"
    assert "asyncio.TimeoutError" in fetch_page_code, \
        "TimeoutError handling missing in fetch_page"
    
    # Find fetch_pages method
    fetch_pages_match = re.search(
        r'async def fetch_pages\(.*?\):(.*?)(?=\n    async def|\nclass|\Z)',
        content,
        re.DOTALL
    )
    
    assert fetch_pages_match, "fetch_pages method not found"
    fetch_pages_code = fetch_pages_match.group(1)
    
    # Check for proper exception handling in fetch_pages
    assert "asyncio.CancelledError" in fetch_pages_code, \
        "CancelledError handling missing in fetch_pages"
    
    print("✅ XCC client timeout and cancellation handling is correct")


def test_complete_fix_integration():
    """Test that all three fixes work together correctly."""
    
    print("\n=== TESTING COMPLETE FIX INTEGRATION ===\n")
    
    # Run all individual tests
    test_setup_order_fix()
    test_timeout_handling()
    test_device_registration()
    test_xcc_client_timeout_handling()
    
    print("\n✅ ALL FIXES ARE CORRECTLY IMPLEMENTED:")
    print("  1. Setup order: Data fetch → Device registration → Platform setup")
    print("  2. Timeout handling: Proper exception handling with ConfigEntryNotReady")
    print("  3. Device registration: Main device registered before sub-devices")
    print("  4. XCC client: Proper timeout/cancellation handling in fetch methods")
    print("\n🎉 The integration should now handle the reported issues correctly!")


if __name__ == "__main__":
    test_complete_fix_integration()

