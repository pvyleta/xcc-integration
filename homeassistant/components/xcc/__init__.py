"""The XCC Heat Pump Controller integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN, PLATFORMS
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

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS_TO_SETUP)

    # Set up MQTT device discovery if MQTT is available (non-blocking)
    try:
        if "mqtt" in hass.config.components:
            # Schedule MQTT setup as a background task to avoid blocking startup
            hass.async_create_task(_setup_mqtt_discovery(hass, coordinator))
        else:
            _LOGGER.debug("MQTT not configured, skipping MQTT discovery")
    except Exception as err:
        _LOGGER.warning("MQTT discovery setup failed, continuing without MQTT: %s", err)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unloading XCC integration for %s", entry.data.get("ip_address"))

    # Get coordinator
    coordinator = hass.data[DOMAIN][entry.entry_id]

    # Clean up MQTT discovery if it exists
    if hasattr(coordinator, 'mqtt_discovery') and coordinator.mqtt_discovery:
        try:
            await coordinator.mqtt_discovery.async_remove()
        except Exception as err:
            _LOGGER.error("Error cleaning up MQTT discovery: %s", err)

    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS_TO_SETUP)

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



