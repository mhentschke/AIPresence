const MonitorTable = ({ data, setData, monitorEditModal, monitorSelector, backend }) => {
  return (
    <table className="w3-table-all w3-hoverable">
      <thead>
        <tr>
          <th>Entity ID</th>
          <th>Options</th>
        </tr>
      </thead>
      <tbody>
        {data.map((monitor, index) => (
          <tr key={monitor.entity_id}>
            <td>{monitor.entity_id}</td>
            <td>
              <button onClick={() => {
                backend.RemoveBeaconMonitor(monitor.entity_id).then(() => {
                  const newData = [...data];
                  newData.splice(index, 1);
                  setData(newData);
                });
              }}>Remove</button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
};

export default MonitorTable;
