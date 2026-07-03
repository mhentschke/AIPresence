import os
import pickle
import uuid

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException

from ..classes import Device, Model
from ..dependencies import get_beacon_names, get_data_gatherer, get_devices, get_repository, get_rooms, get_settings
from ..schemas import (
    DeviceCreate,
    DeviceResponse,
    ModelResponse,
    ModelStatsResponse,
    RoomAverages,
    TrainingAveragesResponse,
    TrainingStart,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _device_to_response(device_id: str, device: Device) -> DeviceResponse:
    model_resp = None
    if device.model is not None and device.model.trained_model_stats is not None:
        model_resp = ModelResponse(
            trained_model_stats=ModelStatsResponse(
                accuracy=device.model.trained_model_stats.accuracy,
                model_type=device.model.trained_model_stats.model_type,
                classification_report=device.model.trained_model_stats.classification_report,
            )
        )
    elif device.model is not None:
        model_resp = ModelResponse(trained_model_stats=None)
    return DeviceResponse(
        id=device_id,
        name=device.name,
        entity_id=device.entity_id,
        beacon_id=device.beacon_id,
        model=model_resp,
    )


def save_model_artifacts(device: Device, settings) -> None:
    """Save pickle/CSV model artifacts to disk."""
    if device.model is None or device.model.trained_model is None:
        return
    data_path = os.path.join(settings.data_path, device.model.data_path)
    os.makedirs(data_path, exist_ok=True)
    device.model.data.to_csv(Model.get_data_filepath(data_path), index=False)
    with open(Model.get_model_filepath(data_path), "wb") as f:
        pickle.dump(device.model.trained_model, f)
    with open(Model.get_scaler_filepath(data_path), "wb") as f:
        pickle.dump(device.model.scaler, f)


def _persist_device_model(device_id: str, device: Device, repo, settings) -> None:
    """Save model artifacts to disk and metadata to the repository."""
    if device.model is None or device.model.trained_model is None:
        return
    save_model_artifacts(device, settings)
    repo.save_model_metadata(
        device_id,
        device.model.data_path,
        device.model.trained_model_stats.accuracy,
        device.model.trained_model_stats.model_type,
        device.model.trained_model_stats.classification_report,
        device.model.trained_columns,
    )


# ---------------------------------------------------------------------------
# CRUD + Location
# ---------------------------------------------------------------------------


@router.get("", response_model=list[DeviceResponse])
def list_devices(devices: dict = Depends(get_devices)):
    return [_device_to_response(k, v) for k, v in devices.items()]


@router.post("")
def create_device(
    body: DeviceCreate,
    devices: dict = Depends(get_devices),
    beacon_names: dict = Depends(get_beacon_names),
    make_data_gatherer=Depends(get_data_gatherer),
    repo=Depends(get_repository),
):
    device_id = str(uuid.uuid4())
    gatherer = make_data_gatherer(body.entity_id, body.beacon_id)
    devices[device_id] = Device(
        name=body.name,
        entity_id=body.entity_id,
        beacon_id=body.beacon_id,
        data_gatherer=gatherer,
    )
    repo.save_device(device_id, body.name, body.entity_id, body.beacon_id)

    response = {"id": device_id}

    # Auto-naming: if device has a beacon_id, manage friendly name
    if body.beacon_id:
        existing_name = beacon_names.get(body.beacon_id)
        if existing_name is None:
            # Auto-create friendly name from device name
            friendly = body.name.strip()
            if friendly:
                beacon_names[body.beacon_id] = friendly
                repo.save_beacon_name(body.beacon_id, friendly)
        else:
            # Inform the frontend about the existing name
            response["existing_beacon_name"] = existing_name

    return response


# Static path "/location" must be declared before the parameterised
# "/{device_id}" routes so FastAPI doesn't match "location" as a device_id.
@router.get("/location")
def get_all_device_locations(devices: dict = Depends(get_devices)):
    device_locations = {}
    for device_id, device in devices.items():
        device_locations[device_id] = device.get_location()
    return device_locations


@router.get("/{device_id}", response_model=DeviceResponse)
def get_device(device_id: str, devices: dict = Depends(get_devices)):
    if device_id not in devices:
        raise HTTPException(status_code=404, detail="Device not found")
    return _device_to_response(device_id, devices[device_id])


@router.put("/{device_id}")
def update_device(
    device_id: str,
    body: DeviceCreate,
    devices: dict = Depends(get_devices),
    beacon_names: dict = Depends(get_beacon_names),
    make_data_gatherer=Depends(get_data_gatherer),
    repo=Depends(get_repository),
):
    # Preserve existing model when updating
    model = None
    if device_id in devices:
        model = devices[device_id].model
    gatherer = make_data_gatherer(body.entity_id, body.beacon_id)
    devices[device_id] = Device(
        name=body.name,
        entity_id=body.entity_id,
        beacon_id=body.beacon_id,
        model=model,
        data_gatherer=gatherer,
    )
    repo.save_device(device_id, body.name, body.entity_id, body.beacon_id)

    response = {"detail": "Success"}

    # Auto-naming: if device has a beacon_id, manage friendly name
    if body.beacon_id:
        existing_name = beacon_names.get(body.beacon_id)
        if existing_name is None:
            # Auto-create friendly name from device name
            friendly = body.name.strip()
            if friendly:
                beacon_names[body.beacon_id] = friendly
                repo.save_beacon_name(body.beacon_id, friendly)
        else:
            # Inform the frontend about the existing name
            response["existing_beacon_name"] = existing_name

    return response


@router.delete("/{device_id}")
def delete_device(device_id: str, devices: dict = Depends(get_devices), repo=Depends(get_repository)):
    if device_id not in devices:
        raise HTTPException(status_code=404, detail="Device not found")
    del devices[device_id]
    repo.delete_device(device_id)
    return {"detail": "Success"}


@router.get("/{device_id}/location")
def get_device_location(device_id: str, devices: dict = Depends(get_devices)):
    if device_id not in devices:
        raise HTTPException(status_code=404, detail="Device not found")
    loc = devices[device_id].get_location()
    if loc is None:
        raise HTTPException(status_code=400, detail="Device is not trained")
    return loc


# ---------------------------------------------------------------------------
# Model / Training
# ---------------------------------------------------------------------------


@router.post("/{device_id}/model/start_training")
def start_training(
    device_id: str,
    body: TrainingStart,
    devices: dict = Depends(get_devices),
    rooms: dict = Depends(get_rooms),
):
    if device_id not in devices:
        raise HTTPException(status_code=404, detail="Device not found")
    if body.room not in rooms:
        raise HTTPException(status_code=404, detail="Room not found")
    devices[device_id].start_training(body.room, append=body.append)
    return {"detail": "Success"}


@router.get("/{device_id}/model/stop_training")
def stop_training(
    device_id: str, devices: dict = Depends(get_devices), repo=Depends(get_repository), settings=Depends(get_settings)
):
    if device_id not in devices:
        raise HTTPException(status_code=404, detail="Device not found")
    if not devices[device_id].training:
        raise HTTPException(status_code=400, detail="Device is not training")
    devices[device_id].stop_training()
    device = devices[device_id]
    repo.save_device(device_id, device.name, device.entity_id, device.beacon_id)

    # Training may not produce a model if insufficient data was collected
    if device.model is not None and device.model.trained_model is not None:
        _persist_device_model(device_id, device, repo, settings)
        return {"detail": "Success"}
    else:
        return {
            "detail": "Training stopped but no model was produced. "
            "Ensure you train in at least 2 rooms with enough samples in each."
        }


@router.get("/{device_id}/model/cancel_training")
def cancel_training(device_id: str, devices: dict = Depends(get_devices)):
    if device_id not in devices:
        raise HTTPException(status_code=404, detail="Device not found")
    if not devices[device_id].training:
        raise HTTPException(status_code=400, detail="Device is not training")
    devices[device_id].cancel_training()
    return {"detail": "Success"}


@router.post("/{device_id}/model/retrain")
def retrain(
    device_id: str, devices: dict = Depends(get_devices), repo=Depends(get_repository), settings=Depends(get_settings)
):
    if device_id not in devices:
        raise HTTPException(status_code=404, detail="Device not found")
    if devices[device_id].training:
        raise HTTPException(status_code=400, detail="Device is already training")
    devices[device_id].retrain()
    device = devices[device_id]
    _persist_device_model(device_id, device, repo, settings)
    return {"detail": "Success"}


@router.post("/{device_id}/model/set_room/{room_id}")
def set_room(
    device_id: str,
    room_id: str,
    devices: dict = Depends(get_devices),
    rooms: dict = Depends(get_rooms),
):
    if device_id not in devices:
        raise HTTPException(status_code=404, detail="Device not found")
    if room_id not in rooms:
        raise HTTPException(status_code=404, detail="Room not found")
    device = devices[device_id]
    if not device.training or device.new_model is None:
        raise HTTPException(status_code=400, detail="Device is not training")
    device.new_model.set_room(room_id)
    return {"detail": "Success"}


@router.get("/{device_id}/model")
def get_model(device_id: str, devices: dict = Depends(get_devices)):
    if device_id not in devices:
        raise HTTPException(status_code=404, detail="Device not found")
    device = devices[device_id]
    if device.model is None:
        raise HTTPException(status_code=400, detail="Device has no model")
    return _device_to_response(device_id, device).model


@router.get("/{device_id}/signal_data")
def get_signal_data(device_id: str, devices: dict = Depends(get_devices)):
    if device_id not in devices:
        raise HTTPException(status_code=404, detail="Device not found")
    device = devices[device_id]
    if device.data_gatherer is None:
        return {"signals": {}}
    try:
        signals = device.data_gatherer()
    except Exception:
        signals = {}
    return {"signals": signals}


@router.get("/{device_id}/training_averages", response_model=TrainingAveragesResponse)
def get_training_averages(
    device_id: str,
    devices: dict = Depends(get_devices),
    rooms: dict = Depends(get_rooms),
):
    if device_id not in devices:
        raise HTTPException(status_code=404, detail="Device not found")
    device = devices[device_id]
    if device.model is None or device.model.data.empty:
        raise HTTPException(status_code=400, detail="Device has no model")

    df = device.model.data
    if "room" not in df.columns:
        raise HTTPException(status_code=400, detail="Device has no model")

    feature_cols = [c for c in df.columns if c != "room"]
    if not feature_cols:
        return TrainingAveragesResponse(rooms={}, feature_columns=[])

    result_rooms: dict[str, RoomAverages] = {}
    for room_id, group in df.groupby("room"):
        numeric = group[feature_cols].apply(pd.to_numeric, errors="coerce")
        means = numeric.mean(skipna=True)
        averages = {k: v for k, v in means.items() if pd.notna(v)}
        room_name = rooms[room_id].name if room_id in rooms else str(room_id)
        result_rooms[str(room_id)] = RoomAverages(name=room_name, averages=averages)

    return TrainingAveragesResponse(rooms=result_rooms, feature_columns=feature_cols)


def _compute_training_averages(model) -> dict:
    """Compute mean of each numeric feature column from the model's training data."""
    if model is None or model.data.empty:
        return {}
    df = model.data
    feature_cols = [c for c in df.columns if c != "room"]
    if not feature_cols:
        return {}
    numeric = df[feature_cols].apply(pd.to_numeric, errors="coerce")
    means = numeric.mean(skipna=True)
    return {k: v for k, v in means.items() if pd.notna(v)}


@router.get("/{device_id}/model/training_progress")
def get_training_progress(device_id: str, devices: dict = Depends(get_devices)):
    if device_id not in devices:
        raise HTTPException(status_code=404, detail="Device not found")
    device = devices[device_id]
    # During active training, progress lives on new_model (not model)
    if device.training and device.new_model is not None:
        progress = device.new_model.get_training_progress()
        if not progress:
            return {"training_averages": _compute_training_averages(device.new_model)}
        progress["training_averages"] = _compute_training_averages(device.new_model)
        return progress
    if device.model is not None:
        progress = device.model.get_training_progress()
        if not progress:
            return {"training_averages": _compute_training_averages(device.model)}
        progress["training_averages"] = _compute_training_averages(device.model)
        return progress
    raise HTTPException(status_code=400, detail="Device is not training")
