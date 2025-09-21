"""Support for XCC button entities."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.button import ButtonEntity
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
    """Set up XCC button entities from a config entry."""
    coordinator: XCCDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    _LOGGER.info("🚀 Setting up XCC button platform")
    
    # Create button entities immediately if data is available
    def _create_button_entities():
        """Create button entities from coordinator data."""
        if not coordinator.data:
            _LOGGER.debug("No coordinator data available yet")
            return []
        
        buttons_data = coordinator.data.get("buttons", {})
        _LOGGER.info("📊 Found %d button entities in coordinator data", len(buttons_data))
        
        if not buttons_data:
            _LOGGER.warning("❌ No button data in coordinator - check entity processing")
            return []
        
        buttons = []
        for entity_key, entity_data in buttons_data.items():
            try:
                prop = entity_data.get("prop", "").upper()
                entity_type = coordinator.get_entity_type(prop)

                if entity_type == "button":
                    button = XCCButton(coordinator, entity_data)
                    buttons.append(button)
                    _LOGGER.info(
                        "🏗️ BUTTON: %s -> '%s' | Action: %s",
                        prop, button.name, entity_data.get("value", "N/A")
                    )
                else:
                    _LOGGER.debug("Skipping %s: type=%s", prop, entity_type)
            except Exception as e:
                _LOGGER.error("❌ Error creating button entity for %s: %s", entity_key, e)
        
        return buttons
    
    # Try to create entities immediately
    buttons = _create_button_entities()
    
    if buttons:
        async_add_entities(buttons)
        _LOGGER.info("✅ Successfully added %d XCC button entities", len(buttons))
    else:
        _LOGGER.warning("⚠️  No button entities created yet - will retry when data becomes available")
        
        # Set up listener for future coordinator updates
        def _on_coordinator_update():
            """Handle coordinator data updates."""
            new_buttons = _create_button_entities()
            if new_buttons:
                async_add_entities(new_buttons)
                _LOGGER.info("✅ Added %d XCC button entities after coordinator update", len(new_buttons))
        
        # Register the update listener
        coordinator.async_add_listener(_on_coordinator_update)
        _LOGGER.info("📡 Registered listener for future coordinator updates")


class XCCButton(XCCEntity, ButtonEntity):
    """Representation of an XCC button entity."""

    def __init__(self, coordinator: XCCDataUpdateCoordinator, entity_data: dict[str, Any]) -> None:
        """Initialize the XCC button."""
        # Extract entity_id from entity_data for XCCEntity base class
        entity_id = entity_data.get("entity_id", "")
        if not entity_id:
            raise ValueError(f"Button entity_data missing entity_id: {entity_data}")

        super().__init__(coordinator, entity_id)

        # Store entity_data for button-specific functionality
        self._entity_data = entity_data

        # Button-specific attributes
        self._attr_entity_category = None  # Buttons are typically configuration entities

        # Get button action value if specified
        self._button_value = entity_data.get("value")
        
        _LOGGER.debug(
            "🔘 Button entity created: %s | Value: %s",
            self.entity_id, self._button_value
        )

    async def async_press(self) -> None:
        """Handle the button press."""
        prop = self._entity_data.get("prop", "").upper()
        
        _LOGGER.info("🔘 Button pressed: %s (prop: %s)", self.name, prop)
        
        try:
            # Use the button value if specified, otherwise use a default action value
            value = self._button_value if self._button_value is not None else "1"
            
            success = await self.coordinator.async_set_value(prop, value)
            
            if success:
                _LOGGER.info("✅ Button action successful: %s = %s", prop, value)
                # Trigger coordinator refresh to get updated state
                await self.coordinator.async_request_refresh()
            else:
                _LOGGER.error("❌ Button action failed: %s", prop)
                
        except Exception as e:
            _LOGGER.error("❌ Error executing button action for %s: %s", prop, e)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        # Buttons are available if coordinator is available and the property exists
        if not self.coordinator.last_update_success:
            return False
        
        prop = self._entity_data.get("prop", "").upper()
        return self.coordinator.has_property(prop)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional state attributes."""
        attributes = super().extra_state_attributes or {}
        
        # Add button-specific attributes
        if self._button_value is not None:
            attributes["button_value"] = self._button_value
        
        # Add action description based on button type
        prop = self._entity_data.get("prop", "").upper()
        if "FLASH" in prop:
            if "10" in str(self._button_value) or "11" in str(self._button_value) or "12" in str(self._button_value):
                attributes["action_type"] = "save_configuration"
            elif "1" in str(self._button_value) or "2" in str(self._button_value) or "3" in str(self._button_value):
                attributes["action_type"] = "load_configuration"
            elif "20" in str(self._button_value) or "21" in str(self._button_value) or "22" in str(self._button_value):
                attributes["action_type"] = "delete_configuration"
            else:
                attributes["action_type"] = "system_action"
        else:
            attributes["action_type"] = "control_action"
        
        return attributes

    @property
    def icon(self) -> str | None:
        """Return the icon for this button."""
        prop = self._entity_data.get("prop", "").upper()
        
        # Icon based on button function
        if "FLASH" in prop:
            if "10" in str(self._button_value) or "11" in str(self._button_value) or "12" in str(self._button_value):
                return "mdi:content-save"  # Save
            elif "1" in str(self._button_value) or "2" in str(self._button_value) or "3" in str(self._button_value):
                return "mdi:upload"  # Load
            elif "20" in str(self._button_value) or "21" in str(self._button_value) or "22" in str(self._button_value):
                return "mdi:delete"  # Delete
            else:
                return "mdi:cog"  # System
        else:
            return "mdi:gesture-tap-button"  # Generic button
