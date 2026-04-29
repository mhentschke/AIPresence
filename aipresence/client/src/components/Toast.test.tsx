import React from 'react';
import { render, screen, act } from '@testing-library/react';
import { vi } from 'vitest';
import ToastContainer from './Toast';
import { ToastProvider, useToast } from './ToastContext';

// Helper that renders a toast via the context
function AddToastButton({ message, type }: { message: string; type: 'success' | 'error' | 'warning' | 'info' }) {
  const { addToast } = useToast();
  return <button onClick={() => addToast(message, type)}>Add Toast</button>;
}

function renderWithProvider(message: string, type: 'success' | 'error' | 'warning' | 'info' = 'success') {
  return render(
    <ToastProvider>
      <AddToastButton message={message} type={type} />
      <ToastContainer />
    </ToastProvider>
  );
}

test('renders toast with correct message after addToast', () => {
  renderWithProvider('Save successful', 'success');

  act(() => {
    screen.getByText('Add Toast').click();
  });

  expect(screen.getByText('Save successful')).toBeInTheDocument();
});

test('renders toast with error type', () => {
  renderWithProvider('Something failed', 'error');

  act(() => {
    screen.getByText('Add Toast').click();
  });

  expect(screen.getByText('Something failed')).toBeInTheDocument();
  expect(screen.getByRole('alert')).toBeInTheDocument();
});

test('auto-dismisses toast after timeout', () => {
  vi.useFakeTimers();

  renderWithProvider('Temporary message', 'info');

  act(() => {
    screen.getByText('Add Toast').click();
  });

  expect(screen.getByText('Temporary message')).toBeInTheDocument();

  act(() => {
    vi.advanceTimersByTime(4000);
  });

  expect(screen.queryByText('Temporary message')).not.toBeInTheDocument();

  vi.useRealTimers();
});
