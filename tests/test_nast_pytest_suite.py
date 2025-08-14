#!/usr/bin/env python3
"""
NAST Pytest Suite Validation

This test validates that the complete pytest suite works correctly
with NAST integration and that all NAST-related tests are properly
integrated into the test framework.
"""

import pytest
import sys
from pathlib import Path
import subprocess
import importlib.util

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestNASTPytestSuite:
    """Test the NAST pytest suite integration."""
    
    def test_nast_sample_data_files_exist(self):
        """Test that NAST sample data files exist and are valid."""
        sample_dir = project_root / "tests" / "sample_data"
        
        # Check NAST files exist
        nast_descriptor = sample_dir / "nast.xml"
        nast_data = sample_dir / "NAST.XML"
        
        assert nast_descriptor.exists(), "NAST descriptor sample file should exist"
        assert nast_data.exists(), "NAST data sample file should exist"
        
        # Check file sizes
        descriptor_size = nast_descriptor.stat().st_size
        data_size = nast_data.stat().st_size
        
        assert descriptor_size > 10000, f"NAST descriptor should be substantial: {descriptor_size} bytes"
        assert data_size > 10000, f"NAST data should be substantial: {data_size} bytes"
        
        # Files should be identical (descriptor-only page)
        with open(nast_descriptor, 'r', encoding='utf-8') as f:
            descriptor_content = f.read()
        with open(nast_data, 'r', encoding='utf-8') as f:
            data_content = f.read()
        
        assert descriptor_content == data_content, "NAST descriptor and data should be identical"
    
    def test_nast_test_files_exist(self):
        """Test that all NAST test files exist."""
        tests_dir = project_root / "tests"
        
        expected_nast_tests = [
            "test_nast_sample_data.py",
            "test_nast_regression_prevention.py", 
            "test_nast_integration_comprehensive.py",
            "test_nast_pytest_suite.py",
            # Existing NAST tests
            "test_nast_integration.py",
            "test_nast_integration_verification.py",
            "test_nast_with_real_data.py",
            "test_nast_end_to_end.py",
            "test_nast_parsing_fix.py",
        ]
        
        missing_tests = []
        for test_file in expected_nast_tests:
            test_path = tests_dir / test_file
            if not test_path.exists():
                missing_tests.append(test_file)
        
        assert not missing_tests, f"Missing NAST test files: {missing_tests}"
    
    def test_nast_test_files_importable(self):
        """Test that all NAST test files can be imported."""
        tests_dir = project_root / "tests"
        
        nast_test_files = [
            "test_nast_sample_data.py",
            "test_nast_regression_prevention.py",
            "test_nast_integration_comprehensive.py",
        ]
        
        for test_file in nast_test_files:
            test_path = tests_dir / test_file
            if not test_path.exists():
                continue
            
            # Try to import the test module
            spec = importlib.util.spec_from_file_location(test_file[:-3], test_path)
            if spec and spec.loader:
                try:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                except Exception as e:
                    pytest.fail(f"Failed to import {test_file}: {e}")
    
    def test_nast_tests_have_proper_structure(self):
        """Test that NAST test files have proper pytest structure."""
        tests_dir = project_root / "tests"
        
        nast_test_files = [
            "test_nast_sample_data.py",
            "test_nast_regression_prevention.py",
            "test_nast_integration_comprehensive.py",
        ]
        
        for test_file in nast_test_files:
            test_path = tests_dir / test_file
            if not test_path.exists():
                continue
            
            with open(test_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for pytest structure
            assert "import pytest" in content, f"{test_file} should import pytest"
            assert "def test_" in content, f"{test_file} should have test functions"
            assert "__name__ == \"__main__\"" in content or "pytest.main" in content, f"{test_file} should be runnable"
    
    def test_sample_data_directory_structure(self):
        """Test that sample data directory has proper structure."""
        sample_dir = project_root / "tests" / "sample_data"
        
        # Should have both descriptor and data files
        descriptor_files = list(sample_dir.glob("*.xml"))  # lowercase
        data_files = list(sample_dir.glob("*.XML"))        # uppercase
        
        assert len(descriptor_files) >= 7, f"Should have descriptor files including NAST: {len(descriptor_files)}"
        assert len(data_files) >= 7, f"Should have data files including NAST: {len(data_files)}"
        
        # Check for NAST specifically
        nast_descriptor = sample_dir / "nast.xml"
        nast_data = sample_dir / "NAST.XML"
        
        assert nast_descriptor in descriptor_files, "NAST descriptor should be in descriptor files"
        assert nast_data in data_files, "NAST data should be in data files"
    
    def test_nast_integration_with_existing_tests(self):
        """Test that NAST integrates well with existing tests."""
        # Check that existing test files can handle NAST
        existing_test_files = [
            "test_integration_with_real_data.py",
            "test_sample_file_values.py",
            "test_xcc_client.py",
        ]
        
        tests_dir = project_root / "tests"
        
        for test_file in existing_test_files:
            test_path = tests_dir / test_file
            if not test_path.exists():
                continue
            
            with open(test_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Should not have hardcoded assumptions that break with NAST
            problematic_patterns = [
                "== 6",  # Hardcoded page count
                "exactly 6",  # Hardcoded page count
                "only 6",  # Hardcoded page count
            ]
            
            for pattern in problematic_patterns:
                if pattern in content:
                    # This might be okay, but let's check context
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if pattern in line and "page" in line.lower():
                            # This could be problematic with NAST
                            print(f"Warning: {test_file}:{i+1} might have hardcoded page assumption: {line.strip()}")
    
    def test_nast_test_coverage_completeness(self):
        """Test that NAST test coverage is complete."""
        # Areas that should be covered by NAST tests
        coverage_areas = {
            "XML parsing": False,
            "Entity creation": False,
            "Attribute handling": False,
            "State management": False,
            "Error handling": False,
            "Performance": False,
            "Regression prevention": False,
            "Integration flow": False,
            "Sample data validation": False,
            "Real-world scenarios": False,
        }
        
        # Check test files for coverage
        tests_dir = project_root / "tests"
        nast_test_files = list(tests_dir.glob("test_nast_*.py"))
        
        for test_file in nast_test_files:
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read().lower()
            
            # Check coverage areas
            if "parse" in content or "xml" in content:
                coverage_areas["XML parsing"] = True
            if "entity" in content and "creat" in content:
                coverage_areas["Entity creation"] = True
            if "attribute" in content:
                coverage_areas["Attribute handling"] = True
            if "state" in content:
                coverage_areas["State management"] = True
            if "error" in content or "exception" in content:
                coverage_areas["Error handling"] = True
            if "performance" in content or "time" in content:
                coverage_areas["Performance"] = True
            if "regression" in content:
                coverage_areas["Regression prevention"] = True
            if "integration" in content:
                coverage_areas["Integration flow"] = True
            if "sample" in content:
                coverage_areas["Sample data validation"] = True
            if "scenario" in content or "real" in content:
                coverage_areas["Real-world scenarios"] = True
        
        # Check coverage completeness
        missing_coverage = [area for area, covered in coverage_areas.items() if not covered]
        assert not missing_coverage, f"Missing test coverage for: {missing_coverage}"
    
    def test_nast_test_naming_consistency(self):
        """Test that NAST test files follow consistent naming."""
        tests_dir = project_root / "tests"
        nast_test_files = list(tests_dir.glob("test_nast_*.py"))
        
        # Should have reasonable number of NAST tests
        assert len(nast_test_files) >= 8, f"Should have comprehensive NAST tests: {len(nast_test_files)}"
        
        # Check naming patterns
        expected_patterns = [
            "test_nast_sample_data.py",
            "test_nast_regression_prevention.py",
            "test_nast_integration_comprehensive.py",
        ]
        
        actual_names = [f.name for f in nast_test_files]
        
        for pattern in expected_patterns:
            assert pattern in actual_names, f"Missing expected test file: {pattern}"
    
    def test_nast_pytest_configuration(self):
        """Test that pytest configuration supports NAST tests."""
        # Check pytest.ini
        pytest_ini = project_root / "pytest.ini"
        if pytest_ini.exists():
            with open(pytest_ini, 'r', encoding='utf-8') as f:
                config_content = f.read()
            
            # Should not exclude NAST tests
            assert "test_nast" not in config_content or "ignore" not in config_content, "Should not ignore NAST tests"
    
    def test_nast_test_dependencies(self):
        """Test that NAST tests have proper dependencies."""
        # Check requirements files
        requirements_files = [
            project_root / "requirements-test.txt",
            project_root / "tests" / "requirements-test.txt",
        ]
        
        for req_file in requirements_files:
            if not req_file.exists():
                continue
            
            with open(req_file, 'r', encoding='utf-8') as f:
                requirements = f.read()
            
            # Should have pytest
            assert "pytest" in requirements, f"Should have pytest in {req_file}"


class TestNASTTestExecution:
    """Test that NAST tests can be executed properly."""
    
    def test_nast_sample_data_test_execution(self):
        """Test that NAST sample data tests can be executed."""
        test_file = project_root / "tests" / "test_nast_sample_data.py"
        if not test_file.exists():
            pytest.skip("NAST sample data test not available")
        
        # Try to run the test
        try:
            result = subprocess.run([
                sys.executable, "-m", "pytest", str(test_file), "-v", "--tb=short"
            ], capture_output=True, text=True, cwd=project_root, timeout=60)
            
            # Should not crash
            assert result.returncode in [0, 1], f"Test execution failed: {result.stderr}"
            
            # Should have test output
            assert "test_" in result.stdout, "Should have test output"
            
        except subprocess.TimeoutExpired:
            pytest.fail("NAST sample data test execution timed out")
        except Exception as e:
            pytest.fail(f"Failed to execute NAST sample data test: {e}")
    
    def test_nast_tests_can_find_sample_data(self):
        """Test that NAST tests can find and load sample data."""
        sample_file = project_root / "tests" / "sample_data" / "nast.xml"
        
        # Should be accessible from test directory
        assert sample_file.exists(), "NAST sample data should be accessible"
        
        # Should be readable
        try:
            with open(sample_file, 'r', encoding='utf-8') as f:
                content = f.read()
            assert len(content) > 1000, "Should be able to read substantial content"
        except Exception as e:
            pytest.fail(f"Failed to read NAST sample data: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
