"""Select platform for XCC Heat Pump Controller integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import XCCDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up XCC select entities from a config entry."""
    coordinator: XCCDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    # Wait for first data update to ensure descriptors are loaded
    await coordinator.async_config_entry_first_refresh()

    # Create select entities for all writable select properties
    selects = []
    for entity_data in coordinator.data.get("entities", []):
        prop = entity_data.get("prop", "").upper()
        entity_type = coordinator.get_entity_type(prop)

        if entity_type == "select" and coordinator.is_writable(prop):
            select = XCCSelect(coordinator, entity_data)
            selects.append(select)
            _LOGGER.debug("Created select entity: %s (%s)", select.name, prop)

    entities = []
    for entity_id, entity_data in select_entities.items():
        try:
            entity = XCCSelect(coordinator, entity_id)
            entities.append(entity)
            _LOGGER.debug("Created select entity: %s", entity_id)
        except Exception as err:
            _LOGGER.error("Error creating select entity %s: %s", entity_id, err)

    if entities:
        async_add_entities(entities)
        _LOGGER.info("Added %d XCC select entities", len(entities))


class XCCSelect(XCCEntity, SelectEntity):
    """Representation of an XCC select."""

    def __init__(self, coordinator: XCCDataUpdateCoordinator, entity_id: str) -> None:
        """Initialize the XCC select."""
        # Create entity description
        description = self._create_entity_description(coordinator, entity_id)
        super().__init__(coordinator, entity_id, description)

        # Store option mapping for value conversion
        self._option_mapping = self._create_option_mapping()
        self._reverse_option_mapping = {v: k for k, v in self._option_mapping.items()}

    def _create_entity_description(
        self, coordinator: XCCDataUpdateCoordinator, entity_id: str
    ) -> SelectEntityDescription:
        """Create entity description for the select."""
        entity_data = coordinator.get_entity_data(entity_id)
        if not entity_data:
            raise ValueError(f"Entity data not found for {entity_id}")

        attributes = entity_data["data"].get("attributes", {})
        options = self._get_localized_options(attributes)

        return SelectEntityDescription(
            key=entity_id,
            name=self._get_entity_name(),
            options=options,
        )

    def _get_localized_options(self, attributes: dict[str, Any]) -> list[str]:
        """Get localized options for the select entity."""
        options = attributes.get("options", [])
        if not options:
            return []

        # Get language preference
        hass_language = self.hass.config.language if self.hass else "en"
        use_czech = hass_language.startswith("cs") or hass_language.startswith("cz")

        localized_options = []
        for option in options:
            if use_czech:
                # Prefer Czech text, fallback to English, then value
                text = option.get("text", option.get("text_en", option["value"]))
            else:
                # Prefer English text, fallback to Czech, then value
                text = option.get("text_en", option.get("text", option["value"]))

            localized_options.append(text)

        return localized_options

    def _create_option_mapping(self) -> dict[str, str]:
        """Create mapping from XCC values to display options."""
        attributes = self._attributes
        options = attributes.get("options", [])
        if not options:
            return {}

        # Get language preference
        hass_language = self.hass.config.language if self.hass else "en"
        use_czech = hass_language.startswith("cs") or hass_language.startswith("cz")

        mapping = {}
        for option in options:
            xcc_value = option["value"]

            if use_czech:
                display_text = option.get("text", option.get("text_en", xcc_value))
            else:
                display_text = option.get("text_en", option.get("text", xcc_value))

            mapping[xcc_value] = display_text

        return mapping

    @property
    def options(self) -> list[str]:
        """Return the list of available options."""
        if hasattr(self.entity_description, 'options'):
            return self.entity_description.options
        return list(self._option_mapping.values())

    @property
    def current_option(self) -> str | None:
        """Return the current selected option."""
        raw_value = self._get_current_value()
        if raw_value is None:
            return None

        # Convert XCC value to display option
        xcc_value = str(raw_value)
        return self._option_mapping.get(xcc_value, xcc_value)

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        # Convert display option back to XCC value
        xcc_value = self._reverse_option_mapping.get(option)
        if xcc_value is None:
            _LOGGER.error("Unknown option %s for select %s", option, self.entity_id_suffix)
            return

        success = await self.async_set_xcc_value(xcc_value)
        if not success:
            _LOGGER.error("Failed to set option %s for select %s", option, self.entity_id_suffix)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        attrs = super().extra_state_attributes

        # Add raw value for debugging
        raw_value = self._get_current_value()
        if raw_value is not None:
            attrs["raw_value"] = raw_value

        # Add option mapping for debugging
        attrs["option_mapping"] = self._option_mapping

        return attrs
