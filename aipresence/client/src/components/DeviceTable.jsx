import React, { useState } from 'react';
import { useToast } from './ToastContext';
import { useBeaconNames } from './BeaconNameContext';
import styles from './DeviceTable.module.css';
import btnStyles from './Button.module.css';


const DeviceTable = ({ data, setData, deviceEditModal, deviceSelector, deviceTrainModal, predictionDetailsModal, backend}) => {
  const { addToast } = useToast();
  const { resolveBeaconName } = useBeaconNames();
  const [expandedRow, setExpandedRow] = useState(null);

  const toggleRow = (rowIndex) => {
    if (expandedRow === rowIndex) {
      setExpandedRow(null);
    } else {
      setExpandedRow(rowIndex);
    }
  };

  return (
    <div className={styles.wrapper}>
      <table className={styles.table}>
        <thead>
          <tr>
            <th>Identifier</th>
            <th>Name</th>
            <th>Trained</th>
            <th>Accuracy</th>
            <th>Location</th>
            <th>Confidence</th>
            <th>Options</th>
          </tr>
        </thead>
        <tbody>
          {data.map((device, index) => (
            <React.Fragment key={device.id}>
              <tr>
                <td>{(() => {
                  if (device.type === "Both") {
                    const resolved = resolveBeaconName(device.beacon_id);
                    const beaconDisplay = resolved.isNamed
                      ? <span title={device.beacon_id}>{resolved.display}</span>
                      : device.beacon_id;
                    return <>Both: {device.entity_id} / {beaconDisplay}</>;
                  }
                  if (device.beacon_id) {
                    const resolved = resolveBeaconName(device.beacon_id);
                    if (resolved.isNamed) {
                      return <span title={device.beacon_id}>{device.type}: {resolved.display}</span>;
                    }
                  }
                  return device.type + ": " + device.identifier;
                })()}</td>
                <td>{device.name}</td>
                <td>{device.trained}</td>
                <td>{device.accuracy}</td>
                <td>{device.location}</td>
                <td>{device.confidence}</td>
                <td>
                  <div className={styles.actions}>
                    <button className={`${btnStyles.secondary} ${btnStyles.small}`} onClick={() => {
                        console.log(data[index]);
                        deviceEditModal(true);
                        deviceSelector(index);
                        console.log(data[index]);
                      }
                    }>Edit</button>
                    <button className={`${btnStyles.danger} ${btnStyles.small}`} onClick={() => {
                      backend.RemoveDevice(data[index]);
                      const newData = JSON.parse(JSON.stringify(data));
                      newData.splice(index, 1);
                      setData(newData);
                      addToast("Device removed", "success");
                      }
                    }>Remove</button>
                    <button className={`${btnStyles.primary} ${btnStyles.small}`} onClick={() => {
                        deviceTrainModal(true);
                        deviceSelector(index);
                        console.log(data[index]);
                      }
                    }>Start Training</button>
                    {device.trained && (
                      <button className={`${btnStyles.secondary} ${btnStyles.small}`} onClick={() => {
                          predictionDetailsModal(true);
                          deviceSelector(index);
                        }
                      }>Details</button>
                    )}
                    <button className={`${btnStyles.secondary} ${btnStyles.small}`} onClick={() => console.log(index)}>Download Model</button>
                  </div>
                </td>
              </tr>
            </React.Fragment>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default DeviceTable;
