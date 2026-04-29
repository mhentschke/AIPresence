"""The AIPresence integration."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DOMAIN
from .coordinator import AIPresenceCoordinator
from .scanner import async_setup_scanner

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.DEVICE_TRACKER, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up AIPresence from a config entry."""
    coordinator = AIPresenceCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # Set up BLE scanner before forwarding platforms so sensor.py can wire
    # scanner entity callbacks during its async_setup_entry.
    await async_setup_scanner(hass, entry)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(_async_options_updated))

    return True


async def _async_options_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options flow changes — update coordinator polling interval."""
    coordinator: AIPresenceCoordinator = hass.data[DOMAIN][entry.entry_id]
    new_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    coordinator.update_interval = timedelta(seconds=new_interval)
    _LOGGER.debug("AIPresence polling interval updated to %s seconds", new_interval)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload an AIPresence config entry."""
    # Unload BLE scanner
    scanner_key = entry.entry_id + "_scanner"
    scanner_manager = hass.data.get(DOMAIN, {}).get(scanner_key)
    if scanner_manager is not None:
        await scanner_manager.async_unload()
        hass.data[DOMAIN].pop(scanner_key, None)

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
