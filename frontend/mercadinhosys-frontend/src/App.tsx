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
              gutter={10}
              containerStyle={{ zIndex: 99999, top: '16px', right: '16px' }}
              toastOptions={{
                duration: 4000,
                // Sem style global — cada toast define o seu próprio
              }}
            />
          </Router>
        </ThemeProvider>
      </ConfigProvider>
    </ErrorBoundary>
  );
};

export default App;
