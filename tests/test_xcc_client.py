"""Tests for XCC client functionality."""

import pytest
import os
import xml.etree.ElementTree as ET

def test_sample_data_parsing(sample_data_dir):
    """Test that sample XML data can be parsed."""
    xml_files = ["BIV.XML", "FVE.XML", "OKRUH.XML", "SPOT.XML", "STAVJED.XML", "TUV1.XML"]
    
    for xml_file in xml_files:
        file_path = os.path.join(sample_data_dir, xml_file)
        
        # Test that XML can be parsed
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            assert root is not None, f"Failed to parse XML root in {xml_file}"
        except ET.ParseError as e:
            pytest.fail(f"XML parsing error in {xml_file}: {e}")

def test_xml_structure(sample_data_dir):
    """Test that XML files have expected structure."""
    xml_files = ["BIV.XML", "FVE.XML", "OKRUH.XML", "SPOT.XML", "STAVJED.XML", "TUV1.XML"]
    
    for xml_file in xml_files:
        file_path = os.path.join(sample_data_dir, xml_file)
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # Check that there are some elements
        assert len(list(root)) > 0, f"No elements found in {xml_file}"
        
        # Check for common XCC XML patterns
        has_inputs = any(elem.tag == "INPUT" for elem in root.iter())
        has_rows = any(elem.tag == "row" for elem in root.iter())
        has_blocks = any(elem.tag == "block" for elem in root.iter())
        has_pages = root.tag == "page"

        assert has_inputs or has_rows or has_blocks or has_pages, f"No expected XCC elements found in {xml_file}"

def test_xml_encoding(sample_data_dir):
    """Test that XML files are properly encoded."""
    xml_files = ["BIV.XML", "FVE.XML", "OKRUH.XML", "SPOT.XML", "STAVJED.XML", "TUV1.XML"]
    
    for xml_file in xml_files:
        file_path = os.path.join(sample_data_dir, xml_file)
        
        # Test reading with UTF-8 encoding
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            assert len(content) > 0, f"Empty content in {xml_file}"
        except UnicodeDecodeError:
            # Try with different encoding
            with open(file_path, 'r', encoding='iso-8859-1') as f:
                content = f.read()
            assert len(content) > 0, f"Empty content in {xml_file}"
