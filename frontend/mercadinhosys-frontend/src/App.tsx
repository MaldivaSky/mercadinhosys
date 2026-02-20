// src/App.tsx
import React from 'react';
import { BrowserRouter as Router } from 'react-router-dom';
import AppRoutes from './routes/AppRoutes';
import DebugRoutes from './components/DebugRoutes';
import { ThemeProvider } from './theme/ThemeProvider';
import { ConfigProvider } from './contexts/ConfigContext';
import { Toaster } from 'react-hot-toast';
import ErrorBoundary from './components/ErrorBoundary';

const App: React.FC = () => {
  return (
    <ErrorBoundary name="MercadinhoSys Global">
      <ConfigProvider>
        <ThemeProvider defaultMode="dark">
          <Router>
            <DebugRoutes />
            <AppRoutes />
            <Toaster
              position="top-right"
              reverseOrder={false}
              gutter={12}
              containerStyle={{ zIndex: 99999, top: '24px', right: '24px' }}
              toastOptions={{
                duration: 3500,
              }}
            />
          </Router>
        </ThemeProvider>
      </ConfigProvider>
    </ErrorBoundary>
  );
};

export default App;
