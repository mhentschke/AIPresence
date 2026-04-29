import React, { useState } from 'react';
import { useToast } from './ToastContext';
import styles from './SensorTable.module.css';
import btnStyles from './Button.module.css';


const SensorTable = ({ data, setData, sensorEditModal, sensorSelector, backend}) => {
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
            <th>Entity_id</th>
            <th>Mobile</th>
            <th>Options</th>
          </tr>
        </thead>
        <tbody>
          {data.map((sensor, index) => (
            <React.Fragment key={sensor.entity_id}>
              <tr>
                <td>{sensor.entity_id}</td>
                <td>
                  <input
                    type="checkbox"
                    className={styles.checkbox}
                    id={`sensor_mobile_${index}`}
                    name="sensor_mobile"
                    checked={sensor.mobile}
                    onChange={async () => {
                      const newData = JSON.parse(JSON.stringify(data));
                      newData[index].mobile = !newData[index].mobile;
                      setData(newData);
                      await backend.UpdateSensor(newData[index]);
                    }}
                  />
                </td>
                <td>
                  <div className={styles.actions}>
                    <button className={`${btnStyles.danger} ${btnStyles.small}`} onClick={() => {
                      backend.RemoveSensor(data[index]);
                      const newData = JSON.parse(JSON.stringify(data));
                      newData.splice(index, 1);
                      setData(newData);
                      addToast("Sensor removed", "success");
                      }
                    }>Remove</button>
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

export default SensorTable;
