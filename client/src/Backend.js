function handle_generic_response(response){
    if (response.status !== 200) {
        alert("Request to Backend Failed: " + response.status + " " + response.statusText)
    }
}

function handle_request_response(response){
    if (response.status === 200) {
        console.log("Request to Backend Succeeded: " + response.status + " " + response.statusText)
        return response.json()
    }
    else {
        alert("Request to Backend Failed: " + response.status + " " + response.statusText + "\n" + response.text())
        return null
    }
}

export class Backend {
    constructor() {

    }

    static GetDevices() {
        // GET on devices
        return new Promise((resolve, reject) => {
            fetch('/devices').then(
                response => response.json()
            ).then(
                data => {
                    for(var d = 0; d < data.length; d++) {
                        if (data[d].model === null) {
                            data[d].trained = false
                            data[d].accuracy = "-"
                        }
                        else{
                            data[d].trained = true
                            data[d].accuracy = data[d].model.trained_model_stats.accuracy
                        }
                        console.log(data[d].entity_id + "  " + data[d].beacon_id)
                        if (data[d].beacon_id !== undefined) {
                            data[d].identifier = data[d].beacon_id
                            data[d].type = "Beacon"                            
                        }
                        else if (data[d].entity_id !== undefined) {
                            data[d].identifier = data[d].entity_id
                            data[d].type = "Tracker"
                        }
                        else {
                            data[d].identifier = "-"
                            data[d].type = "-"
                        }
                        if (data[d].location === undefined) {
                            data[d].location = "-"
                        }
                    }
                    resolve(data)
                }
            )
        })
    }

    static CheckEntityId(entityId) {
        // GET on entities/:id
        return new Promise((resolve, reject) => {
            fetch('/device/check_entity_id/' + entityId).then(
                response => {
                    if (response.status === 200) {
                        resolve(true)
                    }
                    else {
                        resolve(false)
                    }
                }
            )
        })
    }
    
    static UpdateDevice(device) {
        // PUT on devices/:id
        console.log("Device being updated:")
        console.log(device)
        if (device.id === undefined) {
            alert("Device ID is undefined")
        }
        else {
            fetch('/devices/' + device.id, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(device),
            })
            .then(response => handle_generic_response)
        }
    }

    static CreateDevice(device) {
        // POST on devices
        fetch('/devices', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(device),
        })
        .then(response => handle_generic_response)
    }

    static RemoveDevice(device) {
        // DELETE on devices/:id
        console.log("Device being updated:")
        console.log(device)
        if (device.id === undefined) {
            alert("Device ID is undefined")
        }
        else {
            fetch('/devices/' + device.id, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                },
            })
            .then(response => handle_generic_response)
        }
    }

    static GetDeviceLocations() {
        // GET on device_locations
        return new Promise((resolve, reject) => {
            fetch('/devices/location').then(
                response => response.json()
            ).then(
                data => {
                    resolve(data)
                }
            )
        })
    }

    static GetDeviceLocation(device_id) {
        // GET on devices/:id/location
        return new Promise((resolve, reject) => {
            fetch('/devices/' + device_id + '/location').then(
                response => {
                    if (response.status === 200) {
                        resolve(response.json())
                    }
                    else {
                        console.log("Location Request Failed: " + response.status + " " + response.statusText)
                        resolve(null)
                    }
                }
            )
        })
    }

    static GetTrackers() {
        // GET on trackers
        return new Promise((resolve, reject) => {
            fetch('/trackers').then(
                response => response.json()
            ).then(
                data => {
                    for(var d = 0; d < data.length; d++) {
                        if (data[d].whitelist === null) {
                            data[d].whitelist = false
                        }
                        if (data[d].blacklist === null) {
                            data[d].blacklist = false
                        }
                    }
                    resolve(data)
                }
            )
        })
    }

    static UpdateTracker(tracker) {
        // PUT on trackers/:id
        console.log("Tracker being updated:")
        console.log(tracker)
        if (tracker.id === undefined) {
            alert("Tracker ID is undefined")
        }
        else {
            fetch('/trackers/' + tracker.id, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(tracker),
            })
            .then(response => handle_generic_response)
        }
    }

    static CreateTracker(tracker) {
        // POST on trackers
        fetch('/trackers/'+tracker.entity_id, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(tracker),
        })
        .then(response => handle_generic_response)
    }

    static RemoveTracker(tracker) {
        // DELETE on trackers/:id
        console.log("Tracker being updated:")
        console.log(tracker)
        if (tracker.id === undefined) {
            alert("Tracker ID is undefined")
        }
        else {
            fetch('/trackers/' + tracker.id, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                },
            })
            .then(response => handle_generic_response)
        }
    }

    static GetSensors() {
        // GET on sensors
        return new Promise((resolve, reject) => {
            fetch('/sensors').then(
                response => response.json()
            ).then(
                data => {
                    resolve(data)
                }
            )
        })
    }

    static CreateSensor(sensor) {
        // POST on sensors
        fetch('/sensors/' + sensor.entity_id, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(sensor),
        })
        .then(response => handle_generic_response)
    }

    static RemoveSensor(sensor) {
        // DELETE on sensors/:id
        console.log("Sensor being updated:")
        console.log(sensor)
        if (sensor.id === undefined) {
            alert("Sensor ID is undefined")
        }
        else {
            fetch('/sensors/' + sensor.id, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                },
            })
            .then(response => handle_generic_response)
        }
    }

    static GetRooms() {
        // GET on rooms
        return new Promise((resolve, reject) => {
            fetch('/rooms').then(
                response => response.json()
            ).then(
                data => {
                    resolve(data)
                }
            )
        })
    }

    static UpdateRoom(room) {
        // PUT on rooms/:id
        console.log("Room being updated:")
        console.log(room)
        if (room.id === undefined) {
            alert("Room ID is undefined")
        }
        else {
            fetch('/rooms/' + room.id, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(room),
            })
            .then(response => handle_generic_response)
        }
    }

    static CreateRoom(room) {
        // POST on rooms
        fetch('/rooms', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(room),
        })
        .then(response => handle_generic_response)
    }

    static RemoveRoom(room) {
        // DELETE on rooms/:id
        console.log("Room being updated:")
        console.log(room)
        if (room.id === undefined) {
            alert("Room ID is undefined")
        }
        else {
            fetch('/rooms/' + room.id, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                },
            })
            .then(response => handle_generic_response)
        }
    }

    static GetTrainingProgress(device_id) {
        // GET on devices/:id/model/training_progress
        return new Promise((resolve, reject) => {
            fetch('/devices/' + device_id + '/model/training_progress').then(
                response => {
                    if (response.status === 200) {
                        resolve(response.json())
                    }
                    else {
                        console.log("Training Progress Request Failed: " + response.status + " " + response.statusText)
                        resolve(null)
                    }
                }
            )
        })
    }

    static StartTraining(device_id, room_id, overwrite) {
        // POST on devices/:id/model/train
        fetch('/devices/' + device_id + '/model/start_training', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({room: room_id, append: !overwrite}),
        })
        .then(response => handle_generic_response)
    }

    static StopTraining(device_id) {
        // GET on devices/:id/model/stop_training
        fetch('/devices/' + device_id + '/model/stop_training', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
        })
        .then(response => handle_generic_response)
    }

    static CancelTraining(device_id) {
        // GET on devices/:id/model/cancel_training
        fetch('/devices/' + device_id + '/model/cancel_training', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
        })
        .then(response => handle_generic_response)
    }

    static ChangeRoom(device_id, room_id) {
        // POST on devices/:id/model/set_room/:room_id
        fetch('/devices/' + device_id + '/model/set_room/' + room_id, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        })
    }
}
