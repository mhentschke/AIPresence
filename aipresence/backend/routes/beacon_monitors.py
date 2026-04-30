from fastapi import APIRouter, Depends, HTTPException

from ..classes import BeaconMonitor
from ..dependencies import get_beacon_monitors, get_data_source, get_repository
from ..schemas import BeaconMonitorResponse

router = APIRouter()


@router.get("", response_model=list[BeaconMonitorResponse])
def list_beacon_monitors(beacon_monitors: dict = Depends(get_beacon_monitors)):
    return [BeaconMonitorResponse(id=k, entity_id=v.entity_id) for k, v in beacon_monitors.items()]


@router.post("/{entity_id}")
def create_beacon_monitor(
    entity_id: str,
    skip_validation: bool = False,
    beacon_monitors: dict = Depends(get_beacon_monitors),
    data_source=Depends(get_data_source),
    repo=Depends(get_repository),
):
    if entity_id in beacon_monitors:
        raise HTTPException(status_code=409, detail="Beacon monitor already exists")
    if not skip_validation and not data_source.check_entity_exists(entity_id):
        raise HTTPException(status_code=404, detail="Entity not found in Home Assistant")
    beacon_monitors[entity_id] = BeaconMonitor(entity_id=entity_id, data_source=data_source)
    repo.save_beacon_monitor(entity_id)
    return {"detail": "Success"}


@router.delete("/{entity_id}")
def delete_beacon_monitor(
    entity_id: str,
    beacon_monitors: dict = Depends(get_beacon_monitors),
    repo=Depends(get_repository),
):
    if entity_id not in beacon_monitors:
        raise HTTPException(status_code=404, detail="Beacon monitor not found")
    del beacon_monitors[entity_id]
    repo.delete_beacon_monitor(entity_id)
    return {"detail": "Success"}
