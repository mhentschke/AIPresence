from fastapi import APIRouter, Depends, HTTPException

import storage
from classes import Binary_Sensor
from dependencies import get_ha_client, get_sensors
from schemas import SensorResponse

router = APIRouter()


@router.get("/", response_model=list[SensorResponse])
def list_sensors(sensors: dict = Depends(get_sensors)):
    result = []
    for key, sensor in sensors.items():
        result.append(
            SensorResponse(
                id=key,
                entity_id=sensor.entity_id,
                mobile=sensor.mobile,
            )
        )
    return result


@router.post("/{entity_id}")
def create_sensor(
    entity_id: str,
    sensors: dict = Depends(get_sensors),
    client=Depends(get_ha_client),
):
    if entity_id in sensors:
        raise HTTPException(
            status_code=409,
            detail="Already exists. To overwrite, please use the PUT method",
        )
    sensors[entity_id] = Binary_Sensor(entity_id, ha_client=client)
    storage.save_sensors(sensors)
    return {"detail": "Success"}


@router.delete("/{entity_id}")
def delete_sensor(entity_id: str, sensors: dict = Depends(get_sensors)):
    if entity_id not in sensors:
        raise HTTPException(status_code=404, detail="Entity not found")
    del sensors[entity_id]
    storage.save_sensors(sensors)
    return {"detail": "Success"}
