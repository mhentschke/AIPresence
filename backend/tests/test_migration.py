"""Unit tests for JSON-to-SQLite migration logic."""

import json
import os

import pytest

from backend.db.migration import migrate_json_to_db, needs_migration
from backend.db.sqlite import SQLiteRepository


@pytest.fixture()
def repo():
    r = SQLiteRepository(":memory:")
    yield r
    r.close()


@pytest.fixture()
def data_dir(tmp_path):
    """Create a tmp directory with sample JSON data files."""
    rooms = {
        "rooms": {
            "r1": {"id": "r1", "name": "Kitchen", "color": "#ff0000"},
            "r2": {"id": "r2", "name": "Office", "color": "#00ff00"},
        }
    }
    trackers = {
        "trackers": {
            "device_tracker.phone": {
                "entity_id": "device_tracker.phone",
                "mobile": True,
                "whitelist": False,
                "blacklist": False,
            }
        }
    }
    sensors = {
        "sensors": {
            "binary_sensor.motion": {"entity_id": "binary_sensor.motion", "mobile": False}
        }
    }
    devices = {
        "devices": {
            "d1": {
                "name": "Phone",
                "entity_id": "device_tracker.phone",
                "beacon_id": None,
                "model": {
                    "data_path": "d1/",
                    "trained_model_stats": {
                        "accuracy": 0.95,
                        "model_type": "RandomForestClassifier",
                        "classification_report": {"precision": 0.9},
                    },
                    "trained_columns": ["col_a", "col_b"],
                },
            }
        }
    }
    for name, content in [
        ("rooms.json", rooms),
        ("trackers.json", trackers),
        ("sensors.json", sensors),
        ("devices.json", devices),
    ]:
        with open(os.path.join(tmp_path, name), "w") as f:
            json.dump(content, f)
    return tmp_path


class TestNeedsMigration:
    def test_returns_true_when_json_exists_and_db_empty(self, repo, data_dir):
        assert needs_migration(str(data_dir), repo) is True

    def test_returns_false_when_no_json_files(self, repo, tmp_path):
        assert needs_migration(str(tmp_path), repo) is False

    def test_returns_false_when_db_has_data(self, repo, data_dir):
        repo.save_room("r1", "Kitchen", "#ff0000")
        assert needs_migration(str(data_dir), repo) is False


class TestMigrateJsonToDb:
    def test_imports_all_entity_types(self, repo, data_dir):
        migrate_json_to_db(str(data_dir), repo)

        rooms = repo.load_all_rooms()
        assert len(rooms) == 2
        assert rooms["r1"]["name"] == "Kitchen"

        trackers = repo.load_all_trackers()
        assert "device_tracker.phone" in trackers
        assert trackers["device_tracker.phone"]["mobile"] is True

        sensors = repo.load_all_sensors()
        assert "binary_sensor.motion" in sensors

        devices = repo.load_all_devices()
        assert "d1" in devices
        assert devices["d1"]["name"] == "Phone"

        meta = repo.load_model_metadata("d1")
        assert meta is not None
        assert meta["accuracy"] == 0.95
        assert meta["trained_columns"] == ["col_a", "col_b"]

    def test_renames_json_files_to_bak(self, repo, data_dir):
        migrate_json_to_db(str(data_dir), repo)

        for name in ["rooms.json", "trackers.json", "sensors.json", "devices.json"]:
            assert not os.path.exists(os.path.join(data_dir, name))
            assert os.path.exists(os.path.join(data_dir, name + ".bak"))

    def test_skips_malformed_json_and_continues(self, repo, data_dir):
        # Corrupt rooms.json
        with open(os.path.join(data_dir, "rooms.json"), "w") as f:
            f.write("{bad json")

        migrate_json_to_db(str(data_dir), repo)

        # rooms should be empty (skipped), but others should be imported
        assert repo.load_all_rooms() == {}
        assert len(repo.load_all_trackers()) == 1
        assert len(repo.load_all_sensors()) == 1
        assert len(repo.load_all_devices()) == 1
