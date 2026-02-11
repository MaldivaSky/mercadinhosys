// src/features/products/components/ReceivePurchaseModal.tsx
import React, { useState, useEffect } from 'react';
import { X, Package, FileText, Calendar, DollarSign, CheckCircle, AlertCircle, ChevronDown } from 'lucide-react';
import { PedidoCompra, ReceberPedidoData, purchaseOrderService } from '../purchaseOrderService';
import { formatCurrency, formatDate } from '../../../utils/formatters';
import toast from 'react-hot-toast';

interface ReceivePurchaseModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  pedido: PedidoCompra;
}

interface ItemRecebimento {
  item_id: number;
  produto_nome: string;
  quantidade_solicitada: number;
  quantidade_recebida: number;
  preco_unitario: number;
  data_validade: string;  // NOVO
  numero_lote: string;    // NOVO
}

const ReceivePurchaseModal: React.FC<ReceivePurchaseModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
  pedido
}) => {
  const [loading, setLoading] = useState(false);
  const [pedidoDetalhado, setPedidoDetalhado] = useState<PedidoCompra | null>(null);
  const [loadingDetails, setLoadingDetails] = useState(false);
  const [expandedSections, setExpandedSections] = useState({
    notaFiscal: false,
    boleto: true
  });
  const [compactMode, setCompactMode] = useState(true);
  
  // Form data
  const [formData, setFormData] = useState({
    numero_nota_fiscal: '',
    serie_nota_fiscal: '',
    gerar_boleto: true,
    data_vencimento: '',
    numero_documento: ''
  });
  
  const [itensRecebimento, setItensRecebimento] = useState<ItemRecebimento[]>([]);
  
  // Carregar detalhes do pedido
  useEffect(() => {
    if (isOpen && pedido) {
      loadPedidoDetails();
    }
  }, [isOpen, pedido]);
  
  const loadPedidoDetails = async () => {
    setLoadingDetails(true);
    try {
      const detalhes = await purchaseOrderService.obterPedido(pedido.id);
      setPedidoDetalhado(detalhes);
      
      // Inicializar itens de recebimento
      if (detalhes.itens) {
        // Calcular data de validade padrão (1 ano a partir de hoje)
        const dataValidadePadrao = new Date();
        dataValidadePadrao.setFullYear(dataValidadePadrao.getFullYear() + 1);
        
        const itens = detalhes.itens.map((item, index) => ({
          item_id: item.id!,
          produto_nome: item.produto_nome,
          quantidade_solicitada: item.quantidade_solicitada,
          quantidade_recebida: item.quantidade_solicitada, // Por padrão, receber tudo
          preco_unitario: item.preco_unitario,
          data_validade: dataValidadePadrao.toISOString().split('T')[0],  // NOVO
          numero_lote: `LOTE-${detalhes.numero_pedido}-${index + 1}`  // NOVO
        }));
        setItensRecebimento(itens);
      }
      
      // Configurar dados padrão do boleto
      const dataVencimento = new Date();
      dataVencimento.setDate(dataVencimento.getDate() + 30); // 30 dias por padrão
      
      setFormData(prev => ({
        ...prev,
        data_vencimento: dataVencimento.toISOString().split('T')[0],
        numero_documento: `BOL-${detalhes.numero_pedido}`
      }));
      
    } catch (error) {
      console.error('Erro ao carregar detalhes do pedido:', error);
      toast.error('Erro ao carregar detalhes do pedido');
    } finally {
      setLoadingDetails(false);
    }
  };
  
  const handleQuantidadeChange = (index: number, quantidade: number) => {
    const novosItens = [...itensRecebimento];
    novosItens[index].quantidade_recebida = Math.max(0, quantidade);
    setItensRecebimento(novosItens);
  };
  
  const handleDataValidadeChange = (index: number, data: string) => {
    const novosItens = [...itensRecebimento];
    novosItens[index].data_validade = data;
    setItensRecebimento(novosItens);
  };
  
  const handleNumeroLoteChange = (index: number, lote: string) => {
    const novosItens = [...itensRecebimento];
    novosItens[index].numero_lote = lote;
    setItensRecebimento(novosItens);
  };
  
  const handleReceberTudo = () => {
    const novosItens = itensRecebimento.map(item => ({
      ...item,
      quantidade_recebida: item.quantidade_solicitada
    }));
    setItensRecebimento(novosItens);
  };
  
  const handleLimparTudo = () => {
    const novosItens = itensRecebimento.map(item => ({
      ...item,
      quantidade_recebida: 0
    }));
    setItensRecebimento(novosItens);
  };
  
  const calcularTotalRecebido = () => {
    return itensRecebimento.reduce((total, item) => {
      return total + (item.quantidade_recebida * item.preco_unitario);
    }, 0);
  };
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    const itensComRecebimento = itensRecebimento.filter(item => item.quantidade_recebida > 0);
    
    if (itensComRecebimento.length === 0) {
      toast.error('Informe a quantidade recebida para pelo menos um item');
      return;
    }
    
    if (formData.gerar_boleto && !formData.data_vencimento) {
      toast.error('Informe a data de vencimento do boleto');
      return;
    }
    
    setLoading(true);
    
    try {
      const dadosRecebimento: ReceberPedidoData = {
        pedido_id: pedido.id,
        numero_nota_fiscal: formData.numero_nota_fiscal,
        serie_nota_fiscal: formData.serie_nota_fiscal,
        gerar_boleto: formData.gerar_boleto,
        data_vencimento: formData.gerar_boleto ? formData.data_vencimento : undefined,
        numero_documento: formData.gerar_boleto ? formData.numero_documento : undefined,
        itens: itensComRecebimento.map(item => ({
          item_id: item.item_id,
          quantidade_recebida: item.quantidade_recebida,
          data_validade: item.data_validade,  // NOVO
          numero_lote: item.numero_lote       // NOVO
        }))
      };
      
      await purchaseOrderService.receberPedido(dadosRecebimento);
      
      // Feedback visual detalhado
      const totalRecebido = itensComRecebimento.reduce((sum, item) => sum + item.quantidade_recebida, 0);
      const totalValor = calcularTotalRecebido();
      
      toast.success(
        `✅ Pedido Recebido!\n📦 ${totalRecebido} unidades\n💰 R$ ${totalValor.toFixed(2)}\n📊 Estoque Ajustado${formData.gerar_boleto ? '\n📄 Boleto Gerado' : ''}`,
        {
          duration: 4000,
          icon: '✅'
        }
      );
      
      // Aguardar um pouco para o usuário ver o feedback
      setTimeout(() => {
        onSuccess();
        onClose();
      }, 1500);
      
    } catch (error: any) {
      console.error('Erro ao receber pedido:', error);
      toast.error(error.response?.data?.error || 'Erro ao receber pedido');
    } finally {
      setLoading(false);
    }
  };
  
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-2 sm:p-4">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-4xl max-h-[95vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 sm:p-6 border-b border-gray-200 dark:border-gray-700 bg-gradient-to-r from-green-50 to-green-100 dark:from-green-900 dark:to-green-800">
          <div className="flex items-center gap-2 sm:gap-3 min-w-0">
            <Package className="w-5 h-5 sm:w-6 sm:h-6 text-green-600 dark:text-green-300 flex-shrink-0" />
            <div className="min-w-0">
              <h2 className="text-lg sm:text-xl font-bold text-gray-800 dark:text-white truncate">
                Receber Pedido
              </h2>
              <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400 truncate">
                {pedido.numero_pedido} - {pedido.fornecedor_nome}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-green-200 dark:hover:bg-green-700 rounded-lg transition-colors flex-shrink-0"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        
        {loadingDetails ? (
          <div className="flex items-center justify-center py-12">
            <div className="w-8 h-8 border-4 border-green-600 border-t-transparent rounded-full animate-spin"></div>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="flex flex-col h-full">
            <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4 sm:space-y-6">
              {/* Informações do Pedido */}
              <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-3 sm:p-4">
                <h3 className="text-base font-semibold text-gray-800 dark:text-white mb-2 sm:mb-3">
                  Informações do Pedido
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 sm:gap-4 text-xs sm:text-sm">
                  <div>
                    <span className="text-gray-600 dark:text-gray-400">Data do Pedido:</span>
                    <div className="font-medium text-gray-800 dark:text-white">
                      {formatDate(pedido.data_pedido)}
                    </div>
                  </div>
                  <div>
                    <span className="text-gray-600 dark:text-gray-400">Previsão de Entrega:</span>
                    <div className="font-medium text-gray-800 dark:text-white">
                      {pedido.data_previsao_entrega ? formatDate(pedido.data_previsao_entrega) : 'Não informado'}
                    </div>
                  </div>
                  <div>
                    <span className="text-gray-600 dark:text-gray-400">Total do Pedido:</span>
                    <div className="font-medium text-green-600 dark:text-green-400">
                      {formatCurrency(pedido.total)}
                    </div>
                  </div>
                </div>
              </div>
              
              {/* Itens para Recebimento */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-base font-semibold text-gray-800 dark:text-white">
                    Itens para Recebimento
                  </h3>
                  <div className="flex gap-1">
                    <button
                      type="button"
                      onClick={handleReceberTudo}
                      className="px-2 py-1 bg-green-600 text-white rounded text-xs hover:bg-green-700 transition-colors"
                    >
                      Receber Tudo
                    </button>
                    <button
                      type="button"
                      onClick={handleLimparTudo}
                      className="px-2 py-1 bg-gray-600 text-white rounded text-xs hover:bg-gray-700 transition-colors"
                    >
                      Limpar
                    </button>
                  </div>
                </div>
                
                <div className="overflow-x-auto -mx-6 px-6">
                  <table className="w-full text-sm border border-gray-200 dark:border-gray-700 rounded-lg">
                    <thead className="bg-gray-50 dark:bg-gray-700">
                      <tr>
                        <th className="px-2 py-2 text-left font-medium text-gray-700 dark:text-gray-300 text-xs">Produto</th>
                        <th className="px-2 py-2 text-center font-medium text-gray-700 dark:text-gray-300 text-xs">Sol.</th>
                        <th className="px-2 py-2 text-center font-medium text-gray-700 dark:text-gray-300 text-xs">Rec.</th>
                        <th className="px-2 py-2 text-center font-medium text-gray-700 dark:text-gray-300 text-xs">Preço</th>
                        <th className="px-2 py-2 text-center font-medium text-gray-700 dark:text-gray-300 text-xs">Validade</th>
                        <th className="px-2 py-2 text-center font-medium text-gray-700 dark:text-gray-300 text-xs">Lote</th>
                        <th className="px-2 py-2 text-center font-medium text-gray-700 dark:text-gray-300 text-xs">Total</th>
                      </tr>
                    </thead>
                    <tbody>
                      {itensRecebimento.map((item, index) => (
                        <tr key={index} className="border-t border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700">
                          <td className="px-2 py-2 text-gray-800 dark:text-white truncate">
                            {item.produto_nome}
                          </td>
                          <td className="px-2 py-2 text-center text-gray-600 dark:text-gray-400">
                            {item.quantidade_solicitada}
                          </td>
                          <td className="px-2 py-2">
                            <input
                              type="number"
                              min="0"
                              max={item.quantidade_solicitada}
                              value={item.quantidade_recebida}
                              onChange={(e) => handleQuantidadeChange(index, parseInt(e.target.value) || 0)}
                              className="w-16 px-1 py-1 text-center text-sm border border-gray-300 dark:border-gray-600 rounded focus:ring-2 focus:ring-green-500 dark:bg-gray-700 dark:text-white"
                            />
                          </td>
                          <td className="px-2 py-2 text-center text-gray-600 dark:text-gray-400 text-xs">
                            {formatCurrency(item.preco_unitario)}
                          </td>
                          <td className="px-2 py-2">
                            <input
                              type="date"
                              value={item.data_validade}
                              onChange={(e) => handleDataValidadeChange(index, e.target.value)}
                              className="w-28 px-1 py-1 text-center text-xs border border-gray-300 dark:border-gray-600 rounded focus:ring-2 focus:ring-green-500 dark:bg-gray-700 dark:text-white"
                            />
                          </td>
                          <td className="px-2 py-2">
                            <input
                              type="text"
                              value={item.numero_lote}
                              onChange={(e) => handleNumeroLoteChange(index, e.target.value)}
                              className="w-24 px-1 py-1 text-center text-xs border border-gray-300 dark:border-gray-600 rounded focus:ring-2 focus:ring-green-500 dark:bg-gray-700 dark:text-white"
                              placeholder="LOTE"
                            />
                          </td>
                          <td className="px-2 py-2 text-center text-xs font-medium text-gray-800 dark:text-white">
                            {formatCurrency(item.quantidade_recebida * item.preco_unitario)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                
                <div className="mt-3 flex justify-end">
                  <div className="text-sm font-semibold text-gray-800 dark:text-white">
                    Total: <span className="text-green-600 dark:text-green-400">
                      {formatCurrency(calcularTotalRecebido())}
                    </span>
                  </div>
                </div>
              </div>
              
              {/* Informações da Nota Fiscal */}
              <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
                <button
                  type="button"
                  onClick={() => setExpandedSections(prev => ({ ...prev, notaFiscal: !prev.notaFiscal }))}
                  className="flex items-center justify-between w-full mb-3 text-base font-semibold text-gray-800 dark:text-white hover:text-green-600 dark:hover:text-green-400 transition-colors"
                >
                  <span className="flex items-center gap-2">
                    <FileText className="w-4 h-4" />
                    Nota Fiscal (Opcional)
                  </span>
                  <ChevronDown className={`w-4 h-4 transition-transform ${expandedSections.notaFiscal ? 'rotate-180' : ''}`} />
                </button>
                
                {expandedSections.notaFiscal && (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pl-6">
                    <div>
                      <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Número da NF
                      </label>
                      <input
                        type="text"
                        value={formData.numero_nota_fiscal}
                        onChange={(e) => setFormData(prev => ({ ...prev, numero_nota_fiscal: e.target.value }))}
                        className="w-full px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded focus:ring-2 focus:ring-green-500 dark:bg-gray-700 dark:text-white"
                        placeholder="Ex: 123456"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Série
                      </label>
                      <input
                        type="text"
                        value={formData.serie_nota_fiscal}
                        onChange={(e) => setFormData(prev => ({ ...prev, serie_nota_fiscal: e.target.value }))}
                        className="w-full px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded focus:ring-2 focus:ring-green-500 dark:bg-gray-700 dark:text-white"
                        placeholder="Ex: 1"
                      />
                    </div>
                  </div>
                )}
              </div>
              
              {/* Geração de Boleto */}
              <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
                <button
                  type="button"
                  onClick={() => setExpandedSections(prev => ({ ...prev, boleto: !prev.boleto }))}
                  className="flex items-center justify-between w-full mb-3 text-base font-semibold text-gray-800 dark:text-white hover:text-green-600 dark:hover:text-green-400 transition-colors"
                >
                  <span className="flex items-center gap-2">
                    <DollarSign className="w-4 h-4" />
                    Gerar Boleto para Pagamento
                  </span>
                  <ChevronDown className={`w-4 h-4 transition-transform ${expandedSections.boleto ? 'rotate-180' : ''}`} />
                </button>
                
                {expandedSections.boleto && (
                  <div className="pl-6 space-y-3">
                    <div className="flex items-center gap-3 mb-3">
                      <input
                        type="checkbox"
                        id="gerar_boleto"
                        checked={formData.gerar_boleto}
                        onChange={(e) => setFormData(prev => ({ ...prev, gerar_boleto: e.target.checked }))}
                        className="w-4 h-4 text-green-600 border-gray-300 rounded focus:ring-green-500"
                      />
                      <label htmlFor="gerar_boleto" className="text-sm font-medium text-gray-700 dark:text-gray-300">
                        Sim, gerar boleto
                      </label>
                    </div>
                    
                    {formData.gerar_boleto && (
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        <div>
                          <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                            Data de Vencimento *
                          </label>
                          <input
                            type="date"
                            value={formData.data_vencimento}
                            onChange={(e) => setFormData(prev => ({ ...prev, data_vencimento: e.target.value }))}
                            className="w-full px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded focus:ring-2 focus:ring-green-500 dark:bg-gray-700 dark:text-white"
                            required={formData.gerar_boleto}
                          />
                        </div>
                        
                        <div>
                          <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                            Número do Documento
                          </label>
                          <input
                            type="text"
                            value={formData.numero_documento}
                            onChange={(e) => setFormData(prev => ({ ...prev, numero_documento: e.target.value }))}
                            className="w-full px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded focus:ring-2 focus:ring-green-500 dark:bg-gray-700 dark:text-white"
                            placeholder="Ex: BOL-PC000001"
                          />
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
            
            {/* Footer */}
            <div className="flex justify-end gap-2 sm:gap-3 p-4 sm:p-6 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700">
              <button
                type="button"
                onClick={onClose}
                className="px-3 sm:px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600 rounded-lg transition-colors"
              >
                Cancelar
              </button>
              <button
                type="submit"
                disabled={loading || itensRecebimento.every(item => item.quantidade_recebida === 0)}
                className="px-4 sm:px-6 py-2 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 transition-colors"
              >
                {loading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Processando...
                  </>
                ) : (
                  <>
                    <CheckCircle className="w-4 h-4" />
                    Confirmar
                  </>
                )}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};

export default ReceivePurchaseModal;