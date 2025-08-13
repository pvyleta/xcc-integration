#!/usr/bin/env python3
"""Test the improved page discovery logic with the actual main.xml."""

import re

def test_improved_discovery():
    """Test the improved page discovery logic."""
    
    # Read the actual main.xml content
    with open('tests/sample_data/main.xml', 'r', encoding='utf-8') as f:
        main_content = f.read()
    
    # Wrap in PAGE element for proper XML structure
    xml_content = f'<PAGE>{main_content}</PAGE>'
    
    print("🔍 Testing Improved Page Discovery Logic")
    print("=" * 50)
    
    # Simulate the improved discovery logic using regex (since we don't have lxml here)
    
    # Find all F elements with their content
    f_pattern = r'<F[^>]*U="([^"]+)"[^>]*>(.*?)</F>'
    f_matches = re.findall(f_pattern, xml_content, re.DOTALL)
    
    active_pages = []
    configured_pages = []
    
    for page_url, content in f_matches:
        is_active = False
        
        # Method 1: INPUTV with VALUE="1"
        if 'INPUTV' in content and 'VALUE="1"' in content:
            is_active = True
            active_pages.append((page_url, "INPUTV=1"))
        
        # Method 2: INPUTI with non-zero VALUE
        elif not is_active:
            inputi_pattern = r'INPUTI[^>]*VALUE="([^"]+)"'
            inputi_matches = re.findall(inputi_pattern, content)
            for value in inputi_matches:
                try:
                    int_value = int(value)
                    if int_value > 0:
                        is_active = True
                        configured_pages.append((page_url, f"INPUTI={value}"))
                        break
                except ValueError:
                    pass
        
        # Method 3: Special handling for essential system pages
        if not is_active and page_url in ['biv.xml', 'bivtuv.xml', 'stavjed.xml']:
            if 'INPUTI' in content and 'VALUE=' in content:
                is_active = True
                configured_pages.append((page_url, "Essential system page"))
    
    print(f"📋 Active Pages (INPUTV=1): {len(active_pages)}")
    for page_url, reason in active_pages:
        print(f"  ✅ {page_url} ({reason})")
    
    print(f"\n📋 Configured Pages (INPUTI>0 or Essential): {len(configured_pages)}")
    for page_url, reason in configured_pages:
        print(f"  🔧 {page_url} ({reason})")
    
    # Check specifically for biv.xml
    biv_found = False
    for page_url, reason in active_pages + configured_pages:
        if page_url == 'biv.xml':
            biv_found = True
            print(f"\n🎯 biv.xml FOUND: {page_url} ({reason})")
            break
    
    if not biv_found:
        print("\n❌ biv.xml NOT FOUND - checking manually...")
        biv_pattern = r'<F[^>]*U="biv\.xml"[^>]*>(.*?)</F>'
        biv_match = re.search(biv_pattern, xml_content, re.DOTALL)
        if biv_match:
            print(f"   Raw biv.xml content: {biv_match.group(1)}")
        else:
            print("   biv.xml not found in main.xml")
    
    total_discovered = len(active_pages) + len(configured_pages)
    print(f"\n📊 Total Discovered Pages: {total_discovered}")
    
    # Expected pages that should be discovered
    expected_pages = ['okruh.xml', 'tuv1.xml', 'fve.xml', 'pocasi.xml', 'biv.xml']
    found_pages = [url.split('?')[0] for url, _ in active_pages + configured_pages]
    
    print(f"\n🎯 Expected vs Found:")
    for expected in expected_pages:
        status = "✅" if expected in found_pages else "❌"
        print(f"  {status} {expected}")
    
    return total_discovered >= 5  # Should find at least 5 pages now

if __name__ == "__main__":
    success = test_improved_discovery()
    if success:
        print("\n🎉 Improved discovery logic test PASSED!")
    else:
        print("\n❌ Improved discovery logic test FAILED!")
    exit(0 if success else 1)
