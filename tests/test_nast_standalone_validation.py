#!/usr/bin/env python3
"""
NAST Standalone Validation Tests

This test suite validates NAST functionality without requiring
Home Assistant dependencies, making it suitable for CI/CD and
development environments.
"""

import pytest
import sys
from pathlib import Path
import re
import xml.etree.ElementTree as ET

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestNASTStandaloneValidation:
    """Standalone NAST validation tests."""
    
    @pytest.fixture
    def nast_sample_content(self):
        """Load NAST sample content."""
        sample_file = project_root / "tests" / "sample_data" / "nast.xml"
        if not sample_file.exists():
            pytest.skip("NAST sample data not available")
        
        with open(sample_file, 'r', encoding='utf-8') as f:
            return f.read()
    
    def test_nast_sample_data_structure(self, nast_sample_content):
        """Test NAST sample data has correct structure."""
        content = nast_sample_content
        
        # Basic XML validation
        assert content.startswith('<?xml version="1.0"'), "Should start with XML declaration"
        assert '<page' in content, "Should have page element"
        assert '</page>' in content, "Should have closing page element"
        
        # NAST-specific structure
        assert 'name="Nastavení TČ"' in content, "Should have Czech page name"
        assert 'name_en="HP settings"' in content, "Should have English page name"
        
        # Block structure
        blocks = re.findall(r'<block[^>]*data="([^"]*)"', content)
        assert "NAST1" in blocks, "Should have sensor corrections block"
        assert "NAST2" in blocks, "Should have power restrictions block"
        assert "NAST3" in blocks, "Should have heat pump control block"
    
    def test_nast_element_counts(self, nast_sample_content):
        """Test NAST element counts for regression detection."""
        content = nast_sample_content
        
        # Count different element types
        element_counts = {
            "number": len(re.findall(r'<number[^>]*prop="[^"]*"', content)),
            "choice": len(re.findall(r'<choice[^>]*prop="[^"]*"', content)),
            "button": len(re.findall(r'<button[^>]*prop="[^"]*"', content)),
            "text": len(re.findall(r'<text[^>]*prop="[^"]*"', content)),
            "label": len(re.findall(r'<label[^>]*prop="[^"]*"', content)),
        }
        
        # Regression baselines
        expected_minimums = {
            "number": 100,
            "choice": 30,
            "button": 8,
            "text": 3,
            "label": 5,
        }
        
        for element_type, minimum in expected_minimums.items():
            actual = element_counts[element_type]
            assert actual >= minimum, f"Regression in {element_type} elements: expected >={minimum}, got {actual}"
    
    def test_nast_specific_entities(self, nast_sample_content):
        """Test that specific NAST entities exist."""
        content = nast_sample_content
        
        # Critical entities that should always exist
        critical_patterns = [
            r'prop="B0-I"',                    # Sensor B0 correction
            r'prop="MZO-ZONA0-OFFSET"',        # Multi-zone offset 0
            r'prop="OMEZENIVYKONUGLOBALNI"',   # Global power restriction
            r'prop="TCODSTAVENI0"',            # Heat pump I control
            r'prop="FLASH-READWRITE"',         # System backup button
            r'prop="FLASH-HEADER0-NAME"',      # Configuration name
        ]
        
        for pattern in critical_patterns:
            matches = re.findall(pattern, content)
            assert len(matches) >= 1, f"Critical entity missing: {pattern}"
    
    def test_nast_attribute_patterns(self, nast_sample_content):
        """Test NAST attribute patterns."""
        content = nast_sample_content
        
        # Check for important attributes
        attribute_patterns = {
            "min attributes": r'min="[^"]*"',
            "max attributes": r'max="[^"]*"',
            "unit attributes": r'unit="[^"]*"',
            "digits attributes": r'digits="[^"]*"',
            "value attributes": r'value="[^"]*"',
            "text attributes": r'text="[^"]*"',
            "text_en attributes": r'text_en="[^"]*"',
        }
        
        # Adjust thresholds based on actual NAST content
        expected_minimums = {
            "min attributes": 20,
            "max attributes": 1,
            "unit attributes": 20,
            "digits attributes": 20,
            "value attributes": 30,
            "text attributes": 30,
            "text_en attributes": 30,
        }

        for attr_name, pattern in attribute_patterns.items():
            matches = re.findall(pattern, content)
            minimum = expected_minimums.get(attr_name, 5)
            assert len(matches) >= minimum, f"Should have {attr_name}: {len(matches)} (expected >={minimum})"
    
    def test_nast_xml_parsing(self, nast_sample_content):
        """Test that NAST XML can be parsed."""
        content = nast_sample_content
        
        # Remove XML declaration and stylesheet for parsing
        clean_content = re.sub(r'<\?xml[^>]*\?>', '', content)
        clean_content = re.sub(r'<\?xml-stylesheet[^>]*\?>', '', clean_content)
        clean_content = clean_content.strip()
        
        try:
            root = ET.fromstring(clean_content)
            assert root.tag == "page", f"Root element should be 'page', got '{root.tag}'"
            
            # Check for blocks
            blocks = root.findall(".//block")
            assert len(blocks) >= 4, f"Should have multiple blocks, got {len(blocks)}"
            
            # Check for elements with prop attributes
            prop_elements = root.findall(".//*[@prop]")
            assert len(prop_elements) >= 140, f"Should have many prop elements, got {len(prop_elements)}"
            
        except ET.ParseError as e:
            pytest.fail(f"Failed to parse NAST XML: {e}")
    
    def test_nast_client_parsing_logic(self):
        """Test that NAST parsing logic exists in XCC client."""
        xcc_client_file = project_root / "custom_components" / "xcc" / "xcc_client.py"
        
        if not xcc_client_file.exists():
            pytest.skip("XCC client not available")
        
        with open(xcc_client_file, 'r', encoding='utf-8') as f:
            client_content = f.read()
        
        # Check for NAST parsing logic
        nast_indicators = [
            "nast_elements",
            "Processing NAST-style elements",
            'elem.tag == "number"',
            'elem.tag == "choice"',
            'elem.tag == "button"',
            'elem.tag == "text"',
        ]
        
        missing_indicators = []
        for indicator in nast_indicators:
            if indicator not in client_content:
                missing_indicators.append(indicator)
        
        assert not missing_indicators, f"Missing NAST parsing logic: {missing_indicators}"
    
    def test_nast_integration_constants(self):
        """Test NAST integration with constants."""
        const_file = project_root / "custom_components" / "xcc" / "const.py"
        
        if not const_file.exists():
            pytest.skip("Constants file not available")
        
        with open(const_file, 'r', encoding='utf-8') as f:
            const_content = f.read()
        
        # NAST should not be in static constants (dynamic discovery)
        assert '"nast.xml"' not in const_content, "NAST should not be in static descriptor constants"
        assert '"NAST.XML"' not in const_content, "NAST should not be in static data constants"
        
        # Should mention dynamic discovery
        assert "dynamically" in const_content.lower(), "Should mention dynamic discovery"
    
    def test_nast_button_platform_exists(self):
        """Test that button platform exists for NAST."""
        button_file = project_root / "custom_components" / "xcc" / "button.py"
        
        if not button_file.exists():
            pytest.skip("Button platform not available")
        
        with open(button_file, 'r', encoding='utf-8') as f:
            button_content = f.read()
        
        # Should have button platform logic
        assert "class XCCButton" in button_content, "Should have XCCButton class"
        assert "async def async_press" in button_content, "Should have press method"
    
    def test_nast_sample_files_consistency(self):
        """Test that NAST sample files are consistent."""
        sample_dir = project_root / "tests" / "sample_data"
        
        nast_descriptor = sample_dir / "nast.xml"
        nast_data = sample_dir / "NAST.XML"
        
        if not (nast_descriptor.exists() and nast_data.exists()):
            pytest.skip("NAST sample files not available")
        
        # Read both files
        with open(nast_descriptor, 'r', encoding='utf-8') as f:
            descriptor_content = f.read()
        with open(nast_data, 'r', encoding='utf-8') as f:
            data_content = f.read()
        
        # Should be identical (descriptor-only page)
        assert descriptor_content == data_content, "NAST descriptor and data should be identical"
        
        # Should have substantial content
        assert len(descriptor_content) > 15000, f"NAST content should be substantial: {len(descriptor_content)} chars"
    
    def test_nast_entity_patterns(self, nast_sample_content):
        """Test NAST entity patterns for specific functionality."""
        content = nast_sample_content
        
        # Test sensor correction patterns
        sensor_corrections = re.findall(r'prop="([^"]*-I)"', content)
        assert len(sensor_corrections) >= 12, f"Should have sensor corrections: {len(sensor_corrections)}"
        
        # Test multi-zone offset patterns
        mzo_offsets = re.findall(r'prop="(MZO-ZONA\d+-OFFSET)"', content)
        assert len(mzo_offsets) >= 16, f"Should have multi-zone offsets: {len(mzo_offsets)}"
        
        # Test heat pump control patterns
        hp_controls = re.findall(r'prop="(TCODSTAVENI\d+)"', content)
        assert len(hp_controls) >= 10, f"Should have heat pump controls: {len(hp_controls)}"
        
        # Test power restriction patterns
        power_restrictions = re.findall(r'prop="([^"]*OMEZEN[^"]*)"', content)
        assert len(power_restrictions) >= 5, f"Should have power restrictions: {len(power_restrictions)}"
        
        # Test system backup patterns
        backup_entities = re.findall(r'prop="(FLASH-[^"]*)"', content)
        assert len(backup_entities) >= 10, f"Should have backup entities: {len(backup_entities)}"
    
    def test_nast_choice_options(self, nast_sample_content):
        """Test NAST choice element options."""
        content = nast_sample_content
        
        # Find choice elements with options
        choice_blocks = re.findall(r'<choice[^>]*prop="[^"]*"[^>]*>(.*?)</choice>', content, re.DOTALL)
        
        assert len(choice_blocks) >= 30, f"Should have choice elements: {len(choice_blocks)}"
        
        # Check that choices have options
        total_options = 0
        for choice_block in choice_blocks:
            options = re.findall(r'<option[^>]*text="[^"]*"', choice_block)
            total_options += len(options)
        
        assert total_options >= 60, f"Should have many options: {total_options}"
    
    def test_nast_visibility_conditions(self, nast_sample_content):
        """Test NAST visibility conditions."""
        content = nast_sample_content
        
        # Find elements with visibility conditions
        visible_elements = re.findall(r'cl="visib"[^>]*visData="[^"]*"', content)
        
        assert len(visible_elements) >= 50, f"Should have visibility conditions: {len(visible_elements)}"
        
        # Check visibility data patterns
        vis_data_patterns = re.findall(r'visData="([^"]*)"', content)
        
        # Should have various visibility patterns
        unique_patterns = set(vis_data_patterns)
        assert len(unique_patterns) >= 10, f"Should have diverse visibility patterns: {len(unique_patterns)}"


class TestNASTFileStructure:
    """Test NAST file structure and organization."""
    
    def test_nast_test_files_exist(self):
        """Test that NAST test files exist."""
        tests_dir = project_root / "tests"
        
        expected_files = [
            "test_nast_sample_data.py",
            "test_nast_regression_prevention.py",
            "test_nast_integration_comprehensive.py",
            "test_nast_pytest_suite.py",
            "test_nast_standalone_validation.py",
        ]
        
        missing_files = []
        for file_name in expected_files:
            if not (tests_dir / file_name).exists():
                missing_files.append(file_name)
        
        assert not missing_files, f"Missing NAST test files: {missing_files}"
    
    def test_nast_sample_data_exists(self):
        """Test that NAST sample data exists."""
        sample_dir = project_root / "tests" / "sample_data"
        
        required_files = ["nast.xml", "NAST.XML"]
        
        missing_files = []
        for file_name in required_files:
            if not (sample_dir / file_name).exists():
                missing_files.append(file_name)
        
        assert not missing_files, f"Missing NAST sample data files: {missing_files}"
    
    def test_nast_integration_files_exist(self):
        """Test that NAST integration files exist."""
        xcc_dir = project_root / "custom_components" / "xcc"
        
        required_files = [
            "xcc_client.py",  # Should have NAST parsing logic
            "button.py",      # Should exist for NAST buttons
            "const.py",       # Should have dynamic discovery logic
        ]
        
        missing_files = []
        for file_name in required_files:
            if not (xcc_dir / file_name).exists():
                missing_files.append(file_name)
        
        assert not missing_files, f"Missing NAST integration files: {missing_files}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
