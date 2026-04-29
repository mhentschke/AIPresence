"""Root conftest — mock Home Assistant modules so tests run without homeassistant installed."""

import datetime as _datetime
import enum as _enum
import sys
from types import ModuleType
from unittest.mock import MagicMock

_HA_MODULES = [
    "homeassistant",
    "homeassistant.config_entries",
    "homeassistant.core",
    "homeassistant.data_entry_flow",
    "homeassistant.components",
    "homeassistant.components.hassio",
    "homeassistant.components.bluetooth",
    "homeassistant.components.device_tracker",
    "homeassistant.components.sensor",
    "homeassistant.helpers",
    "homeassistant.helpers.aiohttp_client",
    "homeassistant.helpers.entity_platform",
    "homeassistant.const",
]

for name in _HA_MODULES:
    if name not in sys.modules:
        mod = ModuleType(name)
        mod.__dict__.setdefault("__path__", [])
        sys.modules[name] = mod

# ---------------------------------------------------------------------------
# Minimal stubs for HA classes used at import time
# ---------------------------------------------------------------------------

ce = sys.modules["homeassistant.config_entries"]


class _ConfigEntry:
    """Minimal stub for ConfigEntry."""

    def __init__(self):
        self.data = {}
        self.options = {}
        self.entry_id = "test_entry_id"
        self._unload_callbacks = []

    def async_on_unload(self, callback):
        self._unload_callbacks.append(callback)

    def add_update_listener(self, listener):
        return listener


ce.ConfigEntry = _ConfigEntry


def _noop_init_subclass(cls, **kw):
    pass


def _async_show_form(self, *, step_id, data_schema=None, errors=None):
    return {
        "type": "form",
        "step_id": step_id,
        "data_schema": data_schema,
        "errors": errors or {},
    }


def _async_create_entry(self, *, title, data):
    return {"type": "create_entry", "title": title, "data": data}


ce.ConfigFlow = type(
    "ConfigFlow",
    (),
    {
        "__init_subclass__": classmethod(_noop_init_subclass),
        "async_show_form": _async_show_form,
        "async_create_entry": _async_create_entry,
    },
)
ce.OptionsFlow = type(
    "OptionsFlow",
    (),
    {
        "async_show_form": _async_show_form,
        "async_create_entry": _async_create_entry,
    },
)

core = sys.modules["homeassistant.core"]
core.HomeAssistant = type("HomeAssistant", (), {})
core.callback = lambda fn: fn

flow = sys.modules["homeassistant.data_entry_flow"]
flow.FlowResult = dict

hassio = sys.modules["homeassistant.components.hassio"]
hassio.async_get_addon_info = MagicMock()
hassio.is_hassio = MagicMock()

# ---------------------------------------------------------------------------
# Bluetooth component stubs
# ---------------------------------------------------------------------------

bluetooth = sys.modules["homeassistant.components.bluetooth"]


class _BluetoothCallbackMatcher:
    """Minimal stub for BluetoothCallbackMatcher."""

    def __init__(self, **kwargs):
        pass


class _BluetoothChange:
    """Minimal stub for BluetoothChange."""

    ADVERTISEMENT = "advertisement"


class _BluetoothScanningMode:
    """Minimal stub for BluetoothScanningMode."""

    PASSIVE = "passive"
    ACTIVE = "active"


class _BluetoothServiceInfoBleak:
    """Minimal stub for BluetoothServiceInfoBleak."""

    def __init__(self, *, source="", address="", rssi=0, advertisement=None, **kwargs):
        self.source = source
        self.address = address
        self.rssi = rssi
        self.advertisement = advertisement


bluetooth.BluetoothCallbackMatcher = _BluetoothCallbackMatcher
bluetooth.BluetoothChange = _BluetoothChange
bluetooth.BluetoothScanningMode = _BluetoothScanningMode
bluetooth.BluetoothServiceInfoBleak = _BluetoothServiceInfoBleak
bluetooth.async_register_callback = MagicMock(return_value=MagicMock())

# ---------------------------------------------------------------------------
# homeassistant.helpers.event stub
# ---------------------------------------------------------------------------

_helpers_event = ModuleType("homeassistant.helpers.event")
_helpers_event.__path__ = []
sys.modules["homeassistant.helpers.event"] = _helpers_event
_helpers_event.async_track_time_interval = MagicMock(return_value=MagicMock())

# ---------------------------------------------------------------------------
# homeassistant.util.dt stub
# ---------------------------------------------------------------------------

_util = ModuleType("homeassistant.util")
_util.__path__ = []
sys.modules["homeassistant.util"] = _util

_util_dt = ModuleType("homeassistant.util.dt")
_util_dt.__path__ = []
sys.modules["homeassistant.util.dt"] = _util_dt


def _utcnow():
    return _datetime.datetime.now(_datetime.timezone.utc)


_util_dt.utcnow = _utcnow

# ---------------------------------------------------------------------------
# DataUpdateCoordinator stub
# ---------------------------------------------------------------------------

_helpers_update_coordinator = ModuleType("homeassistant.helpers.update_coordinator")
_helpers_update_coordinator.__path__ = []
sys.modules["homeassistant.helpers.update_coordinator"] = _helpers_update_coordinator


class _DataUpdateCoordinator:
    """Minimal stub for DataUpdateCoordinator."""

    def __init__(self, hass, logger, *, name, update_interval=None):
        self.hass = hass
        self.logger = logger
        self.name = name
        self.update_interval = update_interval
        self.data = None
        self.last_update_success = True
        self._listeners: list = []

    async def async_config_entry_first_refresh(self):
        self.data = await self._async_update_data()

    async def _async_update_data(self):
        raise NotImplementedError

    def async_add_listener(self, update_callback):
        self._listeners.append(update_callback)

        def remove_listener():
            self._listeners.remove(update_callback)

        return remove_listener


class _UpdateFailed(Exception):
    """Stub for UpdateFailed exception."""


_helpers_update_coordinator.DataUpdateCoordinator = _DataUpdateCoordinator
_helpers_update_coordinator.UpdateFailed = _UpdateFailed

# ---------------------------------------------------------------------------
# aiohttp_client stub
# ---------------------------------------------------------------------------

aiohttp_client = sys.modules["homeassistant.helpers.aiohttp_client"]
aiohttp_client.async_get_clientsession = MagicMock()

# ---------------------------------------------------------------------------
# Entity platform stub
# ---------------------------------------------------------------------------

entity_platform = sys.modules["homeassistant.helpers.entity_platform"]
entity_platform.AddEntitiesCallback = None  # type alias only

# ---------------------------------------------------------------------------
# Device tracker component stubs
# ---------------------------------------------------------------------------

device_tracker = sys.modules["homeassistant.components.device_tracker"]


class _SourceType(_enum.StrEnum):
    BLUETOOTH = "bluetooth"
    GPS = "gps"
    ROUTER = "router"


device_tracker.SourceType = _SourceType


class _TrackerEntity:
    """Minimal stub for TrackerEntity."""

    _attr_has_entity_name = False
    _attr_unique_id = None
    _attr_name = None

    @property
    def source_type(self):
        return None

    @property
    def location_name(self):
        return None

    @property
    def extra_state_attributes(self):
        return None

    @property
    def state(self):
        loc = self.location_name
        return loc if loc is not None else "unknown"


device_tracker.TrackerEntity = _TrackerEntity

# ---------------------------------------------------------------------------
# Sensor component stubs
# ---------------------------------------------------------------------------

sensor_mod = sys.modules["homeassistant.components.sensor"]


class _SensorStateClass(_enum.StrEnum):
    MEASUREMENT = "measurement"
    TOTAL = "total"
    TOTAL_INCREASING = "total_increasing"


sensor_mod.SensorStateClass = _SensorStateClass


class _SensorEntity:
    """Minimal stub for SensorEntity."""

    _attr_has_entity_name = False
    _attr_unique_id = None
    _attr_name = None
    _attr_native_value = None
    _attr_native_unit_of_measurement = None
    _attr_state_class = None

    @property
    def native_value(self):
        return self._attr_native_value

    @property
    def native_unit_of_measurement(self):
        return self._attr_native_unit_of_measurement

    @property
    def state_class(self):
        return self._attr_state_class


sensor_mod.SensorEntity = _SensorEntity

# ---------------------------------------------------------------------------
# CoordinatorEntity stub
# ---------------------------------------------------------------------------

_helpers_update_coordinator.CoordinatorEntity = type(
    "CoordinatorEntity",
    (),
    {
        "__init__": lambda self, coordinator: setattr(self, "coordinator", coordinator),
    },
)

# ---------------------------------------------------------------------------
# homeassistant.const stub
# ---------------------------------------------------------------------------

ha_const = sys.modules["homeassistant.const"]
ha_const.PERCENTAGE = "%"


class _Platform:
    """Minimal stub for homeassistant.const.Platform."""

    DEVICE_TRACKER = "device_tracker"
    SENSOR = "sensor"


ha_const.Platform = _Platform

# ---------------------------------------------------------------------------
# Entity registry stub
# ---------------------------------------------------------------------------

_helpers_entity_registry = ModuleType("homeassistant.helpers.entity_registry")
_helpers_entity_registry.__path__ = []
sys.modules["homeassistant.helpers.entity_registry"] = _helpers_entity_registry


class _EntityRegistry:
    """Minimal stub for EntityRegistry."""

    def __init__(self):
        self._entities: dict[str, str] = {}  # unique_id -> entity_id

    def async_get_entity_id(self, domain, platform, unique_id):
        return self._entities.get(unique_id)

    def async_remove(self, entity_id):
        self._entities = {k: v for k, v in self._entities.items() if v != entity_id}


_helpers_entity_registry.async_get = MagicMock(return_value=_EntityRegistry())
_helpers_entity_registry.EntityRegistry = _EntityRegistry
