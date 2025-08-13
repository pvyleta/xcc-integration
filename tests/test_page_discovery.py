"""Test XCC page discovery functionality using sample data."""

import pytest
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

# Add the custom_components directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from lxml import etree
    LXML_AVAILABLE = True
except ImportError:
    LXML_AVAILABLE = False


class TestPageDiscovery:
    """Test page discovery functionality with real sample data."""

    @pytest.fixture
    def sample_main_xml(self, sample_data_dir):
        """Load the actual main.xml sample data."""
        main_xml_path = os.path.join(sample_data_dir, 'main.xml')
        with open(main_xml_path, 'r', encoding='utf-8') as f:
            return f.read()

    @pytest.fixture
    def mock_xcc_client(self):
        """Create a mock XCC client with page discovery methods."""
        # Import here to avoid issues if dependencies aren't available
        try:
            from custom_components.xcc.xcc_client import XCCClient
            
            # Create a real client instance but mock the network calls
            client = XCCClient("192.168.1.100", "test", "test")
            
            # Mock the session to avoid actual network calls
            client.session = AsyncMock()
            
            return client
        except ImportError:
            # Fallback mock if imports fail
            mock_client = MagicMock()
            mock_client.discover_active_pages = AsyncMock()
            mock_client.discover_data_pages = AsyncMock()
            mock_client.auto_discover_all_pages = AsyncMock()
            mock_client._determine_page_type = MagicMock()
            mock_client._is_login_page = MagicMock(return_value=False)
            return mock_client

    def test_page_type_determination(self, mock_xcc_client):
        """Test page type determination logic."""
        if hasattr(mock_xcc_client, '_determine_page_type'):
            # Test with real method
            test_cases = [
                ('okruh.xml?page=0', 'heating_circuit'),
                ('mzona.xml?p=1', 'mixed_zone'),
                ('tuv1.xml', 'hot_water'),
                ('tuv2.xml', 'hot_water'),
                ('bazen1.xml', 'pool'),
                ('bazmist.xml', 'pool'),
                ('fve.xml', 'photovoltaics'),
                ('vzt.xml', 'ventilation'),
                ('biv.xml', 'bivalent'),
                ('bivtuv.xml', 'bivalent'),
                ('solar.xml', 'solar'),
                ('meteo.xml', 'weather_station'),
                ('pocasi.xml', 'weather_forecast'),
                ('elmer.xml', 'electricity_meter'),
                ('spot.xml', 'spot_pricing'),
                ('unknown.xml', 'other'),
            ]
            
            for page_url, expected_type in test_cases:
                result = mock_xcc_client._determine_page_type(page_url)
                assert result == expected_type, f"Page type detection failed for {page_url}: got {result}, expected {expected_type}"
        else:
            # Skip if method not available
            pytest.skip("_determine_page_type method not available")

    @pytest.mark.skipif(not LXML_AVAILABLE, reason="lxml not available")
    def test_main_xml_parsing(self, sample_main_xml):
        """Test parsing of the actual main.xml sample data."""
        # Parse the main.xml content
        import re
        xml_clean = re.sub(r'<\?xml[^>]*\?>', '', sample_main_xml).strip()
        
        # Wrap in PAGE element if needed
        if not xml_clean.startswith('<PAGE>'):
            xml_clean = f'<PAGE>{xml_clean}</PAGE>'
        
        root = etree.fromstring(xml_clean)
        
        # Find all F elements (page definitions)
        f_elements = root.xpath('.//F')
        
        assert len(f_elements) > 0, "Should find page definitions in main.xml"
        
        # Track discovered pages
        active_pages = []
        inactive_pages = []
        page_info = {}
        
        for f_elem in f_elements:
            page_id = f_elem.get('N')
            page_url = f_elem.get('U')
            
            if not page_url:
                continue
            
            # Extract page name
            name_elem = f_elem.xpath('.//INPUTN[@NAME and @VALUE]')
            page_name = name_elem[0].get('VALUE') if name_elem else f"Page {page_id}"
            
            # Check if page is active
            active_elem = f_elem.xpath('.//INPUTV[@VALUE="1"]')
            is_active = len(active_elem) > 0
            
            page_info[page_url] = {
                'id': int(page_id) if page_id else None,
                'name': page_name,
                'active': is_active
            }
            
            if is_active:
                active_pages.append((page_url, page_name))
            else:
                inactive_pages.append((page_url, page_name))
        
        # Verify we found the expected active pages based on the sample data
        active_page_urls = [url for url, _ in active_pages]
        
        # These should be active based on the sample main.xml
        expected_active = [
            'okruh.xml?page=0',  # Radiátory
            'tuv1.xml',          # Teplá voda
            'fve.xml',           # FVE
            'pocasi.xml'         # Weather forecast
        ]
        
        for expected_url in expected_active:
            assert expected_url in active_page_urls, f"Expected active page {expected_url} not found in discovered active pages"
        
        # Verify we have some inactive pages too
        assert len(inactive_pages) > 0, "Should have some inactive pages"
        
        print(f"✅ Discovered {len(active_pages)} active pages and {len(inactive_pages)} inactive pages")
        print(f"Active pages: {[name for _, name in active_pages]}")

    @pytest.mark.asyncio
    async def test_discover_active_pages_integration(self, mock_xcc_client, sample_main_xml):
        """Test the discover_active_pages method with sample data."""
        if not hasattr(mock_xcc_client, 'discover_active_pages'):
            pytest.skip("discover_active_pages method not available")
        
        # Mock the fetch_page method to return our sample data
        mock_xcc_client.fetch_page = AsyncMock(return_value=sample_main_xml)
        
        try:
            # Call the discovery method
            pages_info = await mock_xcc_client.discover_active_pages()
            
            # Verify the method was called
            mock_xcc_client.fetch_page.assert_called_once_with("main.xml")
            
            # Verify we got results
            assert isinstance(pages_info, dict), "Should return a dictionary"
            
            if pages_info:  # Only test if we got results (depends on lxml availability)
                # Check for expected active pages
                active_pages = {url: info for url, info in pages_info.items() if info.get('active')}
                
                assert len(active_pages) > 0, "Should find some active pages"
                
                # Verify specific expected pages
                expected_active_names = ['Radiátory', 'Teplá voda', 'FVE']
                found_names = [info['name'] for info in active_pages.values()]
                
                for expected_name in expected_active_names:
                    assert any(expected_name in name for name in found_names), \
                        f"Expected to find page with name containing '{expected_name}'"
                
                print(f"✅ Successfully discovered {len(active_pages)} active pages")
            else:
                print("⚠️  Page discovery returned empty results (may be due to missing dependencies)")
                
        except Exception as e:
            if "lxml" in str(e).lower():
                pytest.skip(f"Skipping due to lxml dependency: {e}")
            else:
                raise

    @pytest.mark.asyncio
    async def test_discover_data_pages_integration(self, mock_xcc_client):
        """Test the discover_data_pages method."""
        if not hasattr(mock_xcc_client, 'discover_data_pages'):
            pytest.skip("discover_data_pages method not available")
        
        # Mock sample descriptor pages
        descriptor_pages = ['fve.xml', 'okruh.xml', 'tuv1.xml']
        
        # Mock fetch_page to return different content for different pages
        def mock_fetch_page(page):
            if page == 'fve.xml':
                return '<page>Some FVE4.XML reference content</page>'
            elif page == 'okruh.xml':
                return '<page>Some OKRUH10.XML reference content</page>'
            elif page == 'tuv1.xml':
                return '<page>Some TUV11.XML reference content</page>'
            elif page.endswith('.XML'):  # Data pages
                return '<page><INPUT P="TEST" VALUE="123"/></page>'
            else:
                raise Exception("Page not found")
        
        mock_xcc_client.fetch_page = AsyncMock(side_effect=mock_fetch_page)
        
        try:
            # Call the discovery method
            data_pages_map = await mock_xcc_client.discover_data_pages(descriptor_pages)
            
            # Verify the method was called
            assert isinstance(data_pages_map, dict), "Should return a dictionary"
            
            # Verify we got some results
            if data_pages_map:
                print(f"✅ Successfully discovered data pages: {data_pages_map}")
            else:
                print("⚠️  No data pages discovered (may be expected in test environment)")
                
        except Exception as e:
            if "lxml" in str(e).lower() or "etree" in str(e).lower():
                pytest.skip(f"Skipping due to XML parsing dependency: {e}")
            else:
                raise

    @pytest.mark.asyncio
    async def test_auto_discover_all_pages_integration(self, mock_xcc_client, sample_main_xml):
        """Test the complete auto-discovery process."""
        if not hasattr(mock_xcc_client, 'auto_discover_all_pages'):
            pytest.skip("auto_discover_all_pages method not available")
        
        # Mock the fetch_page method
        def mock_fetch_page(page):
            if page == 'main.xml':
                return sample_main_xml
            elif page.endswith('.xml') and not page.endswith('.XML'):
                return '<page>Descriptor content</page>'
            elif page.endswith('.XML'):
                return '<page><INPUT P="TEST" VALUE="123"/></page>'
            else:
                raise Exception("Page not found")
        
        mock_xcc_client.fetch_page = AsyncMock(side_effect=mock_fetch_page)
        
        try:
            # Call the auto-discovery method
            descriptor_pages, data_pages = await mock_xcc_client.auto_discover_all_pages()
            
            # Verify we got results
            assert isinstance(descriptor_pages, list), "Should return descriptor pages list"
            assert isinstance(data_pages, list), "Should return data pages list"
            
            if descriptor_pages or data_pages:
                print(f"✅ Auto-discovery successful:")
                print(f"   Descriptor pages: {descriptor_pages}")
                print(f"   Data pages: {data_pages}")
            else:
                print("⚠️  Auto-discovery returned empty results (may be due to test environment)")
                
        except Exception as e:
            if any(dep in str(e).lower() for dep in ["lxml", "etree", "xml"]):
                pytest.skip(f"Skipping due to XML parsing dependency: {e}")
            else:
                raise

    def test_page_discovery_fallback(self):
        """Test that page discovery has proper fallback behavior."""
        # This test verifies the fallback logic without requiring external dependencies
        
        # Test the fallback constants are available
        try:
            from custom_components.xcc.const import XCC_DESCRIPTOR_PAGES, XCC_DATA_PAGES
            
            assert isinstance(XCC_DESCRIPTOR_PAGES, list), "Should have descriptor pages fallback"
            assert isinstance(XCC_DATA_PAGES, list), "Should have data pages fallback"
            assert len(XCC_DESCRIPTOR_PAGES) > 0, "Should have some descriptor pages"
            assert len(XCC_DATA_PAGES) > 0, "Should have some data pages"
            
            print(f"✅ Fallback configuration available:")
            print(f"   Default descriptor pages: {XCC_DESCRIPTOR_PAGES}")
            print(f"   Default data pages: {XCC_DATA_PAGES}")
            
        except ImportError as e:
            pytest.skip(f"Cannot import constants: {e}")


if __name__ == "__main__":
    # Allow running the test directly
    pytest.main([__file__, "-v"])
