import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from homeassistant_api import Client
from homeassistant_api.errors import EndpointNotFoundError

from . import storage
from .dependencies import get_ha_client
from .errors import generic_exception_handler, value_error_handler
from .routes.devices import router as devices_router
from .routes.rooms import router as rooms_router
from .routes.sensors import router as sensors_router
from .routes.trackers import router as trackers_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

    client = Client(
        os.environ["HA_URL"],
        os.environ["HA_TOKEN"],
    )
    app.state.ha_client = client

    # Load persisted state — each block is independent so one failure
    # doesn't prevent the others from loading.
    app.state.trackers = {}
    app.state.sensors = {}
    app.state.devices = {}
    app.state.rooms = {}

    try:
        app.state.trackers = storage.load_trackers()
        for tracker in app.state.trackers.values():
            tracker.ha_client = client
    except FileNotFoundError:
        logger.info("Trackers file not found, starting from scratch")
    except Exception:
        logger.exception("Error loading trackers, starting from scratch")

    try:
        app.state.sensors = storage.load_sensors()
        for sensor in app.state.sensors.values():
            sensor.ha_client = client
    except FileNotFoundError:
        logger.info("Sensors file not found, starting from scratch")
    except Exception:
        logger.exception("Error loading sensors, starting from scratch")

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

    try:
        app.state.devices = storage.load_devices(data_gatherer=data_gatherer)
        for device in app.state.devices.values():
            device.data_gatherer = data_gatherer
            if device.model is not None:
                device.model.data_gatherer = data_gatherer
    except FileNotFoundError:
        logger.info("Devices file not found, starting from scratch")
    except Exception:
        logger.exception("Error loading devices, starting from scratch")

    try:
        app.state.rooms = storage.load_rooms()
    except FileNotFoundError:
        logger.info("Rooms file not found, starting from scratch")
    except Exception:
        logger.exception("Error loading rooms, starting from scratch")

    yield
    # Shutdown — nothing to clean up for now


app = FastAPI(title="AIPresence", lifespan=lifespan)

# --- Global exception handlers ---
app.add_exception_handler(ValueError, value_error_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# --- Route modules ---
app.include_router(devices_router, prefix="/devices", tags=["devices"])
app.include_router(trackers_router, prefix="/trackers", tags=["trackers"])
app.include_router(sensors_router, prefix="/sensors", tags=["sensors"])
app.include_router(rooms_router, prefix="/rooms", tags=["rooms"])


# --- App-level route (doesn't belong to a specific domain) ---
@app.get("/device/check_entity_id/{entity_id}")
def check_entity_id(entity_id: str, client=Depends(get_ha_client)):
    try:
        client.get_entity(entity_id=entity_id)
        return {"detail": "Success"}
    except EndpointNotFoundError:
        raise HTTPException(status_code=404, detail="Entity not found")
