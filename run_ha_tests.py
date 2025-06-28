#!/usr/bin/env python3
"""Run XCC integration tests using pytest-homeassistant-custom-component."""

import subprocess
import sys
from pathlib import Path


def install_requirements():
    """Install test requirements."""
    print("📦 Installing test requirements...")
    
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements-test.txt"
        ], check=True)
        print("  ✅ Requirements installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ❌ Failed to install requirements: {e}")
        return False


def run_tests():
    """Run the tests."""
    print("🧪 Running XCC integration tests...")
    
    # Run pytest with our configuration
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/test_xcc/",
        "-v",
        "--tb=short"
    ]
    
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode == 0
    except Exception as e:
        print(f"  ❌ Error running tests: {e}")
        return False


def main():
    """Main function."""
    print("🏠 Home Assistant XCC Integration Testing")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("custom_components/xcc").exists():
        print("❌ Error: custom_components/xcc directory not found")
        print("   Please run this script from the xcc-integration root directory")
        return False
    
    # Install requirements
    if not install_requirements():
        return False
    
    # Run tests
    success = run_tests()
    
    if success:
        print("\n✅ All tests passed!")
        print("\n📋 What this means:")
        print("  - Your XCC integration is properly structured")
        print("  - Configuration flow works correctly")
        print("  - Integration setup/teardown works")
        print("  - MQTT handling is robust")
        print("  - Import paths are correct (prevents 'cannot_connect' errors)")
        print("  - Connection validation works properly")
        print("  - Ready for real Home Assistant testing")
        
        print("\n🚀 Next steps:")
        print("  1. Test with real Home Assistant: scripts/develop")
        print("  2. Test with mock controller: scripts/mock")
        print("  3. Deploy to your Home Assistant instance")
    else:
        print("\n❌ Some tests failed")
        print("   Check the output above for details")
        print("   Fix issues and run tests again")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
