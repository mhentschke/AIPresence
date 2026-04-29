"""Device tracker platform for AIPresence integration."""

from __future__ import annotations

import logging

from homeassistant.components.device_tracker import SourceType, TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
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

    # Track which device IDs already have entities
    tracked_device_ids: set[str] = set(coordinator.devices.keys())

    entities = [
        AIPresenceDeviceTracker(coordinator, device_id, device) for device_id, device in coordinator.devices.items()
    ]
    async_add_entities(entities)

    @callback
    def _async_handle_coordinator_update() -> None:
        """Add/remove device tracker entities when devices change."""
        if coordinator.added_devices:
            new_entities = [
                AIPresenceDeviceTracker(coordinator, device_id, coordinator.devices[device_id])
                for device_id in coordinator.added_devices
                if device_id not in tracked_device_ids
            ]
            if new_entities:
                for ent in new_entities:
                    tracked_device_ids.add(ent.device_id_aipresence)
                async_add_entities(new_entities)
                _LOGGER.debug("Added %d new device tracker entities", len(new_entities))

        if coordinator.removed_devices:
            ent_reg = er.async_get(hass)
            for device_id in coordinator.removed_devices:
                unique_id = f"{DOMAIN}_{device_id}_tracker"
                entity_id = ent_reg.async_get_entity_id("device_tracker", DOMAIN, unique_id)
                if entity_id:
                    ent_reg.async_remove(entity_id)
                    _LOGGER.debug("Removed device tracker entity %s", entity_id)
                tracked_device_ids.discard(device_id)

    coordinator.async_add_listener(_async_handle_coordinator_update)


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
    def device_id_aipresence(self) -> str:
        """Return the AIPresence device ID (not the HA device_id)."""
        return self._device_id

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
