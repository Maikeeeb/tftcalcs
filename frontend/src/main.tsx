import React from 'react';
import ReactDOM from 'react-dom/client';
import { CssBaseline, PaletteMode, ThemeProvider, createTheme } from '@mui/material';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import App from './App';
import './index.css';

const queryClient = new QueryClient();

const AppWithProviders = () => {
  const [mode, setMode] = React.useState<PaletteMode>('dark');

  const toggleColorMode = React.useCallback(() => {
    setMode((previous) => (previous === 'light' ? 'dark' : 'light'));
  }, []);

  const theme = React.useMemo(
    () =>
      createTheme({
        palette: { mode },
      }),
    [mode],
  );

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <App mode={mode} onToggleColorMode={toggleColorMode} />
      </ThemeProvider>
    </QueryClientProvider>
  );
};

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <AppWithProviders />
  </React.StrictMode>,
);
