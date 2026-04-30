import React, { useState, useEffect, useRef } from 'react'
import DeviceTable from './components/DeviceTable'
import DeviceEditModal from './components/DeviceEditModal'
import DeviceTrainingModal from './components/DeviceTrainingModal'
import PredictionDetailsModal from './components/PredictionDetailsModal'
import MonitorTable from './components/MonitorTable'
import MonitorEditModal from './components/MonitorEditModal'
import SensorTable from './components/SensorTable'
import SensorEditModal from './components/SensorEditModal'
import RoomTable from './components/RoomTable'
import RoomEditModal from './components/RoomEditModal'
import {Backend} from './Backend'
import ErrorBoundary from './components/ErrorBoundary'
import { useToast } from './components/ToastContext'
import styles from './components/App.module.css'
import spinnerStyles from './components/LoadingSpinner.module.css'

const TABS = ['Devices', 'Monitors', 'Sensors', 'Rooms'];

function getElementFromId(list, field, id){
    for (let i = 0; i < list.length; i++){
        if (list[i][field] === id){
            return list[i]
        }
    }
    return -1
}

function App() {
    const { addToast } = useToast()
    const [activeTab, setActiveTab] = useState('Devices')
    const [data, setData] = useState([])
    const [deviceEditModal, setDeviceEditModal] = useState(false)
    const [deviceTrainModal, setDeviceTrainModal] = useState(false)
    const [predictionDetailsModal, setPredictionDetailsModal] = useState(false)
    const [deviceCursor, setDeviceCursor] = useState({})
    const [monitorData, setMonitorData] = useState([])
    const [monitorEditModal, setMonitorEditModal] = useState(false)
    const [sensorData, setSensorData] = useState([])
    const [sensorEditModal, setSensorEditModal] = useState(false)
    const [sensorCursor, setSensorCursor] = useState({})
    const [roomData, setRoomData] = useState([])
    const [roomEditModal, setRoomEditModal] = useState(false)
    const [roomCursor, setRoomCursor] = useState({})

    const [devicesLoading, setDevicesLoading] = useState(true)
    const [monitorsLoading, setMonitorsLoading] = useState(true)
    const [sensorsLoading, setSensorsLoading] = useState(true)
    const [roomsLoading, setRoomsLoading] = useState(true)

    const restoreInputRef = useRef(null);
    const intervalRef = useRef(undefined);
    const dataRef = useRef(data);
    const roomDataRef = useRef(roomData);

    // Keep refs in sync with latest state
    useEffect(() => { dataRef.current = data; }, [data]);
    useEffect(() => { roomDataRef.current = roomData; }, [roomData]);

    const reloadAllData = () => {
        Backend.GetDevices().then(setData).finally(() => setDevicesLoading(false))
        Backend.GetBeaconMonitors().then(setMonitorData).finally(() => setMonitorsLoading(false))
        Backend.GetSensors().then(setSensorData).finally(() => setSensorsLoading(false))
        Backend.GetRooms().then(setRoomData).finally(() => setRoomsLoading(false))
    }

    const handleBackup = async () => {
        try {
            await Backend.CreateBackup()
            addToast('Backup downloaded successfully', 'success')
        } catch (err) {
            addToast('Backup failed: ' + err.message, 'error')
        }
    }

    const handleRestore = async (e) => {
        const file = e.target.files?.[0]
        if (!file) return
        e.target.value = ''
        try {
            await Backend.RestoreBackup(file)
            addToast('Restore completed successfully', 'success')
            reloadAllData()
        } catch (err) {
            addToast('Restore failed: ' + err.message, 'error')
        }
    }

    useEffect(() => {
        Backend.GetDevices().then(
            data => {
                setData(data)
                console.log(data)
            }
        ).finally(() => setDevicesLoading(false))
        Backend.GetBeaconMonitors().then(
            data => {
                setMonitorData(data)
                console.log(data)
            }
        ).finally(() => setMonitorsLoading(false))
        Backend.GetSensors().then(
            data => {
                setSensorData(data)
                console.log(data)
            }
        ).finally(() => setSensorsLoading(false))
        Backend.GetRooms().then(
            data => {
                setRoomData(data)
                console.log(data)
            }
        ).finally(() => setRoomsLoading(false))
    }, [])

    useEffect(() => {
        const anyModalOpen = deviceEditModal || deviceTrainModal || predictionDetailsModal || monitorEditModal || sensorEditModal || roomEditModal;

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
    }, [deviceEditModal, deviceTrainModal, predictionDetailsModal, monitorEditModal, sensorEditModal, roomEditModal]);

    const renderLoading = () => (
        <div className={spinnerStyles.container}>
            <div className={spinnerStyles.spinner} />
        </div>
    );

    const renderTabContent = () => {
        switch (activeTab) {
            case 'Devices':
                return (
                    <ErrorBoundary>
                        {devicesLoading ? renderLoading() : data.length === 0 ? (
                            <p className={spinnerStyles.emptyState}>No devices yet. Click Add Device to get started.</p>
                        ) : (
                            <DeviceTable data={data} setData={setData} deviceEditModal={setDeviceEditModal} deviceTrainModal={setDeviceTrainModal} predictionDetailsModal={setPredictionDetailsModal} deviceSelector={setDeviceCursor} backend={Backend}/>
                        )}
                        <button className={styles.addButton} onClick={() => {
                            setDeviceCursor(-1)
                            setDeviceEditModal(true)
                        }}>Add Device</button>
                    </ErrorBoundary>
                );
            case 'Monitors':
                return (
                    <ErrorBoundary>
                        {monitorsLoading ? renderLoading() : monitorData.length === 0 ? (
                            <p className={spinnerStyles.emptyState}>No monitors yet. Click Add Monitor to get started.</p>
                        ) : (
                            <MonitorTable data={monitorData} setData={setMonitorData} monitorEditModal={setMonitorEditModal} backend={Backend}/>
                        )}
                        <button className={styles.addButton} onClick={() => {
                            setMonitorEditModal(true)
                        }}>Add Monitor</button>
                    </ErrorBoundary>
                );
            case 'Sensors':
                return (
                    <ErrorBoundary>
                        {sensorsLoading ? renderLoading() : sensorData.length === 0 ? (
                            <p className={spinnerStyles.emptyState}>No sensors yet. Click Add Sensor to get started.</p>
                        ) : (
                            <SensorTable data={sensorData} setData={setSensorData} sensorEditModal={setSensorEditModal} sensorSelector={setSensorCursor} backend={Backend}/>
                        )}
                        <button className={styles.addButton} onClick={() => {
                            setSensorCursor(-1)
                            setSensorEditModal(true)
                        }}>Add Sensor</button>
                    </ErrorBoundary>
                );
            case 'Rooms':
                return (
                    <ErrorBoundary>
                        {roomsLoading ? renderLoading() : roomData.length === 0 ? (
                            <p className={spinnerStyles.emptyState}>No rooms yet. Click Add Room to get started.</p>
                        ) : (
                            <RoomTable data={roomData} setData={setRoomData} roomEditModal={setRoomEditModal} roomSelector={setRoomCursor} backend={Backend}/>
                        )}
                        <button className={styles.addButton} onClick={() => {
                            setRoomCursor(-1)
                            setRoomEditModal(true)
                        }}>Add Room</button>
                    </ErrorBoundary>
                );
            default:
                return null;
        }
    };

    return (
        <div className={styles.appContainer}>
            <header className={styles.header}>
                <h1 className={styles.title}>AIPresence</h1>
                <div className={styles.headerActions}>
                    <button className={styles.headerBtn} onClick={handleBackup}>Backup</button>
                    <button className={styles.headerBtn} onClick={() => restoreInputRef.current?.click()}>Restore</button>
                    <input
                        ref={restoreInputRef}
                        type="file"
                        accept=".tar.gz,.tgz"
                        style={{ display: 'none' }}
                        onChange={handleRestore}
                    />
                </div>
            </header>
            <nav className={styles.tabBar}>
                {TABS.map(tab => (
                    <button
                        key={tab}
                        className={`${styles.tab} ${activeTab === tab ? styles.tabActive : ''}`}
                        onClick={() => setActiveTab(tab)}
                    >
                        {tab}
                    </button>
                ))}
            </nav>
            <main className={styles.content}>
                <div className={styles.card}>
                    {renderTabContent()}
                </div>
            </main>

            {/* Modals render regardless of active tab so they can open/close freely */}
            <DeviceEditModal data={data} setData={setData} modal={deviceEditModal} setModal={setDeviceEditModal} deviceCursor={deviceCursor} backend={Backend}/>
            <DeviceTrainingModal devices={data} setDevices={setData} rooms={roomData} setRooms={setRoomData} modal={deviceTrainModal} setModal={setDeviceTrainModal} deviceCursor={deviceCursor} backend={Backend} getElementFromId={getElementFromId}/>
            <PredictionDetailsModal device={typeof deviceCursor === 'number' && deviceCursor >= 0 ? data[deviceCursor] : null} rooms={roomData} modal={predictionDetailsModal} setModal={setPredictionDetailsModal} backend={Backend}/>
            <MonitorEditModal data={monitorData} setData={setMonitorData} modal={monitorEditModal} setModal={setMonitorEditModal} backend={Backend}/>
            <SensorEditModal data={sensorData} setData={setSensorData} modal={sensorEditModal} setModal={setSensorEditModal} sensorCursor={sensorCursor} backend={Backend}/>
            <RoomEditModal data={roomData} setData={setRoomData} modal={roomEditModal} setModal={setRoomEditModal} roomCursor={roomCursor} backend={Backend}/>
        </div>
    )
}

export default App