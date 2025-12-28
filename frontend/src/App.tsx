import { useState } from 'react'; // Remova o React import se não usar
import Header from './components/Layout/Header';
import Sidebar from './components/Layout/Sidebar';
import Dashboard from './pages/Dashboard/Dashboard';
import PdvPage from './pages/PDV/PdvPage';
import './App.css';

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [currentPage, setCurrentPage] = useState<'dashboard' | 'pdv'>('dashboard');

  return (
    <div className="min-h-screen bg-gray-50">
      <Header onMenuClick={() => setSidebarOpen(!sidebarOpen)} />

      <div className="flex">
        <Sidebar
          isOpen={sidebarOpen}
          onClose={() => setSidebarOpen(false)}
          onNavigate={setCurrentPage}
        />

        <main className="flex-1 p-4 md:p-6">
          {currentPage === 'dashboard' ? <Dashboard /> : <PdvPage />}

          <footer className="mt-8 pt-6 border-t border-gray-200">
            <div className="text-center text-gray-500 text-sm">
              <p>Sistema Mercadinho v1.0 • Desenvolvido para gestão de mercadinhos</p>
              <p className="mt-1">© 2025 - Todos os direitos reservados</p>
            </div>
          </footer>
        </main>
      </div>
    </div>
  );
}

export default App;