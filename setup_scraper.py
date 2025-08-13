#!/usr/bin/env python3
"""Setup script for XCC Page Scraper."""

import subprocess
import sys
import venv
from pathlib import Path

def setup_scraper_environment():
    """Set up virtual environment and install dependencies for the scraper."""
    print("🔧 Setting up XCC Page Scraper environment...")
    
    # Create virtual environment
    venv_path = Path("scraper_venv")
    if not venv_path.exists():
        print("📦 Creating virtual environment...")
        venv.create(venv_path, with_pip=True)
        print("✅ Virtual environment created")
    else:
        print("✅ Virtual environment already exists")
    
    # Determine the correct python executable path
    if sys.platform == "win32":
        python_exe = venv_path / "Scripts" / "python.exe"
        pip_exe = venv_path / "Scripts" / "pip.exe"
    else:
        python_exe = venv_path / "bin" / "python"
        pip_exe = venv_path / "bin" / "pip"
    
    # Install dependencies
    print("📦 Installing dependencies...")
    try:
        subprocess.run([
            str(pip_exe), "install", "-r", "requirements-scraper.txt"
        ], check=True)
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False
    
    # Create sample config
    config_file = Path("xcc_config.json")
    if not config_file.exists():
        sample_config = {
            "host": "192.168.1.100",
            "username": "xcc", 
            "password": "your_password_here",
            "output_dir": "./xcc_data"
        }
        
        with open(config_file, 'w') as f:
            json.dump(sample_config, f, indent=2)
        
        print(f"📝 Sample configuration created: {config_file}")
        print("Edit this file with your XCC controller details")
    
    print("\n🎉 Setup complete!")
    print("\n📋 Next steps:")
    print(f"1. Edit {config_file} with your XCC controller details")
    print(f"2. Run: {python_exe} xcc_scraper.py --config {config_file}")
    print(f"   Or: {python_exe} xcc_scraper.py --host IP --username USER --password PASS")
    
    return True

if __name__ == "__main__":
    import json
    success = setup_scraper_environment()
    sys.exit(0 if success else 1)
