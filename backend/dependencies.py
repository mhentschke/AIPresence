from fastapi import Request


def get_ha_client(request: Request):
    return request.app.state.ha_client


def get_devices(request: Request):
    return request.app.state.devices


def get_trackers(request: Request):
    return request.app.state.trackers


def get_sensors(request: Request):
    return request.app.state.sensors


def get_rooms(request: Request):
    return request.app.state.rooms


def get_repository(request: Request):
    return request.app.state.repository


def get_data_gatherer(request: Request):
    """Returns a callable that gathers current data from all trackers and sensors."""
    def gather():
        data = {}
        for entity_id, tracker in {**request.app.state.trackers, **request.app.state.sensors}.items():
            temp_data = tracker.get_data()
            if isinstance(temp_data, dict):
                temp_data = {entity_id + "-" + str(key): val for key, val in temp_data.items()}
            else:
                temp_data = {entity_id: temp_data}
            data.update(temp_data)
        return data
    return gather
