import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

// Importar teste de conectividade (disponível no console como testConnection())
import './utils/testConnection';

// StrictMode removido — causava dupla execução de useEffect (dobrava chamadas de API)
ReactDOM.createRoot(document.getElementById('root')!).render(
  <App />
);
