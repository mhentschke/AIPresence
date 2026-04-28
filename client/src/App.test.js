import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import App from './App';
import { Backend } from './Backend';

// Mock the Backend module
jest.mock('./Backend', () => ({
  Backend: {
    GetDevices: jest.fn(),
    GetTrackers: jest.fn(),
    GetSensors: jest.fn(),
    GetRooms: jest.fn(),
    GetDeviceLocation: jest.fn(),
  },
}));

beforeEach(() => {
  Backend.GetDevices.mockResolvedValue([]);
  Backend.GetTrackers.mockResolvedValue([]);
  Backend.GetSensors.mockResolvedValue([]);
  Backend.GetRooms.mockResolvedValue([]);
});

afterEach(() => {
  jest.restoreAllMocks();
});

test('renders Devices, Trackers, Sensors, and Rooms headings', async () => {
  render(<App />);

  await waitFor(() => {
    expect(screen.getByText('Devices')).toBeInTheDocument();
  });
  expect(screen.getByText('Trackers')).toBeInTheDocument();
  expect(screen.getByText('Sensors')).toBeInTheDocument();
  expect(screen.getByText('Rooms')).toBeInTheDocument();
});

test('calls Backend API methods on mount', async () => {
  render(<App />);

  await waitFor(() => {
    expect(Backend.GetDevices).toHaveBeenCalledTimes(1);
  });
  expect(Backend.GetTrackers).toHaveBeenCalledTimes(1);
  expect(Backend.GetSensors).toHaveBeenCalledTimes(1);
  expect(Backend.GetRooms).toHaveBeenCalledTimes(1);
});
