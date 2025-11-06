import React from "react";

/**
 * ErrorBoundary component to catch React errors
 * Provides fallback UI and error logging
 */
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null
    };
  }

  static getDerivedStateFromError(error) {
    // Update state so next render shows fallback UI
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    // Log error for debugging
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    
    this.setState({
      error,
      errorInfo
    });

    // You can also log to an error reporting service here
    // logErrorToService(error, errorInfo);
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null
    });

    // Call optional reset callback
    if (this.props.onReset) {
      this.props.onReset();
    }
  };

  render() {
    if (this.state.hasError) {
      // Custom fallback UI from props
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default fallback UI
      return (
        <div className="card-stage">
          <div className="card-shell">
            <div className="card-surface">
              <div style={{
                textAlign: 'center',
                padding: '60px 24px',
                maxWidth: '600px',
                margin: '0 auto'
              }}>
                {/* Error Icon */}
                <div style={{
                  fontSize: '4rem',
                  marginBottom: '24px',
                  opacity: 0.7
                }}>
                  ⚠️
                </div>

                {/* Error Title */}
                <h2 style={{
                  margin: '0 0 16px',
                  fontSize: '1.8rem',
                  color: 'var(--text-primary)'
                }}>
                  {this.props.title || "Oops! Something went wrong"}
                </h2>

                {/* Error Message */}
                <p style={{
                  margin: '0 0 32px',
                  color: 'var(--text-secondary)',
                  fontSize: '1.05rem',
                  lineHeight: '1.6'
                }}>
                  {this.props.message || "We encountered an unexpected error. Please try again."}
                </p>

                {/* Action Buttons */}
                <div style={{
                  display: 'flex',
                  gap: '12px',
                  justifyContent: 'center',
                  flexWrap: 'wrap'
                }}>
                  <button
                    className="cta-button"
                    onClick={this.handleReset}
                    style={{ fontSize: '1rem' }}
                  >
                    Try Again
                  </button>

                  <button
                    className="button-secondary"
                    onClick={() => window.location.href = '/'}
                    style={{ fontSize: '1rem' }}
                  >
                    Go Home
                  </button>
                </div>

                {/* Error Details (Development Only) */}
                {process.env.NODE_ENV === 'development' && this.state.error && (
                  <details style={{
                    marginTop: '40px',
                    padding: '16px',
                    background: 'rgba(255, 123, 156, 0.1)',
                    border: '1px solid rgba(255, 123, 156, 0.3)',
                    borderRadius: '8px',
                    textAlign: 'left',
                    fontSize: '0.85rem',
                    color: 'var(--text-secondary)'
                  }}>
                    <summary style={{ 
                      cursor: 'pointer',
                      fontWeight: '600',
                      marginBottom: '12px',
                      color: '#ff7b9c'
                    }}>
                      Error Details (Development)
                    </summary>
                    <pre style={{
                      whiteSpace: 'pre-wrap',
                      wordBreak: 'break-word',
                      fontSize: '0.8rem',
                      margin: '0'
                    }}>
                      <strong>Error:</strong> {this.state.error.toString()}
                      {'\n\n'}
                      <strong>Stack:</strong> {this.state.errorInfo?.componentStack}
                    </pre>
                  </details>
                )}

                {/* Support Link */}
                {this.props.showSupport !== false && (
                  <p style={{
                    marginTop: '32px',
                    fontSize: '0.9rem',
                    color: 'rgba(167, 180, 217, 0.7)'
                  }}>
                    Need help? <a 
                      href="mailto:support@tradingpath.com"
                      style={{
                        color: 'var(--accent)',
                        textDecoration: 'underline'
                      }}
                    >
                      Contact Support
                    </a>
                  </p>
                )}
              </div>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;

