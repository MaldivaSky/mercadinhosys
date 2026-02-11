import React, { useState, useEffect } from 'react';
import { Calendar, Download, Filter, ChevronDown, ChevronUp, AlertCircle } from 'lucide-react';
import { apiClient } from '../../../api/apiClient';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';

interface EspelhoPontoData {
  funcionario_id: number;
  nome: string;
  cargo: string;
  registros_diarios: Array<{
    data: string;
    entrada: string | null;
    saida: string | null;
    intervalo_inicio: string | null;
    intervalo_fim: string | null;
    minutos_atraso: number;
    minutos_extras: number;
    horas_trabalhadas: number;
    observacao?: string;
  }>;
  resumo: {
    total_dias_trabalhados: number;
    total_atrasos: number;
    total_minutos_atraso: number;
    total_horas_extras: number;
    total_horas_trabalhadas: number;
    media_horas_dia: number;
  };
}

interface Funcionario {
  id: number;
  nome: string;
  cargo: string;
}

export default function EspelhoPonto() {
  const [espelhoData, setEspelhoData] = useState<EspelhoPontoData | null>(null);
  const [funcionarios, setFuncionarios] = useState<Funcionario[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [funcionarioId, setFuncionarioId] = useState<string>('');
  const [dataInicio, setDataInicio] = useState<string>('');
  const [dataFim, setDataFim] = useState<string>('');
  const [expandedDays, setExpandedDays] = useState<Record<string, boolean>>({});

  useEffect(() => {
    loadFuncionarios();
    
    const hoje = new Date();
    const primeiroDia = new Date(hoje.getFullYear(), hoje.getMonth(), 1);
    setDataInicio(primeiroDia.toISOString().split('T')[0]);
    setDataFim(hoje.toISOString().split('T')[0]);
  }, []);

  const loadFuncionarios = async () => {
    try {
      const response = await apiClient.get('/funcionarios');
      const items = response?.data?.data || response?.data?.funcionarios || response?.data || [];
      setFuncionarios(Array.isArray(items) ? items : []);
    } catch (err) {
      console.error('Erro ao carregar funcionários:', err);
      setFuncionarios([]);
    }
  };

  const loadEspelhoPonto = async () => {
    if (!funcionarioId || !dataInicio || !dataFim) {
      setError('Por favor, selecione um funcionário e o período');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      const response = await apiClient.get('/dashboard/rh/ponto/espelho', {
        params: {
          funcionario_id: Number(funcionarioId),
          data_inicio: dataInicio,
          data_fim: dataFim
        }
      });
      
      setEspelhoData(response.data?.data);
    } catch (err: any) {
      console.error('Erro ao carregar espelho de ponto:', err);
      setError(err?.response?.data?.message || err?.message || 'Erro ao carregar espelho');
      setEspelhoData(null);
    } finally {
      setLoading(false);
    }
  };

  const toggleDay = (data: string) => {
    setExpandedDays(prev => ({
      ...prev,
      [data]: !prev[data]
    }));
  };

  const exportarPDF = () => {
    if (!espelhoData) return;

    const doc = new jsPDF();
    
    doc.setFillColor(99, 102, 241);
    doc.rect(0, 0, 210, 50, 'F');
    doc.setTextColor(255, 255, 255);
    doc.setFontSize(22);
    doc.text('Espelho de Ponto', 105, 20, { align: 'center' });
    doc.setFontSize(12);
    doc.text(`Funcionário: ${espelhoData.nome}`, 105, 30, { align: 'center' });
    doc.text(`Cargo: ${espelhoData.cargo}`, 105, 37, { align: 'center' });
    doc.setFontSize(10);
    doc.text(`Período: ${new Date(dataInicio).toLocaleDateString('pt-BR')} a ${new Date(dataFim).toLocaleDateString('pt-BR')}`, 105, 44, { align: 'center' });

    const headers = [['Data', 'Entrada', 'Saída', 'Int. Início', 'Int. Fim', 'Atraso', 'Extras', 'H. Trab.']];
    const data = espelhoData.registros_diarios.map(r => [
      new Date(r.data).toLocaleDateString('pt-BR'),
      r.entrada || '-',
      r.saida || '-',
      r.intervalo_inicio || '-',
      r.intervalo_fim || '-',
      r.minutos_atraso > 0 ? `${r.minutos_atraso}m` : '-',
      r.minutos_extras > 0 ? `${(r.minutos_extras / 60).toFixed(1)}h` : '-',
      `${(r.horas_trabalhadas / 60).toFixed(1)}h`
    ]);

    autoTable(doc, {
      head: headers,
      body: data,
      startY: 60,
      theme: 'grid',
      styles: { fontSize: 8, cellPadding: 2 },
      headStyles: { fillColor: [99, 102, 241], textColor: [255, 255, 255] },
      alternateRowStyles: { fillColor: [245, 245, 245] }
    });

    const finalY = (doc as any).lastAutoTable.finalY + 15;
    doc.setFontSize(14);
    doc.setTextColor(0, 0, 0);
    doc.text('Resumo do Período', 14, finalY);
    
    doc.setFontSize(10);
    doc.text(`Dias Trabalhados: ${espelhoData.resumo.total_dias_trabalhados}`, 14, finalY + 8);
    doc.text(`Total de Atrasos: ${espelhoData.resumo.total_atrasos} (${espelhoData.resumo.total_minutos_atraso} minutos)`, 14, finalY + 15);
    doc.text(`Total Horas Extras: ${espelhoData.resumo.total_horas_extras.toFixed(1)}h`, 14, finalY + 22);
    doc.text(`Total Horas Trabalhadas: ${espelhoData.resumo.total_horas_trabalhadas.toFixed(1)}h`, 14, finalY + 29);
    doc.text(`Média Horas/Dia: ${espelhoData.resumo.media_horas_dia.toFixed(1)}h`, 14, finalY + 36);

    doc.save(`espelho-ponto-${espelhoData.nome.replace(/\s+/g, '-')}-${new Date().toISOString().split('T')[0]}.pdf`);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Espelho de Ponto</h2>
          <p className="text-sm text-gray-600 mt-1">Visualização detalhada dos registros por funcionário</p>
        </div>
        {espelhoData && (
          <button
            onClick={exportarPDF}
            className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors flex items-center gap-2"
          >
            <Download className="w-4 h-4" />
            Exportar PDF
          </button>
        )}
      </div>

      <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100">
        <div className="flex items-center gap-2 mb-4">
          <Filter className="w-5 h-5 text-gray-500" />
          <h3 className="font-bold text-gray-900">Selecionar Funcionário e Período</h3>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Funcionário *</label>
            <select
              value={funcionarioId}
              onChange={(e) => setFuncionarioId(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Selecione...</option>
              {funcionarios.map(f => (
                <option key={f.id} value={f.id}>{f.nome} - {f.cargo}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Data Início *</label>
            <input
              type="date"
              value={dataInicio}
              onChange={(e) => setDataInicio(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Data Fim *</label>
            <input
              type="date"
              value={dataFim}
              onChange={(e) => setDataFim(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="flex items-end">
            <button
              onClick={loadEspelhoPonto}
              disabled={!funcionarioId || !dataInicio || !dataFim}
              className="w-full px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Gerar Espelho
            </button>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64 bg-white rounded-xl shadow-md">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Gerando espelho de ponto...</p>
          </div>
        </div>
      ) : error ? (
        <div className="bg-red-50 border border-red-200 rounded-xl p-6">
          <div className="flex items-center gap-3 text-red-700">
            <AlertCircle className="w-6 h-6" />
            <p>{error}</p>
          </div>
        </div>
      ) : espelhoData ? (
        <>
          <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100">
            <h3 className="font-bold text-gray-900 mb-4">Resumo do Período</h3>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div className="p-4 bg-blue-50 rounded-lg text-center">
                <p className="text-2xl font-bold text-blue-700">{espelhoData.resumo.total_dias_trabalhados}</p>
                <p className="text-xs text-blue-600 font-medium uppercase mt-1">Dias Trabalhados</p>
              </div>
              <div className="p-4 bg-red-50 rounded-lg text-center">
                <p className="text-2xl font-bold text-red-700">{espelhoData.resumo.total_atrasos}</p>
                <p className="text-xs text-red-600 font-medium uppercase mt-1">Atrasos</p>
                <p className="text-xs text-red-500 mt-1">{espelhoData.resumo.total_minutos_atraso}m</p>
              </div>
              <div className="p-4 bg-orange-50 rounded-lg text-center">
                <p className="text-2xl font-bold text-orange-700">{espelhoData.resumo.total_horas_extras.toFixed(1)}h</p>
                <p className="text-xs text-orange-600 font-medium uppercase mt-1">Horas Extras</p>
              </div>
              <div className="p-4 bg-green-50 rounded-lg text-center">
                <p className="text-2xl font-bold text-green-700">{espelhoData.resumo.total_horas_trabalhadas.toFixed(1)}h</p>
                <p className="text-xs text-green-600 font-medium uppercase mt-1">Total Trabalhado</p>
              </div>
              <div className="p-4 bg-purple-50 rounded-lg text-center">
                <p className="text-2xl font-bold text-purple-700">{espelhoData.resumo.media_horas_dia.toFixed(1)}h</p>
                <p className="text-xs text-purple-600 font-medium uppercase mt-1">Média/Dia</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-md border border-gray-100 overflow-hidden">
            <div className="p-6 border-b border-gray-200">
              <h3 className="font-bold text-gray-900">Registros Diários</h3>
            </div>
            <div className="divide-y divide-gray-100">
              {espelhoData.registros_diarios.map((registro, idx) => (
                <div key={idx} className="p-4 hover:bg-gray-50 transition-colors">
                  <div 
                    className="flex items-center justify-between cursor-pointer"
                    onClick={() => toggleDay(registro.data)}
                  >
                    <div className="flex items-center gap-4">
                      <div className="p-2 bg-blue-100 rounded-lg">
                        <Calendar className="w-5 h-5 text-blue-600" />
                      </div>
                      <div>
                        <p className="font-bold text-gray-900">
                          {new Date(registro.data).toLocaleDateString('pt-BR', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
                        </p>
                        <p className="text-sm text-gray-600">
                          {registro.entrada || '-'} às {registro.saida || '-'} • {(registro.horas_trabalhadas / 60).toFixed(1)}h trabalhadas
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      {registro.minutos_atraso > 0 && (
                        <span className="px-2 py-1 text-xs font-bold rounded-full bg-red-100 text-red-700">
                          {registro.minutos_atraso}m atraso
                        </span>
                      )}
                      {registro.minutos_extras > 0 && (
                        <span className="px-2 py-1 text-xs font-bold rounded-full bg-orange-100 text-orange-700">
                          {(registro.minutos_extras / 60).toFixed(1)}h extras
                        </span>
                      )}
                      {expandedDays[registro.data] ? <ChevronUp className="w-5 h-5 text-gray-400" /> : <ChevronDown className="w-5 h-5 text-gray-400" />}
                    </div>
                  </div>

                  {expandedDays[registro.data] && (
                    <div className="mt-4 ml-14 grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="p-3 bg-green-50 rounded-lg">
                        <p className="text-xs text-green-600 font-medium uppercase">Entrada</p>
                        <p className="text-lg font-bold text-green-900 mt-1">{registro.entrada || '-'}</p>
                      </div>
                      <div className="p-3 bg-yellow-50 rounded-lg">
                        <p className="text-xs text-yellow-600 font-medium uppercase">Intervalo Início</p>
                        <p className="text-lg font-bold text-yellow-900 mt-1">{registro.intervalo_inicio || '-'}</p>
                      </div>
                      <div className="p-3 bg-blue-50 rounded-lg">
                        <p className="text-xs text-blue-600 font-medium uppercase">Intervalo Fim</p>
                        <p className="text-lg font-bold text-blue-900 mt-1">{registro.intervalo_fim || '-'}</p>
                      </div>
                      <div className="p-3 bg-red-50 rounded-lg">
                        <p className="text-xs text-red-600 font-medium uppercase">Saída</p>
                        <p className="text-lg font-bold text-red-900 mt-1">{registro.saida || '-'}</p>
                      </div>
                      {registro.observacao && (
                        <div className="col-span-2 md:col-span-4 p-3 bg-gray-50 rounded-lg">
                          <p className="text-xs text-gray-600 font-medium uppercase">Observação</p>
                          <p className="text-sm text-gray-900 mt-1">{registro.observacao}</p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </>
      ) : (
        <div className="bg-gray-50 border border-gray-200 rounded-xl p-12 text-center">
          <Calendar className="w-16 h-16 mx-auto text-gray-300 mb-4" />
          <p className="text-gray-600">Selecione um funcionário e período para gerar o espelho de ponto</p>
        </div>
      )}
    </div>
  );
}
