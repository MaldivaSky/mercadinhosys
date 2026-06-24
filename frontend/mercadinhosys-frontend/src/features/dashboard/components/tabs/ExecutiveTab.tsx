import { TrendingUp, AlertTriangle, CheckCircle, Brain, Target, Shield, ArrowRight } from 'lucide-react';
import { formatCurrency } from '../../../../utils/formatters';

interface ExecutiveTabProps {
  data: any;
}

export default function ExecutiveTab({ data }: ExecutiveTabProps) {
  const faturamento = data?.financials?.revenue || data?.summary?.revenue?.value || 0;
  const lucroLiquido = data?.financials?.net_profit || data?.lucro_liquido || 0;
  const margemLiquida = data?.financials?.net_margin || 0;
  const ticketMedio = data?.summary?.avg_ticket?.value || 0;
  
  const recomendacoes = data?.recomendacoes || [];

  return (
    <div className="space-y-8">
      {/* KPIs Principais */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        
        {/* Faturamento */}
        <div className="bg-slate-800/80 backdrop-blur-md rounded-2xl p-6 border border-slate-700/50 shadow-lg relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-32 h-32 bg-blue-500/10 rounded-full blur-3xl -mr-10 -mt-10 transition-transform group-hover:scale-150" />
          <div className="flex justify-between items-start mb-4">
            <h3 className="text-slate-400 font-medium text-sm tracking-wider uppercase">Faturamento</h3>
            <div className="p-2 bg-blue-500/20 rounded-lg">
              <TrendingUp className="w-5 h-5 text-blue-400" />
            </div>
          </div>
          <div className="text-3xl font-black text-white mb-2">{formatCurrency(faturamento)}</div>
          <div className="flex items-center gap-2 text-sm">
             <span className="text-emerald-400 flex items-center bg-emerald-400/10 px-2 py-0.5 rounded-full font-medium">
                <TrendingUp size={14} className="mr-1" />
                +12% vs mês ant.
             </span>
          </div>
        </div>

        {/* Lucro Líquido */}
        <div className="bg-slate-800/80 backdrop-blur-md rounded-2xl p-6 border border-slate-700/50 shadow-lg relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/10 rounded-full blur-3xl -mr-10 -mt-10 transition-transform group-hover:scale-150" />
          <div className="flex justify-between items-start mb-4">
            <h3 className="text-slate-400 font-medium text-sm tracking-wider uppercase">Lucro Líquido</h3>
            <div className="p-2 bg-emerald-500/20 rounded-lg">
              <Target className="w-5 h-5 text-emerald-400" />
            </div>
          </div>
          <div className="text-3xl font-black text-white mb-2">{formatCurrency(lucroLiquido)}</div>
          <div className="flex items-center gap-2 text-sm">
             <span className="text-slate-400">Margem Liquida: </span>
             <span className={`font-bold ${margemLiquida >= 10 ? 'text-emerald-400' : margemLiquida > 0 ? 'text-amber-400' : 'text-red-400'}`}>
               {margemLiquida.toFixed(1)}%
             </span>
          </div>
        </div>

        {/* Ticket Médio */}
        <div className="bg-slate-800/80 backdrop-blur-md rounded-2xl p-6 border border-slate-700/50 shadow-lg relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-32 h-32 bg-purple-500/10 rounded-full blur-3xl -mr-10 -mt-10 transition-transform group-hover:scale-150" />
          <div className="flex justify-between items-start mb-4">
            <h3 className="text-slate-400 font-medium text-sm tracking-wider uppercase">Ticket Médio</h3>
            <div className="p-2 bg-purple-500/20 rounded-lg">
              <Shield className="w-5 h-5 text-purple-400" />
            </div>
          </div>
          <div className="text-3xl font-black text-white mb-2">{formatCurrency(ticketMedio)}</div>
          <div className="flex items-center gap-2 text-sm">
             <span className="text-slate-400">Gasto médio por cliente</span>
          </div>
        </div>
        
        {/* Caixa e Fiado */}
        <div className="bg-slate-800/80 backdrop-blur-md rounded-2xl p-6 border border-slate-700/50 shadow-lg relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-32 h-32 bg-orange-500/10 rounded-full blur-3xl -mr-10 -mt-10 transition-transform group-hover:scale-150" />
          <div className="flex justify-between items-start mb-4">
            <h3 className="text-slate-400 font-medium text-sm tracking-wider uppercase">Contas a Receber</h3>
            <div className="p-2 bg-orange-500/20 rounded-lg">
              <AlertTriangle className="w-5 h-5 text-orange-400" />
            </div>
          </div>
          <div className="text-3xl font-black text-white mb-2">{formatCurrency(data?.receivables?.total_recebivel || 0)}</div>
          <div className="flex items-center gap-2 text-sm">
             <span className="text-orange-400 flex items-center bg-orange-400/10 px-2 py-0.5 rounded-full font-medium">
                Fiado: {formatCurrency(data?.fiado?.total_aberto || 0)}
             </span>
          </div>
        </div>

      </div>

      {/* AI Feed / Briefing Executivo */}
      <div className="bg-slate-800/60 rounded-3xl border border-slate-700/60 overflow-hidden">
        <div className="p-6 border-b border-slate-700/60 bg-slate-800/80 flex items-center justify-between">
           <div className="flex items-center gap-3">
             <div className="p-2.5 bg-blue-500/20 rounded-xl">
               <Brain className="w-6 h-6 text-blue-400" />
             </div>
             <div>
               <h2 className="text-lg font-bold text-white">Briefing de Inteligência</h2>
               <p className="text-sm text-slate-400">O que você precisa saber hoje sobre seu negócio</p>
             </div>
           </div>
        </div>
        <div className="p-6 space-y-4">
           {recomendacoes && recomendacoes.length > 0 ? (
             recomendacoes.map((rec: any, idx: number) => (
               <div key={idx} className={`p-5 rounded-2xl border flex flex-col md:flex-row items-start md:items-center justify-between gap-4 transition-colors ${
                 rec.prioridade === 1 ? 'bg-red-500/10 border-red-500/20 hover:bg-red-500/20' :
                 rec.prioridade === 2 ? 'bg-amber-500/10 border-amber-500/20 hover:bg-amber-500/20' :
                 'bg-blue-500/10 border-blue-500/20 hover:bg-blue-500/20'
               }`}>
                 <div className="flex items-start gap-4">
                   <div className="text-2xl mt-1">{rec.icone || '💡'}</div>
                   <div>
                     <h4 className={`font-bold text-lg mb-1 ${
                       rec.prioridade === 1 ? 'text-red-400' :
                       rec.prioridade === 2 ? 'text-amber-400' :
                       'text-blue-400'
                     }`}>
                       {rec.tipo.replace(/_/g, ' ').toUpperCase()}
                     </h4>
                     <p className="text-slate-300 leading-relaxed text-sm">{rec.mensagem}</p>
                     {rec.impacto_estimado > 0 && (
                       <p className="mt-2 text-sm font-semibold text-emerald-400">
                         Impacto Estimado: {formatCurrency(rec.impacto_estimado)}
                       </p>
                     )}
                   </div>
                 </div>
                 {rec.cta && (
                   <button className="whitespace-nowrap px-5 py-2.5 bg-white/10 hover:bg-white/20 text-white font-medium rounded-xl transition-colors flex items-center gap-2">
                     {rec.cta} <ArrowRight size={16} />
                   </button>
                 )}
               </div>
             ))
           ) : (
             <div className="text-center py-12">
               <CheckCircle className="w-16 h-16 text-emerald-500/50 mx-auto mb-4" />
               <h3 className="text-xl font-bold text-slate-300">Tudo sob controle</h3>
               <p className="text-slate-500 mt-2">Nenhum risco crítico ou anomalia detectada hoje.</p>
             </div>
           )}
        </div>
      </div>

    </div>
  );
}
