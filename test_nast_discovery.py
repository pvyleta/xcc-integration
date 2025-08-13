#!/usr/bin/env python3
"""
Test script to discover nast.xml page and its data pages.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from xcc_client import XCCClient

async def discover_nast_pages():
    """Discover nast.xml and its associated data pages."""
    
    print("🔍 DISCOVERING NAST.XML PAGE")
    print("=" * 50)
    
    # Create XCC client
    client = XCCClient("liskovaxcc.vyleta.com", "xcc", "xcc")
    await client.__aenter__()
    
    try:
        # Test if nast.xml exists
        print("📄 Testing nast.xml descriptor...")
        
        try:
            nast_content = await client.fetch_page("nast.xml")
            if nast_content and len(nast_content) > 100 and '<LOGIN>' not in nast_content:
                print(f"✅ nast.xml exists: {len(nast_content)} characters")
                
                # Save for analysis
                with open("nast_descriptor.xml", "w", encoding="utf-8") as f:
                    f.write(nast_content)
                
                # Look for data page references in the descriptor
                import re
                data_refs = re.findall(r'[A-Z][A-Z0-9]*\.XML', nast_content)
                print(f"📊 Data page references in nast.xml: {data_refs}")
                
                # Test common NAST data page patterns
                potential_data_pages = [
                    "NAST1.XML", "NAST4.XML", "NAST10.XML", "NAST11.XML",
                    "NAST21.XML", "NAST31.XML"
                ]
                
                found_data_pages = []
                
                print(f"\n🔍 Testing potential NAST data pages...")
                for data_page in potential_data_pages:
                    try:
                        data_content = await client.fetch_page(data_page)
                        if data_content and len(data_content) > 100 and '<LOGIN>' not in data_content:
                            print(f"✅ {data_page} exists: {len(data_content)} characters")
                            found_data_pages.append(data_page)
                            
                            # Save for analysis
                            with open(f"nast_{data_page.lower()}", "w", encoding="utf-8") as f:
                                f.write(data_content)
                            
                            # Count entities in this data page
                            entities = re.findall(r'<INPUT[^>]*P="([^"]*)"', data_content)
                            print(f"   📊 Contains {len(entities)} entities")
                            
                            # Show first few entities
                            if entities:
                                print(f"   🏷️  Sample entities: {', '.join(entities[:5])}")
                        else:
                            print(f"❌ {data_page} not available")
                    except Exception as e:
                        print(f"❌ Error testing {data_page}: {e}")
                
                print(f"\n📋 NAST PAGE DISCOVERY RESULTS:")
                print(f"   Descriptor: nast.xml ✅")
                print(f"   Data pages found: {len(found_data_pages)}")
                for page in found_data_pages:
                    print(f"     - {page}")
                
                return "nast.xml", found_data_pages
                
            else:
                print(f"❌ nast.xml not available or login page")
                return None, []
                
        except Exception as e:
            print(f"❌ Error testing nast.xml: {e}")
            return None, []
    
    finally:
        await client.__aexit__(None, None, None)

async def main():
    """Main function."""
    try:
        descriptor, data_pages = await discover_nast_pages()
        
        if descriptor and data_pages:
            print(f"\n🎯 INTEGRATION UPDATE NEEDED:")
            print(f"   Add '{descriptor}' to XCC_DESCRIPTOR_PAGES")
            print(f"   Add {data_pages} to XCC_DATA_PAGES")
            print(f"\n🔧 This will provide additional entities from the NAST system!")
        else:
            print(f"\n❌ NAST pages not found or not accessible")
            
    except Exception as e:
        print(f"❌ Discovery failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
