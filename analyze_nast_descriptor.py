#!/usr/bin/env python3
"""Analyze nast.xml descriptor to find the correct data page pattern."""

import re
import asyncio
import aiohttp

def analyze_nast_descriptor():
    """Analyze the nast.xml descriptor to understand its structure."""
    
    print("🔍 ANALYZING NAST.XML DESCRIPTOR")
    print("=" * 50)
    
    # Load the descriptor
    with open('nast_descriptor.xml', 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"📄 Descriptor length: {len(content)} characters")
    
    # Parse the structure
    print(f"\n📋 PAGE STRUCTURE:")
    
    # Extract page info
    page_match = re.search(r'<page[^>]*name="([^"]*)"[^>]*name_en="([^"]*)"', content)
    if page_match:
        print(f"   Name (CZ): {page_match.group(1)}")
        print(f"   Name (EN): {page_match.group(2)}")
    
    # Find all blocks
    blocks = re.findall(r'<block[^>]*data="([^"]*)"[^>]*name="([^"]*)"[^>]*name_en="([^"]*)"', content)
    print(f"\n📦 BLOCKS FOUND ({len(blocks)}):")
    for i, (data_ref, name_cz, name_en) in enumerate(blocks, 1):
        print(f"   {i}. {data_ref} - {name_en} ({name_cz})")
    
    # Find all entity properties
    number_props = re.findall(r'<number[^>]*prop="([^"]*)"', content)
    choice_props = re.findall(r'<choice[^>]*prop="([^"]*)"', content)
    button_props = re.findall(r'<button[^>]*prop="([^"]*)"', content)
    text_props = re.findall(r'<text[^>]*prop="([^"]*)"', content)
    label_props = re.findall(r'<label[^>]*prop="([^"]*)"', content)
    
    print(f"\n🏷️  ENTITY PROPERTIES:")
    print(f"   Numbers: {len(number_props)} ({', '.join(number_props[:5])}...)")
    print(f"   Choices: {len(choice_props)} ({', '.join(choice_props[:5])}...)")
    print(f"   Buttons: {len(button_props)} ({', '.join(button_props[:3])}...)")
    print(f"   Text: {len(text_props)} ({', '.join(text_props[:3])}...)")
    print(f"   Labels: {len(label_props)} ({', '.join(label_props[:3])}...)")
    
    # Find data references
    data_refs = set(re.findall(r'data="([^"]*)"', content))
    print(f"\n📊 DATA REFERENCES:")
    for ref in sorted(data_refs):
        print(f"   - {ref}")
    
    return list(data_refs)

async def test_nast_data_pages(data_refs):
    """Test the actual data pages based on the descriptor analysis."""
    
    print(f"\n🔍 TESTING NAST DATA PAGES")
    print("=" * 50)
    
    # Based on the descriptor, the data pages should be named after the data references
    # Common patterns: NAST1.XML, NAST2.XML, NAST3.XML
    
    potential_pages = []
    for ref in data_refs:
        # Try different patterns
        patterns = [
            f"{ref}.XML",  # NAST1.XML
            f"{ref}1.XML", # NAST11.XML  
            f"{ref}0.XML", # NAST10.XML
        ]
        potential_pages.extend(patterns)
    
    # Also try some common patterns
    common_patterns = [
        "NAST.XML", "NAST1.XML", "NAST2.XML", "NAST3.XML",
        "NASTAVENI.XML", "NASTAVENI1.XML"
    ]
    potential_pages.extend(common_patterns)
    
    # Remove duplicates
    potential_pages = list(set(potential_pages))
    
    print(f"🧪 Testing {len(potential_pages)} potential data pages...")
    
    found_pages = []
    
    async with aiohttp.ClientSession() as session:
        login_data = {'USER': 'xcc', 'PASS': 'xcc', 'ACER': '0'}
        
        for page in potential_pages:
            try:
                async with session.post(f'http://liskovaxcc.vyleta.com/{page}', data=login_data) as response:
                    data_content = await response.text()
                    
                    if len(data_content) > 100 and '<LOGIN>' not in data_content and 'HTTP Error 404' not in data_content:
                        print(f"✅ {page} exists: {len(data_content)} characters")
                        found_pages.append(page)
                        
                        # Save for analysis
                        safe_name = page.lower().replace('.', '_')
                        with open(f'nast_data_{safe_name}', 'w', encoding='utf-8') as f:
                            f.write(data_content)
                        
                        # Count entities
                        entities = re.findall(r'<INPUT[^>]*P="([^"]*)"', data_content)
                        print(f"   📊 Contains {len(entities)} entities")
                        
                        if entities:
                            print(f"   🏷️  Sample entities: {', '.join(entities[:5])}")
                    else:
                        print(f"❌ {page} not found")
                        
            except Exception as e:
                print(f"❌ Error testing {page}: {e}")
    
    return found_pages

async def main():
    """Main analysis function."""
    
    # First analyze the descriptor
    data_refs = analyze_nast_descriptor()
    
    # Then test for actual data pages
    found_data_pages = await test_nast_data_pages(data_refs)
    
    print(f"\n🎯 NAST DISCOVERY SUMMARY:")
    print(f"   Descriptor: nast.xml ✅")
    print(f"   Data pages found: {len(found_data_pages)}")
    for page in found_data_pages:
        print(f"     - {page}")
    
    if found_data_pages:
        print(f"\n🔧 INTEGRATION UPDATE NEEDED:")
        print(f"   Add 'nast.xml' to XCC_DESCRIPTOR_PAGES")
        print(f"   Add {found_data_pages} to XCC_DATA_PAGES")
        print(f"\n📈 EXPECTED BENEFIT:")
        print(f"   Additional heat pump settings and sensor corrections")
        print(f"   Power restriction controls")
        print(f"   Heat pump on/off switches")
        print(f"   System backup/restore functionality")
    else:
        print(f"\n❌ No data pages found for nast.xml")
        print(f"   The descriptor exists but may not have corresponding data")

if __name__ == "__main__":
    asyncio.run(main())
