import { useState } from 'react';
import { Target, TrendingUp, Users, Award, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { formatCurrency } from '../../../../utils/formatters';

interface SalesSfaTabProps {
  data: any;
}

export default function SalesSfaTab({ data }: SalesSfaTabProps) {
  // Extrai os Vendedores Reais do Backend (DataLayer / Enterprise SEED)
  let vendedores = data?.sfa?.vendedores || [];

  const [searchTerm, setSearchTerm] = useState('');
  const [sortConfig, setSortConfig] = useState<{key: string, direction: 'asc' | 'desc'} | null>(null);

  if (searchTerm) {
    vendedores = vendedores.filter((v: any) => 
      v.nome?.toLowerCase().includes(searchTerm.toLowerCase()) || 
      v.id?.toString().includes(searchTerm)
    );
  }

  if (sortConfig) {
    vendedores = [...vendedores].sort((a: any, b: any) => {
      let valA = a[sortConfig.key];
      let valB = b[sortConfig.key];
      
      if (sortConfig.key === 'progresso') {
        valA = a.meta > 0 ? (a.alcancado / a.meta) * 100 : 0;
        valB = b.meta > 0 ? (b.alcancado / b.meta) * 100 : 0;
      }

      if (valA < valB) return sortConfig.direction === 'asc' ? -1 : 1;
      if (valA > valB) return sortConfig.direction === 'asc' ? 1 : -1;
      return 0;
    });
  }

  const handleSort = (key: string) => {
    let direction: 'asc' | 'desc' = 'asc';
    if (sortConfig && sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  };

  // Clientes únicos: o dashboard científico não traz customer_metrics; derivamos
  // da soma dos segmentos RFM (ex.: {Campeão:4, Fiel:5, ...}). Antes ficava zerado.
  const rfmSegments = data?.rfm?.segments || {};
  const clientesUnicos = data?.customer_metrics?.unique_customers
    ?? Object.values(rfmSegments).reduce((acc: number, s: any) =>
         acc + (typeof s === 'number' ? s : Array.isArray(s) ? s.length : (s?.count ?? s?.total ?? 0)), 0);

  // Cálculos Dinâmicos para os KPIs Globais do SFA
  const globalMeta = vendedores.reduce((acc: number, v: any) => acc + (v.meta || 0), 0);
  const globalAlcancado = vendedores.reduce((acc: number, v: any) => acc + (v.alcancado || 0), 0);
  const globalPerc = globalMeta > 0 ? (globalAlcancado / globalMeta) * 100 : 0;
  
  // Média de tendência global
  const avgTendencia = vendedores.length > 0 
    ? vendedores.reduce((acc: number, v: any) => acc + (v.tendencia || 0), 0) / vendedores.length 
    : 0;

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      
      {/* Resumo de Vendas SFA */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* Card: Meta Global */}
        <div className="bg-slate-800/80 backdrop-blur-xl rounded-3xl p-6 border border-slate-700/60 shadow-xl relative overflow-hidden group hover:border-blue-500/30 transition-colors">
          <div className="absolute top-0 right-0 w-32 h-32 bg-blue-500/10 rounded-full blur-3xl group-hover:bg-blue-500/20 transition-all"></div>
          <div className="flex items-center gap-3 mb-6">
             <div className="p-3 bg-blue-500/10 rounded-xl border border-blue-500/20 text-blue-400">
               <Target className="w-5 h-5" />
             </div>
             <h3 className="text-slate-300 font-bold tracking-wide">Meta Global do Mês</h3>
          </div>
          <div className="text-4xl font-black text-white tracking-tight mb-2">
            {formatCurrency(globalAlcancado)}
          </div>
          <p className="text-sm text-slate-400 font-medium mb-5">
            de {formatCurrency(globalMeta)}
          </p>
          <div className="w-full bg-slate-900 rounded-full h-2 mb-2 overflow-hidden border border-slate-800">
            <div 
              className={`h-full rounded-full transition-all duration-1000 ${globalPerc >= 100 ? 'bg-gradient-to-r from-emerald-500 to-emerald-400' : globalPerc >= 80 ? 'bg-gradient-to-r from-blue-600 to-blue-400' : 'bg-gradient-to-r from-amber-500 to-amber-400'}`} 
              style={{ width: `${Math.min(globalPerc, 100)}%` }}
            ></div>
          </div>
          <div className="flex justify-between items-center text-xs font-bold">
            <span className={globalPerc >= 100 ? 'text-emerald-400' : 'text-blue-400'}>{globalPerc.toFixed(1)}% alcançado</span>
            {globalPerc >= 100 && <span className="flex items-center gap-1 text-emerald-400"><CheckCircle2 className="w-3 h-3"/> Meta Batida</span>}
          </div>
        </div>
        
        {/* Card: Forecast SFA */}
        <div className="bg-slate-800/80 backdrop-blur-xl rounded-3xl p-6 border border-slate-700/60 shadow-xl relative overflow-hidden group hover:border-emerald-500/30 transition-colors">
          <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/10 rounded-full blur-3xl group-hover:bg-emerald-500/20 transition-all"></div>
          <div className="flex items-center gap-3 mb-6">
             <div className="p-3 bg-emerald-500/10 rounded-xl border border-emerald-500/20 text-emerald-400">
               <TrendingUp className="w-5 h-5" />
             </div>
             <h3 className="text-slate-300 font-bold tracking-wide">Forecast da Equipe</h3>
          </div>
          <div className="flex items-baseline gap-2 mb-2">
            <div className={`text-4xl font-black tracking-tight ${avgTendencia >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
              {avgTendencia > 0 ? '+' : ''}{avgTendencia.toFixed(1)}%
            </div>
          </div>
          <p className="text-sm text-slate-400 font-medium">
            Tendência de crescimento baseada no período anterior
          </p>
        </div>

        {/* Card: Clientes Atendidos */}
        <div className="bg-slate-800/80 backdrop-blur-xl rounded-3xl p-6 border border-slate-700/60 shadow-xl relative overflow-hidden group hover:border-purple-500/30 transition-colors">
          <div className="absolute top-0 right-0 w-32 h-32 bg-purple-500/10 rounded-full blur-3xl group-hover:bg-purple-500/20 transition-all"></div>
          <div className="flex items-center gap-3 mb-6">
             <div className="p-3 bg-purple-500/10 rounded-xl border border-purple-500/20 text-purple-400">
               <Users className="w-5 h-5" />
             </div>
             <h3 className="text-slate-300 font-bold tracking-wide">Clientes Atendidos</h3>
          </div>
          <div className="text-4xl font-black text-white tracking-tight mb-2">
            {clientesUnicos || 0}
          </div>
          <p className="text-sm text-slate-400 font-medium">
            Ticket médio geral: <span className="text-purple-400 font-bold">{formatCurrency(data?.summary?.avg_ticket?.value || 0)}</span>
          </p>
        </div>
      </div>

      {/* Painel de Vendedores (SFA) */}
      <div className="bg-slate-800/80 backdrop-blur-xl rounded-3xl border border-slate-700/60 overflow-hidden shadow-2xl">
        <div className="p-6 border-b border-slate-700/60 bg-slate-800/90 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
           <div className="flex items-center gap-4">
             <div className="p-3 bg-gradient-to-br from-amber-400 to-amber-600 rounded-2xl shadow-lg shadow-amber-500/20">
               <Award className="w-6 h-6 text-white" />
             </div>
             <div>
               <h2 className="text-xl font-black text-white tracking-tight">Analytics de Vendedores (SFA)</h2>
               <p className="text-sm text-slate-400 font-medium mt-1">Metas projetadas e performance individual em tempo real</p>
             </div>
           </div>
           
           <div className="flex flex-col sm:flex-row items-center gap-4">
             {/* Alerta Inteligente */}
             {vendedores.some((v:any) => v.tendencia <= -15) && (
               <div className="flex items-center gap-2 px-4 py-2 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm font-bold animate-pulse">
                  <AlertTriangle className="w-4 h-4" />
                  Atenção: Vendedores com queda severa
               </div>
             )}
             <input 
               type="text" 
               placeholder="Buscar vendedor..." 
               value={searchTerm}
               onChange={(e) => setSearchTerm(e.target.value)}
               className="bg-slate-900/50 border border-slate-700/50 text-white text-sm rounded-xl px-4 py-2 w-full sm:w-64 focus:outline-none focus:border-blue-500/50 placeholder-slate-500"
             />
           </div>
        </div>
        
        <div className="p-0 overflow-x-auto">
          {vendedores.length === 0 ? (
            <div className="p-12 text-center flex flex-col items-center">
              <Users className="w-12 h-12 text-slate-600 mb-4" />
              <h3 className="text-lg font-bold text-slate-300">Nenhum vendedor encontrado</h3>
              <p className="text-slate-500 mt-2">O motor SFA não detectou vendas atreladas a vendedores neste período.</p>
            </div>
          ) : (
            <table className="w-full text-left whitespace-nowrap">
              <thead>
                <tr className="text-slate-400 border-b border-slate-700/60 bg-slate-900/40 text-xs uppercase tracking-wider font-bold">
                  <th className="px-6 py-4 cursor-pointer hover:text-white transition-colors select-none" onClick={() => handleSort('nome')}>Vendedor {sortConfig?.key === 'nome' ? (sortConfig.direction === 'asc' ? '↑' : '↓') : ''}</th>
                  <th className="px-6 py-4 cursor-pointer hover:text-white transition-colors select-none" onClick={() => handleSort('vendas_count')}>Vendas {sortConfig?.key === 'vendas_count' ? (sortConfig.direction === 'asc' ? '↑' : '↓') : ''}</th>
                  <th className="px-6 py-4 cursor-pointer hover:text-white transition-colors select-none" onClick={() => handleSort('meta')}>Meta Projetada {sortConfig?.key === 'meta' ? (sortConfig.direction === 'asc' ? '↑' : '↓') : ''}</th>
                  <th className="px-6 py-4 cursor-pointer hover:text-white transition-colors select-none" onClick={() => handleSort('alcancado')}>Faturamento {sortConfig?.key === 'alcancado' ? (sortConfig.direction === 'asc' ? '↑' : '↓') : ''}</th>
                  <th className="px-6 py-4 w-1/3 cursor-pointer hover:text-white transition-colors select-none" onClick={() => handleSort('progresso')}>Progresso {sortConfig?.key === 'progresso' ? (sortConfig.direction === 'asc' ? '↑' : '↓') : ''}</th>
                  <th className="px-6 py-4 text-right cursor-pointer hover:text-white transition-colors select-none" onClick={() => handleSort('tendencia')}>Tendência {sortConfig?.key === 'tendencia' ? (sortConfig.direction === 'asc' ? '↑' : '↓') : ''}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700/50">
                {vendedores.map((v: any, idx: number) => {
                  const perc = v.meta > 0 ? (v.alcancado / v.meta) * 100 : 0;
                  const isTop = idx === 0 && v.alcancado > 0;
                  
                  return (
                    <tr key={v.id || idx} className="hover:bg-slate-700/20 transition-colors group">
                      <td className="px-6 py-5">
                        <div className="flex items-center gap-3">
                          <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-lg shadow-inner ${isTop ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' : 'bg-slate-700 text-slate-300'}`}>
                            {v.nome.charAt(0)}
                          </div>
                          <div>
                            <div className="font-bold text-white flex items-center gap-2">
                              {v.nome}
                              {isTop && <span className="text-[10px] uppercase bg-amber-500/20 text-amber-400 px-2 py-0.5 rounded-full border border-amber-500/20">Top 1</span>}
                            </div>
                            <div className="text-xs text-slate-500">ID: {v.id}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-5">
                        <span className="inline-flex items-center justify-center px-3 py-1 rounded-lg bg-slate-800 border border-slate-700 text-slate-300 font-bold text-sm shadow-inner">
                          {v.vendas_count || 0}
                        </span>
                      </td>
                      <td className="px-6 py-5 text-slate-400 font-medium">{formatCurrency(v.meta)}</td>
                      <td className="px-6 py-5 text-white font-black text-lg">{formatCurrency(v.alcancado)}</td>
                      <td className="px-6 py-5">
                        <div className="flex items-center gap-3">
                          <div className="w-full bg-slate-900 rounded-full h-2.5 overflow-hidden border border-slate-700">
                            <div 
                              className={`h-full rounded-full transition-all duration-1000 ${perc >= 100 ? 'bg-gradient-to-r from-emerald-500 to-emerald-400' : perc >= 80 ? 'bg-gradient-to-r from-blue-600 to-blue-400' : 'bg-gradient-to-r from-amber-500 to-amber-400'}`} 
                              style={{ width: `${Math.min(perc, 100)}%` }}
                            ></div>
                          </div>
                          <span className={`text-sm font-black min-w-[3rem] text-right ${perc >= 100 ? 'text-emerald-400' : 'text-slate-300'}`}>
                            {perc.toFixed(1)}%
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-5 text-right">
                        <span className={`inline-flex items-center px-3 py-1.5 rounded-xl text-sm font-black shadow-sm ${v.tendencia >= 0 ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-red-500/10 text-red-400 border border-red-500/20'}`}>
                          {v.tendencia > 0 ? '+' : ''}{v.tendencia.toFixed(1)}%
                        </span>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
