import React, { useState } from 'react';
import { useToast } from './ToastContext';
import styles from './RoomTable.module.css';
import btnStyles from './Button.module.css';


const RoomTable = ({ data, setData, roomEditModal, roomSelector, backend}) => {
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
                  <input
                    type="color"
                    className={styles.colorInput}
                    name="room_color"
                    value={room.color}
                    onChange={(e) => {
                      const newData = JSON.parse(JSON.stringify(data));
                      newData[index].color = e.target.value;
                      setData(newData);
                      backend.UpdateRoom(newData[index]);
                    }}
                  />
                </td>
                <td>
                  <div className={styles.actions}>
                    <button className={`${btnStyles.secondary} ${btnStyles.small}`} onClick={() => {
                        roomEditModal(true);
                        roomSelector(index);
                      }
                    }>Edit</button>
                    <button className={`${btnStyles.danger} ${btnStyles.small}`} onClick={() => {
                      backend.RemoveRoom(data[index]);
                      const newData = JSON.parse(JSON.stringify(data));
                      newData.splice(index, 1);
                      setData(newData);
                      addToast("Room removed", "success");
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

export default RoomTable;
