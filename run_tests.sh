#!/bin/bash

echo "🧪 Running XCC Integration Tests"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install test dependencies
echo "📥 Installing test dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements-test.txt

# Run validation
echo "🔍 Validating integration structure..."
python validate_integration.py
if [ $? -ne 0 ]; then
    echo "❌ Integration validation failed"
    exit 1
fi

# Run tests
echo "🧪 Running unit tests..."
python -m pytest tests/ -v --tb=short
if [ $? -ne 0 ]; then
    echo "❌ Unit tests failed"
    exit 1
fi

# Check code style (if black is available)
if command -v black &> /dev/null; then
    echo "🎨 Checking code style..."
    black --check homeassistant/components/xcc/ custom_components/xcc/ tests/
    if [ $? -ne 0 ]; then
        echo "⚠️  Code style issues found. Run 'black .' to fix them."
    fi
fi

# Check imports (if isort is available)
if command -v isort &> /dev/null; then
    echo "📦 Checking import order..."
    isort --check-only homeassistant/components/xcc/ custom_components/xcc/ tests/
    if [ $? -ne 0 ]; then
        echo "⚠️  Import order issues found. Run 'isort .' to fix them."
    fi
fi

echo "✅ All tests passed!"
echo ""
echo "🚀 Ready for deployment!"
echo ""
echo "📋 Next steps:"
echo "  1. Commit your changes"
echo "  2. Push to GitHub"
echo "  3. Create a release tag (e.g., v1.0.0)"
echo "  4. The CI/CD pipeline will automatically build and publish"
