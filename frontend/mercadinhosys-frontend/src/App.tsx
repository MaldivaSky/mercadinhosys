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
              duration: 3000,
              style: {
                background: '#333',
                color: '#fff',
                zIndex: 99999, // Ensure it's high but simple
              },
            }}
          />
        </Router>
      </ThemeProvider>
    </ConfigProvider>
  );
};

export default App;
