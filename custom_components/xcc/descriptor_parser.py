"""XCC Descriptor Parser for determining entity types and capabilities."""

import logging
from typing import Any
from xml.etree import ElementTree as ET

_LOGGER = logging.getLogger(__name__)


class XCCDescriptorParser:
    """Parser for XCC descriptor files to determine entity types and capabilities."""

    def __init__(self):
        """Initialize the descriptor parser."""
        self.entity_configs = {}

    def parse_descriptor_files(
        self, descriptor_data: dict[str, str],
    ) -> dict[str, dict[str, Any]]:
        """Parse descriptor XML files to determine entity types and configurations.

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
                _LOGGER.debug(
                    "Found %d entity configurations in %s", len(page_configs), page_name,
                )
            except Exception as err:
                _LOGGER.error("Error parsing descriptor %s: %s", page_name, err)

        _LOGGER.info(
            "Parsed %d total entity configurations from descriptors",
            len(entity_configs),
        )
        return entity_configs

    def _parse_single_descriptor(
        self, xml_content: str, page_name: str,
    ) -> dict[str, dict[str, Any]]:
        """Parse a single descriptor XML file."""
        try:
            root = ET.fromstring(xml_content)
            # Store root for parent row lookup
            self._current_root = root
        except ET.ParseError as err:
            _LOGGER.error("Failed to parse XML for %s: %s", page_name, err)
            return {}

        entity_configs = {}

        # Find all elements that can provide entity information (including readonly sensors)
        for element in root.iter():
            if element.tag in [
                "number",
                "switch",
                "choice",
                "option",
                "button",
                "time",
                "date",  # Add date elements to be processed by _determine_entity_config
            ]:
                prop = element.get("prop")
                if not prop:
                    continue

                config = self._determine_entity_config(element, page_name)
                if config:
                    entity_configs[prop] = config

        # Also find row elements that might contain sensor descriptions
        for row in root.iter("row"):
            # Look for elements with prop attributes in this row
            for element in row.iter():
                prop = element.get("prop")
                if prop and prop not in entity_configs:
                    # Skip elements that should be handled by direct element processing
                    # (time, date, number, switch, choice, button elements are handled in first pass)
                    if element.tag in ["time", "date", "number", "switch", "choice", "button"]:
                        continue

                    # Extract sensor information from row context
                    sensor_config = self._extract_sensor_info_from_row(
                        row, element, page_name,
                    )
                    if sensor_config:
                        entity_configs[prop] = sensor_config

        return entity_configs

    def _extract_sensor_info_from_row(
        self, row: ET.Element, element: ET.Element, page_name: str,
    ) -> dict[str, Any] | None:
        """Extract sensor information from row context for readonly sensors."""
        prop = element.get("prop")
        if not prop:
            return None

        # Get friendly names from row
        text = row.get("text", "")
        text_en = row.get("text_en", "")  # Don't default to text here

        # Create separate Czech and English friendly names
        # English friendly name - prioritize English text
        friendly_name_en = text_en or text or prop

        # Czech friendly name - prioritize Czech text
        friendly_name_cz = text or text_en or prop

        # Get unit from element (try both unit and unit_en)
        unit = element.get("unit_en") or element.get("unit", "")

        # If no unit on element, try to infer from context or prop name
        if not unit:
            unit = self._infer_unit_from_context(prop, row, element)

        # Determine device class from unit
        device_class = self._determine_device_class_from_unit(unit)

        # Create sensor configuration
        sensor_config = {
            "prop": prop,
            "friendly_name": friendly_name_cz,  # Use Czech for friendly_name
            "friendly_name_en": friendly_name_en,  # Use English for friendly_name_en
            "unit": unit,
            "device_class": device_class,
            "page": page_name,
            "writable": False,  # These are readonly sensors
            "entity_type": "sensor",
        }

        # Log sensor extraction for debugging
        _LOGGER.debug(
            "🔍 SENSOR EXTRACTION: %s -> friendly_name='%s', friendly_name_en='%s', device_class=%s, unit='%s'",
            prop, friendly_name_cz, friendly_name_en, device_class, unit
        )

        _LOGGER.debug("Extracted sensor info for %s: %s", prop, sensor_config)
        return sensor_config

    def _determine_device_class_from_unit(self, unit: str) -> str | None:
        """Determine Home Assistant device class from unit."""
        if not unit:
            return None

        # Map units to device classes
        unit_to_device_class = {
            # Temperature
            "°C": "temperature",
            "K": "temperature",
            "°F": "temperature",
            # Power
            "W": "power",
            "kW": "power",
            "MW": "power",
            # Energy
            "Wh": "energy",
            "kWh": "energy",
            "MWh": "energy",
            "J": "energy",
            "kJ": "energy",
            # Pressure
            "Pa": "pressure",
            "kPa": "pressure",
            "MPa": "pressure",
            "bar": "pressure",
            "mbar": "pressure",
            "psi": "pressure",
            # Voltage
            "V": "voltage",
            "mV": "voltage",
            "kV": "voltage",
            # Current
            "A": "current",
            "mA": "current",
            # Frequency
            "Hz": "frequency",
            "kHz": "frequency",
            "MHz": "frequency",
            # Percentage
            "%": None,  # No specific device class for percentage
            # Time
            "s": "duration",
            "min": "duration",
            "h": "duration",
        }

        return unit_to_device_class.get(unit)

    def _infer_unit_from_context(
        self, prop: str, row: ET.Element, element: ET.Element,
    ) -> str:
        """Infer unit from context when not explicitly specified."""
        # Check row context first for temperature-related text
        if row is not None:
            row_text = (row.get("text_en", "") or row.get("text", "")).lower()
            # Temperature indicators in row text
            if any(
                temp_word in row_text
                for temp_word in ["temperature", "teplota", "temp.", "temp "]
            ):
                return "°C"
            # Power indicators
            if any(power_word in row_text for power_word in ["power", "výkon", "watt"]):
                return "W"
            # Price indicators
            if any(price_word in row_text for price_word in ["price", "cena", "cost"]):
                return "€/MWh"

        # Common temperature entities by prop name
        if any(temp_word in prop.upper() for temp_word in ["TEMP", "TEPLOTA", "TEPL"]):
            return "°C"

        # TUV entities are typically temperature-related
        if prop.startswith("TUV") and any(
            temp_hint in prop.upper()
            for temp_hint in ["POZADOVANA", "MINIMALNI", "UTLUM"]
        ):
            return "°C"

        # Power entities
        if any(
            power_word in prop.upper() for power_word in ["POWER", "VYKON", "PREBYTEK"]
        ):
            return "W"

        # Price entities
        if any(price_word in prop.upper() for price_word in ["PRICE", "CENA", "COST"]):
            return "€/MWh"

        # Time entities
        if any(
            time_word in prop.upper() for time_word in ["CAS", "TIME", "HODIN", "HOURS"]
        ):
            return "h"

        # Day entities
        if any(day_word in prop.upper() for day_word in ["DNI", "DAYS", "INTERVAL"]):
            return "days"

        # Percentage entities
        if any(pct_word in prop.upper() for pct_word in ["SOC", "PERCENT"]):
            return "%"

        # Pressure entities
        if any(press_word in prop.upper() for press_word in ["PRESSURE", "TLAK"]):
            return "bar"

        # Check if there's a label with unit information nearby
        if row is not None:
            # Look for labels in the same row that might indicate units
            for label in row.findall(".//label"):
                label_text = label.get("text_en", "") or label.get("text", "")
                if any(
                    unit_hint in label_text.lower()
                    for unit_hint in ["°c", "celsius", "temperature"]
                ):
                    return "°C"
                if any(
                    unit_hint in label_text.lower()
                    for unit_hint in ["watt", "power", "w"]
                ):
                    return "W"
                if any(
                    unit_hint in label_text.lower() for unit_hint in ["hour", "time"]
                ):
                    return "h"

        return ""

    def _determine_entity_config(
        self, element: ET.Element, page_name: str,
    ) -> dict[str, Any] | None:
        """Determine the entity configuration from an XML element."""
        prop = element.get("prop")
        if not prop:
            return None

        # Check if element is readonly - only skip readonly choice elements
        # All other elements (number, switch, time) should be processed and handled appropriately
        config_attr = element.get("config", "")
        if "readonly" in config_attr and element.tag in ["choice"]:
            return None  # Skip readonly choice elements (but allow readonly numbers, switches, and time elements)

        # Get friendly names
        text = element.get("text", "")
        text_en = element.get("text_en", "")  # Don't default to text here

        # Get parent row for additional context
        parent_row = self._find_parent_row(element)
        row_text = ""
        row_text_en = ""
        label_text = ""
        label_text_en = ""

        if parent_row is not None:
            row_text = parent_row.get("text", "")
            row_text_en = parent_row.get("text_en", "")

            _LOGGER.debug(
                "🔍 DESCRIPTOR PARSING ROW TEXT: %s -> row_text='%s', row_text_en='%s'",
                prop, row_text, row_text_en
            )

            # Look for corresponding label in the row that provides text context
            # For TO-FVEPRETOPENI-POVOLENI, this will be Row 7 which has the labels
            label_text, label_text_en = self._find_label_for_element(element, parent_row)
        else:
            _LOGGER.debug(
                "🔍 DESCRIPTOR PARSING ROW TEXT: %s -> NO PARENT ROW FOUND",
                prop
            )



        # Create separate Czech and English friendly names
        # English friendly name - prioritize English text
        friendly_name_en = text_en or label_text_en or row_text_en or text or label_text or row_text or prop

        # Czech friendly name - prioritize Czech text
        friendly_name_cz = text or label_text or row_text or text_en or label_text_en or row_text_en or prop

        _LOGGER.debug(
            "🔍 DESCRIPTOR PARSING FALLBACK: %s -> friendly_name_cz='%s', friendly_name_en='%s'",
            prop, friendly_name_cz, friendly_name_en
        )

        # Handle different combinations of row, label, and element text for ENGLISH
        if row_text_en and (text_en or label_text_en):
            # Both row and element/label have English text - combine them
            element_part_en = text_en or label_text_en
            friendly_name_en = f"{row_text_en} - {element_part_en}"
        elif row_text and (text_en or label_text_en):
            # Row has Czech text, element has English text - use English element with Czech row
            element_part_en = text_en or label_text_en
            friendly_name_en = f"{row_text} - {element_part_en}"
        elif row_text_en and (text or label_text):
            # Row has English text, element has Czech text - use Czech element with English row
            element_part_cz = text or label_text
            friendly_name_en = f"{row_text_en} - {element_part_cz}"
        elif label_text_en:
            # No row text but label has English text
            friendly_name_en = label_text_en
        # friendly_name_en already set above with fallback logic

        # Handle different combinations of row, label, and element text for CZECH
        if row_text and (text or label_text):
            # Both row and element/label have Czech text - combine them
            element_part_cz = text or label_text
            friendly_name_cz = f"{row_text} - {element_part_cz}"
        elif row_text_en and (text or label_text):
            # Row has English text, element has Czech text - use Czech element with English row
            element_part_cz = text or label_text
            friendly_name_cz = f"{row_text_en} - {element_part_cz}"
        elif row_text and (text_en or label_text_en):
            # Row has Czech text, element has English text - use English element with Czech row
            element_part_en = text_en or label_text_en
            friendly_name_cz = f"{row_text} - {element_part_en}"
        elif label_text:
            # No row text but label has Czech text
            friendly_name_cz = label_text
        # friendly_name_cz already set above with fallback logic

        # For backward compatibility, set friendly_name to the Czech version
        friendly_name = friendly_name_cz

        # Determine entity type and configuration
        # Check if element is writable (not readonly)
        is_writable = "readonly" not in config_attr

        entity_config = {
            "prop": prop,
            "friendly_name": friendly_name,
            "friendly_name_en": friendly_name_en,
            "page": page_name,
            "writable": is_writable,
        }

        # Log friendly name extraction for debugging
        _LOGGER.debug(
            "🔍 DESCRIPTOR PARSING: %s -> text='%s', text_en='%s', row_text='%s', row_text_en='%s', label_text='%s', label_text_en='%s'",
            prop, text, text_en, row_text, row_text_en, label_text, label_text_en
        )
        _LOGGER.debug(
            "🔍 DESCRIPTOR PARSING: %s -> friendly_name='%s', friendly_name_en='%s'",
            prop, friendly_name, friendly_name_en
        )

        if element.tag == "switch":
            # Readonly switches become sensors
            if is_writable:
                entity_config.update(
                    {
                        "entity_type": "switch",
                        "data_type": "bool",
                    },
                )
            else:
                entity_config.update(
                    {
                        "entity_type": "sensor",
                        "data_type": "bool",
                    },
                )

        elif element.tag == "number":
            # Get unit with enhanced detection
            unit = element.get("unit_en") or element.get("unit", "")
            if not unit:
                unit = self._infer_unit_from_context(prop, parent_row, element)

            # Determine device class from unit
            device_class = self._determine_device_class_from_unit(unit)

            # Readonly numbers become sensors
            if is_writable:
                entity_config.update(
                    {
                        "entity_type": "number",
                        "data_type": "real",
                        "min": self._get_float_attr(element, "min"),
                        "max": self._get_float_attr(element, "max"),
                        "step": self._get_float_attr(element, "step", 1.0),
                        "digits": self._get_int_attr(element, "digits", 1),
                        "unit": unit,
                        "unit_en": unit,
                        "device_class": device_class,
                    },
                )
            else:
                entity_config.update(
                    {
                        "entity_type": "sensor",
                        "data_type": "real",
                        "unit": unit,
                        "unit_en": unit,
                        "device_class": device_class,
                    },
                )

        elif element.tag == "choice":
            # Get available options
            options = self._get_choice_options(element)
            entity_config.update(
                {
                    "entity_type": "select",
                    "data_type": "enum",
                    "options": options,
                },
            )

        elif element.tag == "button":
            entity_config.update(
                {
                    "entity_type": "button",
                    "data_type": "action",
                },
            )

        elif element.tag == "time":
            # Time elements should be treated as sensors with time values
            # They typically have format like "03:00" and should not be numeric
            entity_config.update(
                {
                    "entity_type": "sensor",
                    "data_type": "time",
                    "unit": "",  # No unit for time strings
                    "device_class": None,  # No device class for time strings
                    "state_class": None,  # No state class for time strings (not numeric)
                },
            )

        elif element.tag == "date":
            # Date elements should be treated as sensors with date/timestamp values
            # They contain string values like "08.07.2025" and should not have numeric units
            # CRITICAL: Override the unit that was extracted from XML to prevent ValueError
            entity_config.update(
                {
                    "entity_type": "sensor",
                    "data_type": "string",
                    "unit": None,  # CRITICAL: Override unit to None for date strings - prevents ValueError
                    "device_class": "timestamp" if "timestamp" in prop.lower() else "date",
                    "state_class": None,  # No state class for date strings (not numeric)
                },
            )

        else:
            return None  # Unknown element type

        return entity_config

    def _find_parent_row(self, element: ET.Element) -> ET.Element | None:
        """Find the parent row element for context."""
        # Since ElementTree doesn't have getparent(), we need to search differently
        # We'll store the element reference and search for it in the tree
        if not hasattr(self, "_current_root"):
            return None

        # Find the element in the tree and get its parent row
        immediate_parent = None
        for row in self._current_root.iter("row"):
            for child in row.iter():
                if child is element:
                    immediate_parent = row
                    break
            if immediate_parent is not None:
                break

        # If the immediate parent has no text, look for the previous row with text
        if immediate_parent is not None:
            row_text = immediate_parent.get("text", "")
            row_text_en = immediate_parent.get("text_en", "")

            if not row_text and not row_text_en:
                # Look for the previous row with text in the same block
                for block in self._current_root.iter("block"):
                    rows = list(block.iter("row"))
                    for i, row in enumerate(rows):
                        if row is immediate_parent and i > 0:
                            # Check previous rows for text
                            for j in range(i - 1, -1, -1):
                                prev_row = rows[j]
                                prev_text = prev_row.get("text", "")
                                prev_text_en = prev_row.get("text_en", "")
                                if prev_text or prev_text_en:
                                    return prev_row
                            break

        return immediate_parent

    def _find_immediate_parent_row(self, element: ET.Element) -> ET.Element | None:
        """Find the immediate parent row element (without looking for text context)."""
        if not hasattr(self, "_current_root"):
            return None

        # Find the element in the tree and get its immediate parent row
        for row in self._current_root.iter("row"):
            for child in row.iter():
                if child is element:
                    return row
        return None

    def _find_label_for_element(self, element: ET.Element, context_row: ET.Element) -> tuple[str, str]:
        """Find the corresponding label for an element.

        The element might be in a different row than the labels, so we need to find
        the corresponding label by matching positions across rows in the same block.

        Returns tuple of (label_text, label_text_en).
        """
        if context_row is None:
            return "", ""

        # Find the block containing both the context row and the element
        element_block = None
        context_block = None

        if hasattr(self, "_current_root"):
            for block in self._current_root.iter("block"):
                # Check if this block contains the context row
                for row in block.iter("row"):
                    if row is context_row:
                        context_block = block
                        break

                # Check if this block contains the element
                for elem in block.iter():
                    if elem is element:
                        element_block = block
                        break

        # If they're not in the same block, can't match labels
        if element_block != context_block or element_block is None:
            return "", ""

        # Get all labels in the context row (but skip status/dynamic labels)
        labels = []
        for label in context_row.iter("label"):
            label_text = label.get("text", "")
            label_text_en = label.get("text_en", "")

            # Skip labels that look like status messages or dynamic content
            if not any(skip_word in label_text.lower() for skip_word in ["probíhá", "nastavování", "writing", "settings"]):
                labels.append(label)

        # Get all input elements in the entire block (across all rows)
        input_elements = []
        for row in element_block.iter("row"):
            for child in row.iter():
                if child.tag in ["number", "switch", "select", "button"] and child.get("prop"):
                    input_elements.append(child)

        # Find the index of our element
        element_index = -1
        for i, input_elem in enumerate(input_elements):
            if input_elem is element:
                element_index = i
                break



        # If we found the element, calculate the corresponding label index
        # Labels might not correspond 1:1 with input elements - they might be for the last N elements
        if element_index >= 0 and len(labels) > 0:
            # Calculate the offset - labels are for the last N input elements
            label_offset = len(input_elements) - len(labels)
            label_index = element_index - label_offset

            if label_index >= 0 and label_index < len(labels):
                label = labels[label_index]
                return label.get("text", ""), label.get("text_en", "")

        return "", ""

    def _get_float_attr(
        self, element: ET.Element, attr: str, default: float | None = None,
    ) -> float | None:
        """Get a float attribute from an element."""
        value = element.get(attr)
        if value is None:
            return default
        try:
            return float(value)
        except ValueError:
            return default

    def _get_int_attr(
        self, element: ET.Element, attr: str, default: int | None = None,
    ) -> int | None:
        """Get an integer attribute from an element."""
        value = element.get(attr)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            return default

    def _get_choice_options(self, choice_element: ET.Element) -> list[dict[str, str]]:
        """Get options for a choice element."""
        options = []
        for option in choice_element.findall("option"):
            option_data = {
                "value": option.get("value", ""),
                "text": option.get("text", ""),
                "text_en": option.get("text_en", option.get("text", "")),
            }
            options.append(option_data)
        return options

    def get_entity_type_for_prop(self, prop: str) -> str:
        """Get the entity type for a given property."""
        config = self.entity_configs.get(prop, {})
        return config.get("entity_type", "sensor")

    def is_writable(self, prop: str) -> bool:
        """Check if a property is writable."""
        config = self.entity_configs.get(prop, {})
        return config.get("writable", False)
