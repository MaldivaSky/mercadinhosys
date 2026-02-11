// src/features/products/components/PurchaseOrderModal.tsx
import React, { useState, useEffect } from 'react';
import { X, Trash2, Package, Save } from 'lucide-react';
import { Fornecedor, Produto } from '../../../types';
import { CreatePedidoData, purchaseOrderService } from '../purchaseOrderService';
import { apiClient } from '../../../api/apiClient';
import { formatCurrency } from '../../../utils/formatters';
import toast from 'react-hot-toast';

interface PurchaseOrderModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  fornecedores: Fornecedor[];
  initialProduct?: Produto | null;
  initialSupplierId?: number;
}

interface ItemPedido {
  produto_id: number;
  produto_nome: string;
  quantidade: number;
  preco_unitario: number;
  desconto_percentual: number;
  total_item: number;
}

const PurchaseOrderModal: React.FC<PurchaseOrderModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
  fornecedores,
  initialProduct,
  initialSupplierId
}) => {
  const [loading, setLoading] = useState(false);
  const [produtos, setProdutos] = useState<Produto[]>([]);
  const [searchProduto, setSearchProduto] = useState('');

  // Form data
  const [formData, setFormData] = useState({
    fornecedor_id: 0,
    condicao_pagamento: '',
    observacoes: '',
    desconto: 0,
    frete: 0
  });

  const [itens, setItens] = useState<ItemPedido[]>([]);

  // Initialize with initial data if provided
  useEffect(() => {
    if (isOpen) {
      if (initialSupplierId) {
        setFormData(prev => ({ ...prev, fornecedor_id: initialSupplierId }));
      }

      if (initialProduct) {
        const novoItem: ItemPedido = {
          produto_id: initialProduct.id,
          produto_nome: initialProduct.nome,
          quantidade: initialProduct.quantidade_minima > initialProduct.quantidade
            ? (initialProduct.quantidade_minima - initialProduct.quantidade) + 10 // Suggest buying enough to exceed min + buffer
            : 10, // Default quantity
          preco_unitario: initialProduct.preco_custo,
          desconto_percentual: 0,
          total_item: initialProduct.preco_custo * (initialProduct.quantidade_minima > initialProduct.quantidade
            ? (initialProduct.quantidade_minima - initialProduct.quantidade) + 10
            : 10)
        };
        setItens([novoItem]);
      } else {
        // Reset if no initial product
        setItens([]);
        setFormData(prev => ({ ...prev, fornecedor_id: 0 }));
      }
    }
  }, [isOpen, initialProduct, initialSupplierId]);

  // Buscar produtos
  useEffect(() => {
    if (searchProduto.length >= 2) {
      const timer = setTimeout(async () => {
        try {
          const response = await apiClient.get<{ produtos: Produto[] }>('/produtos/', {
            params: {
              busca: searchProduto,
              per_page: 20,
              ativos: true
            }
          });
          setProdutos(response.data.produtos);
        } catch (error) {
          console.error('Erro ao buscar produtos:', error);
        }
      }, 300);

      return () => clearTimeout(timer);
    } else {
      setProdutos([]);
    }
  }, [searchProduto]);

  // Calcular totais
  const subtotal = itens.reduce((sum, item) => sum + item.total_item, 0);
  const total = subtotal - formData.desconto + formData.frete;

  const handleAddItem = (produto: Produto) => {
    const itemExistente = itens.find(item => item.produto_id === produto.id);

    if (itemExistente) {
      setItens(itens.map(item =>
        item.produto_id === produto.id
          ? { ...item, quantidade: item.quantidade + 1, total_item: (item.quantidade + 1) * item.preco_unitario * (1 - item.desconto_percentual / 100) }
          : item
      ));
    } else {
      const novoItem: ItemPedido = {
        produto_id: produto.id,
        produto_nome: produto.nome,
        quantidade: 1,
        preco_unitario: produto.preco_custo,
        desconto_percentual: 0,
        total_item: produto.preco_custo
      };
      setItens([...itens, novoItem]);
    }

    setSearchProduto('');
    setProdutos([]);
  };

  const handleUpdateItem = (index: number, field: keyof ItemPedido, value: number) => {
    const novosItens = [...itens];
    novosItens[index] = { ...novosItens[index], [field]: value };

    // Recalcular total do item
    if (field === 'quantidade' || field === 'preco_unitario' || field === 'desconto_percentual') {
      const item = novosItens[index];
      item.total_item = item.quantidade * item.preco_unitario * (1 - item.desconto_percentual / 100);
    }

    setItens(novosItens);
  };

  const handleRemoveItem = (index: number) => {
    setItens(itens.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.fornecedor_id) {
      toast.error('Selecione um fornecedor');
      return;
    }

    if (itens.length === 0) {
      toast.error('Adicione pelo menos um item ao pedido');
      return;
    }

    setLoading(true);

    try {
      const pedidoData: CreatePedidoData = {
        fornecedor_id: formData.fornecedor_id,
        condicao_pagamento: formData.condicao_pagamento,
        observacoes: formData.observacoes,
        desconto: formData.desconto,
        frete: formData.frete,
        itens: itens.map(item => ({
          produto_id: item.produto_id,
          quantidade: item.quantidade,
          preco_unitario: item.preco_unitario,
          desconto_percentual: item.desconto_percentual
        }))
      };

      await purchaseOrderService.criarPedido(pedidoData);
      toast.success('Pedido de compra criado com sucesso!');
      onSuccess();
      handleClose();
    } catch (error: any) {
      console.error('Erro ao criar pedido:', error);
      toast.error(error.response?.data?.error || 'Erro ao criar pedido');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setFormData({
      fornecedor_id: 0,
      condicao_pagamento: '',
      observacoes: '',
      desconto: 0,
      frete: 0
    });
    setItens([]);
    setSearchProduto('');
    setProdutos([]);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-6xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-3">
            <Package className="w-6 h-6 text-blue-600" />
            <h2 className="text-xl font-bold text-gray-800 dark:text-white">
              Novo Pedido de Compra
            </h2>
          </div>
          <button
            onClick={handleClose}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col h-full">
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {/* Informações do Pedido */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Fornecedor *
                </label>
                <select
                  value={formData.fornecedor_id}
                  onChange={(e) => setFormData(prev => ({ ...prev, fornecedor_id: parseInt(e.target.value) }))}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  required
                >
                  <option value={0}>Selecione um fornecedor</option>
                  {fornecedores.map(fornecedor => (
                    <option key={fornecedor.id} value={fornecedor.id}>
                      {fornecedor.nome_fantasia}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Condição de Pagamento
                </label>
                <input
                  type="text"
                  value={formData.condicao_pagamento}
                  onChange={(e) => setFormData(prev => ({ ...prev, condicao_pagamento: e.target.value }))}
                  placeholder="Ex: 30 dias"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                />
              </div>
            </div>

            {/* Busca de Produtos */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Adicionar Produtos
              </label>
              <div className="relative">
                <input
                  type="text"
                  value={searchProduto}
                  onChange={(e) => setSearchProduto(e.target.value)}
                  placeholder="Digite o nome do produto para buscar..."
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                />

                {produtos.length > 0 && (
                  <div className="absolute top-full left-0 right-0 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg mt-1 max-h-60 overflow-y-auto z-10">
                    {produtos.map(produto => (
                      <button
                        key={produto.id}
                        type="button"
                        onClick={() => handleAddItem(produto)}
                        className="w-full px-4 py-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700 border-b border-gray-200 dark:border-gray-600 last:border-b-0"
                      >
                        <div className="font-medium text-gray-800 dark:text-white">{produto.nome}</div>
                        <div className="text-sm text-gray-600 dark:text-gray-400">
                          Custo: {formatCurrency(produto.preco_custo)} | Estoque: {produto.quantidade}
                        </div>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Lista de Itens */}
            {itens.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold text-gray-800 dark:text-white mb-4">
                  Itens do Pedido ({itens.length})
                </h3>

                <div className="overflow-x-auto">
                  <table className="w-full border border-gray-200 dark:border-gray-700 rounded-lg">
                    <thead className="bg-gray-50 dark:bg-gray-700">
                      <tr>
                        <th className="px-4 py-3 text-left text-sm font-medium text-gray-700 dark:text-gray-300">Produto</th>
                        <th className="px-4 py-3 text-center text-sm font-medium text-gray-700 dark:text-gray-300">Qtd</th>
                        <th className="px-4 py-3 text-center text-sm font-medium text-gray-700 dark:text-gray-300">Preço Unit.</th>
                        <th className="px-4 py-3 text-center text-sm font-medium text-gray-700 dark:text-gray-300">Desc. %</th>
                        <th className="px-4 py-3 text-center text-sm font-medium text-gray-700 dark:text-gray-300">Total</th>
                        <th className="px-4 py-3 text-center text-sm font-medium text-gray-700 dark:text-gray-300">Ações</th>
                      </tr>
                    </thead>
                    <tbody>
                      {itens.map((item, index) => (
                        <tr key={index} className="border-t border-gray-200 dark:border-gray-700">
                          <td className="px-4 py-3 text-sm text-gray-800 dark:text-white">
                            {item.produto_nome}
                          </td>
                          <td className="px-4 py-3">
                            <input
                              type="number"
                              min="1"
                              value={item.quantidade}
                              onChange={(e) => handleUpdateItem(index, 'quantidade', parseInt(e.target.value) || 1)}
                              className="w-20 px-2 py-1 text-center border border-gray-300 dark:border-gray-600 rounded focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                            />
                          </td>
                          <td className="px-4 py-3">
                            <input
                              type="number"
                              step="0.01"
                              min="0"
                              value={item.preco_unitario}
                              onChange={(e) => handleUpdateItem(index, 'preco_unitario', parseFloat(e.target.value) || 0)}
                              className="w-24 px-2 py-1 text-center border border-gray-300 dark:border-gray-600 rounded focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                            />
                          </td>
                          <td className="px-4 py-3">
                            <input
                              type="number"
                              step="0.01"
                              min="0"
                              max="100"
                              value={item.desconto_percentual}
                              onChange={(e) => handleUpdateItem(index, 'desconto_percentual', parseFloat(e.target.value) || 0)}
                              className="w-20 px-2 py-1 text-center border border-gray-300 dark:border-gray-600 rounded focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                            />
                          </td>
                          <td className="px-4 py-3 text-center text-sm font-medium text-gray-800 dark:text-white">
                            {formatCurrency(item.total_item)}
                          </td>
                          <td className="px-4 py-3 text-center">
                            <button
                              type="button"
                              onClick={() => handleRemoveItem(index)}
                              className="p-1 text-red-600 hover:bg-red-50 dark:hover:bg-red-900 rounded transition-colors"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Totais e Observações */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Observações
                </label>
                <textarea
                  value={formData.observacoes}
                  onChange={(e) => setFormData(prev => ({ ...prev, observacoes: e.target.value }))}
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  placeholder="Observações sobre o pedido..."
                />
              </div>

              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Subtotal:</span>
                  <span className="text-lg font-semibold text-gray-800 dark:text-white">
                    {formatCurrency(subtotal)}
                  </span>
                </div>

                <div className="flex justify-between items-center">
                  <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Desconto:</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={formData.desconto}
                    onChange={(e) => setFormData(prev => ({ ...prev, desconto: parseFloat(e.target.value) || 0 }))}
                    className="w-24 px-2 py-1 text-right border border-gray-300 dark:border-gray-600 rounded focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  />
                </div>

                <div className="flex justify-between items-center">
                  <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Frete:</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={formData.frete}
                    onChange={(e) => setFormData(prev => ({ ...prev, frete: parseFloat(e.target.value) || 0 }))}
                    className="w-24 px-2 py-1 text-right border border-gray-300 dark:border-gray-600 rounded focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  />
                </div>

                <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
                  <div className="flex justify-between items-center">
                    <span className="text-lg font-bold text-gray-800 dark:text-white">Total:</span>
                    <span className="text-xl font-bold text-blue-600 dark:text-blue-400">
                      {formatCurrency(total)}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="flex justify-end gap-3 p-6 border-t border-gray-200 dark:border-gray-700">
            <button
              type="button"
              onClick={handleClose}
              className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={loading || itens.length === 0}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 transition-colors"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Criando...
                </>
              ) : (
                <>
                  <Save className="w-4 h-4" />
                  Criar Pedido
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default PurchaseOrderModal;