// App.tsx
import { ThemeProvider } from './theme/ThemeProvider';
import { ThemeToggle } from './components/ui/ThemeToggle';
import { ConnectionTest } from './components/ConnectionTest';

function App() {
  return (
    <ThemeProvider defaultMode="dark">
      <div className="min-h-screen bg-dark-900 text-gray-100 flex flex-col items-center justify-center p-4">
        <div className="absolute top-4 right-4">
          <ThemeToggle />
        </div>

        <div className="text-center max-w-2xl">
          <div className="mb-8">
            <h1 className="text-5xl font-bold mb-4 bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
              🚀 MercadinhoSys
            </h1>
            <p className="text-xl text-gray-400">
              Sistema de Gestão Comercial
            </p>
          </div>

          <div className="card p-8 mb-8">
            <h2 className="text-2xl font-semibold mb-6 text-gray-100">
              ✅ Projeto Configurado
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-left">
              <div className="space-y-3">
                <h3 className="font-medium text-gray-300">Frontend</h3>
                <ul className="space-y-2 text-gray-400">
                  <li className="flex items-center">
                    <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                    React 18 + TypeScript
                  </li>
                  <li className="flex items-center">
                    <div className="w-2 h-2 bg-blue-500 rounded-full mr-2"></div>
                    Material-UI v5
                  </li>
                  <li className="flex items-center">
                    <div className="w-2 h-2 bg-purple-500 rounded-full mr-2"></div>
                    TailwindCSS v3
                  </li>
                </ul>
              </div>

              <div className="space-y-3">
                <h3 className="font-medium text-gray-300">Estado & Navegação</h3>
                <ul className="space-y-2 text-gray-400">
                  <li className="flex items-center">
                    <div className="w-2 h-2 bg-red-500 rounded-full mr-2"></div>
                    Redux Toolkit
                  </li>
                  <li className="flex items-center">
                    <div className="w-2 h-2 bg-yellow-500 rounded-full mr-2"></div>
                    React Router v6
                  </li>
                  <li className="flex items-center">
                    <div className="w-2 h-2 bg-indigo-500 rounded-full mr-2"></div>
                    React Hook Form + Zod
                  </li>
                </ul>
              </div>
            </div>

            {/* COMPONENTE DE TESTE ADICIONADO AQUI */}
            <div className="mt-8">
              <ConnectionTest />
            </div>

            <div className="mt-8 pt-6 border-t border-gray-800">
              <p className="text-gray-500 text-sm">
                Tema escuro ativo • Modo: <span className="text-blue-400">Profissional</span>
              </p>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button className="btn-primary px-6 py-3">
              Começar Desenvolvimento
            </button>
            <button className="btn-secondary px-6 py-3">
              Ver Documentação
            </button>
          </div>
        </div>
      </div>
    </ThemeProvider>
  );
}

export default App;