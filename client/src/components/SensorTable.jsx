import React, { useState } from 'react';


const SensorTable = ({ data, setData, sensorEditModal, sensorSelector, backend, forceUpdate}) => {
  const [expandedRow, setExpandedRow] = useState(null);

  const toggleRow = (rowIndex) => {
    if (expandedRow === rowIndex) {
      setExpandedRow(null);
    } else {
      setExpandedRow(rowIndex);
    }
  };

  return (
    <table className="w3-table-all w3-hoverable">
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
                <input type="checkbox" id="sensor_mobile" name="sensor_mobile" defaultChecked={sensor.mobile} onChange={
                  () => {
                    const newData = JSON.parse(JSON.stringify(data));
                    newData[index].mobile = !newData[index].mobile;
                    setData(newData);
                    backend.UpdateSensor(newData[index]);
                    forceUpdate();
                  }
                }>
                </input>
              </td>
              <td>
                <button onClick={() => {
                  backend.RemoveSensor(data[index]);
                  const newData = JSON.parse(JSON.stringify(data));
                  newData.splice(index, 1);
                  setData(newData);
                  forceUpdate();
                  }
                }>Remove</button>
              </td>
            </tr>
          </React.Fragment>
        ))}
      </tbody>
    </table>
  );
};

export default SensorTable; 