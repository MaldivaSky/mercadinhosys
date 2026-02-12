import { useState, useEffect } from 'react';
import { Upload, Download, AlertCircle, CheckCircle, Clock, Filter, ThumbsUp, ThumbsDown, X } from 'lucide-react';
import { apiClient } from '../../../api/apiClient';

interface Justificativa {
  id: number;
  funcionario_id: number;
  funcionario_nome: string;
  tipo: 'atraso' | 'ausencia';
  data: string;
  motivo: string;
  documento_url?: string;
  status: 'pendente' | 'aprovado' | 'rejeitado';
  created_at: string;
  observacao_gerente?: string;
}

interface Funcionario {
  id: number;
  nome: string;
  cargo: string;
}

export default function JustificativasRH() {
  const [justificativas, setJustificativas] = useState<Justificativa[]>([]);
  const [funcionarios, setFuncionarios] = useState<Funcionario[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [filtroFuncionario, setFiltroFuncionario] = useState<string>('');
  const [filtroTipo, setFiltroTipo] = useState<string>('');
  const [filtroStatus, setFiltroStatus] = useState<string>('');

  const [modalAberto, setModalAberto] = useState(false);
  const [modalRespostaAberto, setModalRespostaAberto] = useState(false);
  const [justificativaSelecionada, setJustificativaSelecionada] = useState<Justificativa | null>(null);
  const [acaoResposta, setAcaoResposta] = useState<'aprovar' | 'rejeitar'>('aprovar');
  const [motivoRejeicao, setMotivoRejeicao] = useState('');
  const [respondendo, setRespondendo] = useState(false);
  const [novaJustificativa, setNovaJustificativa] = useState({
    funcionario_id: '',
    tipo: 'atraso' as 'atraso' | 'ausencia',
    data: '',
    motivo: '',
    documento: null as File | null
  });

  useEffect(() => {
    loadFuncionarios();
    loadJustificativas();
  }, [filtroFuncionario, filtroTipo, filtroStatus]);

  const loadFuncionarios = async () => {
    try {
      const response = await apiClient.get('/funcionarios', {
        params: { simples: true, por_pagina: 200, incluir_estatisticas: false },
      });
      const items = response?.data?.data || response?.data?.funcionarios || [];
      setFuncionarios(Array.isArray(items) ? items : []);
    } catch (err) {
      console.error('Erro ao carregar funcionários:', err);
    }
  };

  const loadJustificativas = async () => {
    try {
      setLoading(true);
      const params: any = {};
      if (filtroFuncionario) params.funcionario_id = filtroFuncionario;
      if (filtroTipo) params.tipo = filtroTipo;
      if (filtroStatus) params.status = filtroStatus;

      const response = await apiClient.get('/rh/justificativas', { params });
      setJustificativas(response.data?.data || []);
    } catch (err: any) {
      console.error('Erro ao carregar justificativas:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitJustificativa = async () => {
    if (!novaJustificativa.funcionario_id || !novaJustificativa.data || !novaJustificativa.motivo) {
      alert('Preencha todos os campos obrigatórios');
      return;
    }

    try {
      const formData = new FormData();
      formData.append('funcionario_id', novaJustificativa.funcionario_id);
      formData.append('tipo', novaJustificativa.tipo);
      formData.append('data', novaJustificativa.data);
      formData.append('motivo', novaJustificativa.motivo);
      if (novaJustificativa.documento) {
        formData.append('documento', novaJustificativa.documento);
      }

      await apiClient.post('/rh/justificativas', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      setModalAberto(false);
      setNovaJustificativa({
        funcionario_id: '',
        tipo: 'atraso',
        data: '',
        motivo: '',
        documento: null
      });
      loadJustificativas();
    } catch (err: any) {
      alert('Erro ao salvar justificativa: ' + err.message);
    }
  };

  const abrirModalResposta = (justificativa: Justificativa, acao: 'aprovar' | 'rejeitar') => {
    setJustificativaSelecionada(justificativa);
    setAcaoResposta(acao);
    setMotivoRejeicao('');
    setModalRespostaAberto(true);
  };

  const handleResponderJustificativa = async () => {
    if (!justificativaSelecionada) return;
    if (acaoResposta === 'rejeitar' && !motivoRejeicao.trim()) {
      alert('Informe o motivo da rejeição');
      return;
    }

    try {
      setRespondendo(true);
      const payload: any = { acao: acaoResposta };
      if (acaoResposta === 'rejeitar') {
        payload.motivo_rejeicao = motivoRejeicao;
      }

      await apiClient.put(`/rh/justificativas/${justificativaSelecionada.id}/responder`, payload);
      setModalRespostaAberto(false);
      setJustificativaSelecionada(null);
      loadJustificativas();
    } catch (err: any) {
      alert('Erro ao responder justificativa: ' + (err?.response?.data?.message || err.message));
    } finally {
      setRespondendo(false);
    }
  };

  const getStatusBadge = (status: string) => {
    const badges: Record<string, string> = {
      'pendente': 'bg-yellow-100 text-yellow-700',
      'aprovado': 'bg-green-100 text-green-700',
      'rejeitado': 'bg-red-100 text-red-700'
    };
    return badges[status] || 'bg-gray-100 text-gray-700';
  };

  const getStatusIcon = (status: string) => {
    if (status === 'aprovado') return <CheckCircle className="w-4 h-4" />;
    if (status === 'rejeitado') return <AlertCircle className="w-4 h-4" />;
    return <Clock className="w-4 h-4" />;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Justificativas de Atrasos e Ausências</h2>
          <p className="text-sm text-gray-600 mt-1">Gerenciar documentos e justificativas</p>
        </div>
        <button
          onClick={() => setModalAberto(true)}
          className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors flex items-center gap-2"
        >
          <Upload className="w-4 h-4" />
          Nova Justificativa
        </button>
      </div>

      {/* Filtros */}
      <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100">
        <div className="flex items-center gap-2 mb-4">
          <Filter className="w-5 h-5 text-gray-500" />
          <h3 className="font-bold text-gray-900">Filtros</h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Funcionário</label>
            <select
              value={filtroFuncionario}
              onChange={(e) => setFiltroFuncionario(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Todos</option>
              {funcionarios.map(f => (
                <option key={f.id} value={f.id}>{f.nome}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Tipo</label>
            <select
              value={filtroTipo}
              onChange={(e) => setFiltroTipo(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Todos</option>
              <option value="atraso">Atraso</option>
              <option value="ausencia">Ausência</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
            <select
              value={filtroStatus}
              onChange={(e) => setFiltroStatus(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Todos</option>
              <option value="pendente">Pendente</option>
              <option value="aprovado">Aprovado</option>
              <option value="rejeitado">Rejeitado</option>
            </select>
          </div>
        </div>
      </div>

      {/* Tabela */}
      <div className="bg-white rounded-xl shadow-md border border-gray-100 overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-4 text-gray-600">Carregando justificativas...</p>
            </div>
          </div>
        ) : error ? (
          <div className="p-6 bg-red-50 border border-red-200 rounded-xl">
            <div className="flex items-center gap-3 text-red-700">
              <AlertCircle className="w-6 h-6" />
              <div>
                <h3 className="font-bold">Erro ao carregar justificativas</h3>
                <p className="text-sm">{error}</p>
              </div>
            </div>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="bg-gray-50 text-gray-600 font-medium">
                <tr>
                  <th className="px-4 py-3">Funcionário</th>
                  <th className="px-4 py-3">Tipo</th>
                  <th className="px-4 py-3">Data</th>
                  <th className="px-4 py-3">Motivo</th>
                  <th className="px-4 py-3">Documento</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {justificativas.length > 0 ? (
                  justificativas.map((j) => (
                    <tr key={j.id} className="hover:bg-gray-50 transition-colors">
                      <td className="px-4 py-3 font-medium text-gray-900">{j.funcionario_nome}</td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-1 text-xs font-bold rounded-full ${j.tipo === 'atraso' ? 'bg-red-100 text-red-700' : 'bg-orange-100 text-orange-700'
                          }`}>
                          {j.tipo === 'atraso' ? 'Atraso' : 'Ausência'}
                        </span>
                      </td>
                      <td className="px-4 py-3">{new Date(j.data).toLocaleDateString('pt-BR')}</td>
                      <td className="px-4 py-3 text-gray-600">{j.motivo}</td>
                      <td className="px-4 py-3">
                        {j.documento_url ? (
                          <a href={j.documento_url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline flex items-center gap-1">
                            <Download className="w-4 h-4" />
                            Download
                          </a>
                        ) : (
                          <span className="text-gray-400">-</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-1 text-xs font-bold rounded-full flex items-center gap-1 w-fit ${getStatusBadge(j.status)}`}>
                          {getStatusIcon(j.status)}
                          {j.status === 'pendente' ? 'Pendente' : j.status === 'aprovado' ? 'Aprovado' : 'Rejeitado'}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        {j.status === 'pendente' ? (
                          <div className="flex items-center gap-2">
                            <button
                              onClick={() => abrirModalResposta(j, 'aprovar')}
                              className="p-1.5 bg-green-50 text-green-600 rounded-lg hover:bg-green-100 transition-colors"
                              title="Aprovar"
                            >
                              <ThumbsUp className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => abrirModalResposta(j, 'rejeitar')}
                              className="p-1.5 bg-red-50 text-red-600 rounded-lg hover:bg-red-100 transition-colors"
                              title="Rejeitar"
                            >
                              <ThumbsDown className="w-4 h-4" />
                            </button>
                          </div>
                        ) : (
                          <span className="text-xs text-gray-400 italic">
                            {j.status === 'aprovado' ? 'Aprovado' : 'Rejeitado'}
                          </span>
                        )}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={7} className="px-4 py-10 text-center text-gray-400">
                      Nenhuma justificativa encontrada
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal */}
      {modalAberto && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-xl font-bold text-gray-900 mb-4">Nova Justificativa</h3>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Funcionário *</label>
                <select
                  value={novaJustificativa.funcionario_id}
                  onChange={(e) => setNovaJustificativa({ ...novaJustificativa, funcionario_id: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Selecione...</option>
                  {funcionarios.map(f => (
                    <option key={f.id} value={f.id}>{f.nome}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Tipo *</label>
                <select
                  value={novaJustificativa.tipo}
                  onChange={(e) => setNovaJustificativa({ ...novaJustificativa, tipo: e.target.value as 'atraso' | 'ausencia' })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="atraso">Atraso</option>
                  <option value="ausencia">Ausência</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Data *</label>
                <input
                  type="date"
                  value={novaJustificativa.data}
                  onChange={(e) => setNovaJustificativa({ ...novaJustificativa, data: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Motivo *</label>
                <textarea
                  value={novaJustificativa.motivo}
                  onChange={(e) => setNovaJustificativa({ ...novaJustificativa, motivo: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  rows={3}
                  placeholder="Descreva o motivo..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Documento (Opcional)</label>
                <input
                  type="file"
                  onChange={(e) => setNovaJustificativa({ ...novaJustificativa, documento: e.target.files?.[0] || null })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setModalAberto(false)}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Cancelar
              </button>
              <button
                onClick={handleSubmitJustificativa}
                className="flex-1 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
              >
                Salvar
              </button>
            </div>
          </div>
        </div>
      )}
      {/* Modal Responder Justificativa */}
      {modalRespostaAberto && justificativaSelecionada && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-lg p-6 max-w-md w-full mx-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold text-gray-900">
                {acaoResposta === 'aprovar' ? 'Aprovar Justificativa' : 'Rejeitar Justificativa'}
              </h3>
              <button onClick={() => setModalRespostaAberto(false)} className="text-gray-400 hover:text-gray-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="bg-gray-50 rounded-lg p-4 mb-4 space-y-2">
              <p className="text-sm"><strong>Funcionário:</strong> {justificativaSelecionada.funcionario_nome}</p>
              <p className="text-sm"><strong>Tipo:</strong> {justificativaSelecionada.tipo === 'atraso' ? 'Atraso' : 'Ausência'}</p>
              <p className="text-sm"><strong>Data:</strong> {new Date(justificativaSelecionada.data).toLocaleDateString('pt-BR')}</p>
              <p className="text-sm"><strong>Motivo:</strong> {justificativaSelecionada.motivo}</p>
            </div>

            {acaoResposta === 'aprovar' ? (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
                <div className="flex items-center gap-2 text-green-700">
                  <CheckCircle className="w-5 h-5" />
                  <p className="text-sm font-medium">Esta justificativa será aprovada.</p>
                </div>
              </div>
            ) : (
              <div className="space-y-3 mb-4">
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <div className="flex items-center gap-2 text-red-700 mb-2">
                    <AlertCircle className="w-5 h-5" />
                    <p className="text-sm font-medium">Esta justificativa será rejeitada.</p>
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Motivo da Rejeição *</label>
                  <textarea
                    value={motivoRejeicao}
                    onChange={(e) => setMotivoRejeicao(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500"
                    rows={3}
                    placeholder="Descreva o motivo da rejeição..."
                  />
                </div>
              </div>
            )}

            <div className="flex gap-3">
              <button
                onClick={() => setModalRespostaAberto(false)}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                disabled={respondendo}
              >
                Cancelar
              </button>
              <button
                onClick={handleResponderJustificativa}
                disabled={respondendo}
                className={`flex-1 px-4 py-2 text-white rounded-lg transition-colors flex items-center justify-center gap-2 ${
                  acaoResposta === 'aprovar'
                    ? 'bg-green-500 hover:bg-green-600'
                    : 'bg-red-500 hover:bg-red-600'
                }`}
              >
                {respondendo ? (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                ) : (
                  <>
                    {acaoResposta === 'aprovar' ? <ThumbsUp className="w-4 h-4" /> : <ThumbsDown className="w-4 h-4" />}
                    {acaoResposta === 'aprovar' ? 'Aprovar' : 'Rejeitar'}
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
