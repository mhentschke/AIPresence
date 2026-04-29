"""Sensor platform for AIPresence integration."""

from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import AIPresenceCoordinator
from .device_tracker import _device_model

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up AIPresence sensor entities from a config entry."""
    coordinator: AIPresenceCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Track which device IDs already have sensor entities
    tracked_device_ids: set[str] = set(coordinator.devices.keys())

    entities: list[SensorEntity] = []
    for device_id, device in coordinator.devices.items():
        entities.append(AIPresenceConfidenceSensor(coordinator, device_id, device))
        entities.append(AIPresenceRoomSensor(coordinator, device_id, device))

    async_add_entities(entities)

    @callback
    def _async_handle_coordinator_update() -> None:
        """Add/remove sensor entities when devices change."""
        if coordinator.added_devices:
            new_entities: list[SensorEntity] = []
            for device_id in coordinator.added_devices:
                if device_id not in tracked_device_ids:
                    device = coordinator.devices[device_id]
                    new_entities.append(AIPresenceConfidenceSensor(coordinator, device_id, device))
                    new_entities.append(AIPresenceRoomSensor(coordinator, device_id, device))
                    tracked_device_ids.add(device_id)
            if new_entities:
                async_add_entities(new_entities)
                _LOGGER.debug("Added %d new sensor entities", len(new_entities))

        if coordinator.removed_devices:
            ent_reg = er.async_get(hass)
            for device_id in coordinator.removed_devices:
                for suffix in ("confidence", "room"):
                    unique_id = f"{DOMAIN}_{device_id}_{suffix}"
                    entity_id = ent_reg.async_get_entity_id("sensor", DOMAIN, unique_id)
                    if entity_id:
                        ent_reg.async_remove(entity_id)
                        _LOGGER.debug("Removed sensor entity %s", entity_id)
                tracked_device_ids.discard(device_id)

    coordinator.async_add_listener(_async_handle_coordinator_update)


class AIPresenceConfidenceSensor(CoordinatorEntity, SensorEntity):
    """Sensor reporting the prediction confidence for an AIPresence device."""

    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: AIPresenceCoordinator,
        device_id: str,
        device: dict,
    ) -> None:
        """Initialise the confidence sensor."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._device = device
        self._attr_unique_id = f"{DOMAIN}_{device_id}_confidence"
        self._attr_name = "Confidence"

    @property
    def device_info(self):
        """Return device info to link to the same HA device as the tracker."""
        return {
            "identifiers": {(DOMAIN, self._device_id)},
            "name": self._device.get("name", self._device_id),
            "manufacturer": "AIPresence",
            "model": _device_model(self._device),
        }

    @property
    def native_value(self) -> float | None:
        """Return the confidence percentage, or None for unknown."""
        prediction = self.coordinator.predictions.get(self._device_id)
        if prediction and "confidence" in prediction:
            return round(prediction["confidence"] * 100, 1)
        return None


class AIPresenceRoomSensor(CoordinatorEntity, SensorEntity):
    """Sensor reporting the predicted room name for an AIPresence device."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: AIPresenceCoordinator,
        device_id: str,
        device: dict,
    ) -> None:
        """Initialise the room sensor."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._device = device
        self._attr_unique_id = f"{DOMAIN}_{device_id}_room"
        self._attr_name = "Room"

    @property
    def device_info(self):
        """Return device info to link to the same HA device as the tracker."""
        return {
            "identifiers": {(DOMAIN, self._device_id)},
            "name": self._device.get("name", self._device_id),
            "manufacturer": "AIPresence",
            "model": _device_model(self._device),
        }

    @property
    def native_value(self) -> str | None:
        """Return the predicted room name, or None for unknown."""
        prediction = self.coordinator.predictions.get(self._device_id)
        if prediction and "room_name" in prediction:
            return prediction["room_name"]
        return None
