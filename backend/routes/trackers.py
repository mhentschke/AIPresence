from fastapi import APIRouter, Depends, HTTPException

import storage
from classes import Smartphone_Tracker
from dependencies import get_ha_client, get_trackers
from schemas import TrackerCreate, TrackerResponse

router = APIRouter()


@router.get("/", response_model=list[TrackerResponse])
def list_trackers(trackers: dict = Depends(get_trackers)):
    result = []
    for key, tracker in trackers.items():
        result.append(
            TrackerResponse(
                id=key,
                entity_id=tracker.entity_id,
                mobile=tracker.mobile,
                whitelist=tracker.whitelist,
                blacklist=tracker.blacklist,
            )
        )
    return result


@router.post("/{entity_id}")
def create_tracker(
    entity_id: str,
    body: TrackerCreate,
    trackers: dict = Depends(get_trackers),
    client=Depends(get_ha_client),
):
    if entity_id in trackers:
        raise HTTPException(
            status_code=409,
            detail="Already exists. To overwrite, please use the PUT method",
        )
    trackers[entity_id] = Smartphone_Tracker(
        entity_id,
        ha_client=client,
        mobile=body.mobile,
        whitelist=body.whitelist,
        blacklist=body.blacklist,
    )
    storage.save_trackers(trackers)
    return {"detail": "Success"}


@router.put("/{entity_id}")
def update_tracker(
    entity_id: str,
    body: TrackerCreate,
    trackers: dict = Depends(get_trackers),
    client=Depends(get_ha_client),
):
    if entity_id not in trackers:
        raise HTTPException(status_code=404, detail="Entity not found")
    trackers[entity_id] = Smartphone_Tracker(
        entity_id,
        ha_client=client,
        mobile=body.mobile,
        whitelist=body.whitelist,
        blacklist=body.blacklist,
    )
    storage.save_trackers(trackers)
    return {"detail": "Success"}


@router.delete("/{entity_id}")
def delete_tracker(entity_id: str, trackers: dict = Depends(get_trackers)):
    if entity_id not in trackers:
        raise HTTPException(status_code=404, detail="Entity not found")
    del trackers[entity_id]
    storage.save_trackers(trackers)
    return {"detail": "Success"}
