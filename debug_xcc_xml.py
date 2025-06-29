#!/usr/bin/env python3
"""Debug script to examine XCC XML content and parsing."""

import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from custom_components.xcc.xcc_client import XCCClient, parse_xml_entities
from custom_components.xcc.const import XCC_PAGES


async def debug_xcc_xml():
    """Debug XCC XML content and parsing."""
    print("🔍 XCC XML Content Debugger")
    print("=" * 50)
    
    # Get connection details
    ip_address = input("Enter XCC Controller IP address (default: 192.168.0.50): ").strip() or "192.168.0.50"
    username = input("Enter username (default: xcc): ").strip() or "xcc"
    password = input("Enter password (default: xcc): ").strip() or "xcc"
    
    print(f"\n📡 Connecting to XCC controller {ip_address}...")
    
    try:
        async with XCCClient(ip=ip_address, username=username, password=password) as client:
            print("✅ Connected successfully!")
            
            # Fetch and analyze each page
            for page_name in XCC_PAGES[:3]:  # Check first 3 pages
                print(f"\n📄 Analyzing page: {page_name}")
                print("-" * 30)
                
                try:
                    # Fetch raw XML content
                    xml_content = await client.fetch_page(page_name)
                    
                    print(f"📊 Content length: {len(xml_content)} bytes")
                    
                    if xml_content.startswith("Error:"):
                        print(f"❌ Error response: {xml_content}")
                        continue
                    
                    # Show first 500 characters of XML
                    print(f"📝 Raw XML content (first 500 chars):")
                    print("```xml")
                    print(xml_content[:500])
                    if len(xml_content) > 500:
                        print("... (truncated)")
                    print("```")
                    
                    # Try to parse entities
                    print(f"\n🔍 Parsing entities...")
                    entities = parse_xml_entities(xml_content, page_name)
                    print(f"📈 Found {len(entities)} entities")
                    
                    if entities:
                        print("✅ Sample entities:")
                        for i, entity in enumerate(entities[:3]):
                            print(f"  {i+1}. {entity.get('field_name', 'Unknown')}: {entity.get('value', 'N/A')}")
                    else:
                        print("❌ No entities found - let's analyze why...")
                        
                        # Check XML structure
                        if "<" in xml_content and ">" in xml_content:
                            print("✅ Contains XML tags")
                            
                            # Look for common XCC patterns
                            patterns = [
                                "STAVJED", "OKRUH", "TUV", "BIV", "FVE", "SPOT",
                                "T_OUTDOOR", "T_INDOOR", "COMPRESSOR", "PUMP",
                                "<item", "<value", "<name", "<data"
                            ]
                            
                            found_patterns = []
                            for pattern in patterns:
                                if pattern.lower() in xml_content.lower():
                                    found_patterns.append(pattern)
                            
                            if found_patterns:
                                print(f"✅ Found XCC patterns: {found_patterns}")
                            else:
                                print("❌ No recognized XCC patterns found")
                                
                            # Show XML structure
                            lines = xml_content.split('\n')[:10]
                            print("📋 XML structure (first 10 lines):")
                            for i, line in enumerate(lines, 1):
                                print(f"  {i:2d}: {line.strip()}")
                                
                        else:
                            print("❌ Not valid XML format")
                            print(f"Content type appears to be: {type(xml_content)}")
                    
                except Exception as e:
                    print(f"❌ Error fetching {page_name}: {e}")
            
            # Test specific URL patterns
            print(f"\n🌐 Testing specific URL patterns...")
            test_urls = [
                "stavjed.xml",
                "STAVJED.XML", 
                "index.xml",
                "status.xml",
                "data.xml"
            ]
            
            for test_url in test_urls:
                try:
                    content = await client.fetch_page(test_url)
                    if not content.startswith("Error:") and len(content) > 10:
                        print(f"✅ {test_url}: {len(content)} bytes")
                    else:
                        print(f"❌ {test_url}: {content[:50]}...")
                except:
                    print(f"❌ {test_url}: Failed to fetch")
                    
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return
    
    print(f"\n💡 Recommendations:")
    print("1. Check if your XCC controller model uses different XML format")
    print("2. Verify the XML pages contain actual data (not empty)")
    print("3. Check if authentication is required for data pages")
    print("4. Try accessing pages directly in browser to see format")


async def test_xml_parsing():
    """Test XML parsing with sample data."""
    print("\n🧪 Testing XML Parsing Function")
    print("=" * 40)
    
    # Test with sample XCC XML
    sample_xml = """<?xml version="1.0" encoding="UTF-8"?>
<STAVJED>
    <T_OUTDOOR>5.2</T_OUTDOOR>
    <T_INDOOR>21.5</T_INDOOR>
    <COMPRESSOR>1</COMPRESSOR>
    <PUMP>0</PUMP>
</STAVJED>"""
    
    print("📝 Testing with sample XML:")
    print(sample_xml)
    
    entities = parse_xml_entities(sample_xml, "test.xml")
    print(f"\n📈 Parsed {len(entities)} entities:")
    
    for entity in entities:
        print(f"  - {entity.get('field_name')}: {entity.get('value')} ({entity.get('type')})")


if __name__ == "__main__":
    print("XCC XML Debugger")
    print("Choose an option:")
    print("1. Debug real XCC controller XML")
    print("2. Test XML parsing function")
    print("3. Both")
    
    choice = input("Enter choice (1, 2, or 3): ").strip()
    
    if choice in ["1", "3"]:
        asyncio.run(debug_xcc_xml())
    
    if choice in ["2", "3"]:
        asyncio.run(test_xml_parsing())
