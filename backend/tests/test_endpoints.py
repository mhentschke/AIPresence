"""Integration smoke tests for key API endpoints.

Uses FastAPI TestClient with dependency overrides so no HA client or
persisted files are needed.
"""

import sys
import os
from contextlib import asynccontextmanager
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Ensure the backend package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from backend.routes.devices import router as devices_router
from backend.routes.rooms import router as rooms_router
from backend.routes.sensors import router as sensors_router
from backend.routes.trackers import router as trackers_router
from backend.errors import generic_exception_handler, value_error_handler


# ---------------------------------------------------------------------------
# Test app factory — no HA client, no disk I/O
# ---------------------------------------------------------------------------

def _create_test_app() -> FastAPI:
    """Build a minimal FastAPI app with in-memory state for testing."""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.ha_client = MagicMock()
        app.state.trackers = {}
        app.state.sensors = {}
        app.state.devices = {}
        app.state.rooms = {}
        yield

    app = FastAPI(lifespan=lifespan)
    app.add_exception_handler(ValueError, value_error_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
    app.include_router(rooms_router, prefix="/rooms")
    app.include_router(trackers_router, prefix="/trackers")
    app.include_router(sensors_router, prefix="/sensors")
    app.include_router(devices_router, prefix="/devices")
    return app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """Provide a TestClient with a temp DATA_PATH so saves don't touch real files."""
    import backend.config as config
    monkeypatch.setattr(config, "DATA_PATH", str(tmp_path))
    app = _create_test_app()
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# Rooms CRUD
# ---------------------------------------------------------------------------

class TestRooms:
    def test_list_rooms_empty(self, client):
        resp = client.get("/rooms")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_create_and_get_room(self, client):
        resp = client.post("/rooms", json={"name": "Kitchen", "color": "#ff0000"})
        assert resp.status_code == 200
        room_id = resp.json()

        resp = client.get(f"/rooms/{room_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Kitchen"
        assert data["color"] == "#ff0000"

    def test_update_room(self, client):
        room_id = client.post("/rooms", json={"name": "Office"}).json()
        resp = client.put(f"/rooms/{room_id}", json={"name": "Study", "color": "#00ff00"})
        assert resp.status_code == 200

        data = client.get(f"/rooms/{room_id}").json()
        assert data["name"] == "Study"

    def test_delete_room(self, client):
        room_id = client.post("/rooms", json={"name": "Garage"}).json()
        resp = client.delete(f"/rooms/{room_id}")
        assert resp.status_code == 200

        resp = client.get(f"/rooms/{room_id}")
        assert resp.status_code == 404

    def test_get_room_not_found(self, client):
        resp = client.get("/rooms/nonexistent")
        assert resp.status_code == 404
        assert "detail" in resp.json()

    def test_delete_room_not_found(self, client):
        resp = client.delete("/rooms/nonexistent")
        assert resp.status_code == 404
        assert "detail" in resp.json()


# ---------------------------------------------------------------------------
# Trackers CRUD
# ---------------------------------------------------------------------------

class TestTrackers:
    def test_list_trackers_empty(self, client):
        resp = client.get("/trackers")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_create_and_list_tracker(self, client):
        resp = client.post("/trackers/device_tracker.phone", json={"mobile": True})
        assert resp.status_code == 200

        trackers = client.get("/trackers").json()
        assert len(trackers) == 1
        assert trackers[0]["entity_id"] == "device_tracker.phone"
        assert trackers[0]["mobile"] is True

    def test_create_duplicate_tracker_409(self, client):
        client.post("/trackers/device_tracker.phone", json={})
        resp = client.post("/trackers/device_tracker.phone", json={})
        assert resp.status_code == 409
        assert "detail" in resp.json()

    def test_update_tracker(self, client):
        client.post("/trackers/device_tracker.phone", json={"mobile": False})
        resp = client.put("/trackers/device_tracker.phone", json={"mobile": True})
        assert resp.status_code == 200

    def test_update_tracker_not_found(self, client):
        resp = client.put("/trackers/nonexistent", json={"mobile": True})
        assert resp.status_code == 404
        assert "detail" in resp.json()

    def test_delete_tracker(self, client):
        client.post("/trackers/device_tracker.phone", json={})
        resp = client.delete("/trackers/device_tracker.phone")
        assert resp.status_code == 200
        assert client.get("/trackers").json() == []

    def test_delete_tracker_not_found(self, client):
        resp = client.delete("/trackers/nonexistent")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Sensors CRUD
# ---------------------------------------------------------------------------

class TestSensors:
    def test_list_sensors_empty(self, client):
        resp = client.get("/sensors")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_create_and_list_sensor(self, client):
        resp = client.post("/sensors/binary_sensor.motion")
        assert resp.status_code == 200

        sensors = client.get("/sensors").json()
        assert len(sensors) == 1
        assert sensors[0]["entity_id"] == "binary_sensor.motion"

    def test_create_duplicate_sensor_409(self, client):
        client.post("/sensors/binary_sensor.motion")
        resp = client.post("/sensors/binary_sensor.motion")
        assert resp.status_code == 409

    def test_delete_sensor(self, client):
        client.post("/sensors/binary_sensor.motion")
        resp = client.delete("/sensors/binary_sensor.motion")
        assert resp.status_code == 200
        assert client.get("/sensors").json() == []

    def test_delete_sensor_not_found(self, client):
        resp = client.delete("/sensors/nonexistent")
        assert resp.status_code == 404
        assert "detail" in resp.json()


# ---------------------------------------------------------------------------
# Devices CRUD
# ---------------------------------------------------------------------------

class TestDevices:
    def test_list_devices_empty(self, client):
        resp = client.get("/devices")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_create_and_get_device(self, client):
        resp = client.post("/devices", json={"name": "Phone", "entity_id": "device_tracker.phone"})
        assert resp.status_code == 200
        device_id = resp.json()

        resp = client.get(f"/devices/{device_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Phone"
        assert data["entity_id"] == "device_tracker.phone"

    def test_delete_device(self, client):
        device_id = client.post("/devices", json={"name": "Beacon", "beacon_id": "AA:BB:CC"}).json()
        resp = client.delete(f"/devices/{device_id}")
        assert resp.status_code == 200
        assert client.get(f"/devices/{device_id}").status_code == 404

    def test_get_device_not_found(self, client):
        resp = client.get("/devices/nonexistent")
        assert resp.status_code == 404
        assert "detail" in resp.json()

    def test_delete_device_not_found(self, client):
        resp = client.delete("/devices/nonexistent")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Validation errors (422)
# ---------------------------------------------------------------------------

class TestValidation:
    def test_device_missing_both_ids_422(self, client):
        resp = client.post("/devices", json={"name": "Bad"})
        assert resp.status_code == 422
        body = resp.json()
        assert "detail" in body

    def test_device_both_ids_422(self, client):
        resp = client.post("/devices", json={"name": "Bad", "entity_id": "a", "beacon_id": "b"})
        assert resp.status_code == 422

    def test_room_missing_name_422(self, client):
        resp = client.post("/rooms", json={"color": "#fff"})
        assert resp.status_code == 422
        assert "detail" in resp.json()
