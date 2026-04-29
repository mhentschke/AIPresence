import React, { useState, useEffect, useRef } from 'react'
import DeviceTable from './components/DeviceTable'
import DeviceEditModal from './components/DeviceEditModal'
import DeviceTrainingModal from './components/DeviceTrainingModal'
import MonitorTable from './components/MonitorTable'
import MonitorEditModal from './components/MonitorEditModal'
import SensorTable from './components/SensorTable'
import SensorEditModal from './components/SensorEditModal'
import RoomTable from './components/RoomTable'
import RoomEditModal from './components/RoomEditModal'
import {Backend} from './Backend'

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
    const [monitorData, setMonitorData] = useState([])
    const [monitorEditModal, setMonitorEditModal] = useState(false)
    const [sensorData, setSensorData] = useState([{}])
    const [sensorEditModal, setSensorEditModal] = useState(false)
    const [sensorCursor, setSensorCursor] = useState({})
    const [roomData, setRoomData] = useState([{}])
    const [roomEditModal, setRoomEditModal] = useState(false)
    const [roomCursor, setRoomCursor] = useState({})

    const intervalRef = useRef(undefined);
    const dataRef = useRef(data);
    const roomDataRef = useRef(roomData);

    // Keep refs in sync with latest state
    useEffect(() => { dataRef.current = data; }, [data]);
    useEffect(() => { roomDataRef.current = roomData; }, [roomData]);

    useEffect(() => {
        Backend.GetDevices().then( 
            data => {
                setData(data)
                console.log(data)
            }
        )
        Backend.GetBeaconMonitors().then(
            data => {
                setMonitorData(data)
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
        const anyModalOpen = deviceEditModal || deviceTrainModal || monitorEditModal || sensorEditModal || roomEditModal;

        if (!anyModalOpen) {
            intervalRef.current = setInterval(() => {
                const currentData = dataRef.current;
                const currentRoomData = roomDataRef.current;

                currentData.forEach((device, index) => {
                    if (device.trained) {
                        Backend.GetDeviceLocation(device.id).then(
                            response => {
                                const room = getElementFromId(currentRoomData, "id", response["room"]);
                                const roomName = room !== -1 ? room.name : "Unknown";

                                setData(prev => prev.map((d, i) =>
                                    i === index
                                        ? { ...d, location: roomName, confidence: response["confidence"] }
                                        : d
                                ));
                            }
                        ).catch(err => {
                            console.error("Error fetching device location:", err);
                        });
                    }
                });
            }, 1000);
        } else {
            clearInterval(intervalRef.current);
            intervalRef.current = undefined;
        }

        return () => {
            clearInterval(intervalRef.current);
            intervalRef.current = undefined;
        };
    }, [deviceEditModal, deviceTrainModal, monitorEditModal, sensorEditModal, roomEditModal]);

    return (
        <div>
            <h1>Devices</h1>
            <div className = "w3-responsive">
                <DeviceTable data={data} setData={setData} deviceEditModal={setDeviceEditModal} deviceTrainModal={setDeviceTrainModal} deviceSelector={setDeviceCursor} backend={Backend}/>
                <button onClick={() => {
                        setDeviceCursor(-1)
                        setDeviceEditModal(true)
                    }}>Add Device</button>
            </div> 
            <div className = "w3-responsive">
                <DeviceEditModal data={data} setData={setData} modal={deviceEditModal} setModal={setDeviceEditModal} deviceCursor={deviceCursor} backend={Backend}/>
            </div>
            <div className = "w3-responsive">
                <DeviceTrainingModal devices={data} setDevices={setData} rooms={roomData} setRooms={setRoomData} modal={deviceTrainModal} setModal={setDeviceTrainModal} deviceCursor={deviceCursor} backend={Backend} getElementFromId={getElementFromId}/>
            </div>
            <h1>Monitors</h1>
            <div className = "w3-responsive">
                <MonitorTable data={monitorData} setData={setMonitorData} monitorEditModal={setMonitorEditModal} backend={Backend}/>
                <button onClick={() => {
                        setMonitorEditModal(true)
                    }}>Add Monitor</button>
            </div>
            <div className = "w3-responsive">
                <MonitorEditModal data={monitorData} setData={setMonitorData} modal={monitorEditModal} setModal={setMonitorEditModal} backend={Backend}/>
            </div>
            <h1>Sensors</h1>
            <div className = "w3-responsive">
                <SensorTable data={sensorData} setData={setSensorData} sensorEditModal={setSensorEditModal} sensorSelector={setSensorCursor} backend={Backend}/>
                <button onClick={() => {
                        setSensorCursor(-1)
                        setSensorEditModal(true)
                    }}>Add Sensor</button>
            </div>
            <div className = "w3-responsive">
                <SensorEditModal data={sensorData} setData={setSensorData} modal={sensorEditModal} setModal={setSensorEditModal} sensorCursor={sensorCursor} backend={Backend}/>
            </div>
            <h1>Rooms</h1>
            <div className = "w3-responsive">
                <RoomTable data={roomData} setData={setRoomData} roomEditModal={setRoomEditModal} roomSelector={setRoomCursor} backend={Backend}/>
                <button onClick={() => {
                        setRoomCursor(-1)
                        setRoomEditModal(true)
                    }}>Add Room</button>
            </div>
            <div className = "w3-responsive">
                <RoomEditModal data={roomData} setData={setRoomData} modal={roomEditModal} setModal={setRoomEditModal} roomCursor={roomCursor} backend={Backend}/>
            </div>

        </div>
    )
}

export default App
