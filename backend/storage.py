"""JSON file persistence using pydantic models.

Replaces the marshmallow-based storage layer.  Each entity type has an
explicit ``save_*`` / ``load_*`` pair.  Device model artifacts (pickle
files, CSV training data) are handled inside ``save_devices`` /
``load_devices`` to preserve the same behaviour as the old marshmallow
``@pre_dump`` / ``@post_load`` hooks.
"""

import json
import logging
import os
import pickle

import pandas as pd

import config
from classes import (
    Binary_Sensor,
    Device,
    Model,
    Model_Stats,
    Room,
    Smartphone_Tracker,
)
from schemas import (
    DeviceStorage,
    ModelStatsStorage,
    ModelStorage,
    RoomStorage,
    SensorStorage,
    TrackerStorage,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Generic JSON helpers
# ---------------------------------------------------------------------------


def save_json(data: dict, filename: str) -> None:
    filepath = os.path.join(config.DATA_PATH, filename)
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)


def load_json(filename: str) -> dict:
    filepath = os.path.join(config.DATA_PATH, filename)
    with open(filepath, "r") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Rooms
# ---------------------------------------------------------------------------


def save_rooms(rooms: dict) -> None:
    data = {
        k: RoomStorage(id=v.id, name=v.name, color=v.color).model_dump()
        for k, v in rooms.items()
    }
    save_json({"rooms": data}, "rooms.json")


def load_rooms() -> dict:
    raw = load_json("rooms.json")
    rooms_data = raw.get("rooms", raw)
    result = {}
    for k, v in rooms_data.items():
        storage = RoomStorage.model_validate(v)
        result[k] = Room(storage.id, storage.name, storage.color)
    return result


# ---------------------------------------------------------------------------
# Trackers
# ---------------------------------------------------------------------------


def save_trackers(trackers: dict) -> None:
    data = {
        k: TrackerStorage(
            entity_id=v.entity_id,
            mobile=v.mobile,
            whitelist=v.whitelist,
            blacklist=v.blacklist,
        ).model_dump()
        for k, v in trackers.items()
    }
    save_json({"trackers": data}, "trackers.json")


def load_trackers() -> dict:
    raw = load_json("trackers.json")
    trackers_data = raw.get("trackers", raw)
    result = {}
    for k, v in trackers_data.items():
        storage = TrackerStorage.model_validate(v)
        result[k] = Smartphone_Tracker(
            entity_id=storage.entity_id,
            mobile=storage.mobile,
            whitelist=storage.whitelist,
            blacklist=storage.blacklist,
        )
    return result


# ---------------------------------------------------------------------------
# Sensors
# ---------------------------------------------------------------------------


def save_sensors(sensors: dict) -> None:
    data = {
        k: SensorStorage(entity_id=v.entity_id, mobile=v.mobile).model_dump()
        for k, v in sensors.items()
    }
    save_json({"sensors": data}, "sensors.json")


def load_sensors() -> dict:
    raw = load_json("sensors.json")
    sensors_data = raw.get("sensors", raw)
    result = {}
    for k, v in sensors_data.items():
        storage = SensorStorage.model_validate(v)
        result[k] = Binary_Sensor(
            entity_id=storage.entity_id,
            mobile=storage.mobile,
        )
    return result


# ---------------------------------------------------------------------------
# Devices (with model artifact handling)
# ---------------------------------------------------------------------------


def save_devices(devices: dict) -> None:
    data = {}
    for k, device in devices.items():
        model_data = None
        if device.model is not None and device.model.trained_model is not None:
            # Persist pickle / CSV artifacts to disk
            data_path = os.path.join(config.DATA_PATH, device.model.data_path)
            os.makedirs(data_path, exist_ok=True)

            device.model.data.to_csv(
                Model.get_data_filepath(data_path), index=False
            )
            with open(Model.get_model_filepath(data_path), "wb") as f:
                pickle.dump(device.model.trained_model, f)
            with open(Model.get_scaler_filepath(data_path), "wb") as f:
                pickle.dump(device.model.scaler, f)

            model_data = ModelStorage(
                data_path=device.model.data_path,
                trained_model_stats=ModelStatsStorage(
                    accuracy=device.model.trained_model_stats.accuracy,
                    model_type=device.model.trained_model_stats.model_type,
                    classification_report=device.model.trained_model_stats.classification_report,
                ),
                trained_columns=device.model.trained_columns,
            ).model_dump()

        device_data = DeviceStorage(
            name=device.name,
            entity_id=device.entity_id,
            beacon_id=device.beacon_id,
            model=model_data,
        ).model_dump()
        data[k] = device_data

    save_json({"devices": data}, "devices.json")


def load_devices(data_gatherer=None) -> dict:
    raw = load_json("devices.json")
    devices_data = raw.get("devices", raw)
    result = {}
    for k, v in devices_data.items():
        storage = DeviceStorage.model_validate(v)
        model = None
        if storage.model is not None:
            data_path = os.path.join(config.DATA_PATH, storage.model.data_path)
            with open(Model.get_model_filepath(data_path), "rb") as f:
                trained_model = pickle.load(f)
            with open(Model.get_scaler_filepath(data_path), "rb") as f:
                scaler = pickle.load(f)
            model = Model(
                data_path=storage.model.data_path,
                data=pd.read_csv(Model.get_data_filepath(data_path)),
                trained_model=trained_model,
                trained_model_stats=Model_Stats(
                    model_type=storage.model.trained_model_stats.model_type,
                    classification_report=storage.model.trained_model_stats.classification_report,
                    accuracy=storage.model.trained_model_stats.accuracy,
                ),
                scaler=scaler,
                data_gatherer=data_gatherer,
                trained_columns=storage.model.trained_columns,
            )
        result[k] = Device(
            name=storage.name,
            entity_id=storage.entity_id,
            beacon_id=storage.beacon_id,
            model=model,
            data_gatherer=data_gatherer,
        )
    return result
