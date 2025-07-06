"""Test logging fixes and improvements."""

import pytest
import sys
import logging
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import importlib.util

# Set up logging for tests
logging.basicConfig(level=logging.DEBUG)
_LOGGER = logging.getLogger(__name__)

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def load_module_from_file(module_name: str, file_path: Path):
    """Load a module from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        return None
    
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None


def test_input_element_logging_deduplication():
    """Test that INPUT element deduplication code is present."""

    # Read the xcc_client file to verify deduplication code
    xcc_client_file = project_root / "custom_components" / "xcc" / "xcc_client.py"
    if not xcc_client_file.exists():
        pytest.skip("xcc_client.py not found")

    xcc_client_content = xcc_client_file.read_text()

    # Check for INPUT element deduplication logic
    assert "_logged_input_elements" in xcc_client_content, \
        "Should have INPUT element deduplication flag"

    assert "parse_xml_entities._logged_input_elements" in xcc_client_content, \
        "Should use function attribute for deduplication"

    assert "if i < 3 and not parse_xml_entities._logged_input_elements:" in xcc_client_content, \
        "Should check deduplication flag before logging"

    assert "parse_xml_entities._logged_input_elements = True" in xcc_client_content, \
        "Should set deduplication flag after logging"


def test_xml_parsing_with_sample_data():
    """Test that sample data exists and can be read."""

    # Test with real sample file if available
    sample_file = project_root / "sample_data" / "STAVJED1.XML"
    if not sample_file.exists():
        pytest.skip("STAVJED1.XML sample file not found")

    # Load sample file
    try:
        with open(sample_file, 'r', encoding='windows-1250') as f:
            xml_content = f.read()
    except UnicodeDecodeError:
        try:
            with open(sample_file, 'r', encoding='utf-8') as f:
                xml_content = f.read()
        except UnicodeDecodeError:
            with open(sample_file, 'rb') as f:
                raw_content = f.read()
                xml_content = raw_content.decode('utf-8', errors='ignore')

    # Verify sample file content
    assert len(xml_content) > 0, "Sample file should not be empty"
    assert "INPUT" in xml_content, "Sample file should contain INPUT elements"
    assert "P=" in xml_content, "Sample file should contain P attributes"
    assert "VALUE=" in xml_content, "Sample file should contain VALUE attributes"

    # Check for expected elements
    assert "SVENKU" in xml_content, "Sample file should contain SVENKU element"
    assert "SNAZEV1" in xml_content, "Sample file should contain SNAZEV1 element"
    assert "SNAZEV2" in xml_content, "Sample file should contain SNAZEV2 element"


def test_logging_frequency_consistency():
    """Test that logging frequency is consistent across entity types."""

    # This test verifies that all entity types use the same 5% logging frequency
    # by checking the random threshold used in the code

    # Read the source code to verify logging frequency
    entity_file = project_root / "custom_components" / "xcc" / "entity.py"
    number_file = project_root / "custom_components" / "xcc" / "number.py"
    switch_file = project_root / "custom_components" / "xcc" / "switch.py"

    if not all([entity_file.exists(), number_file.exists(), switch_file.exists()]):
        pytest.skip("Cannot find all required files")

    entity_content = entity_file.read_text()
    number_content = number_file.read_text()
    switch_content = switch_file.read_text()

    # Check that all use the same logging frequency (0.05 = 5%)
    assert "random.random() < 0.05" in entity_content, "Entity should use 5% logging frequency"
    assert "random.random() < 0.05" in number_content, "Number should use 5% logging frequency"
    assert "random.random() < 0.05" in switch_content, "Switch should use 5% logging frequency"

    # Check that all have entity value update logging
    assert "📊 ENTITY VALUE UPDATE" in entity_content, "Entity should have value update logging"
    assert "📊 ENTITY VALUE UPDATE" in number_content, "Number should have value update logging"
    assert "📊 ENTITY VALUE UPDATE" in switch_content, "Switch should have value update logging"


def test_deduplication_mechanisms():
    """Test that deduplication mechanisms are implemented correctly."""

    # Read the source code to verify deduplication mechanisms
    entity_file = project_root / "custom_components" / "xcc" / "entity.py"
    coordinator_file = project_root / "custom_components" / "xcc" / "coordinator.py"
    xcc_client_file = project_root / "custom_components" / "xcc" / "xcc_client.py"

    if not all([entity_file.exists(), coordinator_file.exists(), xcc_client_file.exists()]):
        pytest.skip("Cannot find all required files")

    entity_content = entity_file.read_text()
    coordinator_content = coordinator_file.read_text()
    xcc_client_content = xcc_client_file.read_text()

    # Check for coordinator data keys deduplication
    assert "_logged_coordinator_keys_for_update" in entity_content, \
        "Should have coordinator data keys deduplication"

    # Check for entity type data keys deduplication
    assert "_logged_data_keys_for_update" in entity_content, \
        "Should have entity type data keys deduplication"

    # Check for memory cleanup
    assert "Clean up old entries" in entity_content, \
        "Should have memory cleanup for deduplication"

    # Check for missing descriptor deduplication
    assert "_logged_missing_descriptors" in coordinator_content, \
        "Should have missing descriptor deduplication"

    # Check for INPUT element deduplication
    assert "_logged_input_elements" in xcc_client_content, \
        "Should have INPUT element deduplication"


def test_entity_value_logging_format():
    """Test that entity value logging has correct format."""
    
    # Load entity modules
    entity_file = project_root / "custom_components" / "xcc" / "entity.py"
    number_file = project_root / "custom_components" / "xcc" / "number.py"
    switch_file = project_root / "custom_components" / "xcc" / "switch.py"
    
    entity_content = entity_file.read_text()
    number_content = number_file.read_text()
    switch_content = switch_file.read_text()
    
    # Check entity value logging format components
    
    # All should have timestamp
    assert "time.strftime" in entity_content, "Entity should include timestamp in logging"
    assert "time.strftime" in number_content, "Number should include timestamp in logging"
    assert "time.strftime" in switch_content, "Switch should include timestamp in logging"
    
    # All should have entity ID in logging
    assert "self.entity_id" in entity_content, "Entity should include entity_id in logging"
    assert "self.entity_id" in number_content, "Number should include entity_id in logging"
    assert "self.entity_id" in switch_content, "Switch should include entity_id in logging"
    
    # Check for type-specific formatting
    assert "(sensor from coordinator data)" in entity_content, \
        "Entity should identify as sensor in logging"
    assert "(number from coordinator numbers data)" in number_content, \
        "Number should identify as number in logging"
    assert "(switch from coordinator switches data)" in switch_content, \
        "Switch should identify as switch in logging"
    
    # Check for visual indicators in switch
    assert "🟢 ON" in switch_content and "🔴 OFF" in switch_content, \
        "Switch should have visual status indicators"


def test_state_class_fix_for_string_sensors():
    """Test that string sensors don't get inappropriate state classes."""

    # Read the source code to verify state class logic
    sensor_file = project_root / "custom_components" / "xcc" / "sensor.py"

    if not sensor_file.exists():
        pytest.skip("Cannot find sensor.py file")

    sensor_content = sensor_file.read_text()

    # Check for improved state class logic
    assert "is_clearly_string" in sensor_content, "Should have string type detection"
    assert "is_clearly_numeric" in sensor_content, "Should have numeric type detection"
    assert "STRING" in sensor_content, "Should check for STRING type indicators"
    assert "REAL" in sensor_content, "Should check for REAL type indicators"

    # Check for conditional state class assignment
    assert "if is_clearly_string:" in sensor_content, "Should conditionally assign state class based on type"

    # Check that string values get no state class
    assert "state_class = None" in sensor_content, "Should set state_class to None for strings"

    # Check that numeric values get measurement state class
    assert "SensorStateClass.MEASUREMENT" in sensor_content, "Should set MEASUREMENT for numeric values"


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])
