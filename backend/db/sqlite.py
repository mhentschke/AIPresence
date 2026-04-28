"""SQLite concrete implementation of the Repository protocol."""

import json
import logging
import sqlite3

logger = logging.getLogger(__name__)

# Schema migrations keyed by version number.  Each value is a SQL script
# that brings the database from the previous version to this one.
MIGRATIONS: dict[int, str] = {
    1: """
        CREATE TABLE IF NOT EXISTS rooms (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            color TEXT NOT NULL DEFAULT '#ffffffff'
        );
        CREATE TABLE IF NOT EXISTS trackers (
            entity_id TEXT PRIMARY KEY,
            mobile INTEGER NOT NULL DEFAULT 0,
            whitelist INTEGER NOT NULL DEFAULT 0,
            blacklist INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS sensors (
            entity_id TEXT PRIMARY KEY,
            mobile INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS devices (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            entity_id TEXT,
            beacon_id TEXT
        );
        CREATE TABLE IF NOT EXISTS model_metadata (
            device_id TEXT PRIMARY KEY REFERENCES devices(id) ON DELETE CASCADE,
            data_path TEXT NOT NULL,
            accuracy REAL NOT NULL,
            model_type TEXT NOT NULL,
            classification_report TEXT NOT NULL,
            trained_columns TEXT NOT NULL
        );
    """,
    2: """
        CREATE TABLE IF NOT EXISTS beacon_monitors (
            entity_id TEXT PRIMARY KEY
        );
    """,
}


class SQLiteRepository:
    """SQLite-backed repository for all entity types."""

    def __init__(self, db_path: str) -> None:
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._apply_migrations()

    # ------------------------------------------------------------------
    # Schema versioning
    # ------------------------------------------------------------------

    def _get_schema_version(self) -> int:
        self.conn.execute("CREATE TABLE IF NOT EXISTS schema_version (version INTEGER NOT NULL)")
        row = self.conn.execute("SELECT version FROM schema_version").fetchone()
        if row is None:
            self.conn.execute("INSERT INTO schema_version (version) VALUES (0)")
            self.conn.commit()
            return 0
        return row["version"]

    def _apply_migrations(self) -> None:
        current = self._get_schema_version()
        for version in sorted(MIGRATIONS.keys()):
            if version > current:
                self.conn.executescript(MIGRATIONS[version])
                self.conn.execute("UPDATE schema_version SET version = ?", (version,))
                self.conn.commit()
                logger.info("Applied schema migration v%d", version)
        # Re-enable foreign keys after executescript (it resets pragmas)
        self.conn.execute("PRAGMA foreign_keys = ON")

    # ------------------------------------------------------------------
    # Rooms
    # ------------------------------------------------------------------

    def save_room(self, room_id: str, name: str, color: str) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO rooms (id, name, color) VALUES (?, ?, ?)",
            (room_id, name, color),
        )
        self.conn.commit()

    def delete_room(self, room_id: str) -> None:
        self.conn.execute("DELETE FROM rooms WHERE id = ?", (room_id,))
        self.conn.commit()

    def load_all_rooms(self) -> dict[str, dict]:
        rows = self.conn.execute("SELECT id, name, color FROM rooms").fetchall()
        return {row["id"]: {"id": row["id"], "name": row["name"], "color": row["color"]} for row in rows}

    # ------------------------------------------------------------------
    # Trackers
    # ------------------------------------------------------------------

    def save_tracker(self, entity_id: str, mobile: bool, whitelist: bool, blacklist: bool) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO trackers (entity_id, mobile, whitelist, blacklist) VALUES (?, ?, ?, ?)",
            (entity_id, int(mobile), int(whitelist), int(blacklist)),
        )
        self.conn.commit()

    def delete_tracker(self, entity_id: str) -> None:
        self.conn.execute("DELETE FROM trackers WHERE entity_id = ?", (entity_id,))
        self.conn.commit()

    def load_all_trackers(self) -> dict[str, dict]:
        rows = self.conn.execute("SELECT entity_id, mobile, whitelist, blacklist FROM trackers").fetchall()
        return {
            row["entity_id"]: {
                "entity_id": row["entity_id"],
                "mobile": bool(row["mobile"]),
                "whitelist": bool(row["whitelist"]),
                "blacklist": bool(row["blacklist"]),
            }
            for row in rows
        }

    # ------------------------------------------------------------------
    # Sensors
    # ------------------------------------------------------------------

    def save_sensor(self, entity_id: str, mobile: bool) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO sensors (entity_id, mobile) VALUES (?, ?)",
            (entity_id, int(mobile)),
        )
        self.conn.commit()

    def delete_sensor(self, entity_id: str) -> None:
        self.conn.execute("DELETE FROM sensors WHERE entity_id = ?", (entity_id,))
        self.conn.commit()

    def load_all_sensors(self) -> dict[str, dict]:
        rows = self.conn.execute("SELECT entity_id, mobile FROM sensors").fetchall()
        return {
            row["entity_id"]: {
                "entity_id": row["entity_id"],
                "mobile": bool(row["mobile"]),
            }
            for row in rows
        }

    # ------------------------------------------------------------------
    # Beacon Monitors
    # ------------------------------------------------------------------

    def save_beacon_monitor(self, entity_id: str) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO beacon_monitors (entity_id) VALUES (?)",
            (entity_id,),
        )
        self.conn.commit()

    def delete_beacon_monitor(self, entity_id: str) -> None:
        self.conn.execute("DELETE FROM beacon_monitors WHERE entity_id = ?", (entity_id,))
        self.conn.commit()

    def load_all_beacon_monitors(self) -> dict[str, dict]:
        rows = self.conn.execute("SELECT entity_id FROM beacon_monitors").fetchall()
        return {row["entity_id"]: {"entity_id": row["entity_id"]} for row in rows}

    # ------------------------------------------------------------------
    # Devices
    # ------------------------------------------------------------------

    def save_device(self, device_id: str, name: str, entity_id: str | None, beacon_id: str | None) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO devices (id, name, entity_id, beacon_id) VALUES (?, ?, ?, ?)",
            (device_id, name, entity_id, beacon_id),
        )
        self.conn.commit()

    def delete_device(self, device_id: str) -> None:
        self.conn.execute("DELETE FROM devices WHERE id = ?", (device_id,))
        self.conn.commit()

    def load_all_devices(self) -> dict[str, dict]:
        rows = self.conn.execute("SELECT id, name, entity_id, beacon_id FROM devices").fetchall()
        return {
            row["id"]: {
                "name": row["name"],
                "entity_id": row["entity_id"],
                "beacon_id": row["beacon_id"],
            }
            for row in rows
        }

    # ------------------------------------------------------------------
    # Model Metadata
    # ------------------------------------------------------------------

    def save_model_metadata(
        self,
        device_id: str,
        data_path: str,
        accuracy: float,
        model_type: str,
        classification_report: dict,
        trained_columns: list[str],
    ) -> None:
        self.conn.execute(
            """INSERT OR REPLACE INTO model_metadata
               (device_id, data_path, accuracy, model_type, classification_report, trained_columns)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                device_id,
                data_path,
                accuracy,
                model_type,
                json.dumps(classification_report),
                json.dumps(trained_columns),
            ),
        )
        self.conn.commit()

    def delete_model_metadata(self, device_id: str) -> None:
        self.conn.execute("DELETE FROM model_metadata WHERE device_id = ?", (device_id,))
        self.conn.commit()

    def load_model_metadata(self, device_id: str) -> dict | None:
        row = self.conn.execute(
            "SELECT data_path, accuracy, model_type, classification_report, trained_columns "
            "FROM model_metadata WHERE device_id = ?",
            (device_id,),
        ).fetchone()
        if row is None:
            return None
        return {
            "data_path": row["data_path"],
            "accuracy": row["accuracy"],
            "model_type": row["model_type"],
            "classification_report": json.loads(row["classification_report"]),
            "trained_columns": json.loads(row["trained_columns"]),
        }

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def close(self) -> None:
        self.conn.close()
