#!/usr/bin/env python3
"""
Fetch sample pages to understand the structure better
"""

import asyncio
import aiohttp
import hashlib
import os
from lxml import etree

async def fetch_and_save_page(session, ip, page_name, output_dir="test/sample_pages"):
    """Fetch a single page and save it"""
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        url = f"http://{ip}/{page_name}"
        async with session.get(url) as resp:
            if resp.status == 200:
                content = await resp.text()
                
                # Save raw content
                with open(f"{output_dir}/{page_name}", "w", encoding="utf-8") as f:
                    f.write(content)
                    
                print(f"✓ Saved {page_name} ({len(content)} chars)")
                
                # Try to parse and show structure
                try:
                    root = etree.fromstring(content.encode())
                    print(f"  Root element: {root.tag}")
                    print(f"  Child elements: {[child.tag for child in root[:5]]}")  # First 5 children
                    
                    # Look for input-like elements
                    input_elements = []
                    for tag in ["input", "number", "choice", "option", "switch", "button", "form"]:
                        elements = root.findall(f".//{tag}")
                        if elements:
                            input_elements.append(f"{tag}({len(elements)})")
                    
                    if input_elements:
                        print(f"  Input elements: {', '.join(input_elements)}")
                    else:
                        print(f"  No input elements found")
                        
                except Exception as e:
                    print(f"  XML parse error: {e}")
                    
            else:
                print(f"✗ {page_name}: HTTP {resp.status}")
                
    except Exception as e:
        print(f"✗ {page_name}: {e}")

async def authenticate_session(ip, username, password):
    """Create authenticated session"""
    cookie_jar = aiohttp.CookieJar(unsafe=True)
    session = aiohttp.ClientSession(cookie_jar=cookie_jar)
    
    # Get login page
    login_xml_url = f"http://{ip}/LOGIN.XML"
    async with session.get(login_xml_url) as resp:
        if resp.status != 200:
            raise Exception("Failed to get LOGIN.XML")
            
    # Get session ID
    session_id = next((c.value for c in session.cookie_jar if c.key == "SoftPLC"), None)
    if not session_id:
        raise Exception("No SoftPLC cookie found")
        
    # Login
    passhash = hashlib.sha1(f"{session_id}{password}".encode()).hexdigest()
    login_url = f"http://{ip}/RPC/WEBSES/create.asp"
    payload = {"USER": username, "PASS": passhash}
    
    async with session.post(login_url, data=payload) as resp:
        if resp.status != 200:
            raise Exception("Login failed")
            
    return session

async def main():
    ip = "192.168.0.50"
    username = "xcc"
    password = "xcc"
    
    print("Fetching sample pages to analyze structure...")
    
    session = await authenticate_session(ip, username, password)
    
    try:
        # Fetch interesting pages
        pages_to_fetch = [
            "CONFIG.XML", "CONFIG0.XML", "CONFIG1.XML",
            "SETTINGS.XML", "SETTINGS0.XML", 
            "MAIN.XML", "INDEX.XML",
            "stavjed.xml", "okruh.xml", "tuv1.xml",
            "NETWORK.XML", "SYSTEM.XML", "TIME.XML"
        ]
        
        for page in pages_to_fetch:
            await fetch_and_save_page(session, ip, page)
            
    finally:
        await session.close()
        
    print("\nSample pages saved to 'test/sample_pages/' directory")
    print("You can examine these files to understand the XML structure")

if __name__ == "__main__":
    asyncio.run(main())
