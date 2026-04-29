import { useToast } from './ToastContext';
import styles from './MonitorTable.module.css';
import btnStyles from './Button.module.css';

const MonitorTable = ({ data, setData, monitorEditModal, monitorSelector, backend }) => {
  const { addToast } = useToast();
  return (
    <div className={styles.wrapper}>
      <table className={styles.table}>
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
                <div className={styles.actions}>
                  <button className={`${btnStyles.danger} ${btnStyles.small}`} onClick={() => {
                    backend.RemoveBeaconMonitor(monitor.entity_id).then(() => {
                      const newData = [...data];
                      newData.splice(index, 1);
                      setData(newData);
                      addToast("Monitor removed", "success");
                    });
                  }}>Remove</button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default MonitorTable;
