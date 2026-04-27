"""Pydantic request/response/storage models.

Replaces both api_schemas.py (API serialization) and the schema portion
of storage.py (JSON persistence) with a single set of pydantic models.
"""

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
    def _exactly_one_id(self) -> "DeviceCreate":
        if self.entity_id is None and self.beacon_id is None:
            raise ValueError("Either entity_id or beacon_id must be specified")
        if self.entity_id is not None and self.beacon_id is not None:
            raise ValueError("Only one of entity_id or beacon_id can be specified")
        return self


class TrackerCreate(BaseModel):
    mobile: bool = False
    whitelist: bool = False
    blacklist: bool = False


class TrainingStart(BaseModel):
    room: str
    append: bool = False


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


class RoomResponse(BaseModel):
    id: str
    name: str
    color: str


# ---------------------------------------------------------------------------
# Storage Models (JSON file persistence)
# ---------------------------------------------------------------------------


class ModelStatsStorage(BaseModel):
    accuracy: float
    model_type: str
    classification_report: dict


class ModelStorage(BaseModel):
    data_path: str
    trained_model_stats: ModelStatsStorage
    trained_columns: list[str]


class DeviceStorage(BaseModel):
    name: str
    entity_id: Optional[str] = None
    beacon_id: Optional[str] = None
    model: Optional[ModelStorage] = None


class TrackerStorage(BaseModel):
    entity_id: str
    mobile: bool = False
    whitelist: bool = False
    blacklist: bool = False


class SensorStorage(BaseModel):
    entity_id: str
    mobile: bool = False


class RoomStorage(BaseModel):
    id: str
    name: str
    color: str = "#ffffffff"
