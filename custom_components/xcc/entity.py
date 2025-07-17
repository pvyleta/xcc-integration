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

        # IMPORTANT: Check for empty entity_id to provide better error messages
        if not entity_id or entity_id.strip() == "":
            raise ValueError(f"Entity ID cannot be empty. Received: '{entity_id}'")

        self._entity_data = coordinator.get_entity_data(entity_id)

        if not self._entity_data:
            # Provide more detailed error information for debugging
            available_entities = list(coordinator.entities.keys())[:10]  # Show first 10
            raise ValueError(
                f"Entity data not found for '{entity_id}'. Available entities (first 10): {available_entities}"
            )

        _LOGGER.debug(
            "Entity %s data structure: %s",
            entity_id,
            {k: type(v).__name__ for k, v in self._entity_data.items()},
        )

        self._xcc_data = self._entity_data.get("data", {})
        _LOGGER.debug(
            "Entity %s xcc_data keys: %s",
            entity_id,
            list(self._xcc_data.keys())
            if isinstance(self._xcc_data, dict)
            else type(self._xcc_data).__name__,
        )

        self._attributes = self._xcc_data.get("attributes", {})

        # Ensure _attributes is always a dict
        if not isinstance(self._attributes, dict):
            _LOGGER.warning(
                "Entity %s has invalid attributes type: %s, using empty dict",
                entity_id,
                type(self._attributes),
            )
            self._attributes = {}

        # CRITICAL FIX: Add friendly names from descriptor config to attributes
        # The descriptor config contains friendly_name_en which is needed for proper entity naming
        descriptor_config = self._entity_data.get("descriptor_config", {})
        if descriptor_config:
            # Add friendly names from descriptor to attributes so _get_entity_name can access them
            if "friendly_name" in descriptor_config:
                self._attributes["friendly_name"] = descriptor_config["friendly_name"]
            if "friendly_name_en" in descriptor_config:
                self._attributes["friendly_name_en"] = descriptor_config["friendly_name_en"]

        _LOGGER.debug(
            "Initialized entity %s with attributes: %s",
            entity_id,
            list(self._attributes.keys()),
        )

        # Set entity description if provided
        if description:
            self.entity_description = description

        # Generate unique ID
        self._attr_unique_id = f"{coordinator.ip_address}_{entity_id}"

        # Set entity name
        self._attr_name = self._get_entity_name()

        # Set device info based on entity's assigned device
        device_info = coordinator.get_device_info_for_entity(entity_id)
        self._attr_device_info = DeviceInfo(
            identifiers=device_info["identifiers"],
            name=device_info["name"],
            manufacturer=device_info["manufacturer"],
            model=device_info["model"],
            sw_version=device_info.get("sw_version"),
            configuration_url=device_info.get("configuration_url"),
            via_device=device_info.get("via_device"),  # Link to parent device if applicable
        )

    def _get_entity_name(self) -> str:
        """Get the entity name - always prefer English strings."""
        # Always prefer English friendly name first
        friendly_name_en = self._attributes.get("friendly_name_en", "")
        friendly_name_cz = self._attributes.get("friendly_name", "")

        # Debug logging for entity name selection
        _LOGGER.debug(
            "🏷️ ENTITY NAME SELECTION for %s: friendly_name_en='%s', friendly_name_cz='%s'",
            self.entity_id_suffix, friendly_name_en, friendly_name_cz
        )

        if friendly_name_en:
            selected_name = friendly_name_en
            _LOGGER.debug("   ✅ Using English name: '%s'", selected_name)
        elif friendly_name_cz:
            selected_name = friendly_name_cz
            _LOGGER.debug("   ⚠️ Using Czech name (no English available): '%s'", selected_name)
        else:
            selected_name = self.entity_id_suffix
            _LOGGER.debug("   ❌ Using entity ID suffix (no friendly names): '%s'", selected_name)

        return selected_name

    async def async_added_to_hass(self) -> None:
        """Run when entity is added to Home Assistant."""
        await super().async_added_to_hass()

        # Force update entity name in registry if it has changed
        await self._update_entity_registry_name()

    async def _update_entity_registry_name(self) -> None:
        """Update entity name in the entity registry if needed."""
        try:
            from homeassistant.helpers import entity_registry as er

            registry = er.async_get(self.hass)
            entity_entry = registry.async_get(self.entity_id)

            if entity_entry:
                current_name = self._get_entity_name()

                # Check if the name needs to be updated
                if entity_entry.name != current_name:
                    _LOGGER.info(
                        "🔄 UPDATING ENTITY NAME: %s from '%s' to '%s'",
                        self.entity_id, entity_entry.name or "None", current_name
                    )

                    # Update the entity registry
                    registry.async_update_entity(
                        self.entity_id,
                        name=current_name
                    )
                else:
                    _LOGGER.debug(
                        "✅ Entity name already correct: %s = '%s'",
                        self.entity_id, current_name
                    )
            else:
                _LOGGER.debug("Entity not found in registry: %s", self.entity_id)

        except Exception as e:
            _LOGGER.warning("Failed to update entity registry name for %s: %s", self.entity_id, e)

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
        elif (
            self._attributes.get("data_type") == "enum"
            and "options" in self._attributes
        ):
            options = []
            for option in self._attributes["options"]:
                option_text = option.get("text_en", option.get("text", option["value"]))
                options.append(f"{option['value']}: {option_text}")
            attrs["xcc_options"] = options

        return attrs

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        import logging

        _LOGGER = logging.getLogger(__name__)

        # Update entity data from coordinator
        self._entity_data = self.coordinator.get_entity_data(self.entity_id_suffix)
        if self._entity_data:
            self._xcc_data = self._entity_data["data"]
            self._attributes = self._xcc_data.get("attributes", {})


        else:
            _LOGGER.warning(
                "No entity data found for %s during coordinator update",
                self.entity_id_suffix,
            )

        super()._handle_coordinator_update()

    def _get_current_value(self) -> Any:
        """Get the current value from coordinator data."""
        import logging

        _LOGGER = logging.getLogger(__name__)

        entity_type = self._entity_data["type"]

        # Removed excessive debug logging for entity value retrieval

        # Debug coordinator data structure (only log once per update cycle to avoid spam)
        if hasattr(self.coordinator, "data") and self.coordinator.data:
            # Only log coordinator data keys once per update cycle
            if not hasattr(self.__class__, "_logged_coordinator_keys_for_update"):
                self.__class__._logged_coordinator_keys_for_update = set()

            update_id = id(self.coordinator.data)
            if update_id not in self.__class__._logged_coordinator_keys_for_update:
                _LOGGER.debug(
                    "Coordinator data keys: %s", list(self.coordinator.data.keys())
                )
                self.__class__._logged_coordinator_keys_for_update.add(update_id)

                # Clean up old entries to prevent memory leak
                if len(self.__class__._logged_coordinator_keys_for_update) > 5:
                    old_entries = list(
                        self.__class__._logged_coordinator_keys_for_update
                    )[:2]
                    for old_entry in old_entries:
                        self.__class__._logged_coordinator_keys_for_update.discard(
                            old_entry
                        )

            # Handle plural entity type names (sensors, switches, etc.)
            entity_type_plural = (
                f"{entity_type}s" if not entity_type.endswith("s") else entity_type
            )

            if entity_type_plural in self.coordinator.data:
                type_data = self.coordinator.data[entity_type_plural]
                # IMPORTANT: Only log this once per coordinator update to avoid log spam
                # Use a class variable to track if we've already logged this update cycle
                if not hasattr(self.__class__, "_logged_data_keys_for_update"):
                    self.__class__._logged_data_keys_for_update = set()

                update_id = id(
                    self.coordinator.data
                )  # Use data object ID as update identifier
                log_key = f"{entity_type_plural}_{update_id}"

                if log_key not in self.__class__._logged_data_keys_for_update:
                    _LOGGER.debug(
                        "Entity type '%s' data keys: %s",
                        entity_type_plural,
                        list(type_data.keys())
                        if isinstance(type_data, dict)
                        else type(type_data),
                    )
                    self.__class__._logged_data_keys_for_update.add(log_key)

                    # Clean up old entries to prevent memory leak (keep only last 5 updates)
                    if len(self.__class__._logged_data_keys_for_update) > 10:
                        # Remove oldest entries
                        old_entries = list(self.__class__._logged_data_keys_for_update)[
                            :5
                        ]
                        for old_entry in old_entries:
                            self.__class__._logged_data_keys_for_update.discard(
                                old_entry
                            )

                entity_data = (
                    type_data.get(self.entity_id_suffix)
                    if isinstance(type_data, dict)
                    else None
                )
                if entity_data:
                    state_value = entity_data.get("state")
                    # Log value updates occasionally to verify regular updates
                    import random

                    if (
                        random.random() < 0.05
                    ):  # Log ~5% of value retrievals (consistent with numbers/switches)
                        import time

                        timestamp = time.strftime("%H:%M:%S")
                        # Format value with unit if available
                        unit = entity_data.get("attributes", {}).get("unit", "")
                        value_display = (
                            f"{state_value} {unit}".strip()
                            if unit
                            else str(state_value)
                        )
                        _LOGGER.info(
                            "📊 ENTITY VALUE UPDATE [%s]: %s = %s (sensor from coordinator data)",
                            timestamp,
                            self.entity_id,
                            value_display,
                        )
                    return state_value
                _LOGGER.warning(
                    "No entity data found for suffix '%s' in type '%s'",
                    self.entity_id_suffix,
                    entity_type_plural,
                )
                # Debug: show available keys
                if isinstance(type_data, dict) and type_data:
                    _LOGGER.debug(
                        "Available entity keys in %s: %s",
                        entity_type_plural,
                        list(type_data.keys())[:10],
                    )
            else:
                _LOGGER.warning(
                    "Entity type '%s' not found in coordinator data", entity_type_plural
                )
                _LOGGER.debug(
                    "Available coordinator data keys: %s",
                    list(self.coordinator.data.keys()),
                )
        else:
            _LOGGER.warning("No coordinator data available")

        _LOGGER.warning("❌ ENTITY VALUE: %s = None (no data found)", self.entity_id)
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
        if data_type == "numeric":
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
