import logging
import re

from fastapi import APIRouter, Depends, HTTPException

from ..classes import _BEACON_MONITOR_META_KEYS, BeaconMonitor
from ..datasource import DataSourceUnavailableError
from ..dependencies import (
    get_beacon_monitors,
    get_beacon_names,
    get_data_source,
    get_devices,
    get_repository,
)
from ..schemas import BeaconMonitorResponse, DiscoveredBeacon

logger = logging.getLogger(__name__)

# Patterns for classifying beacon identifier types
_MAC_PATTERN = re.compile(r"^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$")
_IBEACON_PATTERN = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}_\d+_\d+$")

router = APIRouter()


def _classify_identifier(beacon_id: str) -> str:
    """Classify a beacon identifier as 'ibeacon', 'mac', or 'unknown'."""
    if _IBEACON_PATTERN.match(beacon_id):
        return "ibeacon"
    if _MAC_PATTERN.match(beacon_id):
        return "mac"
    return "unknown"


@router.get("/beacons", response_model=list[DiscoveredBeacon])
def discover_beacons(
    beacon_monitors: dict = Depends(get_beacon_monitors),
    beacon_names: dict = Depends(get_beacon_names),
    devices: dict = Depends(get_devices),
    data_source=Depends(get_data_source),
):
    """Discover all beacons currently visible to registered monitors."""
    # Aggregate: beacon_id -> {monitors: [{entity_id, signal_value}]}
    aggregated: dict[str, list[dict]] = {}

    for monitor_eid in beacon_monitors:
        try:
            state = data_source.get_entity_state(monitor_eid)
            for key, value in state.attributes.items():
                if key in _BEACON_MONITOR_META_KEYS:
                    continue
                if not isinstance(value, (int, float)):
                    continue
                aggregated.setdefault(key, []).append({"entity_id": monitor_eid, "signal_value": value})
        except DataSourceUnavailableError:
            logger.debug("Monitor %s unavailable during beacon discovery", monitor_eid)
            continue
        except Exception:
            logger.warning("Unexpected error querying monitor %s during beacon discovery", monitor_eid, exc_info=True)
            continue

    # Build device lookup: beacon_id -> (device_id, device_name)
    device_by_beacon: dict[str, tuple[str, str]] = {}
    for dev_id, dev in devices.items():
        if dev.beacon_id:
            device_by_beacon[dev.beacon_id] = (dev_id, dev.name)

    # Build response
    results: list[DiscoveredBeacon] = []
    for beacon_id, monitors in aggregated.items():
        strongest = max((m["signal_value"] for m in monitors), default=None)
        dev_id, dev_name = device_by_beacon.get(beacon_id, (None, None))
        results.append(
            DiscoveredBeacon(
                beacon_id=beacon_id,
                friendly_name=beacon_names.get(beacon_id),
                identifier_type=_classify_identifier(beacon_id),
                device_name=dev_name,
                device_id=dev_id,
                monitors=monitors,
                strongest_signal=strongest,
            )
        )

    # Sort by number of detecting monitors (most visible first)
    results.sort(key=lambda b: len(b.monitors), reverse=True)
    return results


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
