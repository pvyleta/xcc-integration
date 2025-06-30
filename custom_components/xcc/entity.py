"""Base entity for XCC Heat Pump Controller integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import XCCDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


class XCCEntity(CoordinatorEntity[XCCDataUpdateCoordinator]):
    """Base class for XCC entities."""

    def __init__(
        self,
        coordinator: XCCDataUpdateCoordinator,
        entity_id: str,
        description: EntityDescription | None = None,
    ) -> None:
        """Initialize the XCC entity."""
        super().__init__(coordinator)
        
        self.entity_id_suffix = entity_id
        self._entity_data = coordinator.get_entity_data(entity_id)

        if not self._entity_data:
            raise ValueError(f"Entity data not found for {entity_id}")

        self._xcc_data = self._entity_data.get("data", {})
        self._attributes = self._xcc_data.get("attributes", {})

        # Ensure _attributes is always a dict
        if not isinstance(self._attributes, dict):
            _LOGGER.warning("Entity %s has invalid attributes type: %s, using empty dict",
                          entity_id, type(self._attributes))
            self._attributes = {}

        _LOGGER.debug("Initialized entity %s with attributes: %s", entity_id, list(self._attributes.keys()))
        
        # Set entity description if provided
        if description:
            self.entity_description = description
        
        # Generate unique ID
        self._attr_unique_id = f"{coordinator.ip_address}_{entity_id}"
        
        # Set entity name
        self._attr_name = self._get_entity_name()
        
        # Set device info
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.ip_address)},
            name=coordinator.device_info["name"],
            manufacturer=coordinator.device_info["manufacturer"],
            model=coordinator.device_info["model"],
            sw_version=coordinator.device_info.get("sw_version"),
            configuration_url=coordinator.device_info.get("configuration_url"),
        )

    def _get_entity_name(self) -> str:
        """Get the entity name based on language preference."""
        # Try to get localized name based on Home Assistant language
        hass_language = self.hass.config.language if self.hass else "en"
        
        if hass_language.startswith("cs") or hass_language.startswith("cz"):
            # Czech language preference
            name = self._attributes.get("friendly_name", "")
            if not name:
                name = self._attributes.get("friendly_name_en", self.entity_id_suffix)
        else:
            # English language preference (default)
            name = self._attributes.get("friendly_name_en", "")
            if not name:
                name = self._attributes.get("friendly_name", self.entity_id_suffix)
        
        return name or self.entity_id_suffix

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        attrs = {
            "xcc_field_name": self.entity_id_suffix,
            "xcc_page": self._entity_data.get("page", "unknown"),
            "xcc_data_type": self._attributes.get("data_type", "unknown"),
            "xcc_element_type": self._attributes.get("element_type", "unknown"),
        }
        
        # Add settable indicator
        if "is_settable" in self._attributes:
            attrs["xcc_settable"] = self._attributes["is_settable"]
        
        # Add constraints for numeric fields
        if self._attributes.get("data_type") == "numeric":
            if "min_value" in self._attributes:
                attrs["xcc_min_value"] = self._attributes["min_value"]
            if "max_value" in self._attributes:
                attrs["xcc_max_value"] = self._attributes["max_value"]
            if "unit" in self._attributes:
                attrs["xcc_unit"] = self._attributes["unit"]
        
        # Add options for enum fields
        elif self._attributes.get("data_type") == "enum" and "options" in self._attributes:
            options = []
            for option in self._attributes["options"]:
                option_text = option.get("text_en", option.get("text", option["value"]))
                options.append(f"{option['value']}: {option_text}")
            attrs["xcc_options"] = options
        
        return attrs

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        # Update entity data from coordinator
        self._entity_data = self.coordinator.get_entity_data(self.entity_id_suffix)
        if self._entity_data:
            self._xcc_data = self._entity_data["data"]
            self._attributes = self._xcc_data.get("attributes", {})
        
        super()._handle_coordinator_update()

    def _get_current_value(self) -> Any:
        """Get the current value from coordinator data."""
        entity_type = self._entity_data["type"]
        
        if entity_type in self.coordinator.data:
            entity_data = self.coordinator.data[entity_type].get(self.entity_id_suffix)
            if entity_data:
                return entity_data.get("state")
        
        return None

    def _convert_value_for_ha(self, value: Any) -> Any:
        """Convert XCC value to Home Assistant compatible value."""
        if value is None:
            return None
            
        data_type = self._attributes.get("data_type", "unknown")
        
        # Convert boolean values
        if data_type == "boolean":
            if isinstance(value, str):
                return value.lower() in ("1", "true", "on", "yes")
            return bool(value)
        
        # Convert numeric values
        elif data_type == "numeric":
            try:
                # Try integer first
                if isinstance(value, str) and "." not in value:
                    return int(value)
                return float(value)
            except (ValueError, TypeError):
                return value
        
        # Return string values as-is
        return str(value) if value is not None else None

    def _get_unit_of_measurement(self) -> str | None:
        """Get unit of measurement for the entity."""
        return self._attributes.get("unit")

    def _get_device_class(self) -> str | None:
        """Get device class for the entity."""
        return self._attributes.get("device_class")

    def _get_state_class(self) -> str | None:
        """Get state class for the entity."""
        return self._attributes.get("state_class")

    async def async_set_xcc_value(self, value: Any) -> bool:
        """Set value on XCC controller."""
        success = await self.coordinator.async_set_value(self.entity_id_suffix, value)
        if success:
            # Request immediate update
            await self.coordinator.async_request_refresh()
        return success
