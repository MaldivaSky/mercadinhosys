import { useState, useEffect } from 'react';
import {
  Users, TrendingUp, DollarSign, AlertCircle,
  Download, ChevronDown, ChevronUp, Printer, BarChart
} from 'lucide-react';
import {
  BarChart as RechartsBarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';
import { apiClient } from '../../../api/apiClient';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
import HoleriteModal from './HoleriteModal';

interface RHMetrics {
  total_beneficios_mensal: number;
  total_salarios: number;
  custo_folha_estimado: number;
  funcionarios_ativos: number;
  total_entradas_periodo: number;
  total_atrasos_qtd: number;
  taxa_pontualidade: number;
  total_minutos_atraso: number;
  minutos_extras_estimados: number;
  custo_extras_estimado: number;
  turnover_rate?: number;
  admissoes_periodo?: number;
  demissoes_periodo?: number;
  evolution_turnover?: Array<{ mes: string; admissoes: number; demissoes: number; ausencias?: number; atrasos?: number; horas_extras?: number }>;
  benefits_breakdown?: Array<{ name: string; value: number }>;
  top_overtime_employees?: Array<{ nome: string; horas: number; custo_estimado: number }>;
  atrasos_por_funcionario_mes?: Array<{ funcionario_id: number; nome: string; cargo: string; atrasos_qtd: number; minutos_atraso: number }>;
  horas_extras_por_funcionario_mes?: Array<{ funcionario_id: number; nome: string; cargo: string; minutos_extras: number; custo_extras: number }>;
  faltas_por_funcionario_mes?: Array<{ funcionario_id: number; nome: string; cargo: string; faltas: number; dias_uteis: number; dias_presenca: number }>;
  espelho_pagamento_mes?: Array<{
    funcionario_id: number; nome: string; cargo: string; salario_base: number;
    beneficios: number; horas_extras_horas: number; custo_horas_extras: number;
    atrasos_minutos: number; faltas: number; total_estimado: number
  }>;
  resumo_mes?: { inicio: string | null; fim: string | null; dias_uteis: number; total_atrasos_minutos: number; total_atrasos_qtd: number; total_extras_minutos: number; total_faltas: number };
}

export default function RHDashboard() {
  const [rhData, setRhData] = useState<RHMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    'metricas': true,
    'turnover': true,
    'beneficios': true,
    'folha': true,
    'atrasos': true
  });
  const [filtroAtrasados, setFiltroAtrasados] = useState(false);
  const [periodoDias, setPeriodoDias] = useState(30);

  // Holerite Modal State
  const [holeriteModalOpen, setHoleriteModalOpen] = useState(false);
  const [selectedFuncionarioHolerite, setSelectedFuncionarioHolerite] = useState<any>(null);

  useEffect(() => {
    loadRHData();
  }, [periodoDias]);

  const loadRHData = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiClient.get(`/rh/dashboard?days=${periodoDias}`);
      const rhMetrics = response.data?.data;

      if (rhMetrics) {
        setRhData(rhMetrics);
      } else {
        setError('Dados de RH não disponíveis');
      }
    } catch (err: any) {
      console.error('Erro ao carregar dados de RH:', err);
      setError(err.message || 'Erro ao carregar dados');
    } finally {
      setLoading(false);
    }
  };

  const toggleSection = (section: string) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const openHolerite = (funcionario: any) => {
    setSelectedFuncionarioHolerite(funcionario);
    setHoleriteModalOpen(true);
  };

  const exportarFolhaPagamentoPDF = () => {
    if (!rhData?.espelho_pagamento_mes) return;

    const doc = new jsPDF();

    doc.setFillColor(99, 102, 241);
    doc.rect(0, 0, 210, 40, 'F');
    doc.setTextColor(255, 255, 255);
    doc.setFontSize(20);
    doc.text('Folha de Pagamento', 105, 20, { align: 'center' });
    doc.setFontSize(10);
    doc.text(`Período: ${rhData.resumo_mes?.inicio || '-'} a ${rhData.resumo_mes?.fim || '-'}`, 105, 30, { align: 'center' });

    const headers = [['Funcionário', 'Cargo', 'Salário Base', 'Benefícios', 'H. Extras', 'Faltas', 'Atrasos', 'Total']];
    const data = rhData.espelho_pagamento_mes.map(f => [
      f.nome,
      f.cargo,
      `R$ ${f.salario_base.toFixed(2)}`,
      `R$ ${f.beneficios.toFixed(2)}`,
      `${f.horas_extras_horas.toFixed(1)}h / R$ ${f.custo_horas_extras.toFixed(2)}`,
      f.faltas.toString(),
      `${f.atrasos_minutos}m`,
      `R$ ${f.total_estimado.toFixed(2)}`
    ]);

    autoTable(doc, {
      head: headers,
      body: data,
      startY: 50,
      theme: 'grid',
      styles: { fontSize: 8, cellPadding: 2 },
      headStyles: { fillColor: [99, 102, 241], textColor: [255, 255, 255] },
      alternateRowStyles: { fillColor: [245, 245, 245] }
    });

    const finalY = (doc as any).lastAutoTable.finalY + 10;
    doc.setFontSize(12);
    doc.setTextColor(0, 0, 0);
    doc.text(`Total Folha: R$ ${rhData.custo_folha_estimado.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`, 14, finalY);

    doc.save(`folha-pagamento-${new Date().toISOString().split('T')[0]}.pdf`);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 bg-gray-50 dark:bg-gray-900 rounded-xl">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-400 font-bold">Carregando dados de RH...</p>
        </div>
      </div>
    );
  }

  if (error || !rhData) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6">
        <div className="flex items-center gap-3 text-red-700 dark:text-red-400">
          <AlertCircle className="w-6 h-6" />
          <div>
            <h3 className="font-bold">Erro ao carregar dados</h3>
            <p className="text-sm">{error || 'Dados não disponíveis'}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-black text-gray-950 dark:text-white leading-none mb-1 uppercase tracking-tight">Dashboard de RH</h2>
          <p className="text-sm text-gray-900 dark:text-gray-200 font-black">Análise completa de recursos humanos</p>
        </div>
        <select
          value={periodoDias}
          onChange={(e) => setPeriodoDias(Number(e.target.value))}
          className="px-4 py-2 border-2 border-gray-400 text-gray-900 dark:text-white font-bold bg-white dark:bg-gray-800"
        >
          <option value={7}>Últimos 7 dias</option>
          <option value={15}>Últimos 15 dias</option>
          <option value={30}>Últimos 30 dias</option>
          <option value={60}>Últimos 60 dias</option>
          <option value={90}>Últimos 90 dias</option>
        </select>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-gradient-to-br from-blue-50 to-blue-100 dark:from-slate-800 dark:to-slate-900 p-6 rounded-xl shadow-lg border border-blue-200 dark:border-slate-700">
          <div className="flex items-center justify-between mb-2">
            <div className="p-3 bg-blue-600 rounded-lg shadow-md shadow-blue-500/20 text-white">
              <Users className="w-6 h-6" />
            </div>
          </div>
          <p className="text-xs text-gray-900 dark:text-gray-300 font-black uppercase mt-1">Funcionários Ativos</p>
          <h3 className="text-4xl font-black text-blue-900 dark:text-white font-black">{rhData.funcionarios_ativos}</h3>
        </div>

        <div className="bg-gradient-to-br from-green-50 to-green-100 dark:from-slate-800 dark:to-slate-900 p-6 rounded-xl shadow-lg border border-green-200 dark:border-slate-700">
          <div className="flex items-center justify-between mb-2">
            <div className="p-3 bg-emerald-600 rounded-lg shadow-md shadow-emerald-500/20 text-white">
              <DollarSign className="w-6 h-6" />
            </div>
          </div>
          <p className="text-xs text-emerald-800 dark:text-emerald-400 font-black uppercase tracking-widest">Folha de Pagamento</p>
          <h3 className="text-3xl font-black text-emerald-900 dark:text-white font-black">
            R$ {rhData.custo_folha_estimado.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
          </h3>
          <p className="text-[10px] text-gray-900 dark:text-gray-300 font-bold uppercase mt-1">Estimado mensal</p>
        </div>

        <div
          className="bg-gradient-to-br from-red-50 to-red-100 dark:from-slate-800 dark:to-slate-900 p-6 rounded-xl shadow-lg border border-red-200 dark:border-slate-700 cursor-pointer hover:shadow-xl transition-all"
          onClick={() => setFiltroAtrasados(!filtroAtrasados)}
        >
          <div className="flex items-center justify-between mb-2">
            <div className="p-3 bg-rose-600 rounded-lg shadow-md shadow-rose-500/20 text-white">
              <AlertCircle className="w-6 h-6" />
            </div>
            <span className="text-[10px] font-black text-rose-800 bg-rose-200 px-3 py-1 rounded-full uppercase tracking-tighter shadow-sm">
              Filtrar Lista
            </span>
          </div>
          <p className="text-xs text-rose-800 dark:text-rose-400 font-black uppercase tracking-widest">Total de Atrasos</p>
          <h3 className="text-4xl font-black text-rose-900 dark:text-white font-black">{rhData.total_atrasos_qtd}</h3>
          <p className="text-[10px] text-rose-700 dark:text-rose-300 font-bold uppercase tracking-tighter mt-1">{rhData.total_minutos_atraso} min acumulados</p>
        </div>

        <div className="bg-gradient-to-br from-purple-50 to-purple-100 dark:from-slate-800 dark:to-slate-900 p-6 rounded-xl shadow-lg border border-purple-200 dark:border-slate-700">
          <div className="flex items-center justify-between mb-2">
            <div className="p-3 bg-indigo-600 rounded-lg shadow-md shadow-indigo-500/20 text-white">
              <TrendingUp className="w-6 h-6" />
            </div>
          </div>
          <p className="text-xs text-indigo-800 dark:text-indigo-400 font-black uppercase tracking-widest">Taxa de Pontualidade</p>
          <h3 className="text-4xl font-black text-indigo-900 dark:text-white font-black">{rhData.taxa_pontualidade}%</h3>
          <p className="text-[10px] text-indigo-700 dark:text-indigo-300 font-bold uppercase tracking-tighter mt-1">Eficiência Operacional</p>
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6 border border-gray-100 dark:border-gray-700">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-bold text-gray-900 flex items-center gap-2">
            <BarChart className="w-5 h-5 text-gray-500" />
            Histórico de Admissões, Demissões, Ausências e Atrasos
          </h3>
          <button
            onClick={() => toggleSection('turnover')}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            {expandedSections['turnover'] ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
          </button>
        </div>

        {expandedSections['turnover'] && (
          <div className="h-[400px]">
            {rhData.evolution_turnover && rhData.evolution_turnover.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <RechartsBarChart data={rhData.evolution_turnover}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="mes" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip
                    contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
                  />
                  <Bar dataKey="admissoes" name="Admissões" fill="#10B981" />
                  <Bar dataKey="demissoes" name="Demissões" fill="#EF4444" />
                  <Bar dataKey="ausencias" name="Ausências" fill="#F59E0B" />
                  <Bar dataKey="atrasos" name="Atrasos" fill="#8B5CF6" />
                </RechartsBarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-gray-500">
                <TrendingUp className="w-10 h-10 mb-2 opacity-30" />
                <p className="font-bold">Sem dados históricos suficientes para o gráfico</p>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6 border border-gray-100 dark:border-gray-700">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-bold text-gray-900 flex items-center gap-2">
            <DollarSign className="w-5 h-5 text-purple-600" />
            Folha de Pagamento Detalhada
          </h3>
          <div className="flex gap-2">
            <button
              onClick={exportarFolhaPagamentoPDF}
              className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors flex items-center gap-2"
            >
              <Download className="w-4 h-4" />
              Relatório Geral (PDF)
            </button>
            <button
              onClick={() => toggleSection('folha')}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              {expandedSections['folha'] ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {expandedSections['folha'] && (
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="bg-gray-200 dark:bg-gray-700 text-black dark:text-white font-black border-b-2 border-gray-400 dark:border-gray-500">
                <tr>
                  <th className="px-4 py-3 rounded-l-lg uppercase tracking-tight text-black dark:text-white">Funcionário</th>
                  <th className="px-4 py-3 uppercase tracking-tight text-black dark:text-white">Cargo</th>
                  <th className="px-4 py-3 uppercase tracking-tight text-black dark:text-white">Salário Base</th>
                  <th className="px-4 py-3 uppercase tracking-tight text-black dark:text-white">Benefícios</th>
                  <th className="px-4 py-3 uppercase tracking-tight text-black dark:text-white">H. Extras</th>
                  <th className="px-4 py-3 uppercase tracking-tight text-black dark:text-white">Faltas</th>
                  <th className="px-4 py-3 uppercase tracking-tight text-black dark:text-white">Atrasos</th>
                  <th className="px-4 py-3 uppercase tracking-tight text-black dark:text-white">Total Estimado</th>
                  <th className="px-4 py-3 rounded-r-lg text-right uppercase tracking-tight text-black dark:text-white">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {rhData.espelho_pagamento_mes && rhData.espelho_pagamento_mes.length > 0 ? (
                  rhData.espelho_pagamento_mes.map((row, idx) => (
                    <tr key={idx} className="hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors border-b border-gray-300 dark:border-gray-600">
                      <td className="px-4 py-3">
                        <p className="text-black dark:text-white font-black">{row.nome}</p>
                      </td>
                      <td className="px-4 py-3 text-black dark:text-gray-100 font-black">{row.cargo}</td>
                      <td className="px-4 py-3 text-black dark:text-white font-black">R$ {row.salario_base.toFixed(2)}</td>
                      <td className="px-4 py-3 text-black dark:text-white font-black">R$ {row.beneficios.toFixed(2)}</td>
                      <td className="px-4 py-3 text-black dark:text-white font-black">
                        {row.horas_extras_horas.toFixed(1)}h / R$ {row.custo_horas_extras.toFixed(2)}
                      </td>
                      <td className="px-4 py-3 text-black dark:text-white font-black">{row.faltas}</td>
                      <td className="px-4 py-3 text-black dark:text-white font-black">{row.atrasos_minutos}m</td>
                      <td className="px-4 py-3 text-black dark:text-white font-black">
                        R$ {row.total_estimado.toFixed(2)}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <button
                          onClick={() => openHolerite(row)}
                          className="flex items-center gap-1 text-blue-900 dark:text-blue-300 hover:text-blue-700 font-black text-xs ml-auto uppercase tracking-tighter"
                        >
                          <Printer className="w-4 h-4" />
                          Holerite
                        </button>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={9} className="px-4 py-10 text-center text-gray-400">
                      Sem dados para espelho de pagamento
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal Holerite */}
      {selectedFuncionarioHolerite && rhData?.resumo_mes && (
        <HoleriteModal
          isOpen={holeriteModalOpen}
          onClose={() => setHoleriteModalOpen(false)}
          funcionario={selectedFuncionarioHolerite}
          periodo={`${rhData.resumo_mes.inicio || ''} - ${rhData.resumo_mes.fim || ''}`}
        />
      )}
    </div>
  );
}
