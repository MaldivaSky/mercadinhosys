import { useState, useEffect } from 'react';
import { apiClient } from '../../api/apiClient';
import { Target, Package, AlertTriangle, Users, DollarSign, Activity } from 'lucide-react';

import ExecutiveTab from './components/tabs/ExecutiveTab';
import SalesSfaTab from './components/tabs/SalesSfaTab';
import InventoryTab from './components/tabs/InventoryTab';
import FinancialTab from './components/tabs/FinancialTab';
import RHTab from './components/tabs/RHTab';

export default function DashboardPageV2() {
  const [activeTab, setActiveTab] = useState('executive');
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const response = await apiClient.get('/dashboard/cientifico?days=30');
      setData(response.data?.data || response.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const tabs = [
    { id: 'executive', label: 'Visão Executiva', icon: Activity },
    { id: 'sales', label: 'Vendas & SFA', icon: Target },
    { id: 'inventory', label: 'Estoque Inteligente', icon: Package },
    { id: 'financial', label: 'Financeiro', icon: DollarSign },
    { id: 'rh', label: 'Equipe & RH', icon: Users },
  ];

  return (
    <div className="flex flex-col min-h-screen bg-slate-900 text-slate-100 p-4 md:p-6 lg:p-8 animate-in fade-in duration-500">
      
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight flex items-center gap-2">
            Intelligence Hub <span className="text-blue-500">•</span>
          </h1>
          <p className="text-slate-400 mt-1">Resumo estratégico dos últimos 30 dias</p>
        </div>
        <div className="flex gap-2">
           <button onClick={loadData} className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-sm font-medium rounded-lg transition-colors border border-slate-700">
             Atualizar Dados
           </button>
        </div>
      </div>

      {/* Tabs Navigation */}
      <div className="flex overflow-x-auto hide-scrollbar border-b border-slate-800 mb-6 pb-2 gap-6">
        {tabs.map(tab => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 pb-2 px-1 border-b-2 transition-all whitespace-nowrap ${
                isActive 
                  ? 'border-blue-500 text-blue-400 font-semibold' 
                  : 'border-transparent text-slate-500 hover:text-slate-300'
              }`}
            >
              <Icon size={18} />
              {tab.label}
            </button>
          )
        })}
      </div>

      {/* Content Area */}
      <div className="flex-1 relative">
        {loading ? (
          <div className="absolute inset-0 flex items-center justify-center">
             <div className="flex flex-col items-center gap-4">
               <Activity className="w-10 h-10 text-blue-500 animate-spin" />
               <p className="text-slate-400 font-medium">Processando inteligência de dados...</p>
             </div>
          </div>
        ) : !data ? (
          <div className="flex flex-col items-center justify-center p-12 bg-slate-800/50 rounded-2xl border border-slate-800">
             <AlertTriangle className="w-12 h-12 text-red-400 mb-4" />
             <h3 className="text-xl font-bold">Falha ao carregar dados</h3>
             <p className="text-slate-400 mt-2">Não foi possível obter as estatísticas do servidor.</p>
          </div>
        ) : (
          <div className="animate-in slide-in-from-bottom-4 duration-500">
            {activeTab === 'executive' && <ExecutiveTab data={data} />}
            {activeTab === 'sales' && <SalesSfaTab data={data} />}
            {activeTab === 'inventory' && <InventoryTab data={data} />}
            {activeTab === 'financial' && <FinancialTab data={data} />}
            {activeTab === 'rh' && <RHTab data={data} />}
          </div>
        )}
      </div>

    </div>
  );
}
