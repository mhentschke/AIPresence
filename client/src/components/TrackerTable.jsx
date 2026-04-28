import React, { useState } from 'react';


const TrackerTable = ({ data, setData, trackerEditModal, trackerSelector, backend}) => {
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
          <th>Whitelist</th>
          <th>Blacklist</th>
          <th>Options</th>
        </tr>
      </thead>
      <tbody>
        {data.map((tracker, index) => (
          <React.Fragment key={tracker.entity_id}>
            <tr>
              <td>{tracker.entity_id}</td>
              <td>
                <input type="checkbox" id="tracker_mobile" name="tracker_mobile" defaultChecked={tracker.mobile} onChange={
                  () => {
                    const newData = JSON.parse(JSON.stringify(data));
                    newData[index].mobile = !newData[index].mobile;
                    setData(newData);
                    backend.UpdateTracker(newData[index]);
                  }
                }>
                </input>
              </td>
              <td>
                <input type="checkbox" id="tracker_whitelist" name="tracker_whitelist" defaultChecked={tracker.whitelist} onChange={
                  () => {
                    const newData = JSON.parse(JSON.stringify(data));
                    newData[index].whitelist = !newData[index].whitelist;
                    setData(newData);
                    backend.UpdateTracker(newData[index]);
                  }
                }>
                </input>
              </td>
              <td>
                <input type="checkbox" id="tracker_blacklist" name="tracker_blacklist" defaultChecked={tracker.blacklist} onChange={
                  () => {
                    const newData = JSON.parse(JSON.stringify(data));
                    newData[index].blacklist = !newData[index].blacklist;
                    setData(newData);
                    backend.UpdateTracker(newData[index]);
                  }
                }></input>           
              </td>
              <td>
                <button onClick={() => {
                  backend.RemoveTracker(data[index]);
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

export default TrackerTable; 