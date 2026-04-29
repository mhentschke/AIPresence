import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { vi } from 'vitest';
import ErrorBoundary from './ErrorBoundary';

// Suppress console.error from ErrorBoundary.componentDidCatch during tests
beforeEach(() => {
  vi.spyOn(console, 'error').mockImplementation(() => {});
});

afterEach(() => {
  vi.restoreAllMocks();
});

function ThrowingChild({ shouldThrow }: { shouldThrow: boolean }) {
  if (shouldThrow) throw new Error('Test error');
  return <div>Child content</div>;
}

test('renders children when no error occurs', () => {
  render(
    <ErrorBoundary>
      <ThrowingChild shouldThrow={false} />
    </ErrorBoundary>
  );
  expect(screen.getByText('Child content')).toBeInTheDocument();
});

test('renders fallback UI when child throws', () => {
  render(
    <ErrorBoundary>
      <ThrowingChild shouldThrow={true} />
    </ErrorBoundary>
  );
  expect(screen.getByText('Something went wrong')).toBeInTheDocument();
  expect(screen.getByText('Test error')).toBeInTheDocument();
  expect(screen.getByText('Try Again')).toBeInTheDocument();
});

test('resets error state when Try Again is clicked', () => {
  const { rerender } = render(
    <ErrorBoundary>
      <ThrowingChild shouldThrow={true} />
    </ErrorBoundary>
  );

  expect(screen.getByText('Something went wrong')).toBeInTheDocument();

  // After clicking retry, the ErrorBoundary resets and re-renders children.
  // We need to change the child so it doesn't throw again.
  // Since ErrorBoundary is a class component, we use a ref-based approach:
  // re-render with a non-throwing child, then click retry.
  rerender(
    <ErrorBoundary>
      <ThrowingChild shouldThrow={false} />
    </ErrorBoundary>
  );

  fireEvent.click(screen.getByText('Try Again'));
  expect(screen.getByText('Child content')).toBeInTheDocument();
});
