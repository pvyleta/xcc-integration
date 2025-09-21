"""XCC Descriptor Parser for determining entity types and capabilities."""

import logging
from typing import Any
from xml.etree import ElementTree as ET

_LOGGER = logging.getLogger(__name__)


class XCCDescriptorParser:
    """Parser for XCC descriptor files to determine entity types and capabilities."""

    def __init__(self, ignore_visibility: bool = False):
        """Initialize the descriptor parser.

        Args:
            ignore_visibility: If True, ignore visibility conditions and include all entities
        """
        self.entity_configs = {}
        self.data_values = {}  # Store current data values for visibility checking
        self.ignore_visibility = ignore_visibility

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

        # Post-process to handle duplicate friendly names
        entity_configs = self._handle_duplicate_friendly_names(entity_configs)

        return entity_configs

    def _parse_single_descriptor(
        self, xml_content: str, page_name: str,
    ) -> dict[str, dict[str, Any]]:
        """Parse a single descriptor XML file."""
        # Check if this is an HTML-based descriptor (like FVEINV.XML)
        if xml_content.strip().startswith('<!DOCTYPE html') or '<html' in xml_content[:200]:
            return self._parse_html_descriptor(xml_content, page_name)

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
        friendly_name_en = text_en or text or self._format_prop_name_english(prop)

        # Czech friendly name - prioritize Czech text
        friendly_name_cz = text or text_en or self._format_prop_name_czech(prop)

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

        # Consolidated sensor extraction log
        fallback_info = ""
        if friendly_name_cz == self._format_prop_name_czech(prop):
            fallback_info = " [FALLBACK]"
        elif text_en and not text:
            fallback_info = " [EN-ONLY]"

        _LOGGER.debug(
            "🔍 SENSOR: %s -> CZ:'%s' | EN:'%s' | %s | %s%s",
            prop, friendly_name_cz, friendly_name_en, device_class or "no-class", unit or "no-unit", fallback_info
        )


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

        # Check visibility conditions unless explicitly ignored
        if not self.ignore_visibility and not self._is_element_visible(element):
            return None  # Skip elements that don't meet visibility conditions

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



            # Look for corresponding label in the row that provides text context
            # For TO-FVEPRETOPENI-POVOLENI, this will be Row 7 which has the labels
            label_text, label_text_en = self._find_label_for_element(element, parent_row)

        # Create separate Czech and English friendly names
        # English friendly name - prioritize English text
        friendly_name_en = text_en or label_text_en or row_text_en or text or label_text or row_text or self._format_prop_name_english(prop)

        # Czech friendly name - prioritize Czech text, but try to translate English-only terms
        friendly_name_cz = text or label_text or row_text
        if not friendly_name_cz:
            # Try to translate English terms to Czech
            english_text = text_en or label_text_en or row_text_en
            if english_text:
                friendly_name_cz = self._translate_english_to_czech(english_text)
            else:
                friendly_name_cz = self._format_prop_name_czech(prop)



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

        # Consolidated descriptor parsing log
        source_info = []
        if text or text_en:
            source_info.append(f"text='{text or text_en}'")
        if row_text or row_text_en:
            source_info.append(f"row='{row_text or row_text_en}'")
        if label_text or label_text_en:
            source_info.append(f"label='{label_text or label_text_en}'")

        fallback_info = ""
        if friendly_name == self._format_prop_name_czech(prop):
            fallback_info = " [FALLBACK]"
        elif text_en and not text and not label_text and not row_text:
            fallback_info = " [EN-ONLY]"

        _LOGGER.debug(
            "🔍 DESCRIPTOR: %s -> CZ:'%s' | EN:'%s' | %s%s",
            prop, friendly_name, friendly_name_en, " | ".join(source_info) or "no-text", fallback_info
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



    def _format_prop_name_czech(self, prop):
        """Format a prop name to be more user-friendly in Czech when no text attributes are available."""
        if not prop:
            return prop

        # Handle special cases for user-editable fields
        if prop == "PAGENAME":
            return "Název stránky"

        # Handle CONFIG-NAZEV entities (user-editable names)
        if prop.endswith("-CONFIG-NAZEV"):
            # Extract the circuit/device name and format it
            circuit_name = prop.replace("-CONFIG-NAZEV", "")
            formatted_circuit = self._format_circuit_name(circuit_name, "cs")
            return f"{formatted_circuit} - Název"

        # Handle other NAZEV entities (user-editable names)
        if prop.endswith("-NAZEV"):
            base_name = prop.replace("-NAZEV", "")
            formatted_base = self._format_circuit_name(base_name, "cs")
            return f"{formatted_base} - Název"

        # Use the generic formatting
        return self._format_prop_name_generic(prop)

    def _format_prop_name_english(self, prop):
        """Format a prop name to be more user-friendly in English when no text attributes are available."""
        if not prop:
            return prop

        # Handle special cases for user-editable fields
        if prop == "PAGENAME":
            return "Page Name"

        # Handle CONFIG-NAZEV entities (user-editable names)
        if prop.endswith("-CONFIG-NAZEV"):
            # Extract the circuit/device name and format it
            circuit_name = prop.replace("-CONFIG-NAZEV", "")
            formatted_circuit = self._format_circuit_name(circuit_name, "en")
            return f"{formatted_circuit} - Name"

        # Handle other NAZEV entities (user-editable names)
        if prop.endswith("-NAZEV"):
            base_name = prop.replace("-NAZEV", "")
            formatted_base = self._format_circuit_name(base_name, "en")
            return f"{formatted_base} - Name"

        # Use the generic formatting
        return self._format_prop_name_generic(prop)

    def _format_prop_name_generic(self, prop):
        """Generic prop name formatting used by both Czech and English methods."""
        if not prop:
            return prop

        # Split on common separators and format
        parts = prop.replace("-", " ").replace("_", " ").split()

        # Capitalize each part and handle common abbreviations
        formatted_parts = []
        for part in parts:
            part_lower = part.lower()
            if part_lower in ["config", "nazev", "stats", "boost", "enabled", "mode", "priorita", "priority"]:
                # Keep common words as-is but capitalized
                formatted_parts.append(part_lower.capitalize())
            elif part_lower in ["tuv", "fve", "tc", "hp", "biv"]:
                # Keep technical abbreviations uppercase
                formatted_parts.append(part.upper())
            elif len(part) <= 3 and part.isupper():
                # Keep short uppercase parts as-is
                formatted_parts.append(part)
            else:
                # Capitalize normally
                formatted_parts.append(part.capitalize())

        formatted = " ".join(formatted_parts)
        return formatted

    def _format_circuit_name(self, circuit_name, language="cs"):
        """Format circuit/device names for better readability with language support."""
        if not circuit_name:
            return circuit_name

        # Handle specific circuit patterns with language support
        if circuit_name.startswith("TOPNEOKRUHYIN"):
            # Extract circuit number
            circuit_num = circuit_name.replace("TOPNEOKRUHYIN", "")
            if language == "en":
                return f"Heating Circuit {circuit_num}"
            else:
                return f"Topný okruh {circuit_num}"
        elif circuit_name.startswith("FVE-CASCADECONFIG"):
            # Extract cascade number
            cascade_num = circuit_name.replace("FVE-CASCADECONFIG", "")
            if language == "en":
                return f"PV Cascade {cascade_num}"
            else:
                return f"FVE kaskáda {cascade_num}"
        elif circuit_name.startswith("OKRUH"):
            # Extract circuit number
            circuit_num = circuit_name.replace("OKRUH", "")
            if language == "en":
                return f"Circuit {circuit_num}"
            else:
                return f"Okruh {circuit_num}"
        else:
            # Generic formatting
            return circuit_name.replace("-", " ").title()

    def _translate_english_to_czech(self, english_text):
        """Translate common English terms to Czech for Heat Pump Controller entities."""
        if not english_text:
            return english_text

        # Common translations for Heat Pump Controller entities
        translations = {
            # Heat pump terms
            "Heat Pump": "Tepelné čerpadlo",
            "Heat pump": "Tepelné čerpadlo",
            "HP": "TČ",
            "Compressor": "Kompresor",
            "Evaporator": "Výparník",
            "Condenser": "Kondenzátor",
            "Refrigerant": "Chladivo",

            # Temperature and heating
            "Temperature": "Teplota",
            "Heating": "Vytápění",
            "Cooling": "Chlazení",
            "Hot water": "Teplá voda",
            "Flow": "Průtok",
            "Return": "Zpátečka",
            "Supply": "Přívod",

            # Control and operation
            "Control": "Řízení",
            "Operation": "Provoz",
            "Mode": "Režim",
            "Status": "Stav",
            "Enable": "Povolit",
            "Enabled": "Povoleno",
            "Disable": "Zakázat",
            "Disabled": "Zakázáno",
            "Priority": "Priorita",
            "Configuration": "Konfigurace",
            "Config": "Konfigurace",

            # Measurements
            "Power": "Výkon",
            "Pressure": "Tlak",
            "Current": "Proud",
            "Voltage": "Napětí",
            "Frequency": "Frekvence",
            "Speed": "Rychlost",
            "RPM": "Otáčky",

            # Time and scheduling
            "Time": "Čas",
            "Schedule": "Plán",
            "Timer": "Časovač",
            "Delay": "Zpoždění",

            # System components
            "Pump": "Čerpadlo",
            "Fan": "Ventilátor",
            "Valve": "Ventil",
            "Sensor": "Čidlo",
            "Circuit": "Okruh",
            "Zone": "Zóna",
        }

        # Try exact match first
        if english_text in translations:
            translated = translations[english_text]
            _LOGGER.debug(
                "🔄 ENGLISH->CZECH TRANSLATION: '%s' -> '%s'",
                english_text, translated
            )
            return translated

        # Try partial matches for compound terms
        translated_text = english_text
        for english, czech in translations.items():
            if english.lower() in english_text.lower():
                translated_text = translated_text.replace(english, czech)

        if translated_text != english_text:
            _LOGGER.debug(
                "🔄 PARTIAL ENGLISH->CZECH TRANSLATION: '%s' -> '%s'",
                english_text, translated_text
            )
            return translated_text

        # No translation found, return original
        _LOGGER.debug(
            "❓ NO TRANSLATION FOUND: '%s' (keeping English)",
            english_text
        )
        return english_text

    def _handle_duplicate_friendly_names(self, entity_configs: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
        """Handle duplicate friendly names by adding XCC variable name as suffix."""
        # Track friendly names and their occurrences
        czech_name_counts = {}
        english_name_counts = {}

        # First pass: count occurrences of each friendly name
        for prop, config in entity_configs.items():
            friendly_name_cz = config.get("friendly_name", "")
            friendly_name_en = config.get("friendly_name_en", "")

            if friendly_name_cz:
                czech_name_counts[friendly_name_cz] = czech_name_counts.get(friendly_name_cz, 0) + 1
            if friendly_name_en:
                english_name_counts[friendly_name_en] = english_name_counts.get(friendly_name_en, 0) + 1

        # Find duplicates
        czech_duplicates = {name for name, count in czech_name_counts.items() if count > 1}
        english_duplicates = {name for name, count in english_name_counts.items() if count > 1}

        # Log duplicate detection
        if czech_duplicates:
            _LOGGER.debug("🔍 DUPLICATE CZECH NAMES DETECTED: %s", list(czech_duplicates))
        if english_duplicates:
            _LOGGER.debug("🔍 DUPLICATE ENGLISH NAMES DETECTED: %s", list(english_duplicates))

        # Second pass: add suffixes to duplicates
        for prop, config in entity_configs.items():
            friendly_name_cz = config.get("friendly_name", "")
            friendly_name_en = config.get("friendly_name_en", "")

            # Add suffix to duplicate names and log consolidated fixes
            fixes = []
            if friendly_name_cz in czech_duplicates:
                new_name_cz = f"{friendly_name_cz} ({prop})"
                config["friendly_name"] = new_name_cz
                fixes.append(f"CZ:'{friendly_name_cz}' -> '{new_name_cz}'")

            if friendly_name_en in english_duplicates:
                new_name_en = f"{friendly_name_en} ({prop})"
                config["friendly_name_en"] = new_name_en
                fixes.append(f"EN:'{friendly_name_en}' -> '{new_name_en}'")

            if fixes:
                _LOGGER.debug("🔧 DUPLICATE NAMES FIXED: %s", " | ".join(fixes))

        return entity_configs

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

    def _parse_visibility_condition(self, vis_data: str) -> list[tuple[str, str]]:
        """Parse visData string into list of (property, expected_value) tuples.

        Format: "count;property1;value1;property2;value2;..."
        Example: "1;TUVSCHOVANITEPLOT;0" -> [("TUVSCHOVANITEPLOT", "0")]
        """
        if not vis_data:
            return []

        parts = vis_data.split(';')
        if len(parts) < 1:
            return []

        try:
            count = int(parts[0])
            conditions = []

            for i in range(count):
                prop_idx = 1 + (i * 2)
                val_idx = 2 + (i * 2)

                if prop_idx < len(parts) and val_idx < len(parts):
                    conditions.append((parts[prop_idx], parts[val_idx]))

            return conditions
        except (ValueError, IndexError):
            return []

    def _check_visibility_conditions(self, conditions: list[tuple[str, str]]) -> bool:
        """Check if all visibility conditions are met based on current data values."""
        if not conditions:
            return True  # No conditions means always visible

        for prop, expected_value in conditions:
            actual_value = self.data_values.get(prop)
            if actual_value != expected_value:
                return False

        return True

    def _is_element_visible(self, element: ET.Element) -> bool:
        """Check if an element should be visible based on its visData attribute."""
        vis_data = element.get("visData")
        if not vis_data:
            return True  # No visibility condition means always visible

        conditions = self._parse_visibility_condition(vis_data)
        return self._check_visibility_conditions(conditions)

    def update_data_values(self, data_values: dict[str, str]):
        """Update the current data values for visibility checking."""
        self.data_values = data_values or {}

    def _parse_html_descriptor(
        self, html_content: str, page_name: str,
    ) -> dict[str, dict[str, Any]]:
        """Parse HTML-based descriptor files like FVEINV.XML."""
        import re

        entity_configs = {}

        # Extract CSS class names that look like entity identifiers
        # Look for patterns like FVESTATS-MENIC-TOTALGENERATED, FVESTATS-MENIC-BATTERY-SOC, FVE-CONFIG-MENICECONFIG-READONLY, etc.
        class_pattern = r'class="([^"]*(?:FVESTATS-|FVE-CONFIG-)[^"]*)"'
        class_matches = re.findall(class_pattern, html_content, re.IGNORECASE)

        # Also look for id attributes with similar patterns
        id_pattern = r'id="([^"]*(?:FVESTATS-|FVE-CONFIG-)[^"]*)"'
        id_matches = re.findall(id_pattern, html_content, re.IGNORECASE)

        # Combine all matches
        all_matches = class_matches + id_matches

        for match in all_matches:
            # Split by spaces to get individual class names
            class_names = match.split()

            for class_name in class_names:
                if 'FVESTATS-' in class_name.upper() or 'FVE-CONFIG-' in class_name.upper():
                    entity_name = class_name.upper()

                    # Skip if already processed
                    if entity_name in entity_configs:
                        continue

                    # Determine entity properties based on name patterns
                    config = self._determine_html_entity_config(entity_name, html_content)
                    if config:
                        entity_configs[entity_name] = config

        # Also look for direct text patterns that might indicate entities
        # Look for patterns in the HTML content itself
        text_pattern = r'((?:FVESTATS-|FVE-CONFIG-)[A-Z0-9-]+)'
        text_matches = re.findall(text_pattern, html_content, re.IGNORECASE)

        for match in text_matches:
            entity_name = match.upper()
            if entity_name not in entity_configs:
                config = self._determine_html_entity_config(entity_name, html_content)
                if config:
                    entity_configs[entity_name] = config

        _LOGGER.debug("Found %d entity configurations in HTML descriptor %s", len(entity_configs), page_name)
        return entity_configs

    def _determine_html_entity_config(
        self, entity_name: str, html_content: str,
    ) -> dict[str, Any] | None:
        """Determine entity configuration for HTML-based entities."""
        # Default configuration
        config = {
            "entity_type": "sensor",
            "friendly_name": self._generate_friendly_name_from_entity_name(entity_name),
            "unit": "",
            "device_class": None,
            "state_class": None,
            "icon": None,
            "entity_category": None,
            "page": "pv_inverter",
        }

        # Determine properties based on entity name patterns
        entity_lower = entity_name.lower()

        # Configuration entities (FVE-CONFIG-*)
        if entity_name.startswith('FVE-CONFIG-'):
            if 'readonly' in entity_lower:
                config.update({
                    "entity_type": "switch",  # This is a switch to control read-only mode, not a read-only sensor
                    "unit": "",
                    "device_class": None,
                    "state_class": None,
                    "icon": "mdi:lock",
                    "friendly_name": "Read-only Mode",
                    "writable": True,  # This switch can be toggled
                })
            elif 'komunikovat' in entity_lower:
                config.update({
                    "entity_type": "switch",  # This is also a switch to enable/disable communication
                    "unit": "",
                    "device_class": None,
                    "state_class": None,
                    "icon": "mdi:network",
                    "friendly_name": "Communication Enabled",
                    "writable": True,  # This switch can be toggled
                })
            elif 'pocetstringu' in entity_lower:
                config.update({
                    "entity_type": "sensor",
                    "unit": "",
                    "device_class": None,
                    "state_class": None,
                    "icon": "mdi:counter",
                    "friendly_name": "Number of Strings",
                })
            elif 'batteryconfig' in entity_lower and 'enabled' in entity_lower:
                config.update({
                    "entity_type": "sensor",
                    "unit": "",
                    "device_class": None,
                    "state_class": None,
                    "icon": "mdi:battery-check",
                    "friendly_name": f"Battery {entity_name.split('-')[-2]} Enabled" if len(entity_name.split('-')) > 2 else "Battery Config Enabled",
                })

        # Battery related entities
        if "battery" in entity_lower:
            if "soc" in entity_lower:
                config.update({
                    "unit": "%",
                    "device_class": "battery",
                    "state_class": "measurement",
                    "icon": "mdi:battery",
                })
            elif "power" in entity_lower:
                config.update({
                    "unit": "W",
                    "device_class": "power",
                    "state_class": "measurement",
                    "icon": "mdi:battery-charging",
                })
            elif "voltage" in entity_lower:
                config.update({
                    "unit": "V",
                    "device_class": "voltage",
                    "state_class": "measurement",
                })
            elif "current" in entity_lower:
                config.update({
                    "unit": "A",
                    "device_class": "current",
                    "state_class": "measurement",
                })

        # Power related entities
        elif "power" in entity_lower:
            config.update({
                "unit": "W",
                "device_class": "power",
                "state_class": "measurement",
                "icon": "mdi:flash",
            })

        # Energy related entities
        elif "generated" in entity_lower or "energy" in entity_lower:
            if "today" in entity_lower:
                config.update({
                    "unit": "kWh",
                    "device_class": "energy",
                    "state_class": "total_increasing",
                    "icon": "mdi:solar-power",
                })
            else:
                config.update({
                    "unit": "kWh",
                    "device_class": "energy",
                    "state_class": "total_increasing",
                    "icon": "mdi:solar-power",
                })

        # Voltage entities
        elif "voltage" in entity_lower or "volt" in entity_lower:
            config.update({
                "unit": "V",
                "device_class": "voltage",
                "state_class": "measurement",
            })

        # Current entities
        elif "current" in entity_lower or "amp" in entity_lower:
            config.update({
                "unit": "A",
                "device_class": "current",
                "state_class": "measurement",
            })

        # Frequency entities
        elif "freq" in entity_lower:
            config.update({
                "unit": "Hz",
                "device_class": "frequency",
                "state_class": "measurement",
            })

        # Temperature entities
        elif "temp" in entity_lower:
            config.update({
                "unit": "°C",
                "device_class": "temperature",
                "state_class": "measurement",
            })

        return config

    def _generate_friendly_name_from_entity_name(self, entity_name: str) -> str:
        """Generate a friendly name from entity name."""
        # Remove common prefixes
        name = entity_name.replace("FVESTATS-MENIC-", "").replace("FVESTATS-", "").replace("FVE-CONFIG-MENICECONFIG-", "").replace("FVE-CONFIG-", "")

        # Split by dashes and capitalize
        parts = name.split("-")
        friendly_parts = []

        for part in parts:
            if part.lower() == "soc":
                friendly_parts.append("SOC")
            elif part.lower() == "pv":
                friendly_parts.append("PV")
            elif part.lower() == "ac":
                friendly_parts.append("AC")
            elif part.lower() == "dc":
                friendly_parts.append("DC")
            elif part.lower() == "readonly":
                friendly_parts.append("Read-only")
            elif part.lower() == "komunikovat":
                friendly_parts.append("Communication")
            elif part.lower() == "pocetstringu":
                friendly_parts.append("String Count")
            elif part.lower() == "batteryconfig0":
                friendly_parts.append("Battery 1 Config")
            elif part.lower() == "batteryconfig1":
                friendly_parts.append("Battery 2 Config")
            else:
                friendly_parts.append(part.capitalize())

        return " ".join(friendly_parts)
