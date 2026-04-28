async function apiCall(url, options = {}) {
  const response = await fetch(url, options);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`API error ${response.status}: ${text}`);
  }
  return response;
}

export class Backend {
  // ---- Devices ----

  static async GetDevices() {
    const resp = await apiCall('/devices');
    const data = await resp.json();
    for (let d = 0; d < data.length; d++) {
      if (data[d].model === null) {
        data[d].trained = false;
        data[d].accuracy = "-";
      } else {
        data[d].trained = true;
        data[d].accuracy = data[d].model.trained_model_stats.accuracy;
      }
      if (data[d].beacon_id !== undefined) {
        data[d].identifier = data[d].beacon_id;
        data[d].type = "Beacon";
      } else if (data[d].entity_id !== undefined) {
        data[d].identifier = data[d].entity_id;
        data[d].type = "Tracker";
      } else {
        data[d].identifier = "-";
        data[d].type = "-";
      }
      if (data[d].location === undefined) {
        data[d].location = "-";
      }
    }
    return data;
  }

  static async CheckEntityId(entityId) {
    const response = await fetch('/device/check_entity_id/' + entityId);
    return response.status === 200;
  }

  static async CreateDevice(device) {
    const resp = await apiCall('/devices', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(device),
    });
    return resp.json();
  }

  static async UpdateDevice(device) {
    const resp = await apiCall('/devices/' + device.id, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(device),
    });
    return resp.json();
  }

  static async RemoveDevice(device) {
    const resp = await apiCall('/devices/' + device.id, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
    });
    return resp.json();
  }

  static async GetDeviceLocations() {
    const resp = await apiCall('/devices/location');
    return resp.json();
  }

  static async GetDeviceLocation(device_id) {
    const response = await fetch('/devices/' + device_id + '/location');
    if (response.ok) {
      return response.json();
    }
    return null;
  }

  // ---- Trackers ----

  static async GetTrackers() {
    const resp = await apiCall('/trackers');
    const data = await resp.json();
    for (let d = 0; d < data.length; d++) {
      if (data[d].whitelist === null) {
        data[d].whitelist = false;
      }
      if (data[d].blacklist === null) {
        data[d].blacklist = false;
      }
    }
    return data;
  }

  static async CreateTracker(tracker) {
    const resp = await apiCall('/trackers/' + tracker.entity_id, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(tracker),
    });
    return resp.json();
  }

  static async UpdateTracker(tracker) {
    const resp = await apiCall('/trackers/' + tracker.id, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(tracker),
    });
    return resp.json();
  }

  static async RemoveTracker(tracker) {
    const resp = await apiCall('/trackers/' + tracker.id, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
    });
    return resp.json();
  }

  // ---- Sensors ----

  static async GetSensors() {
    const resp = await apiCall('/sensors');
    return resp.json();
  }

  static async CreateSensor(sensor) {
    const resp = await apiCall('/sensors/' + sensor.entity_id, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(sensor),
    });
    return resp.json();
  }

  static async UpdateSensor(sensor) {
    const resp = await apiCall('/sensors/' + sensor.entity_id, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mobile: sensor.mobile }),
    });
    return resp.json();
  }

  static async RemoveSensor(sensor) {
    const resp = await apiCall('/sensors/' + sensor.id, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
    });
    return resp.json();
  }

  // ---- Rooms ----

  static async GetRooms() {
    const resp = await apiCall('/rooms');
    return resp.json();
  }

  static async CreateRoom(room) {
    const resp = await apiCall('/rooms', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(room),
    });
    return resp.json();
  }

  static async UpdateRoom(room) {
    const resp = await apiCall('/rooms/' + room.id, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(room),
    });
    return resp.json();
  }

  static async RemoveRoom(room) {
    const resp = await apiCall('/rooms/' + room.id, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
    });
    return resp.json();
  }

  // ---- Training ----

  static async GetTrainingProgress(device_id) {
    const response = await fetch('/devices/' + device_id + '/model/training_progress');
    if (response.ok) {
      return response.json();
    }
    return null;
  }

  static async StartTraining(device_id, room_id, overwrite) {
    const resp = await apiCall('/devices/' + device_id + '/model/start_training', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ room: room_id, append: !overwrite }),
    });
    return resp.json();
  }

  static async StopTraining(device_id) {
    const resp = await apiCall('/devices/' + device_id + '/model/stop_training');
    return resp.json();
  }

  static async CancelTraining(device_id) {
    const resp = await apiCall('/devices/' + device_id + '/model/cancel_training');
    return resp.json();
  }

  static async ChangeRoom(device_id, room_id) {
    const resp = await apiCall('/devices/' + device_id + '/model/set_room/' + room_id, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    return resp.json();
  }

  // ---- Home Assistant Entities ----

  static async GetHAEntities(domain) {
    const url = domain ? `/ha/entities?domain=${domain}` : '/ha/entities';
    const response = await fetch(url);
    if (response.status === 503) return null;
    if (!response.ok) {
      throw new Error(`API error ${response.status}`);
    }
    return response.json();
  }
}
