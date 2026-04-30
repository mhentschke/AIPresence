/**
 * Resolve API paths relative to the current page URL.
 * In HA ingress the app is served under /api/hassio_ingress/<token>/,
 * so absolute paths like "/devices" would miss the prefix.
 * Using a relative path (no leading slash) lets the browser resolve
 * against the current <base> or page URL automatically.
 */
function rel(path) {
  // Strip leading slash so the browser resolves relative to the page origin
  return path.startsWith('/') ? path.slice(1) : path;
}

async function apiCall(url, options = {}) {
  const response = await fetch(rel(url), options);
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
      if (data[d].model === null || !data[d].model?.trained_model_stats) {
        data[d].trained = false;
        data[d].accuracy = "-";
      } else {
        data[d].trained = true;
        data[d].accuracy = data[d].model.trained_model_stats.accuracy;
      }
      const hasEntity = data[d].entity_id != null;
      const hasBeacon = data[d].beacon_id != null;
      if (hasEntity && hasBeacon) {
        data[d].identifier = data[d].entity_id;
        data[d].type = "Both";
      } else if (hasEntity) {
        data[d].identifier = data[d].entity_id;
        data[d].type = "Monitor";
      } else if (hasBeacon) {
        data[d].identifier = data[d].beacon_id;
        data[d].type = "Beacon";
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
    const response = await fetch(rel('/device/check_entity_id/' + entityId));
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
    const response = await fetch(rel('/devices/' + device_id + '/location'));
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

  // ---- Beacon Monitors ----

  static async GetBeaconMonitors() {
    const resp = await apiCall('/beacon_monitors');
    return resp.json();
  }

  static async CreateBeaconMonitor(entityId) {
    const resp = await apiCall('/beacon_monitors/' + entityId, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    return resp.json();
  }

  static async RemoveBeaconMonitor(entityId) {
    const resp = await apiCall('/beacon_monitors/' + entityId, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
    });
    return resp.json();
  }

  // ---- Training ----

  static async GetTrainingProgress(device_id) {
    const response = await fetch(rel('/devices/' + device_id + '/model/training_progress'));
    if (response.ok) {
      return response.json();
    }
    return null;
  }

  static async GetSignalData(device_id) {
    const response = await fetch(rel('/devices/' + device_id + '/signal_data'));
    if (response.ok) {
      return response.json();
    }
    return null;
  }

  static async GetTrainingAverages(device_id) {
    const response = await fetch(rel('/devices/' + device_id + '/training_averages'));
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
    const response = await fetch(rel(url));
    if (response.status === 503) return null;
    if (!response.ok) {
      throw new Error(`API error ${response.status}`);
    }
    return response.json();
  }

  // ---- Backup & Restore ----

  static async CreateBackup() {
    const response = await fetch(rel('/admin/backup'));
    if (!response.ok) {
      const text = await response.text();
      throw new Error(`Backup failed: ${text}`);
    }
    const blob = await response.blob();
    const disposition = response.headers.get('Content-Disposition');
    let filename = 'aipresence_backup.tar.gz';
    if (disposition) {
      const match = disposition.match(/filename=(.+)/);
      if (match) filename = match[1];
    }
    // Trigger browser download
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  static async RestoreBackup(file) {
    const formData = new FormData();
    formData.append('file', file);
    const resp = await apiCall('/admin/restore', {
      method: 'POST',
      body: formData,
    });
    return resp.json();
  }
}
