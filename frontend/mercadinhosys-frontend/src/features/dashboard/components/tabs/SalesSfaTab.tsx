import { Target, TrendingUp, Users, Award } from 'lucide-react';
import { formatCurrency } from '../../../../utils/formatters';

interface SalesSfaTabProps {
  data: any;
}

export default function SalesSfaTab({ data }: SalesSfaTabProps) {
  // Mock data for Vendedores if backend doesn't have it yet, simulating the requested feature
  const vendedores = [
    { nome: 'João Silva', meta: 50000, alcancado: 45000, tendencia: '+5%' },
    { nome: 'Maria Costa', meta: 40000, alcancado: 42000, tendencia: '+12%' },
    { nome: 'Carlos Souza', meta: 30000, alcancado: 25000, tendencia: '-2%' },
  ];

  return (
    <div className="space-y-8">
      {/* Resumo de Vendas */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-slate-800/60 rounded-2xl p-6 border border-slate-700/60">
          <div className="flex items-center gap-3 mb-4">
             <div className="p-2 bg-blue-500/20 rounded-lg"><Target className="text-blue-400" /></div>
             <h3 className="text-slate-300 font-bold">Meta Global do Mês</h3>
          </div>
          <div className="text-3xl font-black text-white">{formatCurrency(120000)}</div>
          <div className="mt-4 w-full bg-slate-700 rounded-full h-2">
            <div className="bg-blue-500 h-2 rounded-full" style={{ width: '85%' }}></div>
          </div>
          <p className="text-sm text-slate-400 mt-2">85% alcançado</p>
        </div>
        
        <div className="bg-slate-800/60 rounded-2xl p-6 border border-slate-700/60">
          <div className="flex items-center gap-3 mb-4">
             <div className="p-2 bg-emerald-500/20 rounded-lg"><TrendingUp className="text-emerald-400" /></div>
             <h3 className="text-slate-300 font-bold">Tendência (Forecast)</h3>
          </div>
          <div className="text-3xl font-black text-white">{formatCurrency(125000)}</div>
          <p className="text-sm text-emerald-400 mt-2 font-medium">Projeção de fechamento acima da meta</p>
        </div>

        <div className="bg-slate-800/60 rounded-2xl p-6 border border-slate-700/60">
          <div className="flex items-center gap-3 mb-4">
             <div className="p-2 bg-purple-500/20 rounded-lg"><Users className="text-purple-400" /></div>
             <h3 className="text-slate-300 font-bold">Clientes Atendidos</h3>
          </div>
          <div className="text-3xl font-black text-white">{data?.customer_metrics?.unique_customers || 342}</div>
          <p className="text-sm text-slate-400 mt-2 font-medium">Ticket médio: {formatCurrency(data?.summary?.avg_ticket?.value || 0)}</p>
        </div>
      </div>

      {/* Painel de Vendedores (SFA) */}
      <div className="bg-slate-800/60 rounded-3xl border border-slate-700/60 overflow-hidden">
        <div className="p-6 border-b border-slate-700/60 bg-slate-800/80 flex items-center justify-between">
           <div className="flex items-center gap-3">
             <div className="p-2.5 bg-amber-500/20 rounded-xl">
               <Award className="w-6 h-6 text-amber-400" />
             </div>
             <div>
               <h2 className="text-lg font-bold text-white">Performance de Vendedores (SFA)</h2>
               <p className="text-sm text-slate-400">Metas, alcançado e tendências da equipe comercial</p>
             </div>
           </div>
        </div>
        <div className="p-6">
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="text-slate-400 border-b border-slate-700">
                  <th className="pb-3 font-medium">Vendedor</th>
                  <th className="pb-3 font-medium">Meta</th>
                  <th className="pb-3 font-medium">Alcançado</th>
                  <th className="pb-3 font-medium">Progresso</th>
                  <th className="pb-3 font-medium text-right">Tendência</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700/50">
                {vendedores.map((v, idx) => {
                  const perc = (v.alcancado / v.meta) * 100;
                  return (
                    <tr key={idx}>
                      <td className="py-4 font-bold text-white">{v.nome}</td>
                      <td className="py-4 text-slate-300">{formatCurrency(v.meta)}</td>
                      <td className="py-4 text-white font-medium">{formatCurrency(v.alcancado)}</td>
                      <td className="py-4 w-1/3">
                        <div className="flex items-center gap-3">
                          <div className="w-full bg-slate-700 rounded-full h-2">
                            <div className={`h-2 rounded-full ${perc >= 100 ? 'bg-emerald-500' : perc >= 80 ? 'bg-blue-500' : 'bg-amber-500'}`} style={{ width: `${Math.min(perc, 100)}%` }}></div>
                          </div>
                          <span className="text-sm font-medium text-slate-300">{perc.toFixed(1)}%</span>
                        </div>
                      </td>
                      <td className="py-4 text-right">
                        <span className={`px-2 py-1 rounded-lg text-sm font-bold ${v.tendencia.startsWith('+') ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}`}>
                          {v.tendencia}
                        </span>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
