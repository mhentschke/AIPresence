from fastapi import APIRouter, Depends, HTTPException

from ..classes import Binary_Sensor
from ..dependencies import get_data_source, get_repository, get_sensors
from ..schemas import SensorResponse, SensorUpdate

router = APIRouter()


@router.get("", response_model=list[SensorResponse])
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
    data_source=Depends(get_data_source),
    repo=Depends(get_repository),
):
    if entity_id in sensors:
        raise HTTPException(
            status_code=409,
            detail="Already exists. To overwrite, please use the PUT method",
        )
    sensors[entity_id] = Binary_Sensor(entity_id, data_source=data_source)
    repo.save_sensor(entity_id, False)
    return {"id": entity_id}


@router.put("/{entity_id}")
def update_sensor(
    entity_id: str,
    body: SensorUpdate,
    sensors: dict = Depends(get_sensors),
    repo=Depends(get_repository),
):
    if entity_id not in sensors:
        raise HTTPException(status_code=404, detail="Entity not found")
    sensors[entity_id].mobile = body.mobile
    repo.save_sensor(entity_id, body.mobile)
    return {"detail": "Success"}


@router.delete("/{entity_id}")
def delete_sensor(entity_id: str, sensors: dict = Depends(get_sensors), repo=Depends(get_repository)):
    if entity_id not in sensors:
        raise HTTPException(status_code=404, detail="Entity not found")
    del sensors[entity_id]
    repo.delete_sensor(entity_id)
    return {"detail": "Success"}
