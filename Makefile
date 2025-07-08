# Makefile for XCC Integration Development

.PHONY: help install lint format check test clean setup-dev

# Default target
help:
	@echo "XCC Integration Development Commands:"
	@echo ""
	@echo "Setup:"
	@echo "  setup-dev     Install development dependencies"
	@echo "  install       Install the package in development mode"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint          Run Ruff linter"
	@echo "  format        Run Ruff formatter"
	@echo "  check         Run all checks (lint + format + syntax)"
	@echo "  fix           Auto-fix all issues"
	@echo ""
	@echo "Testing:"
	@echo "  test          Run all tests"
	@echo "  test-cov      Run tests with coverage"
	@echo "  syntax        Check Python syntax"
	@echo ""
	@echo "Maintenance:"
	@echo "  clean         Clean up cache files"
	@echo "  pre-commit    Install pre-commit hooks"

# Setup development environment
setup-dev:
	python -m pip install --upgrade pip
	pip install -r requirements-dev.txt
	pip install -e .

install:
	pip install -e .

# Code quality
lint:
	@echo "🔍 Running Ruff linter..."
	ruff check .

format:
	@echo "🎨 Running Ruff formatter..."
	ruff format .

check: lint format syntax
	@echo "✅ All checks completed"

fix:
	@echo "🔧 Auto-fixing issues..."
	ruff check --fix .
	ruff format .

# Testing
test:
	@echo "🧪 Running tests..."
	pytest tests/ -v

test-cov:
	@echo "🧪 Running tests with coverage..."
	pytest tests/ -v --cov=custom_components/xcc --cov-report=html --cov-report=term

syntax:
	@echo "🔍 Checking Python syntax..."
	python -m py_compile custom_components/xcc/*.py
	python -m py_compile tests/*.py
	@echo "✅ Syntax check passed"

# Maintenance
clean:
	@echo "🧹 Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf build/ dist/ htmlcov/ .coverage coverage.xml

pre-commit:
	@echo "🪝 Installing pre-commit hooks..."
	pre-commit install
	@echo "✅ Pre-commit hooks installed"

# Development workflow
dev-check: clean syntax lint format test
	@echo "🎉 Development check completed successfully!"

# CI simulation
ci: clean syntax lint test
	@echo "🚀 CI simulation completed successfully!"
