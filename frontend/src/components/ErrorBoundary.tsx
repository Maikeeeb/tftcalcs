import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Alert, Box, Button, Stack, Typography } from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // Log error to console in development
    if (import.meta.env.DEV) {
      console.error('ErrorBoundary caught an error:', error, errorInfo);
    }

    this.setState({
      error,
      errorInfo,
    });
  }

  handleReload = (): void => {
    window.location.reload();
  };

  render(): ReactNode {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      const isDevelopment = import.meta.env.DEV;
      const errorMessage = this.state.error?.message || 'An unexpected error occurred';
      const errorStack = this.state.errorInfo?.componentStack;

      return (
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            minHeight: '100vh',
            p: 3,
          }}
        >
          <Alert
            severity="error"
            sx={{
              maxWidth: 600,
              width: '100%',
            }}
            action={
              <Button color="inherit" size="small" onClick={this.handleReload} startIcon={<RefreshIcon />}>
                Reload
              </Button>
            }
          >
            <Stack spacing={2}>
              <Typography variant="h6">Something went wrong</Typography>
              <Typography variant="body1">{errorMessage}</Typography>
              {isDevelopment && errorStack && (
                <Box
                  component="pre"
                  sx={{
                    bgcolor: 'background.default',
                    p: 1,
                    borderRadius: 1,
                    fontSize: '0.75rem',
                    overflow: 'auto',
                    maxHeight: 200,
                    mt: 1,
                  }}
                >
                  {errorStack}
                </Box>
              )}
              <Button variant="outlined" onClick={this.handleReload} startIcon={<RefreshIcon />} sx={{ mt: 1 }}>
                Reload Page
              </Button>
            </Stack>
          </Alert>
        </Box>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
