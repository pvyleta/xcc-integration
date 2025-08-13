#!/usr/bin/env python3
"""Simple test for nast.xml page."""

import asyncio
import aiohttp
import re

async def test_nast():
    """Test if nast.xml exists and find its data pages."""
    
    async with aiohttp.ClientSession() as session:
        login_data = {'USER': 'xcc', 'PASS': 'xcc', 'ACER': '0'}
        
        print('🔍 Testing nast.xml...')
        try:
            async with session.post('http://liskovaxcc.vyleta.com/nast.xml', data=login_data) as response:
                content = await response.text()
                print(f'Response length: {len(content)}')
                
                if len(content) > 100 and '<LOGIN>' not in content:
                    print('✅ nast.xml exists!')
                    
                    # Save the descriptor
                    with open('nast_descriptor.xml', 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    # Look for data page references
                    data_refs = re.findall(r'[A-Z][A-Z0-9]*\.XML', content)
                    print(f'📄 Data references found: {data_refs}')
                    
                    # Test common NAST data patterns
                    test_pages = ['NAST1.XML', 'NAST4.XML', 'NAST10.XML', 'NAST11.XML', 'NAST21.XML']
                    found_pages = []
                    
                    for page in test_pages:
                        try:
                            async with session.post(f'http://liskovaxcc.vyleta.com/{page}', data=login_data) as data_response:
                                data_content = await data_response.text()
                                if len(data_content) > 100 and '<LOGIN>' not in data_content:
                                    print(f'✅ {page} exists: {len(data_content)} characters')
                                    found_pages.append(page)
                                    
                                    # Save data page
                                    with open(f'nast_{page.lower()}', 'w', encoding='utf-8') as f:
                                        f.write(data_content)
                                    
                                    # Count entities
                                    entities = re.findall(r'<INPUT[^>]*P="([^"]*)"', data_content)
                                    print(f'   📊 Contains {len(entities)} entities')
                                    if entities:
                                        print(f'   🏷️  Sample: {", ".join(entities[:3])}...')
                                else:
                                    print(f'❌ {page} not available')
                        except Exception as e:
                            print(f'❌ Error testing {page}: {e}')
                    
                    print(f'\n🎯 NAST DISCOVERY RESULTS:')
                    print(f'   Descriptor: nast.xml ✅')
                    print(f'   Data pages: {found_pages}')
                    
                    return 'nast.xml', found_pages
                    
                else:
                    print('❌ nast.xml not available or login page')
                    return None, []
                    
        except Exception as e:
            print(f'❌ Error testing nast.xml: {e}')
            return None, []

if __name__ == "__main__":
    asyncio.run(test_nast())
