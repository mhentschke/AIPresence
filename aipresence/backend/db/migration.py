"""One-time JSON-to-SQLite migration logic.

On first startup with an empty database and existing JSON data files,
this module imports all records into the repository and renames the
original JSON files to ``.bak``.
"""

import json
import logging
import os

logger = logging.getLogger(__name__)

JSON_FILES = ["rooms.json", "trackers.json", "sensors.json", "devices.json"]


def needs_migration(data_path: str, repo) -> bool:
    """Return True if JSON files exist and the database is empty."""
    has_json = any(os.path.exists(os.path.join(data_path, f)) for f in JSON_FILES)
    if not has_json:
        return False
    has_data = (
        bool(repo.load_all_rooms())
        or bool(repo.load_all_trackers())
        or bool(repo.load_all_sensors())
        or bool(repo.load_all_devices())
    )
    return not has_data


def migrate_json_to_db(data_path: str, repo) -> None:
    """Import JSON files into the repository and rename them to .bak."""
    for filename in JSON_FILES:
        filepath = os.path.join(data_path, filename)
        if not os.path.exists(filepath):
            continue
        try:
            with open(filepath) as f:
                raw = json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Skipping malformed %s: %s", filename, exc)
            continue

        entity_type = filename.replace(".json", "")
        data = raw.get(entity_type, raw)

        if entity_type == "rooms":
            for k, v in data.items():
                repo.save_room(k, v["name"], v.get("color", "#ffffffff"))
        elif entity_type == "trackers":
            for k, v in data.items():
                repo.save_tracker(
                    v["entity_id"],
                    v.get("mobile", False),
                    v.get("whitelist", False),
                    v.get("blacklist", False),
                )
        elif entity_type == "sensors":
            for k, v in data.items():
                repo.save_sensor(v["entity_id"], v.get("mobile", False))
        elif entity_type == "devices":
            for k, v in data.items():
                repo.save_device(k, v["name"], v.get("entity_id"), v.get("beacon_id"))
                if v.get("model"):
                    m = v["model"]
                    repo.save_model_metadata(
                        k,
                        m["data_path"],
                        m["trained_model_stats"]["accuracy"],
                        m["trained_model_stats"]["model_type"],
                        m["trained_model_stats"]["classification_report"],
                        m["trained_columns"],
                    )

        os.rename(filepath, filepath + ".bak")
        logger.info("Migrated %s -> %s.bak", filename, filename)
