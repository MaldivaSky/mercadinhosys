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
  );
};

export default App;
