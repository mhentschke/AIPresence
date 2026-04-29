import { render, screen } from '@testing-library/react';
import SignalChart from './SignalChart';

const sampleBars = [
  { label: 'sensor.proxy_office', value: -65.3 },
  { label: 'sensor.proxy_kitchen', value: -82.1 },
  { label: 'sensor.phone_monitor', value: -71.8 },
];

const barsWithOverlay = [
  { label: 'sensor.proxy_office', value: -65.3, overlay: -60.0 },
  { label: 'sensor.proxy_kitchen', value: -82.1, overlay: -78.5 },
];

test('renders a bar for each signal entry with normalized percentage', () => {
  render(<SignalChart bars={sampleBars} />);

  sampleBars.forEach((bar) => {
    // Full label is in the title attribute
    expect(screen.getByTitle(bar.label)).toBeInTheDocument();
  });
  // Values should show as percentages (e.g. "100%", "0%")
  expect(screen.getAllByText(/%$/).length).toBe(sampleBars.length);
});

test('renders nothing when bars is empty', () => {
  const { container } = render(<SignalChart bars={[]} />);
  expect(container.innerHTML).toBe('');
});

test('renders title when provided', () => {
  render(<SignalChart bars={sampleBars} title="Signal Strength" />);
  expect(screen.getByText('Signal Strength')).toBeInTheDocument();
});

test('renders overlay lines when overlay values are provided', () => {
  const { container } = render(
    <SignalChart bars={barsWithOverlay} overlayLabel="Training Avg" />
  );

  const overlays = container.querySelectorAll('[class*="overlayLine"]');
  expect(overlays).toHaveLength(2);
});

test('renders legend when overlay data and overlayLabel are present', () => {
  render(<SignalChart bars={barsWithOverlay} overlayLabel="Training Avg" />);

  expect(screen.getByText('Current')).toBeInTheDocument();
  expect(screen.getByText('Training Avg')).toBeInTheDocument();
});

test('shows ✕ for out-of-reach signals (null value)', () => {
  const bars = [
    { label: 'sensor.nearby', value: -50 },
    { label: 'sensor.gone', value: null },
  ];
  render(<SignalChart bars={bars} />);

  expect(screen.getByText('✕')).toBeInTheDocument();
});

test('strips monitor prefix and truncates long beacon IDs', () => {
  const fullKey = 'sensor.phone_monitor-very_long_beacon_uuid_major_minor_that_exceeds_limit';
  const bars = [{ label: fullKey, value: -70 }];
  render(<SignalChart bars={bars} />);

  const el = screen.getByTitle(fullKey);
  // Should not contain the monitor entity prefix
  expect(el.textContent).not.toContain('sensor.phone_monitor');
  // Should be truncated with ellipsis
  expect(el.textContent).toContain('…');
});

test('shows full label for short keys without monitor prefix', () => {
  const key = 'binary_sensor.motion';
  const bars = [{ label: key, value: 1 }];
  render(<SignalChart bars={bars} />);

  const el = screen.getByTitle(key);
  expect(el.textContent).toBe(key);
});
