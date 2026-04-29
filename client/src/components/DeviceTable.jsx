import React, { useState } from 'react';
import { useToast } from './ToastContext';
import styles from './DeviceTable.module.css';
import btnStyles from './Button.module.css';


const DeviceTable = ({ data, setData, deviceEditModal, deviceSelector, deviceTrainModal, backend}) => {
  const { addToast } = useToast();
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
            <React.Fragment key={device.entity_id}>
              <tr>
                <td>{device.type + ": " + device.identifier}</td>
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
