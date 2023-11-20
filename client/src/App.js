import React, { useState, useEffect } from 'react'
import DeviceTable from './components/DeviceTable'
import DeviceEditModal from './components/DeviceEditModal'
import TrackerTable from './components/TrackerTable'
import TrackerEditModal from './components/TrackerEditModal'
import {Backend} from './Backend'

function App() {
    const [data, setData] = useState([{}])
    const [deviceEditModal, setDeviceEditModal] = useState(false)
    const [deviceCursor, setDeviceCursor] = useState({})
    const [trackerData, setTrackerData] = useState([{}])
    const [trackerEditModal, setTrackerEditModal] = useState(false)
    const [trackerCursor, setTrackerCursor] = useState({})
    const [sensorData, setSensorData] = useState([{}])
    const [sensorEditModal, setSensorEditModal] = useState(false)
    const [sensorCursor, setSensorCursor] = useState({})
    const [, forceUpdate] = useState()
    //const backend = new Backend();
    useEffect(() => {
        Backend.GetDevices().then( 
            data => {
                setData(data)
                console.log(data)
            }
        )
        Backend.GetTrackers().then(
            data => {
                setTrackerData(data)
                console.log(data)
            }
        )
        Backend.GetSensors().then(
            data => {
                setSensorData(data)
                console.log(data)
            }
        )
        /*fetch('/devices').then(
            res => res.json()
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
                }
                setData(data)
                console.log(data)
            }
        )*/
    }, [])
    return (
        <div>
            <h1>Devices</h1>
            <div class = "w3-responsive">
                <DeviceTable data={data} setData={setData} deviceEditModal={setDeviceEditModal} deviceSelector={setDeviceCursor} backend={Backend} forceUpdate={forceUpdate}/>
                <button onClick={() => {
                        setDeviceCursor(-1)
                        setDeviceEditModal(true)
                    }}>Add Device</button>
            </div> 
            <div class = "w3-responsive">
                <DeviceEditModal data={data} setData={setData} modal={deviceEditModal} setModal={setDeviceEditModal} deviceCursor={deviceCursor} backend={Backend} forceUpdate={forceUpdate}/>
            </div>
            <h1>Trackers</h1>
            <div class = "w3-responsive">
                <TrackerTable data={trackerData} setData={setTrackerData} trackerEditModal={setTrackerEditModal} trackerSelector={setTrackerCursor} backend={Backend} forceUpdate={forceUpdate}/>
                <button onClick={() => {
                        setTrackerCursor(-1)
                        setTrackerEditModal(true)
                    }}>Add Tracker</button>
            </div>
            <div class = "w3-responsive">
                <TrackerEditModal data={data} setData={setData} modal={trackerEditModal} setModal={setTrackerEditModal} trackerCursor={trackerCursor} backend={Backend} forceUpdate={forceUpdate}/>
            </div>
        </div>
    )
}

export default App