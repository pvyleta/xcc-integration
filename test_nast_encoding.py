#!/usr/bin/env python3
"""Test NAST pages with proper encoding handling."""

import asyncio
import aiohttp
import re

async def test_nast_with_encoding():
    """Test NAST pages with different encoding options."""
    
    print("🔍 TESTING NAST PAGES WITH ENCODING HANDLING")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        login_data = {'USER': 'xcc', 'PASS': 'xcc', 'ACER': '0'}
        
        # Test the individual data pages with different encodings
        test_pages = ['NAST1.XML', 'NAST2.XML', 'NAST3.XML']
        found_pages = []
        
        for page in test_pages:
            print(f"\n📄 Testing {page}...")
            
            try:
                async with session.post(f'http://liskovaxcc.vyleta.com/{page}', data=login_data) as response:
                    # Try different encodings
                    encodings = ['windows-1250', 'utf-8', 'iso-8859-2', 'cp1252']
                    
                    content = None
                    used_encoding = None
                    
                    for encoding in encodings:
                        try:
                            content = await response.text(encoding=encoding)
                            if len(content) > 100 and '<LOGIN>' not in content and 'HTTP Error 404' not in content:
                                used_encoding = encoding
                                break
                        except Exception:
                            continue
                    
                    if content and used_encoding:
                        print(f"✅ {page} exists: {len(content)} characters (encoding: {used_encoding})")
                        found_pages.append(page)
                        
                        # Save with proper encoding
                        safe_name = page.lower().replace('.', '_')
                        with open(f'nast_data_{safe_name}', 'w', encoding='utf-8') as f:
                            f.write(content)
                        
                        # Count entities
                        entities = re.findall(r'<INPUT[^>]*P="([^"]*)"', content)
                        print(f"   📊 Contains {len(entities)} entities")
                        
                        if entities:
                            print(f"   🏷️  Sample entities: {', '.join(entities[:5])}")
                            
                            # Look for specific interesting entities
                            interesting = [e for e in entities if any(keyword in e.upper() for keyword in 
                                         ['OFFSET', 'KOREKCE', 'VYKON', 'TEPLOTA', 'ODSTAVENI'])]
                            if interesting:
                                print(f"   🎯 Interesting entities: {', '.join(interesting[:3])}")
                    else:
                        print(f"❌ {page} not accessible or not found")
                        
            except Exception as e:
                print(f"❌ Error testing {page}: {e}")
        
        return found_pages

async def main():
    """Main function."""

    # Analyze the descriptor first
    data_refs = analyze_nast_descriptor()
    
    # Test data pages with proper encoding
    found_data_pages = await test_nast_with_encoding()
    
    print(f"\n🎯 FINAL NAST DISCOVERY RESULTS:")
    print(f"   Descriptor: nast.xml ✅")
    print(f"   Data pages found: {len(found_data_pages)}")
    for page in found_data_pages:
        print(f"     - {page}")
    
    if found_data_pages:
        print(f"\n🔧 INTEGRATION UPDATE NEEDED:")
        print(f"   Add 'nast.xml' to XCC_DESCRIPTOR_PAGES")
        print(f"   Add {found_data_pages} to XCC_DATA_PAGES")
        
        print(f"\n📈 EXPECTED NEW ENTITIES:")
        print(f"   🌡️  Sensor correction offsets (B0-I, B4-I, etc.)")
        print(f"   🔧 Power restriction settings")
        print(f"   🔄 Heat pump on/off controls")
        print(f"   💾 System backup/restore buttons")
        print(f"   🏠 Multi-zone temperature offsets")
        
        # Estimate entity count
        total_entities = 100 + 32 + 10 + 3 + 8  # numbers + choices + buttons + text + labels
        print(f"   📊 Estimated additional entities: ~{total_entities}")
    else:
        print(f"\n❌ No accessible data pages found for nast.xml")

if __name__ == "__main__":
    asyncio.run(main())
