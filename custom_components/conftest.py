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
    "homeassistant.helpers",
    "homeassistant.helpers.aiohttp_client",
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
