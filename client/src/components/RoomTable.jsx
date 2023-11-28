import React, { useState } from 'react';


const RoomTable = ({ data, setData, roomEditModal, roomSelector, backend, forceUpdate}) => {
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
          <th>Name</th>
          <th>Color</th>
          <th>Options</th>
        </tr>
      </thead>
      <tbody>
        {data.map((room, index) => (
          <React.Fragment key={room.entity_id}>
            <tr>
              <td>{room.name}</td>
              <td>
                <input type="color" id="room_color" name="room_color" value={room.color} onChange={
                  (e) => {
                    var newData = JSON.parse(JSON.stringify(data));
                    newData[index].color = e.target.value;
                    setData(newData);
                    backend.UpdateRoom(newData[index]);
                    forceUpdate();
                  }
                }></input>
              </td>

              <td>
                <button onClick={() => {
                    // Open Edit Modal
                    //toggleModal();
                    roomEditModal(true);
                    roomSelector(index);
                  }
                  }>Edit</button>
                <button onClick={() => {
                  backend.RemoveRoom(data[index]);
                  var newData = JSON.parse(JSON.stringify(data));
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

export default RoomTable; 