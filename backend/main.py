import logging
import os
import pickle
from contextlib import asynccontextmanager

import pandas as pd
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from .classes import (
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
from .dependencies import get_data_source
from .errors import generic_exception_handler, value_error_handler
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
        app.state.sensors[k] = Binary_Sensor(
            entity_id=v["entity_id"], data_source=data_source, mobile=v["mobile"]
        )

    # Build the data gatherer closure now that trackers & sensors are loaded.
    def data_gatherer():
        data = {}
        for entity_id, tracker in {**app.state.trackers, **app.state.sensors}.items():
            temp_data = tracker.get_data()
            if isinstance(temp_data, dict):
                temp_data = {
                    entity_id + "-" + str(key): val for key, val in temp_data.items()
                }
            else:
                temp_data = {entity_id: temp_data}
            data.update(temp_data)
        return data

    app.state.devices = {}
    for k, v in repo.load_all_devices().items():
        model = None
        meta = repo.load_model_metadata(k)
        if meta is not None:
            data_path = os.path.join(settings.data_path, meta["data_path"])
            try:
                model = Model(
                    data_path=meta["data_path"],
                    data=pd.read_csv(Model.get_data_filepath(data_path)),
                    trained_model=pickle.load(
                        open(Model.get_model_filepath(data_path), "rb")
                    ),
                    trained_model_stats=Model_Stats(
                        model_type=meta["model_type"],
                        classification_report=meta["classification_report"],
                        accuracy=meta["accuracy"],
                    ),
                    scaler=pickle.load(
                        open(Model.get_scaler_filepath(data_path), "rb")
                    ),
                    data_gatherer=data_gatherer,
                    trained_columns=meta["trained_columns"],
                )
            except Exception:
                logger.warning(
                    "Failed to load model artifacts for device %s, loading without model",
                    k,
                )
        app.state.devices[k] = Device(
            name=v["name"],
            entity_id=v.get("entity_id"),
            beacon_id=v.get("beacon_id"),
            model=model,
            data_gatherer=data_gatherer,
        )

    yield

    # --- Shutdown ---
    repo.close()


app = FastAPI(title="AIPresence", lifespan=lifespan)

# --- Global exception handlers ---
app.add_exception_handler(ValueError, value_error_handler)
app.add_exception_handler(Exception, generic_exception_handler)


async def data_source_unavailable_handler(
    request: Request, exc: DataSourceUnavailableError
):
    return JSONResponse(status_code=503, content={"detail": str(exc)})


app.add_exception_handler(DataSourceUnavailableError, data_source_unavailable_handler)

# --- Route modules ---
app.include_router(devices_router, prefix="/devices", tags=["devices"])
app.include_router(trackers_router, prefix="/trackers", tags=["trackers"])
app.include_router(sensors_router, prefix="/sensors", tags=["sensors"])
app.include_router(rooms_router, prefix="/rooms", tags=["rooms"])


# --- App-level route (doesn't belong to a specific domain) ---
@app.get("/device/check_entity_id/{entity_id}")
def check_entity_id(entity_id: str, data_source=Depends(get_data_source)):
    try:
        exists = data_source.check_entity_exists(entity_id)
        if exists:
            return {"detail": "Success"}
        raise HTTPException(status_code=404, detail="Entity not found")
    except DataSourceUnavailableError:
        raise HTTPException(
            status_code=503, detail="Home Assistant is not configured"
        )
