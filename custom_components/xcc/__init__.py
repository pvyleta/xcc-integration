"""The XCC Heat Pump Controller integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import (
    CONF_ENTITY_TYPE,
    DEFAULT_ENTITY_TYPE,
    DOMAIN,
    ENTITY_TYPE_INTEGRATION,
    PLATFORMS,
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
    Platform.BUTTON,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up XCC Heat Pump Controller from a config entry."""
    # Log integration version for debugging
    from .const import VERSION

    _LOGGER.info(
        "Setting up XCC integration v%s for %s", VERSION, entry.data.get("ip_address")
    )
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

    # Set up integration platforms (sensors, binary_sensors, etc.)
    _LOGGER.debug("Setting up integration entities")
    _LOGGER.info("Setting up platforms: %s", [p.value for p in PLATFORMS_TO_SETUP])
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS_TO_SETUP)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unloading XCC integration for %s", entry.data.get("ip_address"))

    # Get coordinator and entity type
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entity_type = entry.data.get(CONF_ENTITY_TYPE, DEFAULT_ENTITY_TYPE)

    unload_ok = True

    # Unload integration platforms
    _LOGGER.debug("Unloading integration entities")
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, PLATFORMS_TO_SETUP
    )

    # Clean up coordinator resources
    try:
        await coordinator.async_shutdown()
    except Exception as err:
        _LOGGER.error("Error shutting down coordinator: %s", err)

    # Remove coordinator from hass data
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
