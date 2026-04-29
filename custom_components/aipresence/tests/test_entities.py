"""Tests for AIPresence prediction entity platforms (device_tracker + sensors)."""

from __future__ import annotations

from unittest.mock import MagicMock

from custom_components.aipresence.const import DOMAIN
from custom_components.aipresence.device_tracker import (
    AIPresenceDeviceTracker,
    _device_model,
)
from custom_components.aipresence.sensor import (
    AIPresenceConfidenceSensor,
    AIPresenceRoomSensor,
)

# ---------------------------------------------------------------------------
# Shared test data
# ---------------------------------------------------------------------------

BACKEND_URL = "http://localhost:5000"

DEVICE_MONITOR = {
    "id": "dev-1",
    "name": "Phone A",
    "entity_id": "sensor.phone_a_beacon_monitor",
    "beacon_id": "uuid_a",
    "model": None,
}

DEVICE_BEACON_ONLY = {
    "id": "dev-2",
    "name": "Beacon B",
    "entity_id": None,
    "beacon_id": "uuid_b",
    "model": None,
}

DEVICE_MONITOR_ONLY = {
    "id": "dev-3",
    "name": "Tablet C",
    "entity_id": "sensor.tablet_c_beacon_monitor",
    "beacon_id": None,
    "model": None,
}

PREDICTION_DEV1 = {
    "room": "room-1",
    "room_name": "Office",
    "confidence": 0.87,
    "room_room-1": 0.87,
    "room_room-2": 0.13,
}


def _make_coordinator(devices: dict, predictions: dict):
    """Create a minimal mock coordinator with the given data."""
    coordinator = MagicMock()
    coordinator.devices = devices
    coordinator.predictions = predictions
    return coordinator


# ---------------------------------------------------------------------------
# _device_model helper
# ---------------------------------------------------------------------------


def test_device_model_both():
    assert _device_model(DEVICE_MONITOR) == "Both"


def test_device_model_beacon_only():
    assert _device_model(DEVICE_BEACON_ONLY) == "Beacon"


def test_device_model_monitor_only():
    assert _device_model(DEVICE_MONITOR_ONLY) == "Monitor"


# ---------------------------------------------------------------------------
# Device tracker tests
# ---------------------------------------------------------------------------


def test_tracker_state_with_prediction():
    """Tracker location_name returns the predicted room name."""
    coordinator = _make_coordinator(
        {"dev-1": DEVICE_MONITOR},
        {"dev-1": PREDICTION_DEV1},
    )
    tracker = AIPresenceDeviceTracker(coordinator, "dev-1", DEVICE_MONITOR)

    assert tracker.location_name == "Office"


def test_tracker_state_unknown_when_no_prediction():
    """Tracker location_name returns None when no prediction exists."""
    coordinator = _make_coordinator(
        {"dev-2": DEVICE_BEACON_ONLY},
        {"dev-2": None},
    )
    tracker = AIPresenceDeviceTracker(coordinator, "dev-2", DEVICE_BEACON_ONLY)

    assert tracker.location_name is None


def test_tracker_source_type():
    """Tracker source_type is BLUETOOTH."""
    from homeassistant.components.device_tracker import SourceType

    coordinator = _make_coordinator({"dev-1": DEVICE_MONITOR}, {"dev-1": None})
    tracker = AIPresenceDeviceTracker(coordinator, "dev-1", DEVICE_MONITOR)

    assert tracker.source_type == SourceType.BLUETOOTH


def test_tracker_device_info():
    """Tracker device_info links to the correct HA device registry entry."""
    coordinator = _make_coordinator({"dev-1": DEVICE_MONITOR}, {"dev-1": None})
    tracker = AIPresenceDeviceTracker(coordinator, "dev-1", DEVICE_MONITOR)

    info = tracker.device_info
    assert info["identifiers"] == {(DOMAIN, "dev-1")}
    assert info["name"] == "Phone A"
    assert info["manufacturer"] == "AIPresence"
    assert info["model"] == "Both"


def test_tracker_unique_id():
    coordinator = _make_coordinator({"dev-1": DEVICE_MONITOR}, {"dev-1": None})
    tracker = AIPresenceDeviceTracker(coordinator, "dev-1", DEVICE_MONITOR)

    assert tracker._attr_unique_id == f"{DOMAIN}_dev-1_tracker"


def test_tracker_extra_attributes_with_prediction():
    """Extra attributes contain per-room probabilities."""
    coordinator = _make_coordinator(
        {"dev-1": DEVICE_MONITOR},
        {"dev-1": PREDICTION_DEV1},
    )
    tracker = AIPresenceDeviceTracker(coordinator, "dev-1", DEVICE_MONITOR)

    attrs = tracker.extra_state_attributes
    assert attrs == {"room_room-1": 0.87, "room_room-2": 0.13}


def test_tracker_extra_attributes_none_when_no_prediction():
    coordinator = _make_coordinator({"dev-2": DEVICE_BEACON_ONLY}, {"dev-2": None})
    tracker = AIPresenceDeviceTracker(coordinator, "dev-2", DEVICE_BEACON_ONLY)

    assert tracker.extra_state_attributes is None


# ---------------------------------------------------------------------------
# Confidence sensor tests
# ---------------------------------------------------------------------------


def test_confidence_sensor_value():
    """Confidence sensor returns percentage value."""
    coordinator = _make_coordinator(
        {"dev-1": DEVICE_MONITOR},
        {"dev-1": PREDICTION_DEV1},
    )
    sensor = AIPresenceConfidenceSensor(coordinator, "dev-1", DEVICE_MONITOR)

    assert sensor.native_value == 87.0


def test_confidence_sensor_unknown_when_no_prediction():
    coordinator = _make_coordinator({"dev-2": DEVICE_BEACON_ONLY}, {"dev-2": None})
    sensor = AIPresenceConfidenceSensor(coordinator, "dev-2", DEVICE_BEACON_ONLY)

    assert sensor.native_value is None


def test_confidence_sensor_unit_and_state_class():
    from homeassistant.components.sensor import SensorStateClass

    coordinator = _make_coordinator({"dev-1": DEVICE_MONITOR}, {"dev-1": None})
    sensor = AIPresenceConfidenceSensor(coordinator, "dev-1", DEVICE_MONITOR)

    assert sensor._attr_native_unit_of_measurement == "%"
    assert sensor._attr_state_class == SensorStateClass.MEASUREMENT


def test_confidence_sensor_device_info():
    coordinator = _make_coordinator({"dev-1": DEVICE_MONITOR}, {"dev-1": None})
    sensor = AIPresenceConfidenceSensor(coordinator, "dev-1", DEVICE_MONITOR)

    info = sensor.device_info
    assert info["identifiers"] == {(DOMAIN, "dev-1")}
    assert info["manufacturer"] == "AIPresence"


def test_confidence_sensor_unique_id():
    coordinator = _make_coordinator({"dev-1": DEVICE_MONITOR}, {"dev-1": None})
    sensor = AIPresenceConfidenceSensor(coordinator, "dev-1", DEVICE_MONITOR)

    assert sensor._attr_unique_id == f"{DOMAIN}_dev-1_confidence"


# ---------------------------------------------------------------------------
# Room sensor tests
# ---------------------------------------------------------------------------


def test_room_sensor_value():
    """Room sensor returns the friendly room name."""
    coordinator = _make_coordinator(
        {"dev-1": DEVICE_MONITOR},
        {"dev-1": PREDICTION_DEV1},
    )
    sensor = AIPresenceRoomSensor(coordinator, "dev-1", DEVICE_MONITOR)

    assert sensor.native_value == "Office"


def test_room_sensor_unknown_when_no_prediction():
    coordinator = _make_coordinator({"dev-2": DEVICE_BEACON_ONLY}, {"dev-2": None})
    sensor = AIPresenceRoomSensor(coordinator, "dev-2", DEVICE_BEACON_ONLY)

    assert sensor.native_value is None


def test_room_sensor_device_info_matches_tracker():
    """Room sensor links to the same HA device as the tracker."""
    coordinator = _make_coordinator({"dev-1": DEVICE_MONITOR}, {"dev-1": None})
    tracker = AIPresenceDeviceTracker(coordinator, "dev-1", DEVICE_MONITOR)
    room_sensor = AIPresenceRoomSensor(coordinator, "dev-1", DEVICE_MONITOR)

    assert tracker.device_info["identifiers"] == room_sensor.device_info["identifiers"]


def test_room_sensor_unique_id():
    coordinator = _make_coordinator({"dev-1": DEVICE_MONITOR}, {"dev-1": None})
    sensor = AIPresenceRoomSensor(coordinator, "dev-1", DEVICE_MONITOR)

    assert sensor._attr_unique_id == f"{DOMAIN}_dev-1_room"
