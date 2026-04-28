import React from 'react';
import { render, screen } from '@testing-library/react';
import RoomTable from './RoomTable';

const sampleRooms = [
  { entity_id: 'r1', name: 'Office', color: '#ff0000' },
  { entity_id: 'r2', name: 'Kitchen', color: '#00ff00' },
  { entity_id: 'r3', name: 'Bedroom', color: '#0000ff' },
];

const noopFn = () => {};

test('renders correct column headers', () => {
  render(
    <RoomTable data={sampleRooms} setData={noopFn} roomEditModal={noopFn} roomSelector={noopFn} backend={{}} forceUpdate={noopFn} />
  );

  ['Name', 'Color', 'Options'].forEach((header) => {
    expect(screen.getByText(header)).toBeInTheDocument();
  });
});

test('renders correct number of data rows', () => {
  render(
    <RoomTable data={sampleRooms} setData={noopFn} roomEditModal={noopFn} roomSelector={noopFn} backend={{}} forceUpdate={noopFn} />
  );

  // thead row + 3 data rows
  const rows = screen.getAllByRole('row');
  expect(rows).toHaveLength(1 + sampleRooms.length);
});
