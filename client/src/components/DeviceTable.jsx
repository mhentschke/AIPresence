import React, { useState } from 'react';
import DeviceEditModal from './DeviceEditModal';


const DeviceTable = ({ data, deviceEditModal }) => {
  const [expandedRow, setExpandedRow] = useState(null);

  const toggleRow = (rowIndex) => {
    if (expandedRow === rowIndex) {
      setExpandedRow(null);
    } else {
      setExpandedRow(rowIndex);
    }
  };

  return (
    <table class="w3-table-all w3-hoverable">
      <thead>
        <tr>
          <th>Entity_id</th>
          <th>Name</th>
          <th>Trained</th>
          <th>Accuracy</th>
          <th>Options</th>
        </tr>
      </thead>
      <tbody>
        {data.map((device, index) => (
          <React.Fragment key={device.entity_id}>
            <tr>
              <td>{device.entity_id}</td>
              <td>{device.name}</td>
              <td>{device.trained}</td>
              <td>{device.accuracy}</td>
              <td>
                <button onClick={() => {
                    console.log(data[index]);  
                    // Open Edit Modal
                    //toggleModal();
                    deviceEditModal(true);
                  }
                  }>Edit</button>
              </td>
              <td>
                <button onClick={() => {
                  console.log(index);
                  // call delete api at /devices/data[index]['id']
                  // then update the table
                  fetch('/devices/' + data[index]['id'], {
                    method: 'DELETE',
                    headers: {
                      'Content-Type': 'application/json'
                    },
                  }) // check if successful
                  .then(response => alert("response. status: " + response.status))
                }
              }>Remove</button>
              </td>
              <td>
                <button onClick={() => console.log(index)}>Start Training</button>
              </td>
            </tr>
          </React.Fragment>
        ))}
      </tbody>
    </table>
  );
};

export default DeviceTable; 