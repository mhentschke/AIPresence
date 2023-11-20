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
            .then(response => alert("response. status: " + response.status))
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
        .then(response => alert("response. status: " + response.status))
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
            .then(response => alert("response. status: " + response.status))
        }
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
            .then(response => alert("response. status: " + response.status))
        }
    }

    static CreateTracker(tracker) {
        // POST on trackers
        fetch('/trackers', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(tracker),
        })
        .then(response => alert("response. status: " + response.status))
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
            .then(response => alert("response. status: " + response.status))
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


}
