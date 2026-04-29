import { useMemo } from 'react';
import styles from './SignalChart.module.css';

/**
 * Extract a short display label from a signal key.
 *
 * Signal keys look like "sensor.phone_monitor-beacon_uuid_major_minor".
 * We strip the monitor entity prefix (before the first "-") and show only
 * the beacon/attribute portion. The full key goes in the tooltip.
 * For keys without a "-" (e.g. binary sensors), show the full label.
 *
 * Long results are truncated as start…end.
 */
function displayLabel(fullKey, maxLen = 30) {
  const dashIdx = fullKey.indexOf('-');
  const short = dashIdx >= 0 ? fullKey.slice(dashIdx + 1) : fullKey;
  if (short.length <= maxLen) return short;
  const keep = Math.floor((maxLen - 1) / 2);
  return short.slice(0, keep) + '…' + short.slice(-keep);
}

/**
 * Horizontal bar chart for BLE signal visualization during training.
 *
 * @param {Object} props
 * @param {{ label: string, value: number | null, overlay?: number }[]} props.bars
 *   value=null means the signal is out of reach (bar renders at 0 with ✕ marker)
 * @param {string} [props.title]
 * @param {string} [props.overlayLabel] - Legend label for the overlay line
 */
const SignalChart = ({ bars, title, overlayLabel }) => {
  // Min-max normalize all values to 0–100%
  const { min, max } = useMemo(() => {
    if (!bars || bars.length === 0) return { min: 0, max: 1 };

    const allValues = bars.flatMap((b) => {
      const vals = [];
      if (b.value != null) vals.push(b.value);
      if (b.overlay != null) vals.push(b.overlay);
      return vals;
    });

    if (allValues.length === 0) return { min: 0, max: 1 };

    let lo = Math.min(...allValues);
    let hi = Math.max(...allValues);
    if (lo === hi) {
      lo -= 1;
      hi += 1;
    }
    return { min: lo, max: hi };
  }, [bars]);

  const normalize = (v) => {
    if (v == null) return 0;
    const pct = ((v - min) / (max - min)) * 100;
    return Math.max(0, Math.min(100, pct));
  };

  if (!bars || bars.length === 0) {
    return null;
  }

  const hasOverlay = bars.some((b) => b.overlay != null);

  return (
    <div className={styles.container}>
      {title && <h4 className={styles.title}>{title}</h4>}
      {hasOverlay && overlayLabel && (
        <div className={styles.legend}>
          <span className={styles.legendBar}>Current</span>
          <span className={styles.legendOverlay}>{overlayLabel}</span>
        </div>
      )}
      <div className={styles.chart}>
        {bars.map((bar) => {
          const outOfReach = bar.value == null;
          return (
            <div key={bar.label} className={`${styles.row} ${outOfReach ? styles.rowInactive : ''}`}>
              <span className={styles.label} title={bar.label}>
                {displayLabel(bar.label)}
              </span>
              <div className={styles.track}>
                <div
                  className={styles.bar}
                  style={{ width: `${normalize(bar.value)}%` }}
                />
                {bar.overlay != null && (
                  <div
                    className={styles.overlayLine}
                    style={{ left: `${normalize(bar.overlay)}%` }}
                  />
                )}
              </div>
              <span className={styles.value}>
                {outOfReach ? '✕' : `${normalize(bar.value).toFixed(0)}%`}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default SignalChart;
