import React, { useMemo } from 'react';
import styles from './SignalChart.module.css';

/**
 * Reusable horizontal bar chart for BLE signal strength visualization.
 *
 * @param {Object} props
 * @param {{ label: string, value: number, overlay?: number }[]} props.bars
 * @param {string} [props.title]
 * @param {string} [props.overlayLabel] - Legend label for the overlay markers
 */
const SignalChart = ({ bars, title, overlayLabel }) => {
  const { min, max } = useMemo(() => {
    if (!bars || bars.length === 0) return { min: 0, max: 1 };

    const allValues = bars.flatMap((b) => {
      const vals = [b.value];
      if (b.overlay != null) vals.push(b.overlay);
      return vals;
    });

    let lo = Math.min(...allValues);
    let hi = Math.max(...allValues);
    // Avoid zero-width range
    if (lo === hi) {
      lo -= 1;
      hi += 1;
    }
    return { min: lo, max: hi };
  }, [bars]);

  const normalize = (v) => {
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
        {bars.map((bar) => (
          <div key={bar.label} className={styles.row}>
            <span className={styles.label} title={bar.label}>{bar.label}</span>
            <div className={styles.track}>
              <div
                className={styles.bar}
                style={{ width: `${normalize(bar.value)}%` }}
              />
              {bar.overlay != null && (
                <div
                  className={styles.overlay}
                  style={{ left: `${normalize(bar.overlay)}%` }}
                />
              )}
            </div>
            <span className={styles.value}>{typeof bar.value === 'number' ? bar.value.toFixed(1) : bar.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default SignalChart;
