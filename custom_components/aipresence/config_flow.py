"""Config flow for AIPresence integration."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_BACKEND_URL,
    CONF_BEACON_TIMEOUT,
    CONF_SCAN_INTERVAL,
    DEFAULT_BEACON_TIMEOUT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

ADDON_SLUG_SUFFIX = "aipresence"
ADDON_PORT = 8099
VALIDATE_TIMEOUT = 5  # seconds
MIN_BEACON_TIMEOUT = 5
MAX_BEACON_TIMEOUT = 120


async def _async_validate_backend(url: str) -> bool:
    """Validate connectivity to the AIPresence backend."""
    try:
        timeout = aiohttp.ClientTimeout(total=VALIDATE_TIMEOUT)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(f"{url.rstrip('/')}/devices") as resp:
                return resp.status == 200
    except (aiohttp.ClientError, TimeoutError, OSError):
        return False


async def _async_discover_addon(hass) -> str | None:
    """Try to discover the AIPresence add-on via the Supervisor API.

    The add-on slug varies depending on install source (local vs GitHub
    repository), so we search for any installed add-on whose slug ends
    with ``aipresence``.
    """
    try:
        if "hassio" not in hass.config.components:
            _LOGGER.warning("Add-on discovery: hassio not in components")
            return None

        from homeassistant.components.hassio import get_supervisor_client

        client = get_supervisor_client(hass)

        # List all installed add-ons and find ours by slug suffix
        store_info = await client.store.info()
        addon_slug: str | None = None
        for addon in getattr(store_info, "addons", []):
            slug = getattr(addon, "slug", "")
            if slug.endswith(ADDON_SLUG_SUFFIX) and getattr(addon, "installed", False):
                addon_slug = slug
                break

        if addon_slug is None:
            # Fallback: try the local slug directly
            addon_slug = f"local_{ADDON_SLUG_SUFFIX}"
            _LOGGER.debug("Add-on discovery: no installed add-on found by suffix, trying %s", addon_slug)

        addon_info = await client.addons.addon_info(addon_slug)

        state = getattr(addon_info, "state", None)
        _LOGGER.debug("Add-on discovery: addon %s state = %s", addon_slug, state)

        if state is None:
            _LOGGER.warning("Add-on discovery: could not read addon state")
            return None

        state_str = state.value if hasattr(state, "value") else str(state)
        if state_str != "started":
            _LOGGER.warning("Add-on discovery: addon state is %s, not started", state_str)
            return None

        hostname = getattr(addon_info, "hostname", None) or addon_slug.replace("_", "-")
        url = f"http://{hostname}:{ADDON_PORT}"
        _LOGGER.info("Add-on discovery: found AIPresence at %s", url)
        return url
    except Exception:  # noqa: BLE001
        _LOGGER.warning("Add-on auto-discovery failed", exc_info=True)
        return None


class AIPresenceConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for AIPresence."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialise the config flow."""
        self._discovered_url: str | None = None

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Handle the initial step — auto-discover or manual URL entry."""
        errors: dict[str, str] = {}

        if user_input is not None:
            url = user_input[CONF_BACKEND_URL].rstrip("/")
            if await _async_validate_backend(url):
                return self.async_create_entry(
                    title="AIPresence",
                    data={CONF_BACKEND_URL: url},
                )
            errors["base"] = "cannot_connect"
        else:
            # Attempt add-on auto-discovery on first load
            self._discovered_url = await _async_discover_addon(self.hass)

        default_url = ""
        if user_input and CONF_BACKEND_URL in user_input:
            default_url = user_input[CONF_BACKEND_URL]
        elif self._discovered_url:
            default_url = self._discovered_url

        schema = vol.Schema(
            {
                vol.Required(CONF_BACKEND_URL, default=default_url): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Return the options flow handler."""
        return AIPresenceOptionsFlow(config_entry)


class AIPresenceOptionsFlow(OptionsFlow):
    """Handle options for AIPresence."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialise options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_scan = self.config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        current_timeout = self.config_entry.options.get(CONF_BEACON_TIMEOUT, DEFAULT_BEACON_TIMEOUT)

        schema = vol.Schema(
            {
                vol.Required(CONF_SCAN_INTERVAL, default=current_scan): vol.All(
                    vol.Coerce(int),
                    vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL),
                ),
                vol.Required(CONF_BEACON_TIMEOUT, default=current_timeout): vol.All(
                    vol.Coerce(int),
                    vol.Range(min=MIN_BEACON_TIMEOUT, max=MAX_BEACON_TIMEOUT),
                ),
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
