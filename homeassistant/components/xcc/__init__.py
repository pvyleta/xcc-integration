"""The XCC Heat Pump Controller integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import (
    DOMAIN,
    PLATFORMS,
    CONF_ENTITY_TYPE,
    ENTITY_TYPE_MQTT,
    ENTITY_TYPE_INTEGRATION,
    DEFAULT_ENTITY_TYPE
)
from .coordinator import XCCDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

# Supported platforms
PLATFORMS_TO_SETUP = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
    Platform.NUMBER,
    Platform.SELECT,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up XCC Heat Pump Controller from a config entry."""
    # Log integration version for debugging
    from .const import VERSION
    _LOGGER.info("Setting up XCC integration v%s for %s", VERSION, entry.data.get("ip_address"))
    _LOGGER.debug("Setting up XCC integration for %s", entry.data.get("ip_address"))

    # Create data update coordinator
    coordinator = XCCDataUpdateCoordinator(hass, entry)

    # Fetch initial data so we have data when entities subscribe
    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as err:
        _LOGGER.error("Error during initial data fetch: %s", err)
        raise ConfigEntryNotReady from err

    # Store coordinator in hass data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Get entity type preference from config
    entity_type = entry.data.get(CONF_ENTITY_TYPE, DEFAULT_ENTITY_TYPE)
    _LOGGER.info("XCC integration configured for %s entities", entity_type)

    if entity_type == ENTITY_TYPE_INTEGRATION:
        # Set up integration platforms (sensors, binary_sensors, etc.)
        _LOGGER.debug("Setting up integration entities")
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS_TO_SETUP)
    elif entity_type == ENTITY_TYPE_MQTT:
        # Set up MQTT device discovery only
        _LOGGER.debug("Setting up MQTT entities")
        try:
            if "mqtt" in hass.config.components:
                # Schedule MQTT setup as a background task to avoid blocking startup
                hass.async_create_task(_setup_mqtt_discovery(hass, coordinator))
            else:
                _LOGGER.error("MQTT entity type selected but MQTT not configured in Home Assistant")
                raise ConfigEntryNotReady("MQTT not available but required for selected entity type")
        except Exception as err:
            _LOGGER.error("MQTT discovery setup failed: %s", err)
            raise ConfigEntryNotReady from err
    else:
        _LOGGER.error("Unknown entity type: %s", entity_type)
        raise ConfigEntryNotReady(f"Unknown entity type: {entity_type}")

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unloading XCC integration for %s", entry.data.get("ip_address"))

    # Get coordinator and entity type
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entity_type = entry.data.get(CONF_ENTITY_TYPE, DEFAULT_ENTITY_TYPE)

    unload_ok = True

    if entity_type == ENTITY_TYPE_INTEGRATION:
        # Unload integration platforms
        _LOGGER.debug("Unloading integration entities")
        unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS_TO_SETUP)
    elif entity_type == ENTITY_TYPE_MQTT:
        # Clean up MQTT discovery
        _LOGGER.debug("Cleaning up MQTT entities")
        if hasattr(coordinator, 'mqtt_discovery') and coordinator.mqtt_discovery:
            try:
                await coordinator.mqtt_discovery.async_remove()
            except Exception as err:
                _LOGGER.error("Error cleaning up MQTT discovery: %s", err)

    # Remove coordinator from hass data
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def _setup_mqtt_discovery(hass: HomeAssistant, coordinator: XCCDataUpdateCoordinator) -> None:
    """Set up MQTT device discovery for XCC entities."""
    try:
        # Check if MQTT component is loaded
        if "mqtt" not in hass.config.components:
            _LOGGER.debug("MQTT component not loaded, skipping MQTT discovery")
            return

        from .mqtt_discovery import XCCMQTTDiscovery

        _LOGGER.debug("Setting up MQTT discovery for XCC controller")

        # Create and setup MQTT discovery
        mqtt_discovery = XCCMQTTDiscovery(hass, coordinator)
        success = await mqtt_discovery.async_setup()

        if success:
            # Store discovery instance for cleanup
            coordinator.mqtt_discovery = mqtt_discovery
            _LOGGER.info("MQTT discovery setup successful for XCC controller %s", coordinator.ip_address)
        else:
            _LOGGER.warning("MQTT discovery setup failed for XCC controller %s", coordinator.ip_address)

    except ImportError as err:
        _LOGGER.debug("MQTT component not available, skipping MQTT discovery: %s", err)
    except Exception as err:
        _LOGGER.warning("Error setting up MQTT discovery, continuing without MQTT: %s", err)



