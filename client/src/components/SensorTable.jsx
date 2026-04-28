import React, { useState } from 'react';


const SensorTable = ({ data, setData, sensorEditModal, sensorSelector, backend}) => {
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
                <input type="checkbox" id={`sensor_mobile_${index}`} name="sensor_mobile" checked={sensor.mobile} onChange={
                  async () => {
                    const newData = JSON.parse(JSON.stringify(data));
                    newData[index].mobile = !newData[index].mobile;
                    setData(newData);
                    await backend.UpdateSensor(newData[index]);
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