import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useToast } from './ToastContext';
import modalStyles from './Modal.module.css';
import btnStyles from './Button.module.css';
import styles from './DeviceTrainingModal.module.css';

const DeviceTrainingModal = ({ devices, setDevices, rooms, modal, setModal, deviceCursor, backend, getElementFromId }) => {

    const { addToast } = useToast();

    const [trainingOverwrite, setTrainingOverwrite] = useState(false);
    const [roomTrainingProgress, setRoomTrainingProgress] = useState(0);
    const [roomTrainingSamples, setRoomTrainingSamples] = useState(0);
    const [training, setTraining] = useState(false);
    const [roomIndex, setRoomIndex] = useState(-1);

    const intervalRef = useRef(null);
    const currentRoomIdRef = useRef(null);

    // Reset all training state when modal opens
    useEffect(() => {
        if (modal) {
            setTraining(false);
            setTrainingOverwrite(false);
            setRoomTrainingProgress(0);
            setRoomTrainingSamples(0);
            setRoomIndex(-1);
            currentRoomIdRef.current = null;
        }
    }, [modal]);

    const clearPollingInterval = useCallback(() => {
        if (intervalRef.current !== null) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
        }
    }, []);

    const pollProgress = useCallback((deviceId) => {
        backend.GetTrainingProgress(deviceId).then((result) => {
            const rid = currentRoomIdRef.current;
            if (result !== null && rid && rid in result) {
                setRoomTrainingProgress(result[rid]["percentage"] * 100);
                setRoomTrainingSamples(result[rid]["count"]);
            } else {
                setRoomTrainingProgress(0);
                setRoomTrainingSamples(0);
            }
        }).catch(() => {
            // Ignore polling errors silently
        });
    }, [backend]);

    const startPolling = useCallback((deviceId) => {
        clearPollingInterval();
        intervalRef.current = setInterval(() => {
            pollProgress(deviceId);
        }, 1000);
    }, [clearPollingInterval, pollProgress]);

    // Clean up interval when modal closes or component unmounts
    useEffect(() => {
        if (!modal) {
            clearPollingInterval();
        }
        return () => {
            clearPollingInterval();
        };
    }, [modal, clearPollingInterval]);

    const handleRoomButtonClick = async (roomId, index) => {
        const deviceId = devices[deviceCursor].id;

        if (!training) {
            setTraining(true);
            await backend.StartTraining(deviceId, roomId, trainingOverwrite);
        } else {
            await backend.ChangeRoom(deviceId, roomId);
        }

        currentRoomIdRef.current = roomId;
        setRoomIndex(index);

        // Immediately poll once, then start interval
        pollProgress(deviceId);
        startPolling(deviceId);
    };

    const handleDone = async () => {
        if (training) {
            try {
                await backend.StopTraining(devices[deviceCursor].id);
                // Refresh device list to get updated model stats
                const updatedDevices = await backend.GetDevices();
                setDevices(updatedDevices);
                addToast("Training completed successfully", "success");
            } catch (e) {
                addToast("Error stopping training: " + e.message, "error");
            }
            setTraining(false);
        }
        clearPollingInterval();
        setModal(false);
    };

    const handleCancel = async () => {
        if (training) {
            try {
                await backend.CancelTraining(devices[deviceCursor].id);
            } catch (e) {
                // Ignore cancel errors
            }
            setTraining(false);
        }
        clearPollingInterval();
        setModal(false);
    };

    return (
        <>
            {modal && (
                <div className={modalStyles.modal}>
                    <div onClick={handleCancel} className={modalStyles.overlay}></div>
                    <div className={modalStyles.content}>
                        <div className={modalStyles.header}>
                            <h2>Device Training</h2>
                        </div>
                        <div className={modalStyles.body}>
                            <p>Choose a room to start!</p>
                            <div className={styles.overwriteRow}>
                                <input
                                    type="checkbox"
                                    id="training_overwrite"
                                    name="training_overwrite"
                                    checked={trainingOverwrite}
                                    onChange={(e) => setTrainingOverwrite(e.target.checked)}
                                />
                                <label htmlFor="training_overwrite">Overwrite Training</label>
                            </div>
                            <div className={styles.roomGrid}>
                                {rooms.map((room, index) => (
                                    <button
                                        key={room.id}
                                        className={styles.roomButton}
                                        onClick={() => handleRoomButtonClick(room.id, index)}
                                        style={{ backgroundColor: room.color }}
                                    >
                                        {room.name}
                                    </button>
                                ))}
                            </div>
                            {training && (
                                <div className={styles.progressSection}>
                                    <progress className={styles.progressBar} id="training_progress" value={roomTrainingProgress} max="100"></progress>
                                    <p className={styles.statusText}>Training Progress: {roomTrainingProgress.toFixed(0)}% - {roomTrainingSamples} samples</p>
                                    <p className={styles.statusText}>Current Room: {roomIndex >= 0 ? rooms[roomIndex].name : "Not Training"}</p>
                                    <p className={styles.statusText}>Old Model Prediction: {currentRoomIdRef.current ? (() => { const el = getElementFromId(rooms, "id", currentRoomIdRef.current); return el !== -1 ? el.name : "-"; })() : "Not Training"}</p>
                                </div>
                            )}
                        </div>
                        <div className={modalStyles.footer}>
                            <button className={btnStyles.secondary} onClick={handleCancel}>Cancel</button>
                            <button className={btnStyles.primary} onClick={handleDone}>Done</button>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
};

export default DeviceTrainingModal;
