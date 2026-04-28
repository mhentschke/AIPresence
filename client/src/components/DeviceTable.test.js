import React from 'react';
import { render, screen } from '@testing-library/react';
import DeviceTable from './DeviceTable';

const sampleDevices = [
  { entity_id: 'e1', identifier: 'tracker.phone_1', name: 'Phone 1', type: 'Tracker', trained: true, accuracy: 0.95, location: 'Office', confidence: 0.88 },
  { entity_id: 'e2', identifier: 'beacon.tag_1', name: 'Tag 1', type: 'Beacon', trained: false, accuracy: '-', location: '-', confidence: undefined },
  { entity_id: 'e3', identifier: 'tracker.phone_2', name: 'Phone 2', type: 'Tracker', trained: true, accuracy: 0.87, location: 'Kitchen', confidence: 0.72 },
];

const noopFn = () => {};

test('renders correct column headers', () => {
  render(
    <DeviceTable data={sampleDevices} setData={noopFn} deviceEditModal={noopFn} deviceTrainModal={noopFn} deviceSelector={noopFn} backend={{}} forceUpdate={noopFn} />
  );

  ['Identifier', 'Name', 'Trained', 'Accuracy', 'Location', 'Confidence', 'Options'].forEach((header) => {
    expect(screen.getByText(header)).toBeInTheDocument();
  });
});

test('renders correct number of data rows', () => {
  render(
    <DeviceTable data={sampleDevices} setData={noopFn} deviceEditModal={noopFn} deviceTrainModal={noopFn} deviceSelector={noopFn} backend={{}} forceUpdate={noopFn} />
  );

  // thead row + 3 data rows
  const rows = screen.getAllByRole('row');
  expect(rows).toHaveLength(1 + sampleDevices.length);
});
