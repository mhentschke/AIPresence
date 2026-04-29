"""Pydantic request/response models for the API layer."""

from typing import Optional

from pydantic import BaseModel, model_validator

# ---------------------------------------------------------------------------
# API Request Models
# ---------------------------------------------------------------------------


class RoomCreate(BaseModel):
    name: str
    color: str = "#ffffffff"


class DeviceCreate(BaseModel):
    name: str
    entity_id: Optional[str] = None
    beacon_id: Optional[str] = None

    @model_validator(mode="after")
    def _at_least_one_id(self) -> "DeviceCreate":
        if self.entity_id is None and self.beacon_id is None:
            raise ValueError("At least one of entity_id or beacon_id must be specified")
        return self


class TrackerCreate(BaseModel):
    mobile: bool = False
    whitelist: bool = False
    blacklist: bool = False


class TrainingStart(BaseModel):
    room: str
    append: bool = False


class SensorUpdate(BaseModel):
    mobile: bool


# ---------------------------------------------------------------------------
# API Response Models
# ---------------------------------------------------------------------------


class ModelStatsResponse(BaseModel):
    accuracy: float
    model_type: str
    classification_report: dict


class ModelResponse(BaseModel):
    trained_model_stats: Optional[ModelStatsResponse] = None


class DeviceResponse(BaseModel):
    id: str
    name: str
    entity_id: Optional[str] = None
    beacon_id: Optional[str] = None
    model: Optional[ModelResponse] = None


class TrackerResponse(BaseModel):
    id: str
    entity_id: str
    mobile: bool
    whitelist: bool
    blacklist: bool


class SensorResponse(BaseModel):
    id: str
    entity_id: str
    mobile: bool


class BeaconMonitorResponse(BaseModel):
    id: str
    entity_id: str


class RoomResponse(BaseModel):
    id: str
    name: str
    color: str
