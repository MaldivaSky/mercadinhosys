import { TrendingUp, AlertTriangle, CheckCircle, Brain, Target, Shield, ArrowRight, PieChart as PieChartIcon, BarChart3, Info } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { formatCurrency } from '../../../../utils/formatters';

interface ExecutiveTabProps {
  data: any;
}

export default function ExecutiveTab({ data }: ExecutiveTabProps) {
  const navigate = useNavigate();

  // Torna a recomendação acionável: leva à listagem certa, já filtrada.
  const executarRecomendacao = (rec: any) => {
    const alvo = rec?.alvo;
    const ctx = `${rec?.mensagem || ''} ${rec?.cta || ''} ${rec?.tipo || ''}`.toLowerCase();
    if (alvo === 'clientes') { navigate('/customers?segmento=Risco'); return; }
    if (alvo === 'produtos') {
      if (ctx.includes('validade') || ctx.includes('vencer') || ctx.includes('vencid') || ctx.includes('promover'))
        navigate('/products?filtro=validade');
      else if (ctx.includes('ruptura') || ctx.includes('estoque') || ctx.includes('repor') || ctx.includes('mínimo') || ctx.includes('minimo'))
        navigate('/products?filtro=baixo');
      else
        navigate('/products');
      return;
    }
    navigate(alvo === 'clientes' ? '/customers' : '/products');
  };

  const faturamento = data?.financials?.revenue || data?.summary?.revenue?.value || 0;
  const lucroLiquido = data?.financials?.net_profit || data?.lucro_liquido || 0;
  const cogs = data?.financials?.cogs || (faturamento > 0 ? faturamento * 0.5 : 0); // fallback if cogs missing
  const despesas = data?.financials?.expenses || data?.total_despesas || (faturamento > 0 ? faturamento * 0.3 : 0);
  const margemLiquida = data?.financials?.net_margin || (faturamento > 0 ? (lucroLiquido / faturamento) * 100 : 0);
  const ticketMedio = data?.summary?.avg_ticket?.value || 0;
  
  const recomendacoes = data?.recomendacoes || [];

  const dreData = [
    { name: 'Lucro Líquido', value: Math.max(0, lucroLiquido), color: '#10b981', desc: 'Valor real que sobrou no caixa após pagar todos os custos e despesas' },
    { name: 'Custo da Mercadoria (CMV)', value: cogs, color: '#f59e0b', desc: 'O que foi pago aos fornecedores APENAS pelos produtos que foram vendidos' },
    { name: 'Despesas Operacionais', value: despesas, color: '#ef4444', desc: 'Custos do negócio (aluguel, salários, energia, impostos)' },
  ].filter(d => d.value > 0);

  const formatRecommendationType = (tipo: string) => {
    if (!tipo) return 'Outras Ações';
    
    const dict: Record<string, string> = {
      'vencimentocritico': 'Risco de Vencimento',
      'retencao': 'Retenção de Clientes',
      'estoque': 'Otimização de Estoque',
      'ruptura': 'Prevenção de Ruptura',
      'vendas': 'Impulso de Vendas',
      'inadimplencia': 'Risco de Inadimplência',
      'churn': 'Risco de Churn (Perda)',
    };
    
    const key = tipo.toLowerCase().replace(/[_ ]/g, '');
    if (dict[key]) return dict[key];
    
    // Fallback: primeira letra maiúscula e troca _ por espaço
    const formatted = tipo.replace(/_/g, ' ').toLowerCase();
    return formatted.charAt(0).toUpperCase() + formatted.slice(1);
  };

  const aiImpact = recomendacoes.reduce((acc: any, rec: any) => {
    const t = formatRecommendationType(rec.tipo);
    if (!acc[t]) acc[t] = 0;
    acc[t] += (rec.impacto_estimado || 0);
    return acc;
  }, {});

  const radarData = Object.keys(aiImpact).map(k => ({
    tipo: k.length > 22 ? k.substring(0, 22) + '...' : k,
    impacto: aiImpact[k]
  })).sort((a, b) => b.impacto - a.impacto);

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      {/* KPIs Principais */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        
        {/* Faturamento */}
        <div className="bg-slate-800/80 backdrop-blur-md rounded-2xl p-6 border border-slate-700/50 shadow-lg relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-32 h-32 bg-blue-500/10 rounded-full blur-3xl -mr-10 -mt-10 transition-transform group-hover:scale-150" />
          <div className="flex justify-between items-start mb-4">
            <h3 className="text-slate-400 font-medium text-sm tracking-wider uppercase flex items-center gap-1.5 group/tooltip relative">
              Faturamento
              <Info className="w-4 h-4 text-slate-500 cursor-help" />
              <div className="invisible group-hover/tooltip:visible absolute top-full left-0 mt-2 w-48 p-2 bg-slate-900 border border-slate-700 rounded-lg text-xs text-slate-300 z-10 shadow-xl normal-case tracking-normal">
                Soma total de todas as vendas brutas realizadas no período, antes de abater qualquer custo.
              </div>
            </h3>
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
            <h3 className="text-slate-400 font-medium text-sm tracking-wider uppercase flex items-center gap-1.5 group/tooltip relative">
              Lucro Líquido
              <Info className="w-4 h-4 text-slate-500 cursor-help" />
              <div className="invisible group-hover/tooltip:visible absolute top-full left-0 mt-2 w-48 p-2 bg-slate-900 border border-slate-700 rounded-lg text-xs text-slate-300 z-10 shadow-xl normal-case tracking-normal">
                O que sobrou limpo no caixa após pagar os fornecedores da mercadoria vendida e as despesas da loja.
              </div>
            </h3>
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
            <h3 className="text-slate-400 font-medium text-sm tracking-wider uppercase flex items-center gap-1.5 group/tooltip relative">
              Ticket Médio
              <Info className="w-4 h-4 text-slate-500 cursor-help" />
              <div className="invisible group-hover/tooltip:visible absolute top-full left-0 mt-2 w-48 p-2 bg-slate-900 border border-slate-700 rounded-lg text-xs text-slate-300 z-10 shadow-xl normal-case tracking-normal">
                Valor médio que cada cliente gasta em uma única compra. Um ticket maior significa compras mais volumosas.
              </div>
            </h3>
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
            <h3 className="text-slate-400 font-medium text-sm tracking-wider uppercase flex items-center gap-1.5 group/tooltip relative">
              A Receber
              <Info className="w-4 h-4 text-slate-500 cursor-help" />
              <div className="invisible group-hover/tooltip:visible absolute top-full right-0 mt-2 w-48 p-2 bg-slate-900 border border-slate-700 rounded-lg text-xs text-slate-300 z-10 shadow-xl normal-case tracking-normal">
                Soma de todas as vendas a prazo (cartão pendente, carnê) incluindo vendas fiadas. Dinheiro na rua.
              </div>
            </h3>
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

      {/* Gráficos Estratégicos Executivos */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Gráfico 1: DRE Visual */}
        <div className="bg-slate-800/80 backdrop-blur-xl rounded-3xl p-6 border border-slate-700/60 shadow-xl">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 bg-indigo-500/10 rounded-lg text-indigo-400">
              <PieChartIcon className="w-5 h-5" />
            </div>
            <h3 className="text-slate-300 font-bold">Composição Financeira (DRE)</h3>
          </div>
          <div className="h-[280px] w-full flex items-center justify-center">
            {dreData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Tooltip 
                    content={({ active, payload }: any) => {
                      if (active && payload && payload.length) {
                        const d = payload[0].payload;
                        return (
                          <div className="bg-slate-800 border border-slate-700 p-4 rounded-xl shadow-2xl max-w-[220px]">
                            <p className="font-bold text-slate-200 mb-1">{d.name}</p>
                            <p className="text-xl font-black" style={{ color: d.color }}>{formatCurrency(d.value)}</p>
                            <p className="text-xs text-slate-400 mt-2 leading-snug font-medium">{d.desc}</p>
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                  <Pie
                    data={dreData}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    innerRadius="50%"
                    outerRadius="75%"
                    paddingAngle={5}
                  >
                    {dreData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} stroke="rgba(0,0,0,0)" />
                    ))}
                  </Pie>
                  <Legend
                    layout="horizontal"
                    verticalAlign="bottom"
                    align="center"
                    wrapperStyle={{ fontSize: '12px', color: '#cbd5e1' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="text-slate-500 font-medium">Sem dados financeiros suficientes no período.</div>
            )}
          </div>
        </div>

        {/* Gráfico 2: Radar de IA (Impacto) */}
        <div className="bg-slate-800/80 backdrop-blur-xl rounded-3xl p-6 border border-slate-700/60 shadow-xl">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 bg-blue-500/10 rounded-lg text-blue-400">
              <BarChart3 className="w-5 h-5" />
            </div>
            <h3 className="text-slate-300 font-bold">Impacto Financeiro da IA por Ação</h3>
          </div>
          <div className="h-[280px] w-full">
            {radarData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={radarData} layout="vertical" margin={{ top: 0, right: 30, left: 10, bottom: 0 }}>
                  <XAxis type="number" hide />
                  <YAxis type="category" dataKey="tipo" stroke="#cbd5e1" fontSize={11} tickLine={false} axisLine={false} width={140} />
                  <Tooltip 
                    cursor={{ fill: 'rgba(255, 255, 255, 0.05)' }}
                    contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', borderRadius: '0.75rem', color: '#f1f5f9' }}
                    itemStyle={{ fontWeight: 'bold', color: '#f8fafc' }}
                    labelStyle={{ color: '#94a3b8', fontWeight: 'bold', marginBottom: '4px' }}
                    formatter={(value: number) => [formatCurrency(value), 'Impacto Potencial']}
                  />
                  <Bar dataKey="impacto" radius={[0, 4, 4, 0]} maxBarSize={24}>
                    {radarData.map((_, index) => (
                      <Cell key={`cell-${index}`} fill="#3b82f6" />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-full text-slate-500 font-medium">Nenhuma oportunidade com impacto mapeada.</div>
            )}
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
                   <button
                     onClick={() => executarRecomendacao(rec)}
                     className="whitespace-nowrap px-5 py-2.5 bg-white/10 hover:bg-white/20 text-white font-medium rounded-xl transition-colors flex items-center gap-2 cursor-pointer"
                   >
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
