"""Tests for the AIPresence config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from custom_components.aipresence.config_flow import (
    AIPresenceOptionsFlow,
    _async_discover_addon,
    _async_validate_backend,
)
from custom_components.aipresence.const import (
    CONF_BEACON_TIMEOUT,
    CONF_SCAN_INTERVAL,
)

# ---------------------------------------------------------------------------
# Backend validation tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_validate_backend_success(aiohttp_server):
    """Test that validation succeeds when the backend returns 200."""
    from aiohttp import web

    async def handler(request):
        return web.json_response([])

    app = web.Application()
    app.router.add_get("/devices", handler)
    server = await aiohttp_server(app)

    result = await _async_validate_backend(f"http://localhost:{server.port}")
    assert result is True


@pytest.mark.asyncio
async def test_validate_backend_failure_bad_status(aiohttp_server):
    """Test that validation fails on non-200 status."""
    from aiohttp import web

    async def handler(request):
        return web.Response(status=500)

    app = web.Application()
    app.router.add_get("/devices", handler)
    server = await aiohttp_server(app)

    result = await _async_validate_backend(f"http://localhost:{server.port}")
    assert result is False


@pytest.mark.asyncio
async def test_validate_backend_failure_unreachable():
    """Test that validation fails when the backend is unreachable."""
    result = await _async_validate_backend("http://127.0.0.1:19999")
    assert result is False


# ---------------------------------------------------------------------------
# Add-on auto-discovery tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_discover_addon_hassio_not_loaded():
    """Test discovery returns None when hassio is not loaded."""
    hass = AsyncMock()
    hass.config.components = set()

    result = await _async_discover_addon(hass)
    assert result is None


@pytest.mark.asyncio
async def test_discover_addon_found_and_started():
    """Test discovery returns URL when add-on is found and started."""
    hass = AsyncMock()
    hass.config.components = {"hassio"}

    with (
        patch(
            "homeassistant.components.hassio.is_hassio",
            return_value=True,
        ),
        patch(
            "homeassistant.components.hassio.async_get_addon_info",
            new_callable=AsyncMock,
            return_value={"state": "started"},
        ),
    ):
        result = await _async_discover_addon(hass)
        assert result == "http://local-aipresence:8099"


@pytest.mark.asyncio
async def test_discover_addon_not_started():
    """Test discovery returns None when add-on exists but is not started."""
    hass = AsyncMock()
    hass.config.components = {"hassio"}

    with (
        patch(
            "homeassistant.components.hassio.is_hassio",
            return_value=True,
        ),
        patch(
            "homeassistant.components.hassio.async_get_addon_info",
            new_callable=AsyncMock,
            return_value={"state": "stopped"},
        ),
    ):
        result = await _async_discover_addon(hass)
        assert result is None


@pytest.mark.asyncio
async def test_discover_addon_not_found():
    """Test discovery returns None when add-on is not installed."""
    hass = AsyncMock()
    hass.config.components = {"hassio"}

    with (
        patch(
            "homeassistant.components.hassio.is_hassio",
            return_value=True,
        ),
        patch(
            "homeassistant.components.hassio.async_get_addon_info",
            new_callable=AsyncMock,
            return_value=None,
        ),
    ):
        result = await _async_discover_addon(hass)
        assert result is None


# ---------------------------------------------------------------------------
# Options flow tests
# ---------------------------------------------------------------------------


class FakeConfigEntry:
    """Minimal stand-in for a ConfigEntry used in options flow tests."""

    def __init__(self, options: dict | None = None):
        self.options = options or {}


class TestOptionsFlow:
    """Tests for the AIPresence options flow."""

    @pytest.mark.asyncio
    async def test_options_flow_defaults(self):
        """Test that the options form shows current defaults."""
        entry = FakeConfigEntry()
        flow = AIPresenceOptionsFlow(entry)

        result = await flow.async_step_init(user_input=None)
        assert result["type"] == "form"
        assert result["step_id"] == "init"

    @pytest.mark.asyncio
    async def test_options_flow_submit(self):
        """Test that submitting options creates an entry."""
        entry = FakeConfigEntry()
        flow = AIPresenceOptionsFlow(entry)

        result = await flow.async_step_init(user_input={CONF_SCAN_INTERVAL: 10, CONF_BEACON_TIMEOUT: 60})
        assert result["type"] == "create_entry"
        assert result["data"][CONF_SCAN_INTERVAL] == 10
        assert result["data"][CONF_BEACON_TIMEOUT] == 60
