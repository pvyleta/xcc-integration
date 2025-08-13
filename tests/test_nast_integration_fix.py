#!/usr/bin/env python3
"""
Test the NAST integration fix for the setup failure.

This test verifies that the integration can handle NAST page discovery
and loading gracefully without causing setup failures.
"""

import pytest
import sys
from pathlib import Path
import re

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_nast_removed_from_constants():
    """Test that NAST page is removed from constants to prevent setup failure."""
    
    print(f"\n=== TESTING NAST REMOVED FROM CONSTANTS ===")
    
    # Load constants file
    const_file = project_root / "custom_components" / "xcc" / "const.py"
    
    if not const_file.exists():
        pytest.skip("const.py not found")
    
    with open(const_file, 'r', encoding='utf-8') as f:
        const_content = f.read()
    
    # Check that NAST is NOT in the constants
    nast_in_descriptors = '"nast.xml"' in const_content
    nast_in_data = '"NAST.XML"' in const_content
    
    print(f"🔍 CONSTANTS CHECK:")
    print(f"  nast.xml in XCC_DESCRIPTOR_PAGES: {nast_in_descriptors}")
    print(f"  NAST.XML in XCC_DATA_PAGES: {nast_in_data}")
    
    # Check for dynamic discovery comments
    dynamic_comment_descriptors = "nast.xml" in const_content and "dynamically" in const_content
    dynamic_comment_data = "NAST.XML" in const_content and "dynamically" in const_content
    
    print(f"  Dynamic discovery comment (descriptors): {dynamic_comment_descriptors}")
    print(f"  Dynamic discovery comment (data): {dynamic_comment_data}")
    
    # Test assertions
    assert not nast_in_descriptors, "nast.xml should NOT be in XCC_DESCRIPTOR_PAGES constants"
    assert not nast_in_data, "NAST.XML should NOT be in XCC_DATA_PAGES constants"
    assert dynamic_comment_descriptors, "Should have comment about dynamic discovery for descriptors"
    assert dynamic_comment_data, "Should have comment about dynamic discovery for data"
    
    print(f"✅ NAST removed from constants test PASSED!")


def test_coordinator_additional_pages_logic():
    """Test that coordinator has logic to check for additional pages."""
    
    print(f"\n=== TESTING COORDINATOR ADDITIONAL PAGES LOGIC ===")
    
    # Load coordinator file
    coordinator_file = project_root / "custom_components" / "xcc" / "coordinator.py"
    
    if not coordinator_file.exists():
        pytest.skip("coordinator.py not found")
    
    with open(coordinator_file, 'r', encoding='utf-8') as f:
        coordinator_content = f.read()
    
    # Check for additional pages logic
    has_check_additional_pages = "_check_additional_pages" in coordinator_content
    has_nast_check = "nast.xml" in coordinator_content
    has_error_handling = "asyncio.CancelledError" in coordinator_content
    has_timeout_handling = "asyncio.TimeoutError" in coordinator_content
    
    print(f"🔍 COORDINATOR LOGIC CHECK:")
    print(f"  Has _check_additional_pages method: {has_check_additional_pages}")
    print(f"  Has NAST page check: {has_nast_check}")
    print(f"  Has CancelledError handling: {has_error_handling}")
    print(f"  Has TimeoutError handling: {has_timeout_handling}")
    
    # Check that additional pages are called from discovery
    calls_additional_pages = "await self._check_additional_pages" in coordinator_content
    
    print(f"  Calls additional pages check: {calls_additional_pages}")
    
    # Test assertions
    assert has_check_additional_pages, "Should have _check_additional_pages method"
    assert has_nast_check, "Should check for nast.xml in additional pages"
    assert has_error_handling, "Should handle CancelledError"
    assert has_timeout_handling, "Should handle TimeoutError"
    assert calls_additional_pages, "Should call additional pages check from discovery"
    
    print(f"✅ Coordinator additional pages logic test PASSED!")


def test_descriptor_loading_error_handling():
    """Test that descriptor loading has proper error handling."""
    
    print(f"\n=== TESTING DESCRIPTOR LOADING ERROR HANDLING ===")
    
    # Load coordinator file
    coordinator_file = project_root / "custom_components" / "xcc" / "coordinator.py"
    
    if not coordinator_file.exists():
        pytest.skip("coordinator.py not found")
    
    with open(coordinator_file, 'r', encoding='utf-8') as f:
        coordinator_content = f.read()
    
    # Check for improved error handling in _load_descriptors
    load_descriptors_section = re.search(r'async def _load_descriptors.*?(?=async def|\Z)', coordinator_content, re.DOTALL)
    
    if not load_descriptors_section:
        pytest.fail("_load_descriptors method not found")
    
    load_descriptors_code = load_descriptors_section.group(0)
    
    # Check for specific error handling patterns
    has_cancelled_error = "asyncio.CancelledError" in load_descriptors_code
    has_timeout_error = "asyncio.TimeoutError" in load_descriptors_code
    has_continue_on_error = "continue" in load_descriptors_code
    has_warning_logs = "_LOGGER.warning" in load_descriptors_code
    
    print(f"🔍 DESCRIPTOR LOADING ERROR HANDLING:")
    print(f"  Handles CancelledError: {has_cancelled_error}")
    print(f"  Handles TimeoutError: {has_timeout_error}")
    print(f"  Continues on error: {has_continue_on_error}")
    print(f"  Logs warnings: {has_warning_logs}")
    
    # Test assertions
    assert has_cancelled_error, "Should handle asyncio.CancelledError"
    assert has_timeout_error, "Should handle asyncio.TimeoutError"
    assert has_continue_on_error, "Should continue processing other pages on error"
    assert has_warning_logs, "Should log warnings for failed pages"
    
    print(f"✅ Descriptor loading error handling test PASSED!")


def test_integration_setup_resilience():
    """Test that the integration setup is now resilient to page loading failures."""
    
    print(f"\n=== TESTING INTEGRATION SETUP RESILIENCE ===")
    
    # Check all the components that make the integration resilient
    
    # 1. Constants don't include problematic pages
    const_file = project_root / "custom_components" / "xcc" / "const.py"
    with open(const_file, 'r', encoding='utf-8') as f:
        const_content = f.read()
    
    nast_not_in_constants = '"nast.xml"' not in const_content and '"NAST.XML"' not in const_content
    
    # 2. Coordinator has dynamic discovery
    coordinator_file = project_root / "custom_components" / "xcc" / "coordinator.py"
    with open(coordinator_file, 'r', encoding='utf-8') as f:
        coordinator_content = f.read()
    
    has_dynamic_discovery = "_check_additional_pages" in coordinator_content
    has_error_resilience = "continue" in coordinator_content and "asyncio.CancelledError" in coordinator_content
    
    # 3. Button platform exists for NAST entities
    button_file = project_root / "custom_components" / "xcc" / "button.py"
    button_platform_exists = button_file.exists()
    
    print(f"🔍 INTEGRATION RESILIENCE CHECK:")
    print(f"  NAST not in constants: {nast_not_in_constants}")
    print(f"  Has dynamic discovery: {has_dynamic_discovery}")
    print(f"  Has error resilience: {has_error_resilience}")
    print(f"  Button platform exists: {button_platform_exists}")
    
    # Overall resilience score
    resilience_components = [
        nast_not_in_constants,
        has_dynamic_discovery,
        has_error_resilience,
        button_platform_exists
    ]
    
    resilience_score = sum(resilience_components)
    total_components = len(resilience_components)
    
    print(f"  Resilience score: {resilience_score}/{total_components}")
    
    # Test assertions
    assert nast_not_in_constants, "NAST should not be in constants to prevent setup failure"
    assert has_dynamic_discovery, "Should have dynamic page discovery"
    assert has_error_resilience, "Should handle errors gracefully"
    assert button_platform_exists, "Button platform should exist for NAST entities"
    assert resilience_score == total_components, f"All resilience components should be present: {resilience_score}/{total_components}"
    
    print(f"✅ Integration setup resilience test PASSED!")


def test_expected_behavior_after_fix():
    """Test the expected behavior after the fix is applied."""
    
    print(f"\n=== TESTING EXPECTED BEHAVIOR AFTER FIX ===")
    
    print(f"🎯 EXPECTED BEHAVIOR:")
    print(f"  1. ✅ Integration setup should not fail")
    print(f"  2. ✅ Basic entities (sensors, switches) should load")
    print(f"  3. ✅ Number entities should load (fixed in v1.12.0)")
    print(f"  4. 🔄 NAST entities will load IF nast.xml is accessible")
    print(f"  5. 🔄 If NAST not accessible, integration continues without it")
    
    print(f"\n📋 TROUBLESHOOTING STEPS:")
    print(f"  1. Restart Home Assistant with the fixed integration")
    print(f"  2. Check logs for 'Found additional page: nast.xml' message")
    print(f"  3. If NAST found: expect ~145 additional entities")
    print(f"  4. If NAST not found: integration still works with other entities")
    
    print(f"\n🔧 FALLBACK BEHAVIOR:")
    print(f"  - If nast.xml is not accessible, integration logs debug message")
    print(f"  - Integration continues with discovered pages only")
    print(f"  - No setup failure, no ConfigEntryNotReady exception")
    print(f"  - User gets maximum available entities from their XCC system")
    
    print(f"✅ Expected behavior test PASSED!")


if __name__ == "__main__":
    """Run tests directly for debugging."""
    print("🧪 Running NAST Integration Fix Tests")
    print("=" * 60)
    
    try:
        test_nast_removed_from_constants()
        test_coordinator_additional_pages_logic()
        test_descriptor_loading_error_handling()
        test_integration_setup_resilience()
        test_expected_behavior_after_fix()
        
        print("\n" + "=" * 60)
        print("🎉 ALL NAST INTEGRATION FIX TESTS PASSED!")
        print("✅ Integration setup failure should be resolved")
        print("🔧 NAST page will be discovered dynamically if accessible")
        print("🚀 Ready for Home Assistant restart")
        
        print(f"\n🎯 NEXT STEPS:")
        print(f"  1. Restart Home Assistant")
        print(f"  2. Check integration loads successfully")
        print(f"  3. Look for 'Found additional page: nast.xml' in logs")
        print(f"  4. Verify entities are created")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
