"""Config flow for XCC Heat Pump Controller integration."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_IP_ADDRESS, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError

from .const import (
    CONF_ENTITY_TYPE,
    CONF_LANGUAGE,
    CONF_REGENERATE_ENTITY_IDS,
    CONF_SCAN_INTERVAL,
    DEFAULT_LANGUAGE,
    DEFAULT_PASSWORD,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
    DEFAULT_USERNAME,
    DOMAIN,
    ENTITY_TYPE_INTEGRATION,
    LANGUAGE_CZECH,
    LANGUAGE_ENGLISH,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_IP_ADDRESS): str,
        vol.Optional(CONF_USERNAME, default=DEFAULT_USERNAME): str,
        vol.Optional(CONF_PASSWORD, default=DEFAULT_PASSWORD): str,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
            vol.Coerce(int),
            vol.Range(min=10, max=3600),
        ),
        vol.Optional(CONF_LANGUAGE, default=DEFAULT_LANGUAGE): vol.In([
            LANGUAGE_ENGLISH,
            LANGUAGE_CZECH,
        ]),
        # Off by default so a remove+re-add of the integration preserves any
        # entity_ids still held in HA's ``deleted_entities`` registry (and
        # therefore the recorder history attached to those entity_id strings).
        # Tick to rewrite legacy IP-baked ids to the canonical ``xcc_*`` form.
        vol.Optional(CONF_REGENERATE_ENTITY_IDS, default=False): bool,
    },
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    # Import XCC client from the integration package
    try:
        from .xcc_client import XCCClient
    except ImportError as err:
        raise CannotConnect("XCC client library not available") from err

    ip_address = data[CONF_IP_ADDRESS]
    username = data[CONF_USERNAME]
    password = data[CONF_PASSWORD]

    # Test connection to XCC controller
    try:
        async with XCCClient(
            ip=ip_address,
            username=username,
            password=password,
        ) as client:
            # Try to fetch a basic page to validate connection
            await asyncio.wait_for(
                client.fetch_page("stavjed.xml"),
                timeout=DEFAULT_TIMEOUT,
            )
    except TimeoutError as err:
        raise CannotConnect("Connection timeout") from err
    except aiohttp.ClientError as err:
        raise CannotConnect("Connection failed") from err
    except Exception as err:
        _LOGGER.exception("Unexpected error connecting to XCC controller")
        raise CannotConnect("Unexpected error") from err

    # Return info that you want to store in the config entry.
    return {
        "title": f"XCC Controller ({ip_address})",
        "ip_address": ip_address,
        "username": username,
        "password": password,
        "scan_interval": data[CONF_SCAN_INTERVAL],
    }


class XCCConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for XCC Heat Pump Controller."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Return the options flow handler."""
        return XCCOptionsFlowHandler(config_entry)

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                # Check if already configured
                await self.async_set_unique_id(user_input[CONF_IP_ADDRESS])
                self._abort_if_unique_id_configured()

                # Force entity type to integration (MQTT option removed)
                config_data = user_input.copy()
                config_data[CONF_ENTITY_TYPE] = ENTITY_TYPE_INTEGRATION
                return self.async_create_entry(title=info["title"], data=config_data)

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )


class XCCOptionsFlowHandler(OptionsFlow):
    """Handle options for the XCC integration."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Store the config entry for option lookups."""
        self.config_entry = config_entry

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Show the single options step.

        The only option today is ``regenerate_entity_ids``: when submitted as
        true, ``async_setup_entry`` will sweep the entity registry on the next
        reload, rename legacy IP-baked ids to the canonical ``xcc_<suffix>``
        form, and drop any stale duplicates. The flag is cleared after the
        sweep so it behaves as a one-shot trigger.
        """
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_scan = self.config_entry.options.get(
            CONF_SCAN_INTERVAL,
            self.config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        )
        schema = vol.Schema(
            {
                vol.Optional(CONF_SCAN_INTERVAL, default=current_scan): vol.All(
                    vol.Coerce(int),
                    vol.Range(min=10, max=3600),
                ),
                vol.Optional(CONF_REGENERATE_ENTITY_IDS, default=False): bool,
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
