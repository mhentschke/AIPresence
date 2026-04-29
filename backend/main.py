import logging
import os
import pickle
from contextlib import asynccontextmanager

import pandas as pd
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
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
