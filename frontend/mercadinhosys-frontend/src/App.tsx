// src/App.tsx
import React, { useEffect } from 'react';
import { BrowserRouter as Router } from 'react-router-dom';
import AppRoutes from './routes/AppRoutes';
import DebugRoutes from './components/DebugRoutes';

const App: React.FC = () => {
  useEffect(() => {
    console.log('App iniciando...');
    console.log('Token no localStorage:', localStorage.getItem('access_token'));
  }, []);

  return (
    <Router>
      <DebugRoutes />
      <AppRoutes />
    </Router>
  );
};

export default App;