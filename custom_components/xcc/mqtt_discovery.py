"""MQTT Discovery support for XCC Heat Pump Controller integration."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN, MQTT_DEVICE_PREFIX, MQTT_DISCOVERY_PREFIX
from .coordinator import XCCDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


class XCCMQTTDiscovery:
    """Handle MQTT discovery for XCC entities."""

    def __init__(self, hass: HomeAssistant, coordinator: XCCDataUpdateCoordinator) -> None:
        """Initialize MQTT discovery."""
        self.hass = hass
        self.coordinator = coordinator
        self.ip_address = coordinator.ip_address
        self.device_id = f"{MQTT_DEVICE_PREFIX}_{self.ip_address.replace('.', '_')}"
        self._published_entities: set[str] = set()
        self._mqtt = None  # Will be set during async_setup

    async def async_setup(self) -> bool:
        """Set up MQTT discovery."""
        try:
            # Check if MQTT component is available
            try:
                from homeassistant.components import mqtt
                self._mqtt = mqtt  # Store reference for later use
            except ImportError:
                _LOGGER.debug("MQTT component not available")
                return False

            # Wait for MQTT to be available
            if not await mqtt.async_wait_for_mqtt_client(self.hass):
                _LOGGER.warning("MQTT client not available, skipping MQTT discovery setup")
                return False

            # Publish device discovery
            await self._publish_device_discovery()

            # Publish entity discoveries
            await self._publish_entity_discoveries()

            # Set up periodic updates
            self._setup_periodic_updates()

            _LOGGER.info("MQTT discovery setup completed for XCC controller %s", self.ip_address)
            return True

        except Exception as err:
            _LOGGER.error("Error setting up MQTT discovery: %s", err)
            return False

    async def _publish_device_discovery(self) -> None:
        """Publish device discovery message."""
        device_info = self.coordinator.device_info
        
        device_payload = {
            "identifiers": [self.device_id],
            "name": device_info["name"],
            "manufacturer": device_info["manufacturer"],
            "model": device_info["model"],
            "sw_version": device_info.get("sw_version", "Unknown"),
            "configuration_url": device_info.get("configuration_url"),
        }

        # Publish device availability
        availability_topic = f"{MQTT_DEVICE_PREFIX}/{self.ip_address}/availability"
        await self._mqtt.async_publish(
            self.hass,
            availability_topic,
            "online",
            retain=True,
        )

        _LOGGER.debug("Published device discovery for %s", self.device_id)

    async def _publish_entity_discoveries(self) -> None:
        """Publish entity discovery messages."""
        for entity_id, entity_data in self.coordinator.entities.items():
            try:
                await self._publish_entity_discovery(entity_id, entity_data)
            except Exception as err:
                _LOGGER.error("Error publishing discovery for entity %s: %s", entity_id, err)

    async def _publish_entity_discovery(self, entity_id: str, entity_data: dict[str, Any]) -> None:
        """Publish discovery message for a single entity."""
        entity_info = entity_data["data"]
        entity_type = entity_data["type"]
        
        # Map entity type to MQTT discovery component
        mqtt_component = self._get_mqtt_component_for_entity_type(entity_type)
        if not mqtt_component:
            _LOGGER.debug("Skipping entity %s with unsupported type %s", entity_id, entity_type)
            return

        # Create discovery topic and payload
        discovery_topic = f"{MQTT_DISCOVERY_PREFIX}/{mqtt_component}/{self.device_id}/{entity_id}/config"
        
        # Base entity payload
        entity_payload = {
            "unique_id": f"{self.device_id}_{entity_id}",
            "name": self._get_entity_name(entity_info),
            "device": {
                "identifiers": [self.device_id],
                "name": self.coordinator.device_info["name"],
                "manufacturer": self.coordinator.device_info["manufacturer"],
                "model": self.coordinator.device_info["model"],
                "configuration_url": self.coordinator.device_info.get("configuration_url"),
            },
            "state_topic": f"{MQTT_DEVICE_PREFIX}/{self.ip_address}/{entity_id}/state",
            "availability_topic": f"{MQTT_DEVICE_PREFIX}/{self.ip_address}/availability",
            "payload_available": "online",
            "payload_not_available": "offline",
        }

        # Add entity-specific configuration
        self._add_entity_specific_mqtt_config(entity_payload, entity_info, entity_type)

        # Publish discovery message
        await self._mqtt.async_publish(
            self.hass,
            discovery_topic,
            json.dumps(entity_payload, separators=(',', ':')),
            retain=True,
        )

        # Publish initial state
        await self._publish_entity_state(entity_id, entity_info)

        self._published_entities.add(entity_id)
        _LOGGER.debug("Published discovery for entity %s as %s", entity_id, mqtt_component)

    async def _publish_entity_state(self, entity_id: str, entity_info: dict[str, Any]) -> None:
        """Publish current state for an entity."""
        state_topic = f"{MQTT_DEVICE_PREFIX}/{self.ip_address}/{entity_id}/state"
        state_value = entity_info.get("state", "unknown")
        
        await self._mqtt.async_publish(
            self.hass,
            state_topic,
            str(state_value),
            retain=True,
        )

    def _get_mqtt_component_for_entity_type(self, entity_type: str) -> str | None:
        """Get MQTT discovery component name for entity type."""
        mapping = {
            "sensors": "sensor",
            "binary_sensors": "binary_sensor",
            "switches": "switch",
            "numbers": "number",
            "selects": "select",
        }
        return mapping.get(entity_type)

    def _get_entity_name(self, entity_info: dict[str, Any]) -> str:
        """Get localized entity name."""
        attributes = entity_info.get("attributes", {})
        
        # Get language preference
        hass_language = self.hass.config.language if self.hass else "en"
        use_czech = hass_language.startswith("cs") or hass_language.startswith("cz")
        
        if use_czech:
            name = attributes.get("friendly_name", attributes.get("friendly_name_en", ""))
        else:
            name = attributes.get("friendly_name_en", attributes.get("friendly_name", ""))
        
        return name or attributes.get("field_name", "Unknown")

    def _add_entity_specific_mqtt_config(
        self, payload: dict, entity_info: dict, entity_type: str
    ) -> None:
        """Add entity-specific MQTT configuration."""
        attributes = entity_info.get("attributes", {})
        
        # Add unit of measurement if available
        if "unit" in attributes:
            payload["unit_of_measurement"] = attributes["unit"]
        
        # Add device class if available
        if "device_class" in attributes:
            payload["device_class"] = attributes["device_class"]
        
        # Add state class for sensors
        if entity_type == "sensors" and "state_class" in attributes:
            payload["state_class"] = attributes["state_class"]
        
        # Add options for select entities
        if entity_type == "selects" and "options" in attributes:
            hass_language = self.hass.config.language if self.hass else "en"
            use_czech = hass_language.startswith("cs") or hass_language.startswith("cz")
            
            options = []
            for opt in attributes["options"]:
                if use_czech:
                    text = opt.get("text", opt.get("text_en", opt["value"]))
                else:
                    text = opt.get("text_en", opt.get("text", opt["value"]))
                options.append(text)
            payload["options"] = options
        
        # Add min/max for number entities
        if entity_type == "numbers":
            if "min_value" in attributes:
                payload["min"] = attributes["min_value"]
            if "max_value" in attributes:
                payload["max"] = attributes["max_value"]
            if "step" in attributes:
                payload["step"] = attributes["step"]
            else:
                payload["step"] = 1  # Default step

        # Add command topic for settable entities
        if attributes.get("is_settable", False):
            payload["command_topic"] = f"{MQTT_DEVICE_PREFIX}/{self.ip_address}/{entity_info.get('attributes', {}).get('field_name', 'unknown')}/set"

    @callback
    def _setup_periodic_updates(self) -> None:
        """Set up periodic state updates."""
        async def update_states():
            """Update all entity states."""
            for entity_id in self._published_entities:
                entity_data = self.coordinator.get_entity_data(entity_id)
                if entity_data:
                    await self._publish_entity_state(entity_id, entity_data["data"])

        # Schedule periodic updates
        self.hass.async_create_task(self._periodic_update_loop(update_states))

    async def _periodic_update_loop(self, update_func) -> None:
        """Run periodic updates."""
        while True:
            try:
                await asyncio.sleep(self.coordinator.update_interval.total_seconds())
                await update_func()
            except Exception as err:
                _LOGGER.error("Error in periodic MQTT update: %s", err)
                await asyncio.sleep(60)  # Wait before retrying

    async def async_remove(self) -> None:
        """Remove MQTT discovery messages."""
        for entity_id in self._published_entities:
            entity_data = self.coordinator.get_entity_data(entity_id)
            if entity_data:
                entity_type = entity_data["type"]
                mqtt_component = self._get_mqtt_component_for_entity_type(entity_type)
                if mqtt_component:
                    discovery_topic = f"{MQTT_DISCOVERY_PREFIX}/{mqtt_component}/{self.device_id}/{entity_id}/config"
                    await self._mqtt.async_publish(self.hass, discovery_topic, "", retain=True)

        # Remove availability
        availability_topic = f"{MQTT_DEVICE_PREFIX}/{self.ip_address}/availability"
        await self._mqtt.async_publish(self.hass, availability_topic, "offline", retain=True)

        _LOGGER.info("Removed MQTT discovery for XCC controller %s", self.ip_address)
