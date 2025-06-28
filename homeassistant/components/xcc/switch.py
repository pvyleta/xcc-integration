"""Switch platform for XCC Heat Pump Controller integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import XCCDataUpdateCoordinator
from .entity import XCCEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up XCC switch entities from a config entry."""
    coordinator: XCCDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    # Get all switch entities from coordinator
    switch_entities = coordinator.get_entities_by_type("switches")
    
    entities = []
    for entity_id, entity_data in switch_entities.items():
        try:
            entity = XCCSwitch(coordinator, entity_id)
            entities.append(entity)
            _LOGGER.debug("Created switch entity: %s", entity_id)
        except Exception as err:
            _LOGGER.error("Error creating switch entity %s: %s", entity_id, err)

    if entities:
        async_add_entities(entities)
        _LOGGER.info("Added %d XCC switch entities", len(entities))


class XCCSwitch(XCCEntity, SwitchEntity):
    """Representation of an XCC switch."""

    def __init__(self, coordinator: XCCDataUpdateCoordinator, entity_id: str) -> None:
        """Initialize the XCC switch."""
        # Create entity description
        description = self._create_entity_description(coordinator, entity_id)
        super().__init__(coordinator, entity_id, description)

    def _create_entity_description(
        self, coordinator: XCCDataUpdateCoordinator, entity_id: str
    ) -> SwitchEntityDescription:
        """Create entity description for the switch."""
        entity_data = coordinator.get_entity_data(entity_id)
        if not entity_data:
            raise ValueError(f"Entity data not found for {entity_id}")

        return SwitchEntityDescription(
            key=entity_id,
            name=self._get_entity_name(),
        )

    @property
    def is_on(self) -> bool | None:
        """Return true if switch is on."""
        raw_value = self._get_current_value()
        return self._convert_value_for_ha(raw_value)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        success = await self.async_set_xcc_value("1")
        if not success:
            _LOGGER.error("Failed to turn on switch %s", self.entity_id_suffix)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        success = await self.async_set_xcc_value("0")
        if not success:
            _LOGGER.error("Failed to turn off switch %s", self.entity_id_suffix)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        attrs = super().extra_state_attributes
        
        # Add raw value for debugging
        raw_value = self._get_current_value()
        if raw_value is not None:
            attrs["raw_value"] = raw_value
        
        return attrs
