import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Backend } from '../Backend';
import { useBeaconNames } from './BeaconNameContext';
import { useToast } from './ToastContext';
import MiniSignalBars from './MiniSignalBars';
import styles from './BeaconTable.module.css';
import spinnerStyles from './LoadingSpinner.module.css';

/**
 * Truncate an identifier string for display.
 */
function truncateId(id, maxLen = 20) {
  if (!id || id.length <= maxLen) return id;
  return id.slice(0, maxLen - 1) + '…';
}

/**
 * Return the CSS class for an identifier type badge.
 */
function badgeClass(identifierType) {
  switch (identifierType) {
    case 'ibeacon':
      return styles.badgeIbeacon;
    case 'mac':
      return styles.badgeMac;
    default:
      return styles.badgeUnknown;
  }
}

/**
 * Return a human-readable label for the identifier type.
 */
function badgeLabel(identifierType) {
  switch (identifierType) {
    case 'ibeacon':
      return 'iBeacon';
    case 'mac':
      return 'MAC';
    default:
      return 'Unknown';
  }
}

const BeaconTable = () => {
  const { refreshBeaconNames } = useBeaconNames();
  const { addToast } = useToast();

  const [beacons, setBeacons] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedRow, setExpandedRow] = useState(null);
  const [editingId, setEditingId] = useState(null);
  const [editValue, setEditValue] = useState('');

  const intervalRef = useRef(null);
  const inputRef = useRef(null);
  const isCancellingRef = useRef(false);

  const fetchBeacons = useCallback(async () => {
    try {
      const data = await Backend.GetDiscoveredBeacons();
      setBeacons(data);
    } catch (err) {
      console.error('Failed to fetch discovered beacons:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  // Initial fetch and 5-second auto-refresh (pauses during editing)
  useEffect(() => {
    fetchBeacons();
    if (editingId === null) {
      intervalRef.current = setInterval(fetchBeacons, 5000);
    }
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [fetchBeacons, editingId]);

  // Focus input when entering edit mode
  useEffect(() => {
    if (editingId !== null && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [editingId]);

  const handleStartEdit = (e, beacon) => {
    e.stopPropagation();
    setEditingId(beacon.beacon_id);
    setEditValue(beacon.friendly_name || '');
  };

  const handleSave = async (beaconId) => {
    if (isCancellingRef.current) {
      isCancellingRef.current = false;
      return;
    }

    const trimmed = editValue.trim();
    if (!trimmed) {
      const existing = beacons.find((b) => b.beacon_id === beaconId);
      if (existing?.friendly_name) {
        // Delete the existing name
        try {
          await Backend.DeleteBeaconName(beaconId);
          await refreshBeaconNames();
          setBeacons((prev) =>
            prev.map((b) =>
              b.beacon_id === beaconId ? { ...b, friendly_name: null } : b
            )
          );
          addToast('Beacon name removed', 'success');
        } catch (err) {
          console.error('Failed to delete beacon name:', err);
          addToast('Failed to remove beacon name', 'error');
        } finally {
          setEditingId(null);
        }
      } else {
        // No existing name, just cancel
        setEditingId(null);
      }
      return;
    }

    try {
      await Backend.SetBeaconName(beaconId, trimmed);
      await refreshBeaconNames();
      // Update local state immediately
      setBeacons((prev) =>
        prev.map((b) =>
          b.beacon_id === beaconId ? { ...b, friendly_name: trimmed } : b
        )
      );
      addToast('Beacon name saved', 'success');
    } catch (err) {
      console.error('Failed to save beacon name:', err);
      addToast('Failed to save beacon name', 'error');
    } finally {
      setEditingId(null);
    }
  };

  const handleCancel = () => {
    isCancellingRef.current = true;
    setEditingId(null);
    setEditValue('');
  };

  const handleKeyDown = (e, beaconId) => {
    if (e.key === 'Enter') {
      handleSave(beaconId);
    } else if (e.key === 'Escape') {
      handleCancel();
    }
  };

  const toggleRow = (beaconId) => {
    setExpandedRow((prev) => (prev === beaconId ? null : beaconId));
  };

  if (loading) {
    return (
      <div className={spinnerStyles.container}>
        <div className={spinnerStyles.spinner} />
      </div>
    );
  }

  if (beacons.length === 0) {
    return (
      <p className={spinnerStyles.emptyState}>
        No beacons discovered. Make sure you have monitors registered and they can see BLE devices.
      </p>
    );
  }

  return (
    <div className={styles.wrapper}>
      <table className={styles.table}>
        <thead>
          <tr>
            <th>Identifier</th>
            <th>Type</th>
            <th>Name</th>
            <th>Device</th>
            <th>Signals</th>
          </tr>
        </thead>
        <tbody>
          {beacons.map((beacon) => (
            <React.Fragment key={beacon.beacon_id}>
              <tr
                className={styles.clickableRow}
                onClick={() => toggleRow(beacon.beacon_id)}
              >
                <td>
                  <span
                    className={styles.identifier}
                    title={beacon.beacon_id}
                  >
                    {truncateId(beacon.beacon_id)}
                  </span>
                </td>
                <td>
                  <span className={badgeClass(beacon.identifier_type)}>
                    {badgeLabel(beacon.identifier_type)}
                  </span>
                </td>
                <td className={styles.nameCell}>
                  {editingId === beacon.beacon_id ? (
                    <input
                      ref={inputRef}
                      className={styles.nameInput}
                      type="text"
                      value={editValue}
                      onChange={(e) => setEditValue(e.target.value)}
                      onKeyDown={(e) => handleKeyDown(e, beacon.beacon_id)}
                      onBlur={() => handleSave(beacon.beacon_id)}
                      onClick={(e) => e.stopPropagation()}
                    />
                  ) : (
                    <span
                      className={styles.nameDisplay}
                      onClick={(e) => handleStartEdit(e, beacon)}
                    >
                      {beacon.friendly_name ? (
                        <span className={styles.nameText}>
                          {beacon.friendly_name}
                        </span>
                      ) : (
                        <span
                          className={`${styles.nameText} ${styles.namePlaceholder}`}
                        >
                          —
                        </span>
                      )}
                      <span className={styles.editIcon}>✎</span>
                    </span>
                  )}
                </td>
                <td>
                  {beacon.device_name ? (
                    beacon.device_name
                  ) : (
                    <span className={styles.devicePlaceholder}>—</span>
                  )}
                </td>
                <td onClick={(e) => e.stopPropagation()}>
                  <MiniSignalBars monitors={beacon.monitors} />
                </td>
              </tr>

              {/* Expanded detail row */}
              {expandedRow === beacon.beacon_id && (
                <tr className={styles.expandedRow}>
                  <td colSpan={5}>
                    <div className={styles.expandedContent}>
                      <div className={styles.detailSection}>
                        <span className={styles.detailLabel}>
                          Full Identifier
                        </span>
                        <span className={styles.detailValue}>
                          {beacon.beacon_id}
                        </span>
                      </div>

                      <div className={styles.detailSection}>
                        <span className={styles.detailLabel}>
                          Identifier Type
                        </span>
                        <span className={styles.detailValue}>
                          {badgeLabel(beacon.identifier_type)}
                        </span>
                      </div>

                      {beacon.device_name && (
                        <div className={styles.detailSection}>
                          <span className={styles.detailLabel}>
                            Associated Device
                          </span>
                          <span className={styles.deviceLink}>
                            {beacon.device_name}
                          </span>
                        </div>
                      )}

                      <div className={styles.detailSection}>
                        <span className={styles.detailLabel}>
                          Monitor Readings
                        </span>
                        <div className={styles.monitorReadings}>
                          {[...beacon.monitors]
                            .sort(
                              (a, b) =>
                                b.signal_value - a.signal_value
                            )
                            .map((monitor) => (
                              <div
                                key={monitor.entity_id}
                                className={styles.monitorReading}
                              >
                                <span
                                  className={styles.monitorName}
                                  title={monitor.entity_id}
                                >
                                  {monitor.entity_id}
                                </span>
                                <span className={styles.monitorValue}>
                                  {monitor.signal_value.toFixed(1)} dBm
                                </span>
                              </div>
                            ))}
                        </div>
                      </div>
                    </div>
                  </td>
                </tr>
              )}
            </React.Fragment>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default BeaconTable;
