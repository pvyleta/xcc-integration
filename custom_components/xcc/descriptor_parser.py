"""XCC Descriptor Parser for determining entity types and capabilities."""
import logging
import re
from typing import Dict, Any, Optional, List, Tuple
from xml.etree import ElementTree as ET

_LOGGER = logging.getLogger(__name__)


class XCCDescriptorParser:
    """Parser for XCC descriptor files to determine entity types and capabilities."""

    def __init__(self):
        """Initialize the descriptor parser."""
        self.entity_configs = {}

    def parse_descriptor_files(self, descriptor_data: Dict[str, str]) -> Dict[str, Dict[str, Any]]:
        """
        Parse descriptor XML files to determine entity types and configurations.

        Args:
            descriptor_data: Dict mapping page names to XML content

        Returns:
            Dict mapping entity prop names to their configuration
        """
        entity_configs = {}

        for page_name, xml_content in descriptor_data.items():
            _LOGGER.debug("Parsing descriptor file %s", page_name)
            try:
                page_configs = self._parse_single_descriptor(xml_content, page_name)
                entity_configs.update(page_configs)
                _LOGGER.debug("Found %d entity configurations in %s", len(page_configs), page_name)
            except Exception as err:
                _LOGGER.error("Error parsing descriptor %s: %s", page_name, err)

        _LOGGER.info("Parsed %d total entity configurations from descriptors", len(entity_configs))
        return entity_configs

    def _parse_single_descriptor(self, xml_content: str, page_name: str) -> Dict[str, Dict[str, Any]]:
        """Parse a single descriptor XML file."""
        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as err:
            _LOGGER.error("Failed to parse XML for %s: %s", page_name, err)
            return {}

        entity_configs = {}

        # Find all elements that can provide entity information (including readonly sensors)
        for element in root.iter():
            if element.tag in ['number', 'switch', 'choice', 'option', 'button']:
                prop = element.get('prop')
                if not prop:
                    continue

                config = self._determine_entity_config(element, page_name)
                if config:
                    entity_configs[prop] = config

        # Also find row elements that might contain sensor descriptions
        for row in root.iter('row'):
            # Look for elements with prop attributes in this row
            for element in row.iter():
                prop = element.get('prop')
                if prop and prop not in entity_configs:
                    # Extract sensor information from row context
                    sensor_config = self._extract_sensor_info_from_row(row, element, page_name)
                    if sensor_config:
                        entity_configs[prop] = sensor_config

        return entity_configs

    def _extract_sensor_info_from_row(self, row: ET.Element, element: ET.Element, page_name: str) -> Optional[Dict[str, Any]]:
        """Extract sensor information from row context for readonly sensors."""
        prop = element.get('prop')
        if not prop:
            return None

        # Get friendly names from row
        text = row.get('text', '')
        text_en = row.get('text_en', text)

        # Get unit from element
        unit = element.get('unit', '')

        # Determine device class from unit
        device_class = self._determine_device_class_from_unit(unit)

        # Create sensor configuration
        sensor_config = {
            'prop': prop,
            'friendly_name': text_en or text or prop,
            'friendly_name_en': text_en or text or prop,
            'unit': unit,
            'device_class': device_class,
            'page': page_name,
            'writable': False,  # These are readonly sensors
            'entity_type': 'sensor'
        }

        _LOGGER.debug("Extracted sensor info for %s: %s", prop, sensor_config)
        return sensor_config

    def _determine_device_class_from_unit(self, unit: str) -> Optional[str]:
        """Determine Home Assistant device class from unit."""
        if not unit:
            return None

        # Map units to device classes
        unit_to_device_class = {
            # Temperature
            '°C': 'temperature',
            'K': 'temperature',
            '°F': 'temperature',

            # Power
            'W': 'power',
            'kW': 'power',
            'MW': 'power',

            # Energy
            'Wh': 'energy',
            'kWh': 'energy',
            'MWh': 'energy',
            'J': 'energy',
            'kJ': 'energy',

            # Pressure
            'Pa': 'pressure',
            'kPa': 'pressure',
            'MPa': 'pressure',
            'bar': 'pressure',
            'mbar': 'pressure',
            'psi': 'pressure',

            # Voltage
            'V': 'voltage',
            'mV': 'voltage',
            'kV': 'voltage',

            # Current
            'A': 'current',
            'mA': 'current',

            # Frequency
            'Hz': 'frequency',
            'kHz': 'frequency',
            'MHz': 'frequency',

            # Percentage
            '%': None,  # No specific device class for percentage

            # Time
            's': 'duration',
            'min': 'duration',
            'h': 'duration',
        }

        return unit_to_device_class.get(unit)

    def _determine_entity_config(self, element: ET.Element, page_name: str) -> Optional[Dict[str, Any]]:
        """Determine the entity configuration from an XML element."""
        prop = element.get('prop')
        if not prop:
            return None

        # Check if element is readonly
        config_attr = element.get('config', '')
        if 'readonly' in config_attr:
            return None  # Skip readonly elements

        # Get friendly names
        text = element.get('text', '')
        text_en = element.get('text_en', text)

        # Get parent row for additional context
        parent_row = self._find_parent_row(element)
        if parent_row is not None:
            row_text = parent_row.get('text', '')
            row_text_en = parent_row.get('text_en', row_text)
            if row_text and text:
                friendly_name = f"{row_text_en} - {text_en}" if text_en else f"{row_text} - {text}"
            else:
                friendly_name = text_en or text or row_text_en or row_text or prop
        else:
            friendly_name = text_en or text or prop

        # Determine entity type and configuration
        entity_config = {
            'prop': prop,
            'friendly_name': friendly_name,
            'friendly_name_en': text_en or friendly_name,
            'page': page_name,
            'writable': True,
        }

        if element.tag == 'switch':
            entity_config.update({
                'entity_type': 'switch',
                'data_type': 'bool',
            })

        elif element.tag == 'number':
            entity_config.update({
                'entity_type': 'number',
                'data_type': 'real',
                'min': self._get_float_attr(element, 'min'),
                'max': self._get_float_attr(element, 'max'),
                'step': self._get_float_attr(element, 'step', 1.0),
                'digits': self._get_int_attr(element, 'digits', 1),
                'unit': element.get('unit', ''),
                'unit_en': element.get('unit_en', element.get('unit', '')),
            })

        elif element.tag == 'choice':
            # Get available options
            options = self._get_choice_options(element)
            entity_config.update({
                'entity_type': 'select',
                'data_type': 'enum',
                'options': options,
            })

        elif element.tag == 'button':
            entity_config.update({
                'entity_type': 'button',
                'data_type': 'action',
            })

        else:
            return None  # Unknown element type

        return entity_config

    def _find_parent_row(self, element: ET.Element) -> Optional[ET.Element]:
        """Find the parent row element for context."""
        # This is a simplified approach since we're working with parsed XML
        # In a real implementation, we'd need to traverse the tree properly
        return None

    def _get_float_attr(self, element: ET.Element, attr: str, default: Optional[float] = None) -> Optional[float]:
        """Get a float attribute from an element."""
        value = element.get(attr)
        if value is None:
            return default
        try:
            return float(value)
        except ValueError:
            return default

    def _get_int_attr(self, element: ET.Element, attr: str, default: Optional[int] = None) -> Optional[int]:
        """Get an integer attribute from an element."""
        value = element.get(attr)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            return default

    def _get_choice_options(self, choice_element: ET.Element) -> List[Dict[str, str]]:
        """Get options for a choice element."""
        options = []
        for option in choice_element.findall('option'):
            option_data = {
                'value': option.get('value', ''),
                'text': option.get('text', ''),
                'text_en': option.get('text_en', option.get('text', '')),
            }
            options.append(option_data)
        return options

    def get_entity_type_for_prop(self, prop: str) -> str:
        """Get the entity type for a given property."""
        config = self.entity_configs.get(prop, {})
        return config.get('entity_type', 'sensor')

    def is_writable(self, prop: str) -> bool:
        """Check if a property is writable."""
        config = self.entity_configs.get(prop, {})
        return config.get('writable', False)
