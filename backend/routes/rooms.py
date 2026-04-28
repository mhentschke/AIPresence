import uuid

from fastapi import APIRouter, Depends, HTTPException

from .. import storage
from ..classes import Room
from ..dependencies import get_rooms
from ..schemas import RoomCreate, RoomResponse

router = APIRouter()


@router.get("", response_model=list[RoomResponse])
def list_rooms(rooms: dict = Depends(get_rooms)):
    result = []
    for key, room in rooms.items():
        result.append(
            RoomResponse(id=key, name=room.name, color=room.color)
        )
    return result


@router.post("")
def create_room(body: RoomCreate, rooms: dict = Depends(get_rooms)):
    room_id = str(uuid.uuid4())
    rooms[room_id] = Room(room_id, body.name, body.color)
    storage.save_rooms(rooms)
    return room_id


@router.get("/{room_id}", response_model=RoomResponse)
def get_room(room_id: str, rooms: dict = Depends(get_rooms)):
    if room_id not in rooms:
        raise HTTPException(status_code=404, detail="Room not found")
    room = rooms[room_id]
    return RoomResponse(id=room_id, name=room.name, color=room.color)


@router.put("/{room_id}")
def update_room(room_id: str, body: RoomCreate, rooms: dict = Depends(get_rooms)):
    rooms[room_id] = Room(room_id, body.name, body.color)
    storage.save_rooms(rooms)
    return {"detail": "Success"}


@router.delete("/{room_id}")
def delete_room(room_id: str, rooms: dict = Depends(get_rooms)):
    if room_id not in rooms:
        raise HTTPException(status_code=404, detail="Room not found")
    del rooms[room_id]
    storage.save_rooms(rooms)
    return {"detail": "Success"}
