from fastapi import Request


def get_data_source(request: Request):
    """Returns the active data source (HA or standalone)."""
    return request.app.state.data_source


def get_settings(request: Request):
    """Returns the application settings."""
    return request.app.state.settings


def get_devices(request: Request):
    return request.app.state.devices


def get_trackers(request: Request):
    return request.app.state.trackers


def get_sensors(request: Request):
    return request.app.state.sensors


def get_rooms(request: Request):
    return request.app.state.rooms


def get_beacon_monitors(request: Request):
    return request.app.state.beacon_monitors


def get_repository(request: Request):
    return request.app.state.repository


def get_data_gatherer(request: Request):
    """Returns a factory that creates per-device data gatherers."""
    from .classes import _BEACON_MONITOR_META_KEYS

    def make_gatherer(device_entity_id, device_beacon_id):
        def gather():
            data = {}
            data_source = request.app.state.data_source

            # Device's own monitor readings
            if device_entity_id is not None:
                try:
                    state = data_source.get_entity_state(device_entity_id)
                    for key, value in state.attributes.items():
                        if key in _BEACON_MONITOR_META_KEYS:
                            continue
                        if isinstance(value, (int, float)):
                            data[device_entity_id + "-" + str(key)] = value
                except Exception:
                    pass

            # Fixed monitors seeing this device's beacon
            if device_beacon_id is not None:
                for monitor_eid, monitor in request.app.state.beacon_monitors.items():
                    try:
                        state = data_source.get_entity_state(monitor_eid)
                        for key, value in state.attributes.items():
                            if key == device_beacon_id and isinstance(value, (int, float)):
                                data[monitor_eid + "-" + str(key)] = value
                    except Exception:
                        pass

            # Binary sensors
            for sensor_eid, sensor in request.app.state.sensors.items():
                try:
                    temp_data = sensor.get_data()
                    if isinstance(temp_data, dict):
                        for key, val in temp_data.items():
                            data[sensor_eid + "-" + str(key)] = val
                    else:
                        data[sensor_eid] = temp_data
                except Exception:
                    pass

            return data

        return gather

    return make_gatherer
