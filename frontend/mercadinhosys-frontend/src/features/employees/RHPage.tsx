import { useState } from 'react';
import { Users, Clock, FileText, BarChart, Timer, AlertTriangle } from 'lucide-react';
import RHDashboard from './components/RHDashboard';
import PontoHistoricoRH from './components/PontoHistoricoRH';
import EspelhoPonto from './components/EspelhoPonto';
import BancoHorasRH from './components/BancoHorasRH';
import JustificativasRH from './components/JustificativasRH';

type TabType = 'dashboard' | 'historico' | 'espelho' | 'banco-horas' | 'justificativas';

export default function RHPage() {
  const [activeTab, setActiveTab] = useState<TabType>('dashboard');

  const tabs = [
    { id: 'dashboard' as TabType, label: 'Dashboard RH', icon: BarChart, description: 'Métricas e análises' },
    { id: 'historico' as TabType, label: 'Histórico de Registros', icon: Clock, description: 'Todos os registros de ponto' },
    { id: 'espelho' as TabType, label: 'Espelho de Ponto', icon: FileText, description: 'Relatório individual' },
    { id: 'banco-horas' as TabType, label: 'Banco de Horas', icon: Timer, description: 'Saldos e créditos' },
    { id: 'justificativas' as TabType, label: 'Justificativas', icon: AlertTriangle, description: 'Atrasos e ausências' },
  ];

  return (
    <div className="p-6 max-w-7xl mx-auto bg-gray-50 dark:bg-gray-900 min-h-screen">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center space-x-4 mb-6">
          <div className="p-3 bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl shadow-lg">
            <Users className="w-8 h-8 text-white" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
              Recursos Humanos
            </h1>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              Gestão completa de RH, ponto eletrônico e folha de pagamento
            </p>
          </div>
        </div>

        {/* Tabs */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-2 flex gap-2">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex-1 px-4 py-3 rounded-lg transition-all flex items-center justify-center gap-3 ${activeTab === tab.id
                    ? 'bg-gradient-to-r from-purple-500 to-purple-600 text-white shadow-lg'
                    : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
                  }`}
              >
                <Icon className="w-5 h-5" />
                <div className="text-left">
                  <div className="font-medium">{tab.label}</div>
                  <div className="text-xs opacity-75">{tab.description}</div>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Content */}
      <div className="mt-6">
        {activeTab === 'dashboard' && <RHDashboard />}
        {activeTab === 'historico' && <PontoHistoricoRH />}
        {activeTab === 'espelho' && <EspelhoPonto />}
        {activeTab === 'banco-horas' && <BancoHorasRH />}
        {activeTab === 'justificativas' && <JustificativasRH />}
      </div>
    </div>
  );
}
