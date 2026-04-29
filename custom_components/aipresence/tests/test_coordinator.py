"""Tests for the AIPresence coordinator."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import ClientError
from custom_components.aipresence.const import CONF_BACKEND_URL, CONF_SCAN_INTERVAL
from custom_components.aipresence.coordinator import AIPresenceCoordinator

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

BACKEND_URL = "http://localhost:5000"

DEVICES_RESPONSE = [
    {
        "id": "dev-1",
        "name": "Phone A",
        "entity_id": "sensor.phone_a_beacon_monitor",
        "beacon_id": "uuid_a",
        "model": None,
    },
    {
        "id": "dev-2",
        "name": "Beacon B",
        "entity_id": None,
        "beacon_id": "uuid_b",
        "model": None,
    },
]

LOCATIONS_RESPONSE = {
    "dev-1": {
        "room": "room-1",
        "confidence": 0.87,
        "room_room-1": 0.87,
        "room_room-2": 0.13,
    },
    "dev-2": None,
}

ROOMS_RESPONSE = [
    {"id": "room-1", "name": "Office", "color": "#ff0000"},
    {"id": "room-2", "name": "Kitchen", "color": "#00ff00"},
]


def _make_entry(options=None):
    """Create a fake config entry."""
    entry = MagicMock()
    entry.data = {CONF_BACKEND_URL: BACKEND_URL}
    entry.options = options or {}
    return entry


def _make_response(json_data, status=200):
    """Create a mock aiohttp response usable as an async context manager."""
    resp = AsyncMock()
    resp.status = status
    resp.json = AsyncMock(return_value=json_data)
    resp.raise_for_status = MagicMock()
    if status >= 400:
        resp.raise_for_status.side_effect = ClientError("HTTP error")

    # Support `async with session.get(...) as resp:`
    ctx = AsyncMock()
    ctx.__aenter__ = AsyncMock(return_value=resp)
    ctx.__aexit__ = AsyncMock(return_value=False)
    return ctx


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_successful_data_fetch():
    """Test coordinator parses devices, predictions, and rooms correctly."""
    hass = MagicMock()
    entry = _make_entry()

    session = MagicMock()
    responses = [
        _make_response(DEVICES_RESPONSE),
        _make_response(LOCATIONS_RESPONSE),
        _make_response(ROOMS_RESPONSE),
    ]
    session.get = MagicMock(side_effect=responses)

    with patch(
        "custom_components.aipresence.coordinator.async_get_clientsession",
        return_value=session,
    ):
        coordinator = AIPresenceCoordinator(hass, entry)
        result = await coordinator._async_update_data()

    # Devices parsed
    assert "dev-1" in result["devices"]
    assert "dev-2" in result["devices"]
    assert result["devices"]["dev-1"]["name"] == "Phone A"

    # Predictions parsed with room name resolved
    pred_1 = result["predictions"]["dev-1"]
    assert pred_1 is not None
    assert pred_1["room_name"] == "Office"
    assert pred_1["confidence"] == 0.87

    # No prediction for dev-2
    assert result["predictions"]["dev-2"] is None


@pytest.mark.asyncio
async def test_room_name_resolution():
    """Test that room IDs in predictions are resolved to friendly names."""
    hass = MagicMock()
    entry = _make_entry()

    locations = {
        "dev-1": {"room": "room-2", "confidence": 0.65},
    }

    session = MagicMock()
    responses = [
        _make_response(DEVICES_RESPONSE[:1]),
        _make_response(locations),
        _make_response(ROOMS_RESPONSE),
    ]
    session.get = MagicMock(side_effect=responses)

    with patch(
        "custom_components.aipresence.coordinator.async_get_clientsession",
        return_value=session,
    ):
        coordinator = AIPresenceCoordinator(hass, entry)
        result = await coordinator._async_update_data()

    assert result["predictions"]["dev-1"]["room_name"] == "Kitchen"


@pytest.mark.asyncio
async def test_device_addition_detection():
    """Test that new devices are detected as additions."""
    hass = MagicMock()
    entry = _make_entry()

    session = MagicMock()
    responses = [
        _make_response(DEVICES_RESPONSE),
        _make_response(LOCATIONS_RESPONSE),
        _make_response(ROOMS_RESPONSE),
    ]
    session.get = MagicMock(side_effect=responses)

    with patch(
        "custom_components.aipresence.coordinator.async_get_clientsession",
        return_value=session,
    ):
        coordinator = AIPresenceCoordinator(hass, entry)
        # First fetch — all devices are new
        await coordinator._async_update_data()

    assert coordinator.added_devices == {"dev-1", "dev-2"}
    assert coordinator.removed_devices == set()


@pytest.mark.asyncio
async def test_device_removal_detection():
    """Test that removed devices are detected."""
    hass = MagicMock()
    entry = _make_entry()

    session = MagicMock()

    with patch(
        "custom_components.aipresence.coordinator.async_get_clientsession",
        return_value=session,
    ):
        coordinator = AIPresenceCoordinator(hass, entry)

        # First fetch: two devices
        session.get = MagicMock(
            side_effect=[
                _make_response(DEVICES_RESPONSE),
                _make_response(LOCATIONS_RESPONSE),
                _make_response(ROOMS_RESPONSE),
            ]
        )
        await coordinator._async_update_data()

        # Second fetch: only dev-1 remains
        session.get = MagicMock(
            side_effect=[
                _make_response(DEVICES_RESPONSE[:1]),
                _make_response({"dev-1": LOCATIONS_RESPONSE["dev-1"]}),
                _make_response(ROOMS_RESPONSE),
            ]
        )
        await coordinator._async_update_data()

    assert coordinator.removed_devices == {"dev-2"}
    assert coordinator.added_devices == set()


@pytest.mark.asyncio
async def test_error_raises_update_failed():
    """Test that a backend error raises UpdateFailed."""
    from homeassistant.helpers.update_coordinator import UpdateFailed

    hass = MagicMock()
    entry = _make_entry()

    session = MagicMock()
    session.get = MagicMock(side_effect=ClientError("Connection refused"))

    with patch(
        "custom_components.aipresence.coordinator.async_get_clientsession",
        return_value=session,
    ):
        coordinator = AIPresenceCoordinator(hass, entry)
        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()


@pytest.mark.asyncio
async def test_custom_scan_interval():
    """Test that scan interval is read from options."""
    from datetime import timedelta

    hass = MagicMock()
    entry = _make_entry(options={CONF_SCAN_INTERVAL: 15})

    with patch(
        "custom_components.aipresence.coordinator.async_get_clientsession",
        return_value=MagicMock(),
    ):
        coordinator = AIPresenceCoordinator(hass, entry)

    assert coordinator.update_interval == timedelta(seconds=15)
