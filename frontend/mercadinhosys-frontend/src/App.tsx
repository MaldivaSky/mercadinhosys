// src/App.tsx
import React from 'react';
import { BrowserRouter as Router } from 'react-router-dom';
import AppRoutes from './routes/AppRoutes';
import DebugRoutes from './components/DebugRoutes';
import { ThemeProvider } from './theme/ThemeProvider';
import { ConfigProvider } from './contexts/ConfigContext';
import { Toaster } from 'react-hot-toast';

const App: React.FC = () => {
  return (
    <ConfigProvider>
      <ThemeProvider defaultMode="dark">
        <Router>
          <DebugRoutes />
          <AppRoutes />
          <Toaster
          position="top-right"
          toastOptions={{
            duration: 2500,
            style: {
              background: '#363636',
              color: '#fff',
              fontSize: '14px',
              fontWeight: '500',
            },
            success: {
              duration: 2500,
              style: {
                background: '#10b981',
              },
            },
            error: {
              duration: 3500,
              style: {
                background: '#ef4444',
              },
            },
          }}
        />
      </Router>
      </ThemeProvider>
    </ConfigProvider>
  );
};

export default App;
