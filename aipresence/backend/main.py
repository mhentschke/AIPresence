import io
import json
import logging
import os
import pickle
import sqlite3
import tarfile
import tempfile
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import pandas as pd
from fastapi import Depends, FastAPI, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from .classes import (
    _BEACON_MONITOR_META_KEYS,
    BeaconMonitor,
    Binary_Sensor,
    Device,
    Model,
    Model_Stats,
    Room,
    Smartphone_Tracker,
)
from .config import Settings
from .datasource import (
    DataSourceUnavailableError,
    HADataSource,
    StandaloneDataSource,
)
from .db.migration import migrate_json_to_db, needs_migration
from .db.sqlite import SQLiteRepository
from .dependencies import get_data_source, get_settings
from .errors import generic_exception_handler, value_error_handler
from .routes.beacon_monitors import router as beacon_monitors_router
from .routes.devices import router as devices_router
from .routes.rooms import router as rooms_router
from .routes.sensors import router as sensors_router
from .routes.trackers import router as trackers_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Configuration ---
    settings = Settings()
    app.state.settings = settings

    # --- Logging ---
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    # --- Database ---
    db_path = os.path.join(settings.data_path, settings.db_filename)
    repo = SQLiteRepository(db_path)
    app.state.repository = repo

    # --- JSON migration (one-time) ---
    if needs_migration(settings.data_path, repo):
        migrate_json_to_db(settings.data_path, repo)

    # --- Data Source ---
    if settings.ha_configured:
        data_source = HADataSource(settings.ha_url, settings.ha_token)
        logger.info("HA data source configured (%s)", settings.ha_url)
    else:
        data_source = StandaloneDataSource()
        logger.warning("No HA credentials configured — running in standalone mode")
    app.state.data_source = data_source

    # --- Load state from DB ---
    app.state.rooms = {}
    for k, v in repo.load_all_rooms().items():
        app.state.rooms[k] = Room(v["id"], v["name"], v["color"])

    app.state.trackers = {}
    for k, v in repo.load_all_trackers().items():
        app.state.trackers[k] = Smartphone_Tracker(
            entity_id=v["entity_id"],
            data_source=data_source,
            mobile=v["mobile"],
            whitelist=v["whitelist"],
            blacklist=v["blacklist"],
        )

    app.state.sensors = {}
    for k, v in repo.load_all_sensors().items():
        app.state.sensors[k] = Binary_Sensor(entity_id=v["entity_id"], data_source=data_source, mobile=v["mobile"])

    app.state.beacon_monitors = {}
    for k, v in repo.load_all_beacon_monitors().items():
        app.state.beacon_monitors[k] = BeaconMonitor(entity_id=v["entity_id"], data_source=data_source)

    # Build a per-device data gatherer factory.
    # Each device gets its own gatherer that collects only data relevant to locating THAT device:
    #   1. The device's own monitor readings (if it has entity_id) — beacon distances it sees
    #   2. Fixed monitors' readings of the device's beacon (if it has beacon_id)
    #   3. Binary sensors (fixed environmental data)
    def make_data_gatherer(device_entity_id, device_beacon_id):
        def gather():
            data = {}

            # Source 1: device's own monitor — reads all beacon distances it can see
            if device_entity_id is not None:
                try:
                    state = data_source.get_entity_state(device_entity_id)
                    for key, value in state.attributes.items():
                        if key in _BEACON_MONITOR_META_KEYS:
                            continue
                        if isinstance(value, (int, float)):
                            data[device_entity_id + "-" + str(key)] = value
                except Exception as e:
                    logger.warning("Failed to read device monitor %s: %s", device_entity_id, e)

            # Source 2: fixed monitors seeing this device's beacon
            if device_beacon_id is not None:
                for monitor_eid, monitor in app.state.beacon_monitors.items():
                    try:
                        state = data_source.get_entity_state(monitor_eid)
                        for key, value in state.attributes.items():
                            if key == device_beacon_id and isinstance(value, (int, float)):
                                data[monitor_eid + "-" + str(key)] = value
                    except Exception as e:
                        logger.warning("Failed to read fixed monitor %s: %s", monitor_eid, e)

            # Source 3: binary sensors (environmental)
            for sensor_eid, sensor in app.state.sensors.items():
                try:
                    temp_data = sensor.get_data()
                    if isinstance(temp_data, dict):
                        for key, val in temp_data.items():
                            data[sensor_eid + "-" + str(key)] = val
                    else:
                        data[sensor_eid] = temp_data
                except Exception as e:
                    logger.warning("Failed to read sensor %s: %s", sensor_eid, e)

            return data

        return gather

    app.state.devices = {}
    for k, v in repo.load_all_devices().items():
        dev_entity_id = v.get("entity_id")
        dev_beacon_id = v.get("beacon_id")
        gatherer = make_data_gatherer(dev_entity_id, dev_beacon_id)
        model = None
        meta = repo.load_model_metadata(k)
        if meta is not None:
            data_path = os.path.join(settings.data_path, meta["data_path"])
            try:
                model = Model(
                    data_path=meta["data_path"],
                    data=pd.read_csv(Model.get_data_filepath(data_path)),
                    trained_model=pickle.load(open(Model.get_model_filepath(data_path), "rb")),
                    trained_model_stats=Model_Stats(
                        model_type=meta["model_type"],
                        classification_report=meta["classification_report"],
                        accuracy=meta["accuracy"],
                    ),
                    scaler=pickle.load(open(Model.get_scaler_filepath(data_path), "rb")),
                    data_gatherer=gatherer,
                    trained_columns=meta["trained_columns"],
                )
            except Exception:
                logger.warning(
                    "Failed to load model artifacts for device %s, loading without model",
                    k,
                )
        app.state.devices[k] = Device(
            name=v["name"],
            entity_id=dev_entity_id,
            beacon_id=dev_beacon_id,
            model=model,
            data_gatherer=gatherer,
        )

    yield

    # --- Shutdown ---
    repo.close()


app = FastAPI(title="AIPresence", lifespan=lifespan)

# --- Global exception handlers ---
app.add_exception_handler(ValueError, value_error_handler)
app.add_exception_handler(Exception, generic_exception_handler)


async def data_source_unavailable_handler(request: Request, exc: DataSourceUnavailableError):
    return JSONResponse(status_code=503, content={"detail": str(exc)})


app.add_exception_handler(DataSourceUnavailableError, data_source_unavailable_handler)

# --- Route modules ---
app.include_router(devices_router, prefix="/devices", tags=["devices"])
app.include_router(trackers_router, prefix="/trackers", tags=["trackers"])
app.include_router(sensors_router, prefix="/sensors", tags=["sensors"])
app.include_router(rooms_router, prefix="/rooms", tags=["rooms"])
app.include_router(beacon_monitors_router, prefix="/beacon_monitors", tags=["beacon_monitors"])


# --- App-level route (doesn't belong to a specific domain) ---
@app.get("/device/check_entity_id/{entity_id}")
def check_entity_id(entity_id: str, data_source=Depends(get_data_source)):
    try:
        exists = data_source.check_entity_exists(entity_id)
        if exists:
            return {"detail": "Success"}
        raise HTTPException(status_code=404, detail="Entity not found")
    except DataSourceUnavailableError:
        raise HTTPException(status_code=503, detail="Home Assistant is not configured")


@app.get("/ha/entities")
def list_ha_entities(domain: str | None = None, data_source=Depends(get_data_source)):
    return data_source.list_entities(domain)


@app.get("/ha/entity/{entity_id:path}")
def get_ha_entity_state(entity_id: str, data_source=Depends(get_data_source)):
    """Debug endpoint: return raw state + attributes for any HA entity."""
    state = data_source.get_entity_state(entity_id)
    return {"state": state.state, "attributes": state.attributes}


# --- Admin endpoints ---
RELOAD_SAFE_KEYS = {"log_level", "sample_rate", "minimum_training_samples", "ha_url", "ha_token"}
RESTART_ONLY_KEYS = {"data_path", "db_filename"}


@app.post("/admin/reload-config")
def reload_config(request: Request, settings=Depends(get_settings)):
    new_settings = Settings()
    changed: list[str] = []

    # Apply reload-safe settings
    for key in RELOAD_SAFE_KEYS:
        old_val = getattr(settings, key)
        new_val = getattr(new_settings, key)
        if old_val != new_val:
            setattr(settings, key, new_val)
            changed.append(key)

    # Adjust root logger level immediately
    if "log_level" in changed:
        logging.getLogger().setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
        logger.info("Log level changed to %s", settings.log_level)

    # Recreate data source if HA credentials changed
    if "ha_url" in changed or "ha_token" in changed:
        if settings.ha_configured:
            data_source = HADataSource(settings.ha_url, settings.ha_token)
            logger.info("HA data source reconfigured (%s)", settings.ha_url)
        else:
            data_source = StandaloneDataSource()
            logger.warning("HA credentials removed — switching to standalone mode")
        request.app.state.data_source = data_source
        for tracker in request.app.state.trackers.values():
            tracker.data_source = data_source
        for sensor in request.app.state.sensors.values():
            sensor.data_source = data_source

    # Warn about restart-only settings that changed but won't be applied
    for key in RESTART_ONLY_KEYS:
        old_val = getattr(settings, key)
        new_val = getattr(new_settings, key)
        if old_val != new_val:
            logger.warning("Config '%s' changed in .env but requires restart to take effect", key)

    return {"reloaded": changed}


# --- Backup & Restore endpoints ---

AIPRESENCE_VERSION = "0.1.0"


@app.get("/admin/backup")
def create_backup(request: Request, settings=Depends(get_settings)):
    """Create a .tar.gz backup archive containing the DB, model artifacts, and metadata."""
    data_path = settings.data_path

    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        # 1. metadata.json
        repo: SQLiteRepository = request.app.state.repository
        schema_version = repo._get_schema_version()
        metadata = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": AIPRESENCE_VERSION,
            "db_schema_version": schema_version,
        }
        meta_bytes = json.dumps(metadata, indent=2).encode("utf-8")
        meta_info = tarfile.TarInfo(name="backup/metadata.json")
        meta_info.size = len(meta_bytes)
        tar.addfile(meta_info, io.BytesIO(meta_bytes))

        # 2. SQLite database (safe copy via backup API)
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_db:
            tmp_db_path = tmp_db.name
        try:
            backup_conn = sqlite3.connect(tmp_db_path)
            repo.conn.backup(backup_conn)
            backup_conn.close()
            tar.add(tmp_db_path, arcname=f"backup/{settings.db_filename}")
        finally:
            os.unlink(tmp_db_path)

        # 3. Model artifact directories (subdirs of data_path containing .pkl/.csv)
        if os.path.isdir(data_path):
            for entry in os.listdir(data_path):
                entry_path = os.path.join(data_path, entry)
                if os.path.isdir(entry_path):
                    # Include directories that contain model artifacts
                    for fname in os.listdir(entry_path):
                        fpath = os.path.join(entry_path, fname)
                        if os.path.isfile(fpath):
                            tar.add(fpath, arcname=f"backup/models/{entry}/{fname}")

    buf.seek(0)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"aipresence_backup_{timestamp}.tar.gz"
    return StreamingResponse(
        buf,
        media_type="application/gzip",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.post("/admin/restore")
async def restore_backup(request: Request, file: UploadFile, settings=Depends(get_settings)):
    """Restore from a .tar.gz backup archive."""
    data_path = settings.data_path
    db_filename = settings.db_filename

    # Read uploaded file
    contents = await file.read()
    buf = io.BytesIO(contents)

    # Validate archive structure
    try:
        with tarfile.open(fileobj=buf, mode="r:gz") as tar:
            names = tar.getnames()
    except tarfile.TarError:
        raise HTTPException(status_code=400, detail="Invalid archive: not a valid .tar.gz file")

    has_metadata = any(n.endswith("metadata.json") for n in names)
    has_db = any(n.endswith(db_filename) for n in names)
    if not has_metadata:
        raise HTTPException(status_code=400, detail="Invalid archive: missing metadata.json")
    if not has_db:
        raise HTTPException(status_code=400, detail=f"Invalid archive: missing {db_filename}")

    # Extract to temp directory
    buf.seek(0)
    with tempfile.TemporaryDirectory() as tmp_dir:
        with tarfile.open(fileobj=buf, mode="r:gz") as tar:
            # Security: filter out absolute paths and path traversal
            for member in tar.getmembers():
                if member.name.startswith("/") or ".." in member.name:
                    raise HTTPException(status_code=400, detail="Invalid archive: unsafe file paths detected")
            tar.extractall(tmp_dir, filter="data")

        # Find the backup root (could be tmp_dir/backup/ or tmp_dir/ directly)
        backup_root = tmp_dir
        candidate = os.path.join(tmp_dir, "backup")
        if os.path.isdir(candidate):
            backup_root = candidate

        # Validate extracted contents
        extracted_db = os.path.join(backup_root, db_filename)
        extracted_meta = os.path.join(backup_root, "metadata.json")
        if not os.path.isfile(extracted_db):
            raise HTTPException(status_code=400, detail=f"Archive missing {db_filename} after extraction")
        if not os.path.isfile(extracted_meta):
            raise HTTPException(status_code=400, detail="Archive missing metadata.json after extraction")

        # Close current DB connection
        repo: SQLiteRepository = request.app.state.repository
        repo.close()

        try:
            # Replace DB file
            dest_db = os.path.join(data_path, db_filename)
            with open(extracted_db, "rb") as src, open(dest_db, "wb") as dst:
                dst.write(src.read())

            # Replace model artifact directories
            models_dir = os.path.join(backup_root, "models")
            if os.path.isdir(models_dir):
                for entry in os.listdir(models_dir):
                    src_dir = os.path.join(models_dir, entry)
                    dest_dir = os.path.join(data_path, entry)
                    if os.path.isdir(src_dir):
                        # Remove existing model dir if present
                        if os.path.isdir(dest_dir):
                            import shutil

                            shutil.rmtree(dest_dir)
                        os.makedirs(dest_dir, exist_ok=True)
                        for fname in os.listdir(src_dir):
                            src_file = os.path.join(src_dir, fname)
                            dst_file = os.path.join(dest_dir, fname)
                            with open(src_file, "rb") as sf, open(dst_file, "wb") as df:
                                df.write(sf.read())

            # Re-open DB
            new_repo = SQLiteRepository(dest_db)
            request.app.state.repository = new_repo

            # Reload all in-memory state (mirrors lifespan startup logic)
            data_source = request.app.state.data_source

            request.app.state.rooms = {}
            for k, v in new_repo.load_all_rooms().items():
                request.app.state.rooms[k] = Room(v["id"], v["name"], v["color"])

            request.app.state.trackers = {}
            for k, v in new_repo.load_all_trackers().items():
                request.app.state.trackers[k] = Smartphone_Tracker(
                    entity_id=v["entity_id"],
                    data_source=data_source,
                    mobile=v["mobile"],
                    whitelist=v["whitelist"],
                    blacklist=v["blacklist"],
                )

            request.app.state.sensors = {}
            for k, v in new_repo.load_all_sensors().items():
                request.app.state.sensors[k] = Binary_Sensor(
                    entity_id=v["entity_id"], data_source=data_source, mobile=v["mobile"]
                )

            request.app.state.beacon_monitors = {}
            for k, v in new_repo.load_all_beacon_monitors().items():
                request.app.state.beacon_monitors[k] = BeaconMonitor(entity_id=v["entity_id"], data_source=data_source)

            # Rebuild devices with models
            def make_data_gatherer(device_entity_id, device_beacon_id):
                def gather():
                    data = {}
                    if device_entity_id is not None:
                        try:
                            state = data_source.get_entity_state(device_entity_id)
                            for key, value in state.attributes.items():
                                if key in _BEACON_MONITOR_META_KEYS:
                                    continue
                                if isinstance(value, (int, float)):
                                    data[device_entity_id + "-" + str(key)] = value
                        except Exception:
                            pass
                    if device_beacon_id is not None:
                        for monitor_eid, monitor in request.app.state.beacon_monitors.items():
                            try:
                                state = data_source.get_entity_state(monitor_eid)
                                for key, value in state.attributes.items():
                                    if key == device_beacon_id and isinstance(value, (int, float)):
                                        data[monitor_eid + "-" + str(key)] = value
                            except Exception:
                                pass
                    for sensor_eid, sensor in request.app.state.sensors.items():
                        try:
                            temp_data = sensor.get_data()
                            if isinstance(temp_data, dict):
                                for key, val in temp_data.items():
                                    data[sensor_eid + "-" + str(key)] = val
                            else:
                                data[sensor_eid] = temp_data
                        except Exception:
                            pass
                    return data

                return gather

            request.app.state.devices = {}
            for k, v in new_repo.load_all_devices().items():
                dev_entity_id = v.get("entity_id")
                dev_beacon_id = v.get("beacon_id")
                gatherer = make_data_gatherer(dev_entity_id, dev_beacon_id)
                model = None
                meta = new_repo.load_model_metadata(k)
                if meta is not None:
                    model_data_path = os.path.join(data_path, meta["data_path"])
                    try:
                        model = Model(
                            data_path=meta["data_path"],
                            data=pd.read_csv(Model.get_data_filepath(model_data_path)),
                            trained_model=pickle.load(open(Model.get_model_filepath(model_data_path), "rb")),
                            trained_model_stats=Model_Stats(
                                model_type=meta["model_type"],
                                classification_report=meta["classification_report"],
                                accuracy=meta["accuracy"],
                            ),
                            scaler=pickle.load(open(Model.get_scaler_filepath(model_data_path), "rb")),
                            data_gatherer=gatherer,
                            trained_columns=meta["trained_columns"],
                        )
                    except Exception:
                        logger.warning(
                            "Failed to load model artifacts for device %s during restore",
                            k,
                        )
                request.app.state.devices[k] = Device(
                    name=v["name"],
                    entity_id=dev_entity_id,
                    beacon_id=dev_beacon_id,
                    model=model,
                    data_gatherer=gatherer,
                )

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Restore failed: %s", e, exc_info=True)
            raise HTTPException(status_code=500, detail=f"Restore failed: {e}")

    return {"detail": "Restore completed successfully"}


# --- Static file serving (React SPA) ---
# Must be registered AFTER all API routes so they take priority.
STATIC_DIR = os.environ.get("STATIC_DIR", "client/dist")

if os.path.isdir(STATIC_DIR):
    _assets_dir = os.path.join(STATIC_DIR, "assets")
    if os.path.isdir(_assets_dir):
        app.mount("/assets", StaticFiles(directory=_assets_dir), name="assets")

    @app.get("/{path:path}")
    async def serve_spa(path: str):
        """Serve static files from the built SPA, falling back to index.html for client-side routing."""
        file_path = os.path.join(STATIC_DIR, path)
        if path and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))
