#!/usr/bin/env python3
"""Diagnostic script to test XCC controller connection."""

import asyncio
import aiohttp
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from custom_components.xcc.xcc_client import XCCClient, parse_xml_entities
from custom_components.xcc.const import XCC_PAGES


async def diagnose_xcc_connection():
    """Diagnose XCC controller connection issues."""
    print("🔍 XCC Controller Connection Diagnostics")
    print("=" * 50)
    
    # Get connection details from user
    ip_address = input("Enter XCC Controller IP address: ").strip()
    username = input("Enter username (default: xcc): ").strip() or "xcc"
    password = input("Enter password (default: xcc): ").strip() or "xcc"
    
    print(f"\n📡 Testing connection to {ip_address}...")
    
    # Test 1: Basic HTTP connectivity
    print("\n1️⃣ Testing basic HTTP connectivity...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"http://{ip_address}", timeout=10) as resp:
                print(f"   ✅ HTTP connection successful (status: {resp.status})")
    except Exception as e:
        print(f"   ❌ HTTP connection failed: {e}")
        print("   💡 Check if XCC controller is reachable and web interface is enabled")
        return
    
    # Test 2: XCC Client connection
    print("\n2️⃣ Testing XCC client connection...")
    try:
        async with XCCClient(ip=ip_address, username=username, password=password) as client:
            print("   ✅ XCC client connection successful")
            
            # Test 3: Authentication
            print("\n3️⃣ Testing authentication...")
            print("   ✅ Authentication successful")
            
            # Test 4: Fetch individual pages
            print("\n4️⃣ Testing individual page access...")
            successful_pages = []
            failed_pages = []
            
            for page in XCC_PAGES:
                try:
                    content = await client.fetch_page(page)
                    if content and not content.startswith("Error:"):
                        print(f"   ✅ {page}: OK ({len(content)} bytes)")
                        successful_pages.append(page)
                    else:
                        print(f"   ⚠️  {page}: Empty or error response")
                        failed_pages.append(page)
                except Exception as e:
                    print(f"   ❌ {page}: Failed - {e}")
                    failed_pages.append(page)
            
            # Test 5: Parse entities from successful pages
            print("\n5️⃣ Testing entity parsing...")
            total_entities = 0
            
            for page in successful_pages[:2]:  # Test first 2 successful pages
                try:
                    content = await client.fetch_page(page)
                    entities = parse_xml_entities(content, page)
                    entity_count = len(entities)
                    total_entities += entity_count
                    print(f"   ✅ {page}: Parsed {entity_count} entities")
                    
                    # Show sample entities
                    if entities:
                        for i, entity in enumerate(entities[:3]):  # Show first 3
                            print(f"      - {entity.get('field_name', 'Unknown')}: {entity.get('value', 'N/A')}")
                        if len(entities) > 3:
                            print(f"      ... and {len(entities) - 3} more")
                            
                except Exception as e:
                    print(f"   ❌ {page}: Parsing failed - {e}")
            
            # Test 6: Summary
            print("\n6️⃣ Summary:")
            print(f"   📊 Successful pages: {len(successful_pages)}/{len(XCC_PAGES)}")
            print(f"   🏷️  Total entities found: {total_entities}")
            
            if total_entities > 0:
                print("   ✅ XCC controller is working correctly!")
                print("   💡 If no entities appear in Home Assistant, check the logs for errors")
            else:
                print("   ⚠️  No entities found - this may explain why no devices appear")
                print("   💡 Check if your XCC controller model is supported")
                
    except Exception as e:
        print(f"   ❌ XCC client connection failed: {e}")
        
        # Provide specific troubleshooting based on error type
        error_str = str(e).lower()
        if "authentication" in error_str or "login" in error_str:
            print("   💡 Authentication issue - check username/password")
        elif "timeout" in error_str:
            print("   💡 Timeout issue - check network connectivity")
        elif "connection" in error_str:
            print("   💡 Connection issue - check IP address and XCC web interface")
        else:
            print("   💡 Unknown issue - check XCC controller status")
    
    # Test 7: MQTT check
    print("\n7️⃣ MQTT Integration Check:")
    print("   ℹ️  MQTT is optional for XCC integration")
    print("   ℹ️  The integration should work without MQTT")
    print("   ℹ️  MQTT only adds automatic device discovery")


async def test_specific_page():
    """Test a specific XCC page."""
    print("\n🔍 Testing Specific XCC Page")
    print("=" * 30)
    
    ip_address = input("Enter XCC Controller IP address: ").strip()
    page_name = input("Enter page name (e.g., stavjed.xml): ").strip()
    
    try:
        async with aiohttp.ClientSession() as session:
            url = f"http://{ip_address}/{page_name}"
            print(f"Testing: {url}")
            
            async with session.get(url, timeout=10) as resp:
                content = await resp.text()
                print(f"Status: {resp.status}")
                print(f"Content length: {len(content)} bytes")
                print(f"Content preview:\n{content[:500]}...")
                
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    print("XCC Controller Diagnostic Tool")
    print("Choose an option:")
    print("1. Full connection diagnosis")
    print("2. Test specific page")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        asyncio.run(diagnose_xcc_connection())
    elif choice == "2":
        asyncio.run(test_specific_page())
    else:
        print("Invalid choice")
