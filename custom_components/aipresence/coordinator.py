"""DataUpdateCoordinator for the AIPresence integration."""

from __future__ import annotations

import logging
from datetime import timedelta

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_BACKEND_URL, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)

REQUEST_TIMEOUT = 10  # seconds


class AIPresenceCoordinator(DataUpdateCoordinator):
    """Polls the AIPresence backend for device predictions."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialise the coordinator."""
        self.backend_url: str = entry.data[CONF_BACKEND_URL]
        self.session = async_get_clientsession(hass)
        interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=interval),
        )

        self.devices: dict[str, dict] = {}
        self.predictions: dict[str, dict | None] = {}
        self.added_devices: set[str] = set()
        self.removed_devices: set[str] = set()

    async def _async_update_data(self) -> dict:
        """Fetch devices, predictions, and rooms from the backend."""
        timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
        try:
            async with self.session.get(f"{self.backend_url}/devices", timeout=timeout) as devices_resp:
                devices_resp.raise_for_status()
                devices_json = await devices_resp.json()

            async with self.session.get(f"{self.backend_url}/devices/location", timeout=timeout) as locations_resp:
                locations_resp.raise_for_status()
                locations_json = await locations_resp.json()

            async with self.session.get(f"{self.backend_url}/rooms", timeout=timeout) as rooms_resp:
                rooms_resp.raise_for_status()
                rooms_json = await rooms_resp.json()
        except (aiohttp.ClientError, TimeoutError) as err:
            raise UpdateFailed(f"Error communicating with AIPresence backend: {err}") from err

        # Build room ID → name lookup
        rooms: dict[str, str] = {r["id"]: r["name"] for r in rooms_json}

        # Build device and prediction dicts
        new_devices: dict[str, dict] = {}
        new_predictions: dict[str, dict | None] = {}

        for device in devices_json:
            did = device["id"]
            new_devices[did] = device
            pred = locations_json.get(did)
            if pred and "room" in pred:
                pred["room_name"] = rooms.get(pred["room"], pred["room"])
            new_predictions[did] = pred

        # Detect additions and removals
        old_ids = set(self.devices.keys())
        new_ids = set(new_devices.keys())
        self.added_devices = new_ids - old_ids
        self.removed_devices = old_ids - new_ids

        self.devices = new_devices
        self.predictions = new_predictions

        return {"devices": new_devices, "predictions": new_predictions}
