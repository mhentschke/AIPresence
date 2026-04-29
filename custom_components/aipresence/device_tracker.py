"""Device tracker platform for AIPresence integration."""

from __future__ import annotations

import logging

from homeassistant.components.device_tracker import SourceType, TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import AIPresenceCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up AIPresence device tracker entities from a config entry."""
    coordinator: AIPresenceCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        AIPresenceDeviceTracker(coordinator, device_id, device) for device_id, device in coordinator.devices.items()
    ]
    async_add_entities(entities)


def _device_model(device: dict) -> str:
    """Derive the HA device model string from the backend device data."""
    has_entity = bool(device.get("entity_id"))
    has_beacon = bool(device.get("beacon_id"))
    if has_entity and has_beacon:
        return "Both"
    if has_entity:
        return "Monitor"
    return "Beacon"


class AIPresenceDeviceTracker(CoordinatorEntity, TrackerEntity):
    """Represent an AIPresence tracked device as a device_tracker entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: AIPresenceCoordinator,
        device_id: str,
        device: dict,
    ) -> None:
        """Initialise the device tracker."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._device = device
        self._attr_unique_id = f"{DOMAIN}_{device_id}_tracker"
        self._attr_name = "Tracker"

    @property
    def device_info(self):
        """Return device info to link this entity to the HA device registry."""
        return {
            "identifiers": {(DOMAIN, self._device_id)},
            "name": self._device.get("name", self._device_id),
            "manufacturer": "AIPresence",
            "model": _device_model(self._device),
        }

    @property
    def source_type(self) -> SourceType:
        """Return the source type of the tracker."""
        return SourceType.BLUETOOTH

    @property
    def location_name(self) -> str | None:
        """Return the predicted room name, or None for unknown."""
        prediction = self.coordinator.predictions.get(self._device_id)
        if prediction and "room_name" in prediction:
            return prediction["room_name"]
        return None

    @property
    def extra_state_attributes(self) -> dict | None:
        """Return per-room probabilities as extra attributes."""
        prediction = self.coordinator.predictions.get(self._device_id)
        if prediction is None:
            return None
        return {k: v for k, v in prediction.items() if k.startswith("room_") and k != "room_name"}
