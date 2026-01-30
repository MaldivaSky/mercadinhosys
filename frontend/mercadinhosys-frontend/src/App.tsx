// src/App.tsx
import React, { useEffect } from 'react';
import { BrowserRouter as Router } from 'react-router-dom';
import AppRoutes from './routes/AppRoutes';
import DebugRoutes from './components/DebugRoutes';
import { ThemeProvider } from './theme/ThemeProvider';
import { ConfigProvider } from './contexts/ConfigContext';
import { Toaster } from 'react-hot-toast';

const App: React.FC = () => {
  useEffect(() => {
    console.log('App iniciando...');
    console.log('Token no localStorage:', localStorage.getItem('access_token'));
  }, []);

  return (
    <ThemeProvider defaultMode="dark">
      <ConfigProvider>
        <Router>
          <DebugRoutes />
          <AppRoutes />
          <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#363636',
              color: '#fff',
              fontSize: '14px',
              fontWeight: '500',
            },
            success: {
              duration: 5000,
              style: {
                background: '#10b981',
              },
            },
            error: {
              duration: 6000,
              style: {
                background: '#ef4444',
              },
            },
          }}
        />
      </Router>
      </ConfigProvider>
    </ThemeProvider>
  );
};

export default App;