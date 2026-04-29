"""Root conftest — mock Home Assistant modules so tests run without homeassistant installed."""

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
ce.ConfigEntry = type("ConfigEntry", (), {})


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

    async def async_config_entry_first_refresh(self):
        self.data = await self._async_update_data()

    async def _async_update_data(self):
        raise NotImplementedError


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

import enum as _enum  # noqa: E402

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
