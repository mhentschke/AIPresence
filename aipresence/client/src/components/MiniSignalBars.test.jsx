import { render, screen } from '@testing-library/react';
import MiniSignalBars from './MiniSignalBars';

const sampleMonitors = [
  { entity_id: 'sensor.tablet_beacon_monitor', signal_value: -65.2 },
  { entity_id: 'sensor.office_proxy', signal_value: -78.1 },
  { entity_id: 'sensor.bedroom_proxy', signal_value: -89.0 },
];

test('renders one row per monitor', () => {
  const { container } = render(<MiniSignalBars monitors={sampleMonitors} />);
  const rows = container.querySelectorAll('[class*="row"]');
  expect(rows).toHaveLength(3);
});

test('displays truncated monitor names with full entity_id in tooltip', () => {
  render(<MiniSignalBars monitors={sampleMonitors} />);

  expect(screen.getByTitle('sensor.tablet_beacon_monitor')).toBeInTheDocument();
  expect(screen.getByTitle('sensor.office_proxy')).toBeInTheDocument();
  expect(screen.getByTitle('sensor.bedroom_proxy')).toBeInTheDocument();
});

test('displays rounded signal values', () => {
  render(<MiniSignalBars monitors={sampleMonitors} />);

  expect(screen.getByText('-65')).toBeInTheDocument();
  expect(screen.getByText('-78')).toBeInTheDocument();
  expect(screen.getByText('-89')).toBeInTheDocument();
});

test('sorts monitors by signal strength (strongest first)', () => {
  const unordered = [
    { entity_id: 'sensor.weak', signal_value: -90 },
    { entity_id: 'sensor.strong', signal_value: -50 },
    { entity_id: 'sensor.mid', signal_value: -70 },
  ];
  const { container } = render(<MiniSignalBars monitors={unordered} />);
  const values = container.querySelectorAll('[class*="value"]');
  expect(values[0].textContent).toBe('-50');
  expect(values[1].textContent).toBe('-70');
  expect(values[2].textContent).toBe('-90');
});

test('normalizes bars: strongest gets full width, weakest gets minimum', () => {
  const { container } = render(<MiniSignalBars monitors={sampleMonitors} />);
  const bars = container.querySelectorAll('[class*="bar"]');

  // Strongest signal (-65.2) should have 100% width
  expect(bars[0].style.width).toBe('100%');
  // Weakest signal (-89.0) should have minimum bar width (5%)
  expect(bars[2].style.width).toBe('5%');
});

test('renders dash when monitors array is empty', () => {
  render(<MiniSignalBars monitors={[]} />);
  expect(screen.getByText('—')).toBeInTheDocument();
});

test('renders dash when monitors is undefined', () => {
  render(<MiniSignalBars monitors={undefined} />);
  expect(screen.getByText('—')).toBeInTheDocument();
});

test('handles single monitor (all bars at full width)', () => {
  const single = [{ entity_id: 'sensor.only_one', signal_value: -72 }];
  const { container } = render(<MiniSignalBars monitors={single} />);
  const bars = container.querySelectorAll('[class*="bar"]');
  expect(bars).toHaveLength(1);
  expect(bars[0].style.width).toBe('100%');
});

test('strips domain prefix from entity_id for display', () => {
  const monitors = [{ entity_id: 'sensor.office_proxy', signal_value: -70 }];
  render(<MiniSignalBars monitors={monitors} />);
  const nameEl = screen.getByTitle('sensor.office_proxy');
  expect(nameEl.textContent).toBe('office_proxy');
});
