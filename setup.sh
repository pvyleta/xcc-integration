#!/bin/bash

# Setup script for XCC Heat Pump Controller CLI

echo "🔧 Setting up XCC Heat Pump Controller CLI..."

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    echo "Please install Python 3.9 or later and try again."
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"

# Check Python version (require 3.9+)
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
required_version="3.9"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python $required_version or later is required. Found: $python_version"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📥 Installing dependencies..."
if pip install -r requirements.txt; then
    echo "✓ Dependencies installed successfully"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

# Make shell script executable
echo "🔧 Making shell script executable..."
chmod +x xcc
echo "✓ Shell script is now executable"

# Run tests to verify installation
echo "🧪 Running tests to verify installation..."
if python -m pytest test/ -v --tb=short; then
    echo "✓ All tests passed"
else
    echo "⚠️ Some tests failed - installation may have issues"
fi

# Test CLI basic functionality
echo "🔍 Testing CLI basic functionality..."
if python xcc_cli.py --help > /dev/null 2>&1; then
    echo "✓ CLI is working correctly"
else
    echo "❌ CLI test failed"
    exit 1
fi

# Note about field database
echo "📋 Field database will be auto-generated on first CLI run if needed"

echo ""
echo "🎉 Setup complete!"
echo ""
echo "📋 Quick start:"
echo "  ./xcc --help                    # Show help"
echo "  ./xcc pages                     # List available pages (requires connection)"
echo "  ./xcc --lang cz spot --list     # Use Czech language"
echo ""
echo "🔧 Next steps:"
echo "1. Connect to your heat pump network (IP: 192.168.0.50 by default)"
echo "2. Test connection: ./xcc pages"
echo "3. If needed, refresh database: ./xcc refresh-db"
echo "4. Explore: ./xcc spot --list"
echo ""
echo "💡 The field database will be generated automatically when you first run the CLI"
echo ""
echo "📚 Documentation:"
echo "  README.md     - English documentation"
echo "  README_CZ.md  - Czech documentation"
echo ""
echo "Happy heat pump controlling! 🌡️"
