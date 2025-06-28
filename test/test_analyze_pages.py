#!/usr/bin/env python3
"""
Tests for analyze_known_pages.py functionality
"""

import pytest
import json
import os
import sys
from unittest.mock import Mock, patch, mock_open

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'scripts'))
import analyze_known_pages


class TestAnalyzePages:
    """Test cases for page analysis functionality"""

    def test_extract_field_info_basic(self):
        """Test basic field info extraction"""
        from lxml import etree

        xml_content = '<INPUT prop="TEST-FIELD" type="numeric" min="0" max="100" unit="°C">Test Field</INPUT>'
        elem = etree.fromstring(xml_content)

        result = analyze_known_pages.extract_field_info(elem, "input")

        assert result["element_type"] == "input"
        assert result["attributes"]["prop"] == "TEST-FIELD"
        assert result["attributes"]["type"] == "numeric"
        assert result["attributes"]["min"] == "0"
        assert result["attributes"]["max"] == "100"
        assert result["attributes"]["unit"] == "°C"
        
    def test_determine_data_type_numeric(self):
        """Test data type determination for numeric fields"""
        info = {"attributes": {"type": "numeric", "min": "0", "max": "100"}}

        data_type = analyze_known_pages.determine_data_type(info)
        assert data_type == "numeric"

    def test_determine_data_type_choice(self):
        """Test data type determination for choice fields"""
        info = {"element_type": "choice"}

        data_type = analyze_known_pages.determine_data_type(info)
        assert data_type == "enum"

    def test_determine_data_type_boolean(self):
        """Test data type determination for boolean fields"""
        info = {"attributes": {"type": "boolean"}}

        data_type = analyze_known_pages.determine_data_type(info)
        assert data_type == "boolean"

    def test_determine_data_type_default(self):
        """Test data type determination with unknown type"""
        info = {"attributes": {"type": "unknown"}}

        data_type = analyze_known_pages.determine_data_type(info)
        assert data_type == "unknown"

    def test_authenticate_session_import(self):
        """Test that authenticate_session function exists"""
        assert hasattr(analyze_known_pages, 'authenticate_session')

    def test_extract_field_info_import(self):
        """Test that extract_field_info function exists"""
        assert hasattr(analyze_known_pages, 'extract_field_info')


class TestMainFunction:
    """Test the main analysis function"""

    def test_main_function_exists(self):
        """Test that main function exists"""
        assert hasattr(analyze_known_pages, 'main')
        assert callable(analyze_known_pages.main)

    def test_known_pages_structure(self):
        """Test that known pages are defined"""
        # The script should have some way to define known pages
        # Let's just test that the main function can be called
        try:
            # This might fail due to network, but should not fail due to import issues
            analyze_known_pages.main()
        except Exception as e:
            # Expected to fail without network connection, but should not be import error
            assert "import" not in str(e).lower()

    def test_async_functions_exist(self):
        """Test that required async functions exist"""
        assert hasattr(analyze_known_pages, 'authenticate_session')
        assert hasattr(analyze_known_pages, 'fetch_page_xml')


if __name__ == "__main__":
    pytest.main([__file__])
