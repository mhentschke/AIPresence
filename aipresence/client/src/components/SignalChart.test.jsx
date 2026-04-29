import React from 'react';
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

test('renders a bar for each signal entry', () => {
  render(<SignalChart bars={sampleBars} />);

  sampleBars.forEach((bar) => {
    expect(screen.getByText(bar.label)).toBeInTheDocument();
    expect(screen.getByText(bar.value.toFixed(1))).toBeInTheDocument();
  });
});

test('renders nothing when bars is empty', () => {
  const { container } = render(<SignalChart bars={[]} />);
  expect(container.innerHTML).toBe('');
});

test('renders title when provided', () => {
  render(<SignalChart bars={sampleBars} title="Signal Strength" />);
  expect(screen.getByText('Signal Strength')).toBeInTheDocument();
});

test('renders overlay markers when overlay values are provided', () => {
  const { container } = render(
    <SignalChart bars={barsWithOverlay} overlayLabel="Training Avg" />
  );

  const overlays = container.querySelectorAll('.overlay');
  expect(overlays).toHaveLength(2);
});

test('does not render overlay markers when no overlay values exist', () => {
  const { container } = render(<SignalChart bars={sampleBars} />);

  const overlays = container.querySelectorAll('.overlay');
  expect(overlays).toHaveLength(0);
});

test('renders legend when overlay data and overlayLabel are present', () => {
  render(<SignalChart bars={barsWithOverlay} overlayLabel="Training Avg" />);

  expect(screen.getByText('Current')).toBeInTheDocument();
  expect(screen.getByText('Training Avg')).toBeInTheDocument();
});

test('labels each bar with the source entity ID', () => {
  render(<SignalChart bars={sampleBars} />);

  sampleBars.forEach((bar) => {
    const label = screen.getByText(bar.label);
    expect(label).toBeInTheDocument();
    expect(label.getAttribute('title')).toBe(bar.label);
  });
});
