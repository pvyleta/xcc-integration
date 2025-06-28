#!/usr/bin/env python3
"""
Basic functionality tests that don't require network connection
"""

import pytest
import sys
import os

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestBasicImports:
    """Test that all modules can be imported"""
    
    def test_import_xcc_cli(self):
        """Test that xcc_cli can be imported"""
        try:
            import xcc_cli
            assert hasattr(xcc_cli, 'XCCController')
            assert hasattr(xcc_cli, 'cli')
        except ImportError as e:
            pytest.fail(f"Failed to import xcc_cli: {e}")
            
    def test_import_analyze_known_pages(self):
        """Test that analyze_known_pages can be imported"""
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'scripts'))
            import analyze_known_pages
            assert hasattr(analyze_known_pages, 'main')
        except ImportError as e:
            pytest.fail(f"Failed to import analyze_known_pages: {e}")
            
    def test_import_xcc_client(self):
        """Test that xcc_client can be imported"""
        try:
            import xcc_client
            assert hasattr(xcc_client, 'XCCClient')
            assert hasattr(xcc_client, 'parse_xml_entities')
        except ImportError as e:
            pytest.fail(f"Failed to import xcc_client: {e}")


class TestXCCControllerBasic:
    """Basic tests for XCCController that don't require network"""
    
    def test_controller_creation(self):
        """Test that controller can be created"""
        from xcc_cli import XCCController
        
        controller = XCCController()
        assert controller.ip == "192.168.0.50"
        assert controller.username == "xcc"
        assert controller.password == "xcc"
        
    def test_controller_with_params(self):
        """Test controller with custom parameters"""
        from xcc_cli import XCCController
        
        controller = XCCController(
            ip="192.168.1.100",
            username="admin",
            password="secret",
            verbose=True,
            language="cz"
        )
        
        assert controller.ip == "192.168.1.100"
        assert controller.username == "admin"
        assert controller.password == "secret"
        assert controller.verbose == True
        assert controller.language == "cz"
        
    def test_language_support(self):
        """Test language support functionality"""
        from xcc_cli import XCCController
        
        controller_en = XCCController(language="en")
        controller_cz = XCCController(language="cz")
        
        field_info = {
            "friendly_name": "Czech Name",
            "friendly_name_en": "English Name"
        }
        
        desc_en = controller_en.get_field_description(field_info)
        desc_cz = controller_cz.get_field_description(field_info)
        
        assert desc_en == "English Name"
        assert desc_cz == "Czech Name"


class TestCLIBasic:
    """Basic CLI tests"""
    
    def test_cli_structure(self):
        """Test CLI has expected structure"""
        from xcc_cli import cli
        
        # Should be a Click group
        assert hasattr(cli, 'commands')
        
    def test_cli_help_works(self):
        """Test that CLI help can be generated"""
        from click.testing import CliRunner
        from xcc_cli import cli
        
        runner = CliRunner()
        result = runner.invoke(cli, ['--help'])
        
        # Should not crash
        assert 'XCC Heat Pump Controller CLI Tool' in result.output


class TestFileStructure:
    """Test that required files exist"""
    
    def test_required_files_exist(self):
        """Test that all required files exist"""
        required_files = [
            'xcc_cli.py',
            'xcc_client.py',
            'scripts/analyze_known_pages.py',
            'requirements.txt',
            'README.md',
            'README_CZ.md',
            'xcc'
        ]
        
        for filename in required_files:
            assert os.path.exists(filename), f"Required file {filename} not found"
            
    def test_shell_script_executable(self):
        """Test that shell script is executable"""
        import stat
        
        file_stat = os.stat('xcc')
        assert file_stat.st_mode & stat.S_IEXEC, "Shell script 'xcc' is not executable"


if __name__ == "__main__":
    pytest.main([__file__])
