import React, { useState } from 'react';


const DeviceTable = ({ data, setData, deviceEditModal, deviceSelector, deviceTrainModal, backend, forceUpdate}) => {
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
                <button onClick={() => {
                    console.log(data[index]);  
                    // Open Edit Modal
                    //toggleModal();
                    deviceEditModal(true);
                    deviceSelector(index);
                    console.log(data[index]);
                  }
                  }>Edit</button>
                <button onClick={() => {
                  backend.RemoveDevice(data[index]);
                  const newData = JSON.parse(JSON.stringify(data));
                  newData.splice(index, 1);
                  setData(newData);
                  forceUpdate();
                  }
                }>Remove</button>
                <button onClick={() => {
                    // Open Training Modal
                    deviceTrainModal(true);
                    deviceSelector(index);
                    console.log(data[index]);
                  }
                }>Start Training</button>
                <button onClick={() => console.log(index)}>Download Model</button>
              </td>
            </tr>
          </React.Fragment>
        ))}
      </tbody>
    </table>
  );
};

export default DeviceTable; 