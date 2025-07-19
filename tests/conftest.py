"""Test configuration for XCC integration tests."""

import pytest
import sys
import os

# Add the custom_components directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

@pytest.fixture
def sample_data_dir():
    """Return the path to the sample data directory."""
    return os.path.join(os.path.dirname(__file__), '..', 'sample_data')
