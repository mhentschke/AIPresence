import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import App from './App';
import { Backend } from './Backend';

// Mock the Backend module
vi.mock('./Backend', () => ({
  Backend: {
    GetDevices: vi.fn(),
    GetBeaconMonitors: vi.fn(),
    GetSensors: vi.fn(),
    GetRooms: vi.fn(),
    GetDeviceLocation: vi.fn(),
  },
}));

beforeEach(() => {
  Backend.GetDevices.mockResolvedValue([]);
  Backend.GetBeaconMonitors.mockResolvedValue([]);
  Backend.GetSensors.mockResolvedValue([]);
  Backend.GetRooms.mockResolvedValue([]);
});

afterEach(() => {
  vi.restoreAllMocks();
});

test('renders Devices, Monitors, Sensors, and Rooms headings', async () => {
  render(<App />);

  await waitFor(() => {
    expect(screen.getByText('Devices')).toBeInTheDocument();
  });
  expect(screen.getByText('Monitors')).toBeInTheDocument();
  expect(screen.getByText('Sensors')).toBeInTheDocument();
  expect(screen.getByText('Rooms')).toBeInTheDocument();
});

test('calls Backend API methods on mount', async () => {
  render(<App />);

  await waitFor(() => {
    expect(Backend.GetDevices).toHaveBeenCalled();
  });
  expect(Backend.GetBeaconMonitors).toHaveBeenCalled();
  expect(Backend.GetSensors).toHaveBeenCalled();
  expect(Backend.GetRooms).toHaveBeenCalled();
});
