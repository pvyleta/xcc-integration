#!/usr/bin/env python3
"""
Comprehensive test runner for XCC Integration.
Run this before every release to catch silly mistakes!
"""

import sys
import os
import subprocess
from pathlib import Path


def run_command(command, description):
    """Run a command and return success status."""
    print(f"\n🔧 {description}")
    print("-" * 60)
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )
        
        if result.stdout:
            print(result.stdout)
        
        if result.stderr:
            print("STDERR:", result.stderr)
        
        if result.returncode == 0:
            print(f"✅ {description} - PASSED")
            return True
        else:
            print(f"❌ {description} - FAILED (exit code: {result.returncode})")
            return False
            
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False


def test_python_compilation():
    """Test that all Python files compile without errors."""
    print(f"\n🔧 Testing Python Compilation")
    print("-" * 60)
    
    xcc_dir = Path(__file__).parent / "custom_components" / "xcc"
    python_files = list(xcc_dir.glob("*.py"))
    
    failed_files = []
    
    for py_file in python_files:
        try:
            result = subprocess.run(
                [sys.executable, "-m", "py_compile", str(py_file)],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print(f"✓ {py_file.name}")
            else:
                print(f"❌ {py_file.name}: {result.stderr}")
                failed_files.append(py_file.name)
                
        except Exception as e:
            print(f"❌ {py_file.name}: {e}")
            failed_files.append(py_file.name)
    
    if failed_files:
        print(f"\n❌ Python Compilation - FAILED ({len(failed_files)} files)")
        return False
    else:
        print(f"\n✅ Python Compilation - PASSED (all {len(python_files)} files)")
        return True


def check_required_files():
    """Check that all required files exist."""
    print(f"\n🔧 Checking Required Files")
    print("-" * 60)
    
    required_files = [
        "custom_components/xcc/__init__.py",
        "custom_components/xcc/manifest.json",
        "custom_components/xcc/const.py",
        "custom_components/xcc/coordinator.py",
        "custom_components/xcc/xcc_client.py",
        "custom_components/xcc/descriptor_parser.py",
        "custom_components/xcc/sensor.py",
        "custom_components/xcc/switch.py",
        "custom_components/xcc/number.py",
        "custom_components/xcc/select.py",
        "custom_components/xcc/config_flow.py",
    ]
    
    missing_files = []
    
    for file_path in required_files:
        full_path = Path(__file__).parent / file_path
        if full_path.exists():
            print(f"✓ {file_path}")
        else:
            print(f"❌ {file_path} - MISSING")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n❌ Required Files Check - FAILED ({len(missing_files)} missing)")
        return False
    else:
        print(f"\n✅ Required Files Check - PASSED (all {len(required_files)} files)")
        return True


def check_version_consistency():
    """Check that version is consistent across files."""
    print(f"\n🔧 Checking Version Consistency")
    print("-" * 60)
    
    # Read version from const.py
    const_file = Path(__file__).parent / "custom_components" / "xcc" / "const.py"
    
    try:
        with open(const_file, 'r') as f:
            content = f.read()
        
        # Extract version
        import re
        version_match = re.search(r'VERSION.*?=.*?"([^"]+)"', content)
        if not version_match:
            print("❌ Could not find VERSION in const.py")
            return False
        
        version = version_match.group(1)
        print(f"Found version: {version}")
        
        # Check manifest.json
        manifest_file = Path(__file__).parent / "custom_components" / "xcc" / "manifest.json"
        with open(manifest_file, 'r') as f:
            import json
            manifest = json.load(f)
        
        manifest_version = manifest.get("version", "")
        
        if version == manifest_version:
            print(f"✓ Version consistency: {version}")
            return True
        else:
            print(f"❌ Version mismatch: const.py={version}, manifest.json={manifest_version}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking version: {e}")
        return False


def main():
    """Run all tests."""
    print("🧪 XCC Integration Pre-Release Test Suite")
    print("=" * 80)
    print("This test suite catches common mistakes before release!")
    print("=" * 80)
    
    all_passed = True
    
    # Test 1: Check required files
    if not check_required_files():
        all_passed = False
    
    # Test 2: Python compilation
    if not test_python_compilation():
        all_passed = False
    
    # Test 3: Syntax tests
    if not run_command("python3 tests/test_syntax.py", "Syntax Validation"):
        all_passed = False
    
    # Test 4: Import tests
    if not run_command("python3 tests/test_imports.py", "Import Validation"):
        all_passed = False
    
    # Test 5: Version consistency
    if not check_version_consistency():
        all_passed = False
    
    # Test 6: Descriptor analysis (to ensure sample data works)
    if not run_command("python3 analyze_changeable_entities.py", "Descriptor Analysis"):
        all_passed = False
    
    # Final result
    print("\n" + "=" * 80)
    if all_passed:
        print("🎉 ALL TESTS PASSED! Integration is ready for release! 🚀")
        print("=" * 80)
        print("You can now safely:")
        print("  1. git commit -m 'your message'")
        print("  2. git push origin main")
        print("  3. git tag vX.X.X && git push origin vX.X.X")
        print("  4. gh release create vX.X.X")
        print("=" * 80)
        sys.exit(0)
    else:
        print("❌ TESTS FAILED! Fix issues before release!")
        print("=" * 80)
        print("Do NOT release until all tests pass!")
        print("=" * 80)
        sys.exit(1)


if __name__ == "__main__":
    main()
