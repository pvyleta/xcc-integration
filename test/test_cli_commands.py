#!/usr/bin/env python3
"""
Tests for CLI command functionality
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, AsyncMock
from click.testing import CliRunner

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from xcc_cli import cli, XCCController


class TestCLICommands:
    """Test CLI command functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.runner = CliRunner()
        
    def test_cli_help(self):
        """Test CLI help command"""
        result = self.runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'XCC Heat Pump Controller CLI Tool' in result.output
        
    def test_cli_version_info(self):
        """Test CLI shows version and basic info"""
        result = self.runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'Options:' in result.output
        assert 'Commands:' in result.output
        
    @patch('xcc_cli.XCCController')
    def test_pages_command(self, mock_controller_class):
        """Test pages command"""
        # Mock controller instance
        mock_controller = Mock()
        mock_controller.load_field_database.return_value = None
        mock_controller.get_available_pages.return_value = ['test.xml']
        mock_controller.pages_info = {'test.xml': {'name': 'Test Page'}}
        mock_controller.get_page_fields.return_value = {'FIELD1': {}}
        mock_controller_class.return_value = mock_controller
        
        result = self.runner.invoke(cli, ['pages'])
        assert result.exit_code == 0
        assert 'Available Configuration Pages' in result.output
        
    @patch('xcc_cli.XCCController')
    def test_search_command(self, mock_controller_class):
        """Test search command"""
        # Mock controller instance
        mock_controller = Mock()
        mock_controller.load_field_database.return_value = None
        mock_controller.search_fields.return_value = {
            'TEST-FIELD': {'friendly_name': 'Test Field'}
        }
        mock_controller.display_field_info = Mock()
        mock_controller.__aenter__ = AsyncMock(return_value=mock_controller)
        mock_controller.__aexit__ = AsyncMock(return_value=None)
        mock_controller.get_current_values = AsyncMock()
        mock_controller_class.return_value = mock_controller
        
        result = self.runner.invoke(cli, ['search', 'test'])
        assert result.exit_code == 0
        
    def test_global_options(self):
        """Test global options parsing"""
        # Test that global options are recognized
        result = self.runner.invoke(cli, ['--ip', '192.168.1.100', '--help'])
        assert result.exit_code == 0
        
        result = self.runner.invoke(cli, ['--lang', 'cz', '--help'])
        assert result.exit_code == 0
        
        result = self.runner.invoke(cli, ['--verbose', '--help'])
        assert result.exit_code == 0
        
    def test_invalid_language(self):
        """Test invalid language option"""
        result = self.runner.invoke(cli, ['--lang', 'invalid', 'pages'])
        assert result.exit_code != 0
        
    def test_missing_command(self):
        """Test behavior when no command is provided"""
        result = self.runner.invoke(cli, [])
        # Should show help when no command provided
        assert 'Usage:' in result.output


class TestPageCommands:
    """Test page-specific commands"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.runner = CliRunner()
        
    def test_page_commands_structure(self):
        """Test that page commands can be created"""
        # Test that the CLI has the expected structure
        from xcc_cli import create_page_command

        # Test that the function exists
        assert callable(create_page_command)

        # Test creating a mock page command
        page_info = {"name": "Test Page"}
        try:
            create_page_command("test.xml", page_info)
        except Exception as e:
            # Should not fail due to structure issues
            assert "import" not in str(e).lower()

    def test_init_page_commands_function(self):
        """Test that init_page_commands function exists"""
        from xcc_cli import init_page_commands
        assert callable(init_page_commands)


class TestErrorHandling:
    """Test error handling in CLI"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.runner = CliRunner()
        
    def test_invalid_command(self):
        """Test invalid command handling"""
        result = self.runner.invoke(cli, ['invalid-command'])
        assert result.exit_code != 0
        
    def test_invalid_option(self):
        """Test invalid option handling"""
        result = self.runner.invoke(cli, ['--invalid-option'])
        assert result.exit_code != 0


if __name__ == "__main__":
    pytest.main([__file__])
