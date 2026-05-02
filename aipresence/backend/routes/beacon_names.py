from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import get_beacon_names, get_repository
from ..schemas import BeaconNameResponse, BeaconNameUpdate

router = APIRouter()


@router.get("", response_model=list[BeaconNameResponse])
def list_beacon_names(beacon_names: dict = Depends(get_beacon_names)):
    return [BeaconNameResponse(beacon_id=bid, friendly_name=name) for bid, name in beacon_names.items()]


@router.put("/{beacon_id:path}")
def set_beacon_name(
    beacon_id: str,
    body: BeaconNameUpdate,
    beacon_names: dict = Depends(get_beacon_names),
    repo=Depends(get_repository),
):
    if not body.friendly_name.strip():
        raise HTTPException(status_code=400, detail="friendly_name must not be empty")
    beacon_names[beacon_id] = body.friendly_name
    repo.save_beacon_name(beacon_id, body.friendly_name)
    return {"detail": "Success"}


@router.delete("/{beacon_id:path}")
def delete_beacon_name(
    beacon_id: str,
    beacon_names: dict = Depends(get_beacon_names),
    repo=Depends(get_repository),
):
    if beacon_id not in beacon_names:
        raise HTTPException(status_code=404, detail="Beacon name not found")
    del beacon_names[beacon_id]
    repo.delete_beacon_name(beacon_id)
    return {"detail": "Success"}
