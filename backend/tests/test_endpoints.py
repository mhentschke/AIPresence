"""Integration smoke tests for key API endpoints.

Uses FastAPI TestClient with dependency overrides so no HA client or
persisted files are needed.
"""

import os
import sys
from contextlib import asynccontextmanager

import pytest
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

# Ensure the backend package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from backend.config import Settings
from backend.datasource import DataSourceUnavailableError, StandaloneDataSource
from backend.db.sqlite import SQLiteRepository
from backend.dependencies import get_data_source
from backend.errors import generic_exception_handler, value_error_handler
from backend.routes.devices import router as devices_router
from backend.routes.rooms import router as rooms_router
from backend.routes.sensors import router as sensors_router
from backend.routes.trackers import router as trackers_router

# ---------------------------------------------------------------------------
# Test app factory — no HA client, no disk I/O
# ---------------------------------------------------------------------------


def _create_test_app() -> FastAPI:
    """Build a minimal FastAPI app with in-memory state for testing."""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.data_source = StandaloneDataSource()
        app.state.settings = Settings(data_path="data", db_filename="aipresence.db")
        app.state.trackers = {}
        app.state.sensors = {}
        app.state.devices = {}
        app.state.rooms = {}
        app.state.repository = SQLiteRepository(":memory:")
        yield

    app = FastAPI(lifespan=lifespan)
    app.add_exception_handler(ValueError, value_error_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    async def data_source_unavailable_handler(request: Request, exc: DataSourceUnavailableError):
        return JSONResponse(status_code=503, content={"detail": str(exc)})

    app.add_exception_handler(DataSourceUnavailableError, data_source_unavailable_handler)

    app.include_router(rooms_router, prefix="/rooms")
    app.include_router(trackers_router, prefix="/trackers")
    app.include_router(sensors_router, prefix="/sensors")
    app.include_router(devices_router, prefix="/devices")

    @app.get("/device/check_entity_id/{entity_id}")
    def check_entity_id(entity_id: str, data_source=Depends(get_data_source)):
        try:
            exists = data_source.check_entity_exists(entity_id)
            if exists:
                return {"detail": "Success"}
            raise HTTPException(status_code=404, detail="Entity not found")
        except DataSourceUnavailableError:
            raise HTTPException(status_code=503, detail="Home Assistant is not configured")

    return app


@pytest.fixture()
def client(tmp_path):
    """Provide a TestClient with a temp DATA_PATH so saves don't touch real files."""
    app = _create_test_app()
    with TestClient(app) as c:
        # Override settings.data_path after lifespan has run
        c.app.state.settings = Settings(data_path=str(tmp_path), db_filename="aipresence.db")
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


# ---------------------------------------------------------------------------
# Check Entity ID endpoint (standalone mode → 503)
# ---------------------------------------------------------------------------


class TestCheckEntityId:
    def test_check_entity_id_returns_503_in_standalone_mode(self, client):
        resp = client.get("/device/check_entity_id/binary_sensor.motion")
        assert resp.status_code == 503
        assert "Home Assistant is not configured" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# DataSourceUnavailableError handler
# ---------------------------------------------------------------------------


class TestDataSourceUnavailableHandler:
    def test_datasource_unavailable_returns_503(self, client):
        """Verify the global exception handler catches DataSourceUnavailableError and returns 503."""
        from backend.classes import Binary_Sensor
        from backend.datasource import StandaloneDataSource

        # Create a sensor backed by StandaloneDataSource, then add a route
        # that triggers get_data() which raises DataSourceUnavailableError.
        sensor = Binary_Sensor(entity_id="binary_sensor.test", data_source=StandaloneDataSource())
        client.app.state.sensors["binary_sensor.test"] = sensor

        # The training/prediction flow calls get_data() on sensors, which raises
        # DataSourceUnavailableError in standalone mode. We simulate this by
        # adding a temporary endpoint that calls get_data().
        @client.app.get("/_test/trigger_datasource_error")
        def _trigger():
            sensor.get_data()

        resp = client.get("/_test/trigger_datasource_error")
        assert resp.status_code == 503
        assert "unavailable" in resp.json()["detail"].lower()
