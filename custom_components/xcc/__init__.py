"""The XCC Heat Pump Controller integration."""

from __future__ import annotations

import asyncio
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
    from homeassistant.helpers import device_registry as dr

    _LOGGER.info(
        "Setting up XCC integration v%s for %s", VERSION, entry.data.get("ip_address")
    )
    _LOGGER.debug("Setting up XCC integration for %s", entry.data.get("ip_address"))

    # Create data update coordinator
    coordinator = XCCDataUpdateCoordinator(hass, entry)

    # Store coordinator in hass data BEFORE first refresh
    # This allows the coordinator to be accessed during setup
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Fetch initial data BEFORE setting up platforms
    # This ensures data is available when entities are created
    # If this fails, we raise ConfigEntryNotReady to retry later
    try:
        _LOGGER.debug("Performing initial data fetch before platform setup")
        await coordinator.async_config_entry_first_refresh()
        _LOGGER.info("✅ Initial data fetch successful")
    except asyncio.TimeoutError as err:
        _LOGGER.error("Timeout during initial data fetch: %s", err)
        # Clean up coordinator from hass data
        hass.data[DOMAIN].pop(entry.entry_id)
        raise ConfigEntryNotReady(f"Timeout fetching initial data: {err}") from err
    except asyncio.CancelledError as err:
        _LOGGER.error("Request cancelled during initial data fetch: %s", err)
        # Clean up coordinator from hass data
        hass.data[DOMAIN].pop(entry.entry_id)
        raise ConfigEntryNotReady(f"Request cancelled during initial data fetch: {err}") from err
    except Exception as err:
        _LOGGER.error("Error during initial data fetch: %s", err)
        # Clean up coordinator from hass data
        hass.data[DOMAIN].pop(entry.entry_id)
        raise ConfigEntryNotReady(f"Error fetching initial data: {err}") from err

    # Register the main XCC controller device BEFORE setting up platforms
    # This ensures the device exists when sub-devices try to reference it via via_device
    device_registry = dr.async_get(hass)
    if coordinator.device_info:
        _LOGGER.debug("Registering main XCC controller device in device registry")
        device_registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            identifiers=coordinator.device_info["identifiers"],
            name=coordinator.device_info["name"],
            manufacturer=coordinator.device_info["manufacturer"],
            model=coordinator.device_info["model"],
            sw_version=coordinator.device_info.get("sw_version"),
            configuration_url=coordinator.device_info.get("configuration_url"),
        )
        _LOGGER.info("✅ Main XCC controller device registered")
    else:
        _LOGGER.warning("⚠️  Coordinator device_info not available, device registration skipped")

    # Get entity type preference from config
    entity_type = entry.data.get(CONF_ENTITY_TYPE, DEFAULT_ENTITY_TYPE)
    _LOGGER.info("XCC integration configured for %s entities", entity_type)

    # Set up integration platforms (sensors, binary_sensors, etc.)
    # Only do this AFTER we have successfully fetched initial data AND registered the main device
    _LOGGER.debug("Setting up integration entities")
    _LOGGER.info("Setting up platforms: %s", [p.value for p in PLATFORMS_TO_SETUP])
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS_TO_SETUP)

    _LOGGER.info("✅ XCC integration setup complete for %s", entry.data.get("ip_address"))

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
