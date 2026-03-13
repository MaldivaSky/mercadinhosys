// src/App.tsx
import React from 'react';
import { BrowserRouter as Router } from 'react-router-dom';
import AppRoutes from './routes/AppRoutes';
import WelcomeTour from './components/WelcomeTour';
import DebugRoutes from './components/DebugRoutes';
import { ThemeProvider } from './theme/ThemeProvider';
import { ConfigProvider } from './contexts/ConfigContext';
import { AuthProvider } from './contexts/AuthContext';
import { SuperAdminProvider } from './contexts/SuperAdminContext';
import { Toaster } from 'react-hot-toast';
import ErrorBoundary from './components/ErrorBoundary';

const App: React.FC = () => {
  return (
    <ErrorBoundary name="MercadinhoSys Global">
      <SuperAdminProvider>
        <AuthProvider>
          <ConfigProvider>
            <ThemeProvider defaultMode="dark">
              <Router>
                <DebugRoutes />
                <AppRoutes />
                <WelcomeTour />
                <Toaster
                  position="top-right"
                  reverseOrder={false}
                  gutter={12}
                  containerStyle={{ zIndex: 999999, top: '24px', right: '24px' }}
                  toastOptions={{
                    duration: 2500,
                  }}
                />
              </Router>
            </ThemeProvider>
          </ConfigProvider>
        </AuthProvider>
      </SuperAdminProvider>
    </ErrorBoundary>
  );
};

export default App;
