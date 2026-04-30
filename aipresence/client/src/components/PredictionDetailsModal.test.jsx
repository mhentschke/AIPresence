import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import PredictionDetailsModal from './PredictionDetailsModal';
import { ToastProvider } from './ToastContext';

const mockRooms = [
  { id: 'room-1', name: 'Office', color: '#ff0000' },
  { id: 'room-2', name: 'Kitchen', color: '#00ff00' },
];

const mockDevice = { id: 'dev-1', name: 'Phone', trained: true };

const mockSignalData = {
  signals: {
    'sensor.proxy_a': -65,
    'sensor.proxy_b': -80,
  },
};

const mockPrediction = {
  room: 'room-1',
  confidence: 0.87,
  room_room_1: 0.87,
  'room_room-1': 0.87,
  'room_room-2': 0.13,
};

const mockTrainingAverages = {
  rooms: {
    'room-1': { name: 'Office', averages: { 'sensor.proxy_a': -60, 'sensor.proxy_b': -75 } },
    'room-2': { name: 'Kitchen', averages: { 'sensor.proxy_a': -85, 'sensor.proxy_b': -55 } },
  },
  feature_columns: ['sensor.proxy_a', 'sensor.proxy_b'],
};

function createMockBackend(overrides = {}) {
  return {
    GetSignalData: vi.fn().mockResolvedValue(mockSignalData),
    GetDeviceLocation: vi.fn().mockResolvedValue(mockPrediction),
    GetTrainingAverages: vi.fn().mockResolvedValue(mockTrainingAverages),
    ...overrides,
  };
}

function renderModal(props = {}) {
  const defaults = {
    device: mockDevice,
    rooms: mockRooms,
    modal: true,
    setModal: vi.fn(),
    backend: createMockBackend(),
  };
  return render(
    <ToastProvider>
      <PredictionDetailsModal {...defaults} {...props} />
    </ToastProvider>
  );
}

test('renders device name in header', async () => {
  renderModal();
  await waitFor(() => {
    expect(screen.getByText(/Prediction Details — Phone/)).toBeInTheDocument();
  });
});

test('displays predicted room and confidence', async () => {
  renderModal();
  await waitFor(() => {
    // The confidence value appears as "(87.0%)" inside the predicted value span
    expect(screen.getByText('Predicted Room:')).toBeInTheDocument();
    expect(screen.getByText(/\(87\.0%\)/)).toBeInTheDocument();
  });
});

test('renders room probability bars', async () => {
  renderModal();
  await waitFor(() => {
    expect(screen.getByText('Room Probabilities')).toBeInTheDocument();
  });
});

test('renders signal chart with overlay', async () => {
  const { container } = renderModal();
  await waitFor(() => {
    // Signal chart should have overlay lines from training averages
    const overlays = container.querySelectorAll('[class*="overlayLine"]');
    expect(overlays.length).toBeGreaterThan(0);
  });
});

test('renders room selector dropdown', async () => {
  renderModal();
  await waitFor(() => {
    expect(screen.getByLabelText('Overlay:')).toBeInTheDocument();
  });
});

test('returns null when modal is false', () => {
  const { container } = renderModal({ modal: false });
  expect(container.innerHTML).toBe('');
});

test('returns null when device is null', () => {
  const { container } = renderModal({ device: null });
  expect(container.innerHTML).toBe('');
});

test('calls backend APIs on open', async () => {
  const backend = createMockBackend();
  renderModal({ backend });
  await waitFor(() => {
    expect(backend.GetSignalData).toHaveBeenCalledWith('dev-1');
    expect(backend.GetDeviceLocation).toHaveBeenCalledWith('dev-1');
    expect(backend.GetTrainingAverages).toHaveBeenCalledWith('dev-1');
  });
});
