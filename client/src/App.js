import React, { useState, useEffect } from 'react'
import DeviceTable from './components/DeviceTable'
import DeviceEditModal from './components/DeviceEditModal'
import DeviceTrainingModal from './components/DeviceTrainingModal'
import TrackerTable from './components/TrackerTable'
import TrackerEditModal from './components/TrackerEditModal'
import SensorTable from './components/SensorTable'
import SensorEditModal from './components/SensorEditModal'
import RoomTable from './components/RoomTable'
import RoomEditModal from './components/RoomEditModal'
import {Backend} from './Backend'

let interval = undefined;

function getElementFromId(list, field, id){
    for (let i = 0; i < list.length; i++){
        if (list[i][field] === id){
            return list[i]
        }
    }
    return -1

}

function App() {
    const [data, setData] = useState([{}])
    const [deviceEditModal, setDeviceEditModal] = useState(false)
    const [deviceTrainModal, setDeviceTrainModal] = useState(false)
    const [deviceCursor, setDeviceCursor] = useState({})
    const [trackerData, setTrackerData] = useState([{}])
    const [trackerEditModal, setTrackerEditModal] = useState(false)
    const [trackerCursor, setTrackerCursor] = useState({})
    const [sensorData, setSensorData] = useState([{}])
    const [sensorEditModal, setSensorEditModal] = useState(false)
    const [sensorCursor, setSensorCursor] = useState({})
    const [roomData, setRoomData] = useState([{}])
    const [roomEditModal, setRoomEditModal] = useState(false)
    const [roomCursor, setRoomCursor] = useState({})
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
        Backend.GetRooms().then(
            data => {
                setRoomData(data)
                console.log(data)
            }
        )
    }, [])

    useEffect(() => {
        if (!(deviceEditModal || trackerEditModal || sensorEditModal || roomEditModal) && interval === undefined){
            interval = setInterval(() => {
                data.forEach((device, index) => {
                    console.log("Checking device:", device);
                    if (device.trained){
                        console.log("Getting location for device:", device.id)
                        Backend.GetDeviceLocation(device.id).then(
                            response => {
                                console.log("Updating predictions:", response);
                                data[index].location = getElementFromId(roomData, "id", response["room"]).name;
                                data[index].confidence = response["confidence"];
                                
                                forceUpdate({});
                            }
                        )
                    }
                });
            }, 1000);
        }
        else{
            console.log("Clearing Interval");
            clearInterval(interval);
            interval = undefined;
        }
    }, [deviceEditModal, trackerEditModal, sensorEditModal, roomEditModal]);

    return (
        <div>
            <h1>Devices</h1>
            <div class = "w3-responsive">
                <DeviceTable data={data} setData={setData} deviceEditModal={setDeviceEditModal} deviceTrainModal={setDeviceTrainModal} deviceSelector={setDeviceCursor} backend={Backend} forceUpdate={forceUpdate}/>
                <button onClick={() => {
                        setDeviceCursor(-1)
                        setDeviceEditModal(true)
                    }}>Add Device</button>
            </div> 
            <div class = "w3-responsive">
                <DeviceEditModal data={data} setData={setData} modal={deviceEditModal} setModal={setDeviceEditModal} deviceCursor={deviceCursor} backend={Backend} forceUpdate={forceUpdate}/>
            </div>
            <div class = "w3-responsive">
                <DeviceTrainingModal devices={data} setDevices={setData} rooms={roomData} setRooms={setRoomData} modal={deviceTrainModal} setModal={setDeviceTrainModal} deviceCursor={deviceCursor} backend={Backend} forceUpdate={forceUpdate} getElementFromId={getElementFromId}/>
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
                <TrackerEditModal data={trackerData} setData={setTrackerData} modal={trackerEditModal} setModal={setTrackerEditModal} trackerCursor={trackerCursor} backend={Backend} forceUpdate={forceUpdate}/>
            </div>
            <h1>Sensors</h1>
            <div class = "w3-responsive">
                <SensorTable data={sensorData} setData={setSensorData} sensorEditModal={setSensorEditModal} sensorSelector={setSensorCursor} backend={Backend} forceUpdate={forceUpdate}/>
                <button onClick={() => {
                        setSensorCursor(-1)
                        setSensorEditModal(true)
                    }}>Add Sensor</button>
            </div>
            <div class = "w3-responsive">
                <SensorEditModal data={sensorData} setData={setSensorData} modal={sensorEditModal} setModal={setSensorEditModal} sensorCursor={sensorCursor} backend={Backend} forceUpdate={forceUpdate}/>
            </div>
            <h1>Rooms</h1>
            <div class = "w3-responsive">
                <RoomTable data={roomData} setData={setRoomData} roomEditModal={setRoomEditModal} roomSelector={setRoomCursor} backend={Backend} forceUpdate={forceUpdate}/>
                <button onClick={() => {
                        setRoomCursor(-1)
                        setRoomEditModal(true)
                    }}>Add Room</button>
            </div>
            <div class = "w3-responsive">
                <RoomEditModal data={roomData} setData={setRoomData} modal={roomEditModal} setModal={setRoomEditModal} roomCursor={roomCursor} backend={Backend} forceUpdate={forceUpdate}/>
            </div>

        </div>
    )
}

export default App