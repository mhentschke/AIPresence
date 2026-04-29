"""Tests for backup and restore endpoints."""

import io
import json
import os
import pickle
import sqlite3
import sys
import tarfile
from contextlib import asynccontextmanager

import pandas as pd
import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from backend.classes import Room
from backend.config import Settings
from backend.datasource import DataSourceUnavailableError, StandaloneDataSource
from backend.db.sqlite import SQLiteRepository
from backend.errors import generic_exception_handler, value_error_handler
from backend.main import AIPRESENCE_VERSION, create_backup, restore_backup


def _create_test_app(data_path: str) -> FastAPI:
    """Build a minimal FastAPI app with backup/restore endpoints for testing."""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        settings = Settings(data_path=data_path, db_filename="aipresence.db")
        app.state.settings = settings

        db_path = os.path.join(data_path, "aipresence.db")
        repo = SQLiteRepository(db_path)
        app.state.repository = repo
        app.state.data_source = StandaloneDataSource()
        app.state.rooms = {}
        app.state.trackers = {}
        app.state.sensors = {}
        app.state.beacon_monitors = {}
        app.state.devices = {}
        yield
        repo.close()

    app = FastAPI(lifespan=lifespan)
    app.add_exception_handler(ValueError, value_error_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    async def data_source_unavailable_handler(request: Request, exc: DataSourceUnavailableError):
        return JSONResponse(status_code=503, content={"detail": str(exc)})

    app.add_exception_handler(DataSourceUnavailableError, data_source_unavailable_handler)

    # Register the backup/restore endpoints directly
    app.get("/admin/backup")(create_backup)
    app.post("/admin/restore")(restore_backup)

    return app


@pytest.fixture()
def client(tmp_path):
    data_path = str(tmp_path)
    app = _create_test_app(data_path)
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def seeded_client(tmp_path):
    """Client with pre-populated rooms and a mock model artifact directory."""
    data_path = str(tmp_path)
    app = _create_test_app(data_path)
    with TestClient(app) as c:
        # Add some rooms via the repository
        repo: SQLiteRepository = c.app.state.repository
        repo.save_room("room1", "Office", "#ff0000")
        repo.save_room("room2", "Kitchen", "#00ff00")
        c.app.state.rooms["room1"] = Room("room1", "Office", "#ff0000")
        c.app.state.rooms["room2"] = Room("room2", "Kitchen", "#00ff00")

        # Create a mock model artifact directory
        model_dir = os.path.join(data_path, "sensor.test_device")
        os.makedirs(model_dir, exist_ok=True)
        # Write a dummy CSV
        df = pd.DataFrame({"feature1": [1.0, 2.0], "room": ["room1", "room2"]})
        df.to_csv(os.path.join(model_dir, "data.csv"), index=False)
        # Write dummy pickle files
        with open(os.path.join(model_dir, "model.pkl"), "wb") as f:
            pickle.dump({"dummy": "model"}, f)
        with open(os.path.join(model_dir, "scaler.pkl"), "wb") as f:
            pickle.dump({"dummy": "scaler"}, f)

        yield c


class TestBackup:
    def test_backup_returns_tar_gz(self, client):
        resp = client.get("/admin/backup")
        assert resp.status_code == 200
        assert "application/gzip" in resp.headers["content-type"]
        assert "attachment" in resp.headers["content-disposition"]

    def test_backup_contains_metadata_and_db(self, client):
        resp = client.get("/admin/backup")
        buf = io.BytesIO(resp.content)
        with tarfile.open(fileobj=buf, mode="r:gz") as tar:
            names = tar.getnames()
            assert any("metadata.json" in n for n in names)
            assert any("aipresence.db" in n for n in names)

    def test_backup_metadata_content(self, client):
        resp = client.get("/admin/backup")
        buf = io.BytesIO(resp.content)
        with tarfile.open(fileobj=buf, mode="r:gz") as tar:
            meta_member = [m for m in tar.getmembers() if "metadata.json" in m.name][0]
            meta = json.load(tar.extractfile(meta_member))
            assert "timestamp" in meta
            assert meta["version"] == AIPRESENCE_VERSION
            assert "db_schema_version" in meta

    def test_backup_includes_model_artifacts(self, seeded_client):
        resp = seeded_client.get("/admin/backup")
        buf = io.BytesIO(resp.content)
        with tarfile.open(fileobj=buf, mode="r:gz") as tar:
            names = tar.getnames()
            model_files = [n for n in names if "sensor.test_device" in n]
            assert len(model_files) == 3  # data.csv, model.pkl, scaler.pkl

    def test_backup_db_contains_rooms(self, seeded_client):
        resp = seeded_client.get("/admin/backup")
        buf = io.BytesIO(resp.content)
        with tarfile.open(fileobj=buf, mode="r:gz") as tar:
            db_member = [m for m in tar.getmembers() if "aipresence.db" in m.name][0]
            db_bytes = tar.extractfile(db_member).read()
            # Write to temp file and query
            import tempfile

            with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
                tmp.write(db_bytes)
                tmp_path = tmp.name
            try:
                conn = sqlite3.connect(tmp_path)
                conn.row_factory = sqlite3.Row
                rows = conn.execute("SELECT id, name FROM rooms").fetchall()
                room_ids = {row["id"] for row in rows}
                assert "room1" in room_ids
                assert "room2" in room_ids
                conn.close()
            finally:
                os.unlink(tmp_path)


class TestRestore:
    def _make_backup_archive(self, db_path, model_dir=None, metadata=None):
        """Helper to create a valid backup archive."""
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w:gz") as tar:
            # metadata.json
            if metadata is None:
                metadata = {
                    "timestamp": "2026-01-01T00:00:00Z",
                    "version": AIPRESENCE_VERSION,
                    "db_schema_version": 2,
                }
            meta_bytes = json.dumps(metadata).encode("utf-8")
            meta_info = tarfile.TarInfo(name="backup/metadata.json")
            meta_info.size = len(meta_bytes)
            tar.addfile(meta_info, io.BytesIO(meta_bytes))

            # DB file
            tar.add(db_path, arcname="backup/aipresence.db")

            # Model artifacts
            if model_dir and os.path.isdir(model_dir):
                dirname = os.path.basename(model_dir)
                for fname in os.listdir(model_dir):
                    fpath = os.path.join(model_dir, fname)
                    if os.path.isfile(fpath):
                        tar.add(fpath, arcname=f"backup/models/{dirname}/{fname}")

        buf.seek(0)
        return buf

    def test_restore_with_valid_archive(self, seeded_client, tmp_path):
        # Create a backup first
        resp = seeded_client.get("/admin/backup")
        assert resp.status_code == 200

        # Clear current state
        repo = seeded_client.app.state.repository
        repo.delete_room("room1")
        repo.delete_room("room2")
        seeded_client.app.state.rooms.clear()

        # Restore from the backup
        backup_bytes = resp.content
        resp = seeded_client.post(
            "/admin/restore",
            files={"file": ("backup.tar.gz", io.BytesIO(backup_bytes), "application/gzip")},
        )
        assert resp.status_code == 200
        assert "successfully" in resp.json()["detail"].lower()

        # Verify rooms were restored
        assert "room1" in seeded_client.app.state.rooms
        assert "room2" in seeded_client.app.state.rooms

    def test_restore_rejects_non_tar_gz(self, client):
        resp = client.post(
            "/admin/restore",
            files={"file": ("bad.txt", io.BytesIO(b"not a tar file"), "text/plain")},
        )
        assert resp.status_code == 400
        assert "not a valid" in resp.json()["detail"].lower()

    def test_restore_rejects_missing_metadata(self, client, tmp_path):
        # Create archive with DB but no metadata
        db_path = os.path.join(str(tmp_path), "aipresence.db")
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE test (id TEXT)")
        conn.close()

        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w:gz") as tar:
            tar.add(db_path, arcname="backup/aipresence.db")
        buf.seek(0)

        resp = client.post(
            "/admin/restore",
            files={"file": ("backup.tar.gz", buf, "application/gzip")},
        )
        assert resp.status_code == 400
        assert "metadata" in resp.json()["detail"].lower()

    def test_restore_rejects_missing_db(self, client):
        # Create archive with metadata but no DB
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w:gz") as tar:
            meta = json.dumps({"timestamp": "now", "version": "0.1.0"}).encode()
            info = tarfile.TarInfo(name="backup/metadata.json")
            info.size = len(meta)
            tar.addfile(info, io.BytesIO(meta))
        buf.seek(0)

        resp = client.post(
            "/admin/restore",
            files={"file": ("backup.tar.gz", buf, "application/gzip")},
        )
        assert resp.status_code == 400
        assert "aipresence.db" in resp.json()["detail"].lower()

    def test_restore_restores_model_artifacts(self, seeded_client):
        data_path = seeded_client.app.state.settings.data_path

        # Create backup (which includes model artifacts)
        resp = seeded_client.get("/admin/backup")
        backup_bytes = resp.content

        # Remove model artifacts
        import shutil

        model_dir = os.path.join(data_path, "sensor.test_device")
        if os.path.isdir(model_dir):
            shutil.rmtree(model_dir)
        assert not os.path.isdir(model_dir)

        # Restore
        resp = seeded_client.post(
            "/admin/restore",
            files={"file": ("backup.tar.gz", io.BytesIO(backup_bytes), "application/gzip")},
        )
        assert resp.status_code == 200

        # Verify model artifacts were restored
        assert os.path.isdir(model_dir)
        assert os.path.isfile(os.path.join(model_dir, "data.csv"))
        assert os.path.isfile(os.path.join(model_dir, "model.pkl"))
        assert os.path.isfile(os.path.join(model_dir, "scaler.pkl"))
