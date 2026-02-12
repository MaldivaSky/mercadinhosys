import { useState, useEffect } from 'react';
import { Clock, Filter, Download, ChevronLeft, ChevronRight, User, AlertCircle } from 'lucide-react';
import { apiClient } from '../../../api/apiClient';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';

interface PontoRegistro {
  id: number;
  funcionario_id: number;
  funcionario_nome: string;
  funcionario_cargo: string;
  data: string;
  hora: string;
  tipo: 'entrada' | 'saida' | 'intervalo_inicio' | 'intervalo_fim';
  foto_path?: string;
  observacao?: string;
  minutos_atraso?: number;
  minutos_extras?: number;
}

interface Funcionario {
  id: number;
  nome: string;
  cargo: string;
}

export default function PontoHistoricoRH() {
  const [registros, setRegistros] = useState<PontoRegistro[]>([]);
  const [funcionarios, setFuncionarios] = useState<Funcionario[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [filtroFuncionarioId, setFiltroFuncionarioId] = useState<string>('');
  const [filtroDataInicio, setFiltroDataInicio] = useState<string>('');
  const [filtroDataFim, setFiltroDataFim] = useState<string>('');
  const [filtroTipo, setFiltroTipo] = useState<string>('');

  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(25);
  const [total, setTotal] = useState(0);
  const [pages, setPages] = useState(1);

  useEffect(() => {
    loadFuncionarios();
  }, []);

  useEffect(() => {
    loadRegistros();
  }, [page, perPage, filtroFuncionarioId, filtroDataInicio, filtroDataFim, filtroTipo]);

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

  const loadRegistros = async () => {
    try {
      setLoading(true);
      setError(null);

      const params: any = { page, per_page: perPage };
      if (filtroDataInicio) params.data_inicio = filtroDataInicio;
      if (filtroDataFim) params.data_fim = filtroDataFim;
      if (filtroFuncionarioId) params.funcionario_id = Number(filtroFuncionarioId);
      if (filtroTipo) params.tipo = filtroTipo;

      const response = await apiClient.get('/dashboard/rh/ponto/historico', { params });
      const data = response?.data?.data;

      setRegistros(data?.items || []);
      setPage(data?.page || page);
      setPerPage(data?.per_page || perPage);
      setTotal(data?.total || 0);
      setPages(data?.pages || 1);
    } catch (err: any) {
      console.error('Erro ao carregar histórico de ponto:', err);
      setError(err?.response?.data?.message || err?.message || 'Erro ao carregar histórico');
      setRegistros([]);
      setTotal(0);
      setPages(1);
    } finally {
      setLoading(false);
    }
  };

  const limparFiltros = () => {
    setFiltroFuncionarioId('');
    setFiltroDataInicio('');
    setFiltroDataFim('');
    setFiltroTipo('');
    setPage(1);
  };

  const exportarPDF = () => {
    const doc = new jsPDF();

    doc.setFillColor(99, 102, 241);
    doc.rect(0, 0, 210, 40, 'F');
    doc.setTextColor(255, 255, 255);
    doc.setFontSize(20);
    doc.text('Histórico de Registros de Ponto', 105, 20, { align: 'center' });
    doc.setFontSize(10);
    doc.text(`Gerado em: ${new Date().toLocaleDateString('pt-BR')}`, 105, 30, { align: 'center' });

    const headers = [['Data', 'Hora', 'Funcionário', 'Cargo', 'Tipo', 'Atraso', 'Extras']];
    const data = registros.map(r => [
      new Date(r.data).toLocaleDateString('pt-BR'),
      r.hora,
      r.funcionario_nome,
      r.funcionario_cargo,
      r.tipo,
      r.minutos_atraso ? `${r.minutos_atraso}m` : '-',
      r.minutos_extras ? `${(r.minutos_extras / 60).toFixed(1)}h` : '-'
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

    doc.save(`historico-ponto-${new Date().toISOString().split('T')[0]}.pdf`);
  };

  const getTipoLabel = (tipo: string) => {
    const labels: Record<string, string> = {
      'entrada': 'Entrada',
      'saida': 'Saída',
      'intervalo_inicio': 'Início Intervalo',
      'intervalo_fim': 'Fim Intervalo'
    };
    return labels[tipo] || tipo;
  };

  const getTipoBadgeColor = (tipo: string) => {
    const colors: Record<string, string> = {
      'entrada': 'bg-green-100 text-green-700',
      'saida': 'bg-red-100 text-red-700',
      'intervalo_inicio': 'bg-yellow-100 text-yellow-700',
      'intervalo_fim': 'bg-blue-100 text-blue-700'
    };
    return colors[tipo] || 'bg-gray-100 text-gray-700';
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Histórico de Registros de Ponto</h2>
          <p className="text-sm text-gray-600 mt-1">Visualização detalhada de todos os registros</p>
        </div>
        <button
          onClick={exportarPDF}
          className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors flex items-center gap-2"
        >
          <Download className="w-4 h-4" />
          PDF
        </button>
      </div>

      <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100">
        <div className="flex items-center gap-2 mb-4">
          <Filter className="w-5 h-5 text-gray-500" />
          <h3 className="font-bold text-gray-900">Filtros</h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Funcionário</label>
            <select
              value={filtroFuncionarioId}
              onChange={(e) => {
                setFiltroFuncionarioId(e.target.value);
                setPage(1);
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Todos</option>
              {funcionarios.map(f => (
                <option key={f.id} value={f.id}>{f.nome}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Data Início</label>
            <input
              type="date"
              value={filtroDataInicio}
              onChange={(e) => {
                setFiltroDataInicio(e.target.value);
                setPage(1);
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Data Fim</label>
            <input
              type="date"
              value={filtroDataFim}
              onChange={(e) => {
                setFiltroDataFim(e.target.value);
                setPage(1);
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Tipo</label>
            <select
              value={filtroTipo}
              onChange={(e) => {
                setFiltroTipo(e.target.value);
                setPage(1);
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Todos</option>
              <option value="entrada">Entrada</option>
              <option value="saida">Saída</option>
              <option value="intervalo_inicio">Início Intervalo</option>
              <option value="intervalo_fim">Fim Intervalo</option>
            </select>
          </div>

          <div className="flex items-end">
            <button
              onClick={limparFiltros}
              className="w-full px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
            >
              Limpar Filtros
            </button>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-md border border-gray-100 overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-4 text-gray-600">Carregando registros...</p>
            </div>
          </div>
        ) : error ? (
          <div className="p-6 bg-red-50 border border-red-200">
            <div className="flex items-center gap-3 text-red-700">
              <AlertCircle className="w-6 h-6" />
              <div>
                <h3 className="font-bold">Erro ao carregar registros</h3>
                <p className="text-sm">{error}</p>
              </div>
            </div>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead className="bg-gray-50 text-gray-600 font-medium">
                  <tr>
                    <th className="px-4 py-3">Data</th>
                    <th className="px-4 py-3">Hora</th>
                    <th className="px-4 py-3">Funcionário</th>
                    <th className="px-4 py-3">Cargo</th>
                    <th className="px-4 py-3">Tipo</th>
                    <th className="px-4 py-3">Atraso</th>
                    <th className="px-4 py-3">Extras</th>
                    <th className="px-4 py-3">Observação</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {registros.length > 0 ? (
                    registros.map((registro) => (
                      <tr key={registro.id} className="hover:bg-gray-50 transition-colors">
                        <td className="px-4 py-3 font-medium text-gray-900">
                          {new Date(registro.data).toLocaleDateString('pt-BR')}
                        </td>
                        <td className="px-4 py-3 text-gray-900">{registro.hora}</td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            <User className="w-4 h-4 text-gray-400" />
                            <span className="font-medium text-gray-900">{registro.funcionario_nome}</span>
                          </div>
                        </td>
                        <td className="px-4 py-3 text-gray-600">{registro.funcionario_cargo}</td>
                        <td className="px-4 py-3">
                          <span className={`px-2 py-1 text-xs font-bold rounded-full ${getTipoBadgeColor(registro.tipo)}`}>
                            {getTipoLabel(registro.tipo)}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          {registro.minutos_atraso && registro.minutos_atraso > 0 ? (
                            <span className="px-2 py-1 text-xs font-bold rounded-full bg-red-100 text-red-700">
                              {registro.minutos_atraso}m
                            </span>
                          ) : (
                            <span className="text-gray-400">-</span>
                          )}
                        </td>
                        <td className="px-4 py-3">
                          {registro.minutos_extras && registro.minutos_extras > 0 ? (
                            <span className="px-2 py-1 text-xs font-bold rounded-full bg-orange-100 text-orange-700">
                              {(registro.minutos_extras / 60).toFixed(1)}h
                            </span>
                          ) : (
                            <span className="text-gray-400">-</span>
                          )}
                        </td>
                        <td className="px-4 py-3 text-gray-600 text-xs">
                          {registro.observacao || '-'}
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={8} className="px-4 py-12 text-center text-gray-400">
                        <Clock className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                        <p>Nenhum registro encontrado</p>
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            {pages > 1 && (
              <div className="flex items-center justify-between px-6 py-4 bg-gray-50 border-t border-gray-200">
                <div className="text-sm text-gray-600">
                  Mostrando {((page - 1) * perPage) + 1} a {Math.min(page * perPage, total)} de {total} registros
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setPage(Math.max(1, page - 1))}
                    disabled={page === 1}
                    className="px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    <ChevronLeft className="w-4 h-4" />
                  </button>

                  <span className="px-4 py-2 text-sm font-medium text-gray-700">
                    Página {page} de {pages}
                  </span>

                  <button
                    onClick={() => setPage(Math.min(pages, page + 1))}
                    disabled={page === pages}
                    className="px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
