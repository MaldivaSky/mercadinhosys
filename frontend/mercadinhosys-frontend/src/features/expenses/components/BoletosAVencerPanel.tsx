// src/features/expenses/components/BoletosAVencerPanel.tsx
import React, { useState, useEffect } from 'react';
import {
  AlertTriangle,
  Calendar,
  DollarSign,
  CheckCircle,
  Clock,
  Truck,
  Eye,
  CreditCard
} from 'lucide-react';
import { BoletoFornecedor, purchaseOrderService } from '../../products/purchaseOrderService';
import { formatCurrency, formatDate } from '../../../utils/formatters';
import toast from 'react-hot-toast';

interface BoletosAVencerPanelProps {
  className?: string;
}

const BoletosAVencerPanel: React.FC<BoletosAVencerPanelProps> = ({ className = '' }) => {
  const [boletos, setBoletos] = useState<BoletoFornecedor[]>([]);
  const [resumo, setResumo] = useState({
    total_boletos: 0,
    total_valor: 0,
    vencidos: 0,
    vence_hoje: 0,
    vence_7_dias: 0,
    valor_vencidos: 0,
    valor_vence_hoje: 0,
    valor_vence_7_dias: 0
  });
  const [loading, setLoading] = useState(false);
  const [filtro, setFiltro] = useState<'todos' | 'vencidos' | 'hoje' | '7_dias'>('todos');
  const [showPayModal, setShowPayModal] = useState(false);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [selectedBoleto, setSelectedBoleto] = useState<BoletoFornecedor | null>(null);

  const loadBoletos = async () => {
    setLoading(true);
    try {
      const response = await purchaseOrderService.boletosAVencer({
        dias: 30,
        apenas_vencidos: false
      });

      setBoletos(response.boletos);
      setResumo(response.resumo);
    } catch (error) {
      console.error('Erro ao carregar boletos:', error);
      toast.error('Erro ao carregar boletos a vencer');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadBoletos();
  }, []);

  const getStatusBadge = (status: string) => {
    const styles = {
      vencido: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300',
      vence_hoje: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-300',
      vence_em_breve: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300',
      normal: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300'
    };

    const icons = {
      vencido: AlertTriangle,
      vence_hoje: Clock,
      vence_em_breve: Calendar,
      normal: CheckCircle
    };

    const labels = {
      vencido: 'Vencido',
      vence_hoje: 'Vence Hoje',
      vence_em_breve: 'Vence em Breve',
      normal: 'Normal'
    };

    const Icon = icons[status as keyof typeof icons] || Clock;
    const label = labels[status as keyof typeof labels] || 'Normal';

    return (
      <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${styles[status as keyof typeof styles] || styles.normal}`}>
        <Icon className="w-3 h-3" />
        {label}
      </span>
    );
  };

  const boletosFiltrados = boletos.filter(boleto => {
    switch (filtro) {
      case 'vencidos':
        return boleto.status_vencimento === 'vencido';
      case 'hoje':
        return boleto.status_vencimento === 'vence_hoje';
      case '7_dias':
        return boleto.status_vencimento === 'vence_em_breve';
      default:
        return true;
    }
  });

  const handlePagar = async (boleto: BoletoFornecedor) => {
    setSelectedBoleto(boleto);
    setShowPayModal(true);
  };

  const handleVerDetalhes = (boleto: BoletoFornecedor) => {
    setSelectedBoleto(boleto);
    setShowDetailModal(true);
  };

  if (loading) {
    return (
      <div className={`bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 ${className}`}>
        <div className="flex items-center justify-center py-8">
          <div className="w-8 h-8 border-4 border-orange-600 border-t-transparent rounded-full animate-spin"></div>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white dark:bg-gray-800 rounded-xl shadow-lg ${className}`}>
      {/* Header */}
      <div className="p-6 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-6 h-6 text-orange-600" />
            <h2 className="text-xl font-bold text-gray-800 dark:text-white">
              Boletos a Vencer
            </h2>
          </div>
          <button
            onClick={loadBoletos}
            className="px-3 py-1 bg-orange-600 text-white rounded-lg hover:bg-orange-700 text-sm transition-colors"
          >
            Atualizar
          </button>
        </div>

        {/* Resumo */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
          <div className="bg-red-50 dark:bg-red-900 p-3 rounded-lg">
            <div className="text-sm text-red-600 dark:text-red-300">Vencidos</div>
            <div className="text-lg font-bold text-red-800 dark:text-red-200">
              {resumo.vencidos}
            </div>
            <div className="text-xs text-red-600 dark:text-red-400">
              {formatCurrency(resumo.valor_vencidos)}
            </div>
          </div>

          <div className="bg-orange-50 dark:bg-orange-900 p-3 rounded-lg">
            <div className="text-sm text-orange-600 dark:text-orange-300">Hoje</div>
            <div className="text-lg font-bold text-orange-800 dark:text-orange-200">
              {resumo.vence_hoje}
            </div>
            <div className="text-xs text-orange-600 dark:text-orange-400">
              {formatCurrency(resumo.valor_vence_hoje)}
            </div>
          </div>

          <div className="bg-yellow-50 dark:bg-yellow-900 p-3 rounded-lg">
            <div className="text-sm text-yellow-600 dark:text-yellow-300">7 Dias</div>
            <div className="text-lg font-bold text-yellow-800 dark:text-yellow-200">
              {resumo.vence_7_dias}
            </div>
            <div className="text-xs text-yellow-600 dark:text-yellow-400">
              {formatCurrency(resumo.valor_vence_7_dias)}
            </div>
          </div>

          <div className="bg-blue-50 dark:bg-blue-900 p-3 rounded-lg">
            <div className="text-sm text-blue-600 dark:text-blue-300">Total</div>
            <div className="text-lg font-bold text-blue-800 dark:text-blue-200">
              {resumo.total_boletos}
            </div>
            <div className="text-xs text-blue-600 dark:text-blue-400">
              {formatCurrency(resumo.total_valor)}
            </div>
          </div>
        </div>

        {/* Filtros */}
        <div className="flex gap-2 mt-4">
          <button
            onClick={() => setFiltro('todos')}
            className={`px-3 py-1 rounded-lg text-sm transition-colors ${filtro === 'todos'
                ? 'bg-orange-600 text-white'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
              }`}
          >
            Todos
          </button>
          <button
            onClick={() => setFiltro('vencidos')}
            className={`px-3 py-1 rounded-lg text-sm transition-colors ${filtro === 'vencidos'
                ? 'bg-red-600 text-white'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
              }`}
          >
            Vencidos ({resumo.vencidos})
          </button>
          <button
            onClick={() => setFiltro('hoje')}
            className={`px-3 py-1 rounded-lg text-sm transition-colors ${filtro === 'hoje'
                ? 'bg-orange-600 text-white'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
              }`}
          >
            Hoje ({resumo.vence_hoje})
          </button>
          <button
            onClick={() => setFiltro('7_dias')}
            className={`px-3 py-1 rounded-lg text-sm transition-colors ${filtro === '7_dias'
                ? 'bg-yellow-600 text-white'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
              }`}
          >
            7 Dias ({resumo.vence_7_dias})
          </button>
        </div>
      </div>

      {/* Lista de Boletos */}
      <div className="p-6">
        {boletosFiltrados.length === 0 ? (
          <div className="text-center py-8">
            <CheckCircle className="w-16 h-16 text-green-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-800 dark:text-white mb-2">
              {filtro === 'todos' ? 'Nenhum boleto encontrado' : 'Nenhum boleto neste filtro'}
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              {filtro === 'todos'
                ? 'Não há boletos de fornecedores pendentes no momento'
                : 'Tente outro filtro para ver mais boletos'
              }
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {boletosFiltrados.map(boleto => (
              <div
                key={boleto.id}
                className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 border border-gray-200 dark:border-gray-600"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-lg font-semibold text-gray-800 dark:text-white">
                        {boleto.numero_documento}
                      </h3>
                      {getStatusBadge(boleto.status_vencimento)}
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-gray-600 dark:text-gray-400">
                      <div className="flex items-center gap-2">
                        <Truck className="w-4 h-4" />
                        <span>{boleto.fornecedor_nome}</span>
                      </div>

                      <div className="flex items-center gap-2">
                        <Calendar className="w-4 h-4" />
                        <span>Vence: {formatDate(boleto.data_vencimento)}</span>
                      </div>

                      <div className="flex items-center gap-2">
                        <DollarSign className="w-4 h-4" />
                        <span className="font-medium text-gray-800 dark:text-white">
                          {formatCurrency(boleto.valor_atual)}
                        </span>
                      </div>
                    </div>

                    {boleto.pedido_numero && (
                      <div className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                        Pedido: {boleto.pedido_numero}
                      </div>
                    )}

                    {boleto.dias_vencimento < 0 && (
                      <div className="mt-2 text-sm text-red-600 dark:text-red-400 font-medium">
                        Vencido há {Math.abs(boleto.dias_vencimento)} dias
                      </div>
                    )}
                  </div>

                  <div className="flex items-center gap-2 ml-4">
                    <button
                      onClick={() => handlePagar(boleto)}
                      className="px-3 py-1 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-1 text-sm transition-colors"
                    >
                      <CreditCard className="w-4 h-4" />
                      Pagar
                    </button>

                    <button
                      onClick={() => {
                        handleVerDetalhes(boleto);
                      }}
                      className="px-3 py-1 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-1 text-sm transition-colors"
                    >
                      <Eye className="w-4 h-4" />
                      Ver
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Modal de Detalhes do Boleto */}
      {showDetailModal && selectedBoleto && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200 dark:border-gray-700">
              <div className="flex items-center justify-between">
                <h3 className="text-xl font-bold text-gray-800 dark:text-white">
                  Detalhes do Boleto
                </h3>
                <button
                  onClick={() => {
                    setShowDetailModal(false);
                    setSelectedBoleto(null);
                  }}
                  className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                >
                  ✕
                </button>
              </div>
            </div>

            <div className="p-6 space-y-6">
              {/* Informações Principais */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Número do Documento
                  </label>
                  <div className="text-lg font-semibold text-gray-800 dark:text-white">
                    {selectedBoleto.numero_documento}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Status
                  </label>
                  <div>
                    {getStatusBadge(selectedBoleto.status_vencimento)}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Fornecedor
                  </label>
                  <div className="text-gray-800 dark:text-white">
                    {selectedBoleto.fornecedor_nome}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Data de Vencimento
                  </label>
                  <div className="text-gray-800 dark:text-white">
                    {formatDate(selectedBoleto.data_vencimento)}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Valor Original
                  </label>
                  <div className="text-lg font-semibold text-gray-800 dark:text-white">
                    {formatCurrency(selectedBoleto.valor_original)}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Valor Atual
                  </label>
                  <div className="text-lg font-semibold text-blue-600 dark:text-blue-400">
                    {formatCurrency(selectedBoleto.valor_atual)}
                  </div>
                </div>
              </div>

              {/* Informações do Pedido */}
              {selectedBoleto.pedido_numero && (
                <div className="bg-blue-50 dark:bg-blue-900 p-4 rounded-lg">
                  <h4 className="font-semibold text-blue-900 dark:text-blue-100 mb-3">
                    Informações do Pedido
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-blue-700 dark:text-blue-300">Número:</span>
                      <div className="font-medium text-blue-900 dark:text-blue-100">
                        {selectedBoleto.pedido_numero}
                      </div>
                    </div>
                    {selectedBoleto.data_pedido && (
                      <div>
                        <span className="text-blue-700 dark:text-blue-300">Data do Pedido:</span>
                        <div className="font-medium text-blue-900 dark:text-blue-100">
                          {formatDate(selectedBoleto.data_pedido)}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Informações de Vencimento */}
              <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                <h4 className="font-semibold text-gray-800 dark:text-white mb-3">
                  Informações de Vencimento
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600 dark:text-gray-400">Dias para Vencer:</span>
                    <div className={`font-medium text-lg ${selectedBoleto.dias_vencimento < 0
                        ? 'text-red-600 dark:text-red-400'
                        : selectedBoleto.dias_vencimento === 0
                          ? 'text-orange-600 dark:text-orange-400'
                          : 'text-green-600 dark:text-green-400'
                      }`}>
                      {selectedBoleto.dias_vencimento < 0
                        ? `Vencido há ${Math.abs(selectedBoleto.dias_vencimento)} dias`
                        : selectedBoleto.dias_vencimento === 0
                          ? 'Vence Hoje'
                          : `${selectedBoleto.dias_vencimento} dias`
                      }
                    </div>
                  </div>

                  <div>
                    <span className="text-gray-600 dark:text-gray-400">Juros/Multa:</span>
                    <div className="font-medium text-gray-800 dark:text-white">
                      {formatCurrency(selectedBoleto.valor_juros || 0)}
                    </div>
                  </div>

                  <div>
                    <span className="text-gray-600 dark:text-gray-400">Desconto:</span>
                    <div className="font-medium text-gray-800 dark:text-white">
                      {formatCurrency(selectedBoleto.valor_desconto || 0)}
                    </div>
                  </div>
                </div>
              </div>

              {/* Observações */}
              {selectedBoleto.observacoes && (
                <div className="bg-yellow-50 dark:bg-yellow-900 p-4 rounded-lg">
                  <h4 className="font-semibold text-yellow-900 dark:text-yellow-100 mb-2">
                    Observações
                  </h4>
                  <p className="text-yellow-800 dark:text-yellow-200 text-sm">
                    {selectedBoleto.observacoes}
                  </p>
                </div>
              )}

              {/* Produtos do Pedido */}
              {selectedBoleto.itens && selectedBoleto.itens.length > 0 && (
                <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                  <h4 className="font-semibold text-gray-800 dark:text-white mb-4">
                    Produtos do Pedido ({selectedBoleto.itens.length})
                  </h4>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-gray-200 dark:border-gray-600">
                          <th className="text-left py-2 px-3 text-gray-700 dark:text-gray-300 font-medium">
                            Produto
                          </th>
                          <th className="text-right py-2 px-3 text-gray-700 dark:text-gray-300 font-medium">
                            Qtd. Solicitada
                          </th>
                          <th className="text-right py-2 px-3 text-gray-700 dark:text-gray-300 font-medium">
                            Qtd. Recebida
                          </th>
                          <th className="text-right py-2 px-3 text-gray-700 dark:text-gray-300 font-medium">
                            Preço Unit.
                          </th>
                          <th className="text-right py-2 px-3 text-gray-700 dark:text-gray-300 font-medium">
                            Total
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        {selectedBoleto.itens.map((item, idx) => (
                          <tr key={idx} className="border-b border-gray-200 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors">
                            <td className="py-3 px-3 text-gray-800 dark:text-white">
                              {item.produto_nome}
                            </td>
                            <td className="text-right py-3 px-3 text-gray-800 dark:text-white">
                              {item.quantidade_solicitada}
                            </td>
                            <td className="text-right py-3 px-3 text-gray-800 dark:text-white">
                              {item.quantidade_recebida}
                            </td>
                            <td className="text-right py-3 px-3 text-gray-800 dark:text-white">
                              {formatCurrency(item.preco_unitario)}
                            </td>
                            <td className="text-right py-3 px-3 font-medium text-gray-800 dark:text-white">
                              {formatCurrency(item.total_item)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Ações */}
              <div className="flex justify-end gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
                <button
                  onClick={() => {
                    setShowDetailModal(false);
                    setSelectedBoleto(null);
                  }}
                  className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                >
                  Fechar
                </button>
                <button
                  onClick={() => {
                    setShowDetailModal(false);
                    handlePagar(selectedBoleto);
                  }}
                  className="px-4 py-2 bg-green-600 text-white hover:bg-green-700 rounded-lg transition-colors flex items-center gap-2"
                >
                  <CreditCard className="w-4 h-4" />
                  Pagar Agora
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modal de Pagamento Funcional */}
      {showPayModal && selectedBoleto && (
        <ModalPagamentoBoleto
          boleto={selectedBoleto}
          onClose={() => { setShowPayModal(false); setSelectedBoleto(null); }}
          onPago={() => {
            setShowPayModal(false);
            setSelectedBoleto(null);
            loadBoletos();
            toast.success('Boleto pago com sucesso!');
          }}
        />
      )}
    </div>
  );
};

// ===============================================
// Componente Modal de Pagamento de Boleto
// ===============================================

interface ModalPagamentoBoletoProps {
  boleto: BoletoFornecedor;
  onClose: () => void;
  onPago: () => void;
}

const ModalPagamentoBoleto: React.FC<ModalPagamentoBoletoProps> = ({ boleto, onClose, onPago }) => {
  const [formaPagamento, setFormaPagamento] = useState('pix');
  const [valorPago, setValorPago] = useState(boleto.valor_atual.toString());
  const [dataPagamento, setDataPagamento] = useState(new Date().toISOString().split('T')[0]);
  const [observacoes, setObservacoes] = useState('');
  const [processando, setProcessando] = useState(false);

  const handlePagar = async () => {
    setProcessando(true);
    try {
      await purchaseOrderService.pagarBoleto(boleto.id, {
        valor_pago: parseFloat(valorPago),
        data_pagamento: dataPagamento,
        forma_pagamento: formaPagamento,
        observacoes: observacoes || undefined,
      });
      onPago();
    } catch (error: any) {
      console.error('Erro ao pagar boleto:', error);
      toast.error(error.response?.data?.error || 'Erro ao registrar pagamento');
    } finally {
      setProcessando(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl max-w-lg w-full">
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 dark:bg-green-900/40 rounded-lg">
                <CreditCard className="w-5 h-5 text-green-600 dark:text-green-400" />
              </div>
              <h3 className="text-lg font-bold text-gray-800 dark:text-white">
                Registrar Pagamento
              </h3>
            </div>
            <button onClick={onClose} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">
              <span className="text-xl">&times;</span>
            </button>
          </div>
        </div>

        <div className="p-6 space-y-5">
          {/* Resumo do boleto */}
          <div className="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-4 space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-500 dark:text-gray-400">Documento</span>
              <span className="font-medium text-gray-800 dark:text-white">{boleto.numero_documento}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-500 dark:text-gray-400">Fornecedor</span>
              <span className="font-medium text-gray-800 dark:text-white">{boleto.fornecedor_nome}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-500 dark:text-gray-400">Vencimento</span>
              <span className={`font-medium ${boleto.dias_vencimento < 0 ? 'text-red-600 dark:text-red-400' : 'text-gray-800 dark:text-white'}`}>
                {formatDate(boleto.data_vencimento)}
                {boleto.dias_vencimento < 0 && ` (${Math.abs(boleto.dias_vencimento)}d atrasado)`}
              </span>
            </div>
            <div className="flex justify-between text-sm border-t border-gray-200 dark:border-gray-600 pt-2 mt-2">
              <span className="text-gray-500 dark:text-gray-400 font-medium">Valor</span>
              <span className="font-bold text-lg text-blue-600 dark:text-blue-400">{formatCurrency(boleto.valor_atual)}</span>
            </div>
          </div>

          {/* Formulario de pagamento */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                Valor Pago (R$)
              </label>
              <input
                type="number"
                step="0.01"
                value={valorPago}
                onChange={(e) => setValorPago(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-green-500 dark:bg-gray-700 dark:text-white text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                Data do Pagamento
              </label>
              <input
                type="date"
                value={dataPagamento}
                onChange={(e) => setDataPagamento(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-green-500 dark:bg-gray-700 dark:text-white text-sm"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
              Forma de Pagamento
            </label>
            <div className="grid grid-cols-3 gap-2">
              {[
                { value: 'pix', label: 'PIX' },
                { value: 'transferencia', label: 'Transf.' },
                { value: 'boleto', label: 'Boleto' },
                { value: 'dinheiro', label: 'Dinheiro' },
                { value: 'cartao_debito', label: 'Debito' },
                { value: 'cheque', label: 'Cheque' },
              ].map(({ value, label }) => (
                <button
                  key={value}
                  onClick={() => setFormaPagamento(value)}
                  className={`px-3 py-2 rounded-lg text-sm font-medium border transition-all ${
                    formaPagamento === value
                      ? 'bg-green-600 text-white border-green-600 shadow-md'
                      : 'bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-600'
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
              Observacoes (opcional)
            </label>
            <textarea
              value={observacoes}
              onChange={(e) => setObservacoes(e.target.value)}
              rows={2}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-green-500 dark:bg-gray-700 dark:text-white text-sm resize-none"
              placeholder="Comprovante, numero da transacao..."
            />
          </div>
        </div>

        <div className="p-6 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-3">
          <button
            onClick={onClose}
            disabled={processando}
            className="px-5 py-2.5 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors text-sm font-medium"
          >
            Cancelar
          </button>
          <button
            onClick={handlePagar}
            disabled={processando || !valorPago || parseFloat(valorPago) <= 0}
            className="px-5 py-2.5 bg-green-600 text-white hover:bg-green-700 rounded-lg transition-colors flex items-center gap-2 text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed shadow-md"
          >
            {processando ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Processando...
              </>
            ) : (
              <>
                <CheckCircle className="w-4 h-4" />
                Confirmar Pagamento
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default BoletosAVencerPanel;