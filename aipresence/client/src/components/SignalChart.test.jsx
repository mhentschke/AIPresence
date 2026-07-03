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

  // Labels without "-" render as full text, no tooltip
  sampleBars.forEach((bar) => {
    expect(screen.getByText(bar.label)).toBeInTheDocument();
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

  // No beaconNames passed, so no tooltip — find by text content
  const labelEl = screen.getByText(/…/);
  // Should not contain the monitor entity prefix
  expect(labelEl.textContent).not.toContain('sensor.phone_monitor');
  // Should be truncated with ellipsis
  expect(labelEl.textContent).toContain('…');
  // No tooltip when no friendly name is resolved
  expect(labelEl).not.toHaveAttribute('title');
});

test('shows full label for short keys without monitor prefix', () => {
  const key = 'binary_sensor.motion';
  const bars = [{ label: key, value: 1 }];
  render(<SignalChart bars={bars} />);

  const el = screen.getByText(key);
  expect(el.textContent).toBe(key);
  // No tooltip for keys without "-"
  expect(el).not.toHaveAttribute('title');
});

test('displays friendly name when beaconNames maps the beacon portion', () => {
  const fullKey = 'sensor.office_proxy-abc123_100_200';
  const bars = [{ label: fullKey, value: -65 }];
  const beaconNames = { 'abc123_100_200': "Dad's Phone" };

  render(<SignalChart bars={bars} beaconNames={beaconNames} />);

  // Friendly name is displayed
  expect(screen.getByText("Dad's Phone")).toBeInTheDocument();
  // Full key is in the tooltip
  expect(screen.getByTitle(fullKey)).toBeInTheDocument();
});

test('falls back to beacon portion when beaconNames has no entry', () => {
  const fullKey = 'sensor.office_proxy-unknown_beacon_id';
  const bars = [{ label: fullKey, value: -72 }];
  const beaconNames = { 'some_other_beacon': 'Other Device' };

  render(<SignalChart bars={bars} beaconNames={beaconNames} />);

  // Shows the raw beacon portion (after the dash)
  expect(screen.getByText('unknown_beacon_id')).toBeInTheDocument();
  // No tooltip when no friendly name
  const labelEl = screen.getByText('unknown_beacon_id');
  expect(labelEl).not.toHaveAttribute('title');
});

test('shows no tooltip when beaconNames prop is not provided', () => {
  const fullKey = 'sensor.monitor-some_beacon';
  const bars = [{ label: fullKey, value: -60 }];

  render(<SignalChart bars={bars} />);

  const labelEl = screen.getByText('some_beacon');
  expect(labelEl).not.toHaveAttribute('title');
});

test('handles empty beaconNames object gracefully', () => {
  const fullKey = 'sensor.monitor-beacon_xyz';
  const bars = [{ label: fullKey, value: -55 }];

  render(<SignalChart bars={bars} beaconNames={{}} />);

  expect(screen.getByText('beacon_xyz')).toBeInTheDocument();
  const labelEl = screen.getByText('beacon_xyz');
  expect(labelEl).not.toHaveAttribute('title');
});
