"""Unit tests for SQLiteRepository against an in-memory database."""

import pytest

from backend.db.sqlite import SQLiteRepository


@pytest.fixture()
def repo():
    r = SQLiteRepository(":memory:")
    yield r
    r.close()


# ------------------------------------------------------------------
# Schema migration
# ------------------------------------------------------------------


class TestSchemaMigration:
    def test_initial_migration_creates_tables(self, repo):
        tables = repo.conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
        names = {row["name"] for row in tables}
        assert {"rooms", "trackers", "sensors", "devices", "model_metadata", "beacon_names"}.issubset(names)

    def test_schema_version_is_set(self, repo):
        row = repo.conn.execute("SELECT version FROM schema_version").fetchone()
        assert row["version"] == max(SQLiteRepository._migration_keys())

    def test_reopening_does_not_rerun_migrations(self):
        """Opening a second repo on the same DB should not fail."""
        import sqlite3

        conn = sqlite3.connect(":memory:")
        # Simulate a first open
        r1 = SQLiteRepository.__new__(SQLiteRepository)
        r1.conn = conn
        r1.conn.row_factory = sqlite3.Row
        r1.conn.execute("PRAGMA foreign_keys = ON")
        r1._apply_migrations()
        # Second open on same connection
        r1._apply_migrations()
        version = conn.execute("SELECT version FROM schema_version").fetchone()[0]
        assert version == max(SQLiteRepository._migration_keys())
        conn.close()


# ------------------------------------------------------------------
# Rooms CRUD
# ------------------------------------------------------------------


class TestRooms:
    def test_save_and_load(self, repo):
        repo.save_room("r1", "Kitchen", "#ff0000")
        rooms = repo.load_all_rooms()
        assert "r1" in rooms
        assert rooms["r1"] == {"id": "r1", "name": "Kitchen", "color": "#ff0000"}

    def test_upsert(self, repo):
        repo.save_room("r1", "Kitchen", "#ff0000")
        repo.save_room("r1", "Office", "#00ff00")
        rooms = repo.load_all_rooms()
        assert rooms["r1"]["name"] == "Office"

    def test_delete(self, repo):
        repo.save_room("r1", "Kitchen", "#ff0000")
        repo.delete_room("r1")
        assert repo.load_all_rooms() == {}

    def test_load_empty(self, repo):
        assert repo.load_all_rooms() == {}


# ------------------------------------------------------------------
# Trackers CRUD
# ------------------------------------------------------------------


class TestTrackers:
    def test_save_and_load(self, repo):
        repo.save_tracker("device_tracker.phone", True, False, True)
        trackers = repo.load_all_trackers()
        assert "device_tracker.phone" in trackers
        t = trackers["device_tracker.phone"]
        assert t["mobile"] is True
        assert t["whitelist"] is False
        assert t["blacklist"] is True

    def test_delete(self, repo):
        repo.save_tracker("device_tracker.phone", False, False, False)
        repo.delete_tracker("device_tracker.phone")
        assert repo.load_all_trackers() == {}


# ------------------------------------------------------------------
# Sensors CRUD
# ------------------------------------------------------------------


class TestSensors:
    def test_save_and_load(self, repo):
        repo.save_sensor("binary_sensor.motion", True)
        sensors = repo.load_all_sensors()
        assert "binary_sensor.motion" in sensors
        assert sensors["binary_sensor.motion"]["mobile"] is True

    def test_delete(self, repo):
        repo.save_sensor("binary_sensor.motion", False)
        repo.delete_sensor("binary_sensor.motion")
        assert repo.load_all_sensors() == {}


# ------------------------------------------------------------------
# Devices CRUD
# ------------------------------------------------------------------


class TestDevices:
    def test_save_and_load(self, repo):
        repo.save_device("d1", "Phone", "device_tracker.phone", None)
        devices = repo.load_all_devices()
        assert "d1" in devices
        assert devices["d1"]["name"] == "Phone"
        assert devices["d1"]["entity_id"] == "device_tracker.phone"
        assert devices["d1"]["beacon_id"] is None

    def test_delete(self, repo):
        repo.save_device("d1", "Phone", "device_tracker.phone", None)
        repo.delete_device("d1")
        assert repo.load_all_devices() == {}


# ------------------------------------------------------------------
# Model Metadata
# ------------------------------------------------------------------


class TestModelMetadata:
    def test_save_and_load(self, repo):
        repo.save_device("d1", "Phone", "device_tracker.phone", None)
        repo.save_model_metadata(
            "d1",
            "d1/",
            0.95,
            "RandomForestClassifier",
            {"precision": 0.9},
            ["room_kitchen", "room_office"],
        )
        meta = repo.load_model_metadata("d1")
        assert meta is not None
        assert meta["accuracy"] == 0.95
        assert meta["model_type"] == "RandomForestClassifier"
        assert meta["classification_report"] == {"precision": 0.9}
        assert meta["trained_columns"] == ["room_kitchen", "room_office"]

    def test_load_returns_none_for_device_without_model(self, repo):
        repo.save_device("d1", "Phone", "device_tracker.phone", None)
        assert repo.load_model_metadata("d1") is None

    def test_cascade_delete(self, repo):
        repo.save_device("d1", "Phone", "device_tracker.phone", None)
        repo.save_model_metadata(
            "d1",
            "d1/",
            0.9,
            "RF",
            {},
            ["col1"],
        )
        repo.delete_device("d1")
        assert repo.load_model_metadata("d1") is None

    def test_delete_model_metadata(self, repo):
        repo.save_device("d1", "Phone", "device_tracker.phone", None)
        repo.save_model_metadata("d1", "d1/", 0.9, "RF", {}, [])
        repo.delete_model_metadata("d1")
        assert repo.load_model_metadata("d1") is None


# ------------------------------------------------------------------
# Beacon Names CRUD
# ------------------------------------------------------------------


class TestBeaconNames:
    def test_save_and_load(self, repo):
        repo.save_beacon_name("a3f498e7_100_40004", "Dad's Phone")
        names = repo.load_all_beacon_names()
        assert names == {"a3f498e7_100_40004": "Dad's Phone"}

    def test_upsert(self, repo):
        repo.save_beacon_name("a3f498e7_100_40004", "Dad's Phone")
        repo.save_beacon_name("a3f498e7_100_40004", "Kitchen Tag")
        names = repo.load_all_beacon_names()
        assert names["a3f498e7_100_40004"] == "Kitchen Tag"

    def test_delete(self, repo):
        repo.save_beacon_name("a3f498e7_100_40004", "Dad's Phone")
        repo.delete_beacon_name("a3f498e7_100_40004")
        assert repo.load_all_beacon_names() == {}

    def test_load_empty(self, repo):
        assert repo.load_all_beacon_names() == {}

    def test_multiple_entries(self, repo):
        repo.save_beacon_name("beacon_1", "Phone")
        repo.save_beacon_name("beacon_2", "Tablet")
        names = repo.load_all_beacon_names()
        assert len(names) == 2
        assert names["beacon_1"] == "Phone"
        assert names["beacon_2"] == "Tablet"
