#!/usr/bin/env python3
"""
Comprehensive test runner for XCC integration using real sample data.

This script runs all tests that validate the complete flow from sample data
parsing to entity creation, ensuring no regressions occur.
"""
import subprocess
import sys
from pathlib import Path


def run_tests():
    """Run comprehensive tests with proper environment setup."""
    
    # Get the project root directory
    project_root = Path(__file__).parent.parent
    
    print("🧪 XCC Integration Comprehensive Test Suite")
    print("=" * 60)
    print("Testing complete flow from sample data to entity creation")
    print("=" * 60)
    
    # Test files to run in order
    test_files = [
        "tests/test_xcc/test_end_to_end_with_sample_data.py",
        "tests/test_xcc/test_platform_setup_with_sample_data.py", 
        "tests/test_xcc/test_regression_prevention.py",
        "tests/test_xcc/test_coordinator_entity_types.py",
    ]
    
    # Check if virtual environment exists
    venv_path = project_root / "venv"
    if venv_path.exists():
        python_cmd = str(venv_path / "bin" / "python")
        print(f"✅ Using virtual environment: {venv_path}")
    else:
        python_cmd = "python3"
        print("⚠️  No virtual environment found, using system python3")
    
    # Check if sample data exists
    sample_data_path = project_root / "sample_data"
    if not sample_data_path.exists():
        print("❌ ERROR: sample_data directory not found!")
        print("   The comprehensive tests require real sample data files.")
        return False
    
    required_files = [
        "STAVJED.XML", "OKRUH.XML", "TUV1.XML", "BIV.XML", "FVE.XML", "SPOT.XML",
        "STAVJED1.XML", "OKRUH10.XML", "TUV11.XML", "BIV1.XML", "FVE4.XML", "SPOT1.XML"
    ]
    
    missing_files = []
    for filename in required_files:
        if not (sample_data_path / filename).exists():
            missing_files.append(filename)
    
    if missing_files:
        print(f"❌ ERROR: Missing required sample data files: {missing_files}")
        return False
    
    print(f"✅ Found all required sample data files in {sample_data_path}")
    print()
    
    # Run each test file
    all_passed = True
    
    for test_file in test_files:
        test_path = project_root / test_file
        if not test_path.exists():
            print(f"⚠️  Skipping {test_file} (file not found)")
            continue
        
        print(f"🔍 Running {test_file}...")
        print("-" * 40)
        
        try:
            # Run pytest with verbose output
            cmd = [
                python_cmd, "-m", "pytest", 
                str(test_path),
                "-v",
                "--tb=short",
                "--no-header"
            ]
            
            result = subprocess.run(
                cmd,
                cwd=str(project_root),
                capture_output=True,
                text=True,
                timeout=120  # 2 minute timeout per test file
            )
            
            if result.returncode == 0:
                print(f"✅ {test_file} - PASSED")
                # Print summary of passed tests
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'PASSED' in line and '::' in line:
                        test_name = line.split('::')[-1].split()[0]
                        print(f"   ✓ {test_name}")
            else:
                print(f"❌ {test_file} - FAILED")
                all_passed = False
                
                # Print error details
                if result.stdout:
                    print("STDOUT:")
                    print(result.stdout)
                if result.stderr:
                    print("STDERR:")
                    print(result.stderr)
        
        except subprocess.TimeoutExpired:
            print(f"⏰ {test_file} - TIMEOUT (>2 minutes)")
            all_passed = False
        
        except Exception as e:
            print(f"💥 {test_file} - ERROR: {e}")
            all_passed = False
        
        print()
    
    # Final summary
    print("=" * 60)
    if all_passed:
        print("🎉 ALL COMPREHENSIVE TESTS PASSED!")
        print("✅ Complete flow from sample data to entity creation works correctly")
        print("✅ No regressions detected")
        print("✅ All platforms would create entities properly")
    else:
        print("❌ SOME TESTS FAILED!")
        print("🚨 There are issues in the complete flow that need to be fixed")
    print("=" * 60)
    
    return all_passed


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
