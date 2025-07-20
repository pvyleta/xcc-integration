"""
Standalone tests for XCC modules that don't require Home Assistant.

These tests verify the core functionality works independently.
"""

import pytest
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Add the XCC module path directly
xcc_path = project_root / "custom_components" / "xcc"
sys.path.insert(0, str(xcc_path))


def test_xcc_client_standalone():
    """Test XCC client can be imported and used standalone."""
    try:
        import xcc_client
        
        # Test client creation
        client = xcc_client.XCCClient(ip="192.168.1.100", username="test", password="test")
        assert client.ip == "192.168.1.100"
        assert client.username == "test"
        assert client.password == "test"
        
        # Test parse function exists
        assert hasattr(xcc_client, 'parse_xml_entities')
        assert callable(xcc_client.parse_xml_entities)
        
    except ImportError as e:
        pytest.skip(f"Cannot import xcc_client standalone: {e}")


def test_descriptor_parser_standalone():
    """Test descriptor parser can be imported and used standalone."""
    try:
        import descriptor_parser
        
        # Test parser creation
        parser = descriptor_parser.XCCDescriptorParser()
        assert parser is not None
        
        # Test basic methods exist
        assert hasattr(parser, 'parse_descriptor_files')
        assert callable(parser.parse_descriptor_files)
        
    except ImportError as e:
        pytest.skip(f"Cannot import descriptor_parser standalone: {e}")


def test_xml_parsing_basic():
    """Test basic XML parsing functionality."""
    try:
        import xcc_client
        
        # Test with empty content
        entities = xcc_client.parse_xml_entities("", "test.xml")
        assert entities == []
        
        # Test with invalid XML
        entities = xcc_client.parse_xml_entities("not xml", "test.xml")
        assert entities == []
        
        # Test with basic XML
        basic_xml = '<?xml version="1.0"?><root><item P="TEST" V="123"/></root>'
        entities = xcc_client.parse_xml_entities(basic_xml, "test.xml")
        # Should handle basic XML without errors
        assert isinstance(entities, list)
        
    except ImportError as e:
        pytest.skip(f"Cannot test XML parsing: {e}")


def test_sample_data_exists():
    """Test that sample data files exist and are readable."""
    sample_dir = project_root / "sample_data"
    
    if not sample_dir.exists():
        pytest.skip("Sample data directory not found")
    
    # Check for key sample files
    required_files = [
        "STAVJED1.XML",
        "OKRUH10.XML", 
        "OKRUH.XML"
    ]
    
    existing_files = []
    for filename in required_files:
        file_path = sample_dir / filename
        if file_path.exists():
            existing_files.append(filename)
            assert file_path.stat().st_size > 0, f"{filename} is empty"
    
    # At least one sample file should exist
    if not existing_files:
        pytest.skip("No sample data files found")
    
    assert len(existing_files) > 0


def test_sample_data_parsing():
    """Test parsing sample data if available."""
    try:
        import xcc_client
        
        sample_dir = project_root / "sample_data"
        if not sample_dir.exists():
            pytest.skip("Sample data directory not found")
        
        sample_file = sample_dir / "STAVJED1.XML"
        if not sample_file.exists():
            pytest.skip("STAVJED1.XML sample file not found")
        
        with open(sample_file, 'r', encoding='windows-1250') as f:
            xml_content = f.read()
        
        entities = xcc_client.parse_xml_entities(xml_content, "STAVJED1.XML")
        
        # Should parse some entities
        assert len(entities) > 0
        
        # Check entity structure
        for entity in entities:
            assert "entity_id" in entity
            assert "attributes" in entity
            assert "field_name" in entity["attributes"]
            
    except ImportError as e:
        pytest.skip(f"Cannot test sample data parsing: {e}")


def test_descriptor_sample_parsing():
    """Test parsing descriptor sample data if available."""
    try:
        import descriptor_parser
        
        sample_dir = project_root / "sample_data"
        if not sample_dir.exists():
            pytest.skip("Sample data directory not found")
        
        sample_file = sample_dir / "OKRUH.XML"
        if not sample_file.exists():
            pytest.skip("OKRUH.XML sample file not found")
        
        with open(sample_file, 'r', encoding='windows-1250') as f:
            xml_content = f.read()
        
        parser = descriptor_parser.XCCDescriptorParser()
        entities = parser.parse_descriptor_files({"OKRUH.XML": xml_content})
        
        # Should parse some entities
        assert len(entities) > 0
        
        # Check entity structure
        for prop, config in entities.items():
            assert isinstance(prop, str)
            assert isinstance(config, dict)
            
    except ImportError as e:
        pytest.skip(f"Cannot test descriptor parsing: {e}")


def test_file_structure():
    """Test that required files exist."""
    xcc_dir = project_root / "custom_components" / "xcc"
    
    required_files = [
        "xcc_client.py",
        "descriptor_parser.py",
        "const.py",
        "manifest.json"
    ]
    
    for filename in required_files:
        file_path = xcc_dir / filename
        assert file_path.exists(), f"Required file {filename} not found"
        assert file_path.stat().st_size > 0, f"Required file {filename} is empty"


def test_manifest_valid():
    """Test that manifest.json is valid."""
    import json
    
    manifest_path = project_root / "custom_components" / "xcc" / "manifest.json"
    assert manifest_path.exists(), "manifest.json not found"
    
    with open(manifest_path) as f:
        manifest = json.load(f)
    
    assert manifest["domain"] == "xcc"
    assert manifest["name"] == "XCC Heat Pump Controller"
    assert "version" in manifest
    assert len(manifest["version"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
