import React, { Component } from 'react';

interface ErrorBoundaryProps {
  children: React.ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export default class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error('ErrorBoundary caught:', error, info.componentStack);
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: 'var(--spacing-xl)',
          textAlign: 'center',
          gap: 'var(--spacing-md)',
        }}>
          <div style={{
            background: 'var(--color-surface)',
            borderRadius: 'var(--radius-md)',
            boxShadow: 'var(--shadow-sm)',
            padding: 'var(--spacing-lg)',
            maxWidth: '400px',
            width: '100%',
          }}>
            <h2 style={{
              margin: '0 0 var(--spacing-sm)',
              fontSize: 'var(--font-size-lg)',
              color: 'var(--color-error)',
            }}>
              Something went wrong
            </h2>
            <p style={{
              margin: '0 0 var(--spacing-md)',
              color: 'var(--color-text-secondary)',
              fontSize: 'var(--font-size-sm)',
            }}>
              {this.state.error?.message || 'An unexpected error occurred.'}
            </p>
            <button
              onClick={this.handleRetry}
              style={{
                background: 'var(--color-primary)',
                color: 'var(--color-primary-text)',
                border: 'none',
                borderRadius: 'var(--radius-sm)',
                padding: 'var(--spacing-sm) var(--spacing-md)',
                fontSize: 'var(--font-size-md)',
                cursor: 'pointer',
              }}
            >
              Try Again
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
