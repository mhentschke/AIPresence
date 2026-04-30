import { useState, useEffect } from 'react';
import SignalChart from './SignalChart';
import modalStyles from './Modal.module.css';
import btnStyles from './Button.module.css';
import styles from './PredictionDetailsModal.module.css';

const PredictionDetailsModal = ({ device, rooms, modal, setModal, backend }) => {
  const [prediction, setPrediction] = useState(null);
  const [signalBars, setSignalBars] = useState([]);
  const [trainingAverages, setTrainingAverages] = useState(null);
  const [selectedRoom, setSelectedRoom] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!modal || !device) return;

    setLoading(true);
    setPrediction(null);
    setSignalBars([]);
    setTrainingAverages(null);
    setSelectedRoom(null);

    const fetchData = async () => {
      try {
        const [signalResult, locationResult, avgResult] = await Promise.all([
          backend.GetSignalData(device.id),
          backend.GetDeviceLocation(device.id),
          backend.GetTrainingAverages(device.id),
        ]);

        setPrediction(locationResult);
        setTrainingAverages(avgResult);

        // Default overlay room = predicted room
        const predictedRoomId = locationResult?.room || null;
        setSelectedRoom(predictedRoomId);

        // Build signal bars from current readings with overlay from predicted room
        const signals = signalResult?.signals || {};
        const roomAvgs = predictedRoomId && avgResult?.rooms?.[predictedRoomId]?.averages || {};

        const bars = Object.keys(signals).sort().map((key) => ({
          label: key,
          value: signals[key],
          overlay: roomAvgs[key] != null ? roomAvgs[key] : undefined,
        }));
        setSignalBars(bars);
      } catch {
        // Errors handled gracefully — empty state shown
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [modal, device, backend]);

  // Update overlay when user switches room selector
  useEffect(() => {
    if (!trainingAverages || !selectedRoom || signalBars.length === 0) return;

    const roomAvgs = trainingAverages.rooms?.[selectedRoom]?.averages || {};
    setSignalBars((prev) =>
      prev.map((bar) => ({
        ...bar,
        overlay: roomAvgs[bar.label] != null ? roomAvgs[bar.label] : undefined,
      }))
    );
  }, [selectedRoom, trainingAverages]);

  if (!modal || !device) return null;

  const close = () => setModal(false);

  // Extract per-room probabilities from prediction
  const roomProbabilities = [];
  if (prediction) {
    for (const [key, value] of Object.entries(prediction)) {
      if (key === 'room' || key === 'confidence') continue;
      // Keys are "room_<id>" — strip prefix
      const roomId = key.startsWith('room_') ? key.slice(5) : key;
      const room = rooms.find((r) => r.id === roomId);
      roomProbabilities.push({
        roomId,
        name: room ? room.name : roomId,
        probability: typeof value === 'number' ? value : 0,
      });
    }
    roomProbabilities.sort((a, b) => b.probability - a.probability);
  }

  const predictedRoom = prediction?.room;
  const predictedRoomObj = rooms.find((r) => r.id === predictedRoom);
  const predictedRoomName = predictedRoomObj ? predictedRoomObj.name : predictedRoom || '—';
  const confidence = prediction?.confidence;

  return (
    <div className={modalStyles.modal}>
      <div onClick={close} className={modalStyles.overlay}></div>
      <div className={modalStyles.content}>
        <div className={modalStyles.header}>
          <h2>Prediction Details — {device.name}</h2>
        </div>
        <div className={modalStyles.body}>
          {loading ? (
            <p className={styles.loadingText}>Loading...</p>
          ) : (
            <>
              <div className={styles.predictionSummary}>
                <span className={styles.predictedLabel}>Predicted Room:</span>
                <span className={styles.predictedValue}>
                  {predictedRoomName}
                  {confidence != null && (
                    <span className={styles.confidence}> ({(confidence * 100).toFixed(1)}%)</span>
                  )}
                </span>
              </div>

              {roomProbabilities.length > 0 && (
                <div className={styles.probabilitiesSection}>
                  <h4 className={styles.sectionTitle}>Room Probabilities</h4>
                  <div className={styles.probBars}>
                    {roomProbabilities.map((rp) => (
                      <div key={rp.roomId} className={styles.probRow}>
                        <span className={styles.probLabel}>{rp.name}</span>
                        <div className={styles.probTrack}>
                          <div
                            className={styles.probBar}
                            style={{ width: `${(rp.probability * 100).toFixed(1)}%` }}
                          />
                        </div>
                        <span className={styles.probValue}>{(rp.probability * 100).toFixed(1)}%</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {signalBars.length > 0 && (
                <div className={styles.signalSection}>
                  <div className={styles.signalHeader}>
                    <h4 className={styles.sectionTitle}>Signal Comparison</h4>
                    {trainingAverages && Object.keys(trainingAverages.rooms || {}).length > 0 && (
                      <div className={styles.roomSelector}>
                        <label htmlFor="overlay-room">Overlay:</label>
                        <select
                          id="overlay-room"
                          value={selectedRoom || ''}
                          onChange={(e) => setSelectedRoom(e.target.value)}
                        >
                          {Object.entries(trainingAverages.rooms).map(([rid, rdata]) => (
                            <option key={rid} value={rid}>{rdata.name}</option>
                          ))}
                        </select>
                      </div>
                    )}
                  </div>
                  <SignalChart
                    bars={signalBars}
                    overlayLabel={
                      selectedRoom && trainingAverages?.rooms?.[selectedRoom]
                        ? `${trainingAverages.rooms[selectedRoom].name} Avg`
                        : 'Training Avg'
                    }
                  />
                </div>
              )}

              {!prediction && (
                <p className={styles.noData}>No prediction data available for this device.</p>
              )}
            </>
          )}
        </div>
        <div className={modalStyles.footer}>
          <button className={btnStyles.secondary} onClick={close}>Close</button>
        </div>
      </div>
    </div>
  );
};

export default PredictionDetailsModal;
