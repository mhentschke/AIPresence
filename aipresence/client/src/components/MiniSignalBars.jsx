import { useMemo } from 'react';
import styles from './MiniSignalBars.module.css';

/**
 * Extract a short display name from a monitor entity_id.
 * e.g. "sensor.tablet_beacon_monitor" → "tablet_beacon_monitor"
 */
function shortMonitorName(entityId, maxLen = 18) {
  const dotIdx = entityId.indexOf('.');
  const name = dotIdx >= 0 ? entityId.slice(dotIdx + 1) : entityId;
  if (name.length <= maxLen) return name;
  return name.slice(0, maxLen - 1) + '…';
}

/**
 * Compact inline signal bars for a beacon's per-monitor readings.
 *
 * Renders one line per monitor with: truncated name, proportional bar, raw dBm value.
 * Bars are normalized within the cell — strongest signal = full bar, weakest = shortest.
 *
 * @param {Object} props
 * @param {{ entity_id: string, signal_value: number }[]} props.monitors
 *   Array of monitor readings for this beacon, sorted strongest-first by caller or internally.
 */
const MiniSignalBars = ({ monitors }) => {
  const { minVal, maxVal } = useMemo(() => {
    if (!monitors || monitors.length === 0) return { minVal: 0, maxVal: 0 };

    const values = monitors.map((m) => m.signal_value);
    const lo = Math.min(...values);
    const hi = Math.max(...values);

    // If all values are the same, avoid division by zero
    if (lo === hi) return { minVal: lo - 1, maxVal: hi };

    return { minVal: lo, maxVal: hi };
  }, [monitors]);

  if (!monitors || monitors.length === 0) {
    return <span className={styles.empty}>—</span>;
  }

  // Normalize: strongest (closest to 0 for RSSI) = 100%, weakest = minimum bar width
  const normalize = (value) => {
    if (minVal === maxVal) return 100;
    return ((value - minVal) / (maxVal - minVal)) * 100;
  };

  // Sort by signal strength descending (strongest first, i.e., closest to 0)
  const sorted = [...monitors].sort((a, b) => b.signal_value - a.signal_value);

  return (
    <div className={styles.container}>
      {sorted.map((monitor) => {
        const pct = normalize(monitor.signal_value);
        return (
          <div key={monitor.entity_id} className={styles.row}>
            <span className={styles.name} title={monitor.entity_id}>
              {shortMonitorName(monitor.entity_id)}
            </span>
            <div className={styles.track}>
              <div
                className={styles.bar}
                style={{ width: `${Math.max(pct, 5)}%` }}
              />
            </div>
            <span className={styles.value}>
              {Math.round(monitor.signal_value)}
            </span>
          </div>
        );
      })}
    </div>
  );
};

export default MiniSignalBars;
