import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Plus, Search, Filter, Download,
  X, ChevronDown, RefreshCw, Calculator,
  ShoppingCart, AlertTriangle,
} from 'lucide-react';
import { Fornecedor, Produto, ProdutoFiltros } from '../../types';
import { productsService } from './productsService';
import { formatCurrency } from '../../utils/formatters';
import { apiClient } from '../../api/apiClient';
import { Toaster, toast } from 'react-hot-toast';
import { useConfig } from '../../contexts/ConfigContext';
import ProductAnalyticsDashboard from './components/ProductAnalyticsDashboard';
import QuickFiltersPanel from './components/QuickFiltersPanel';
import ProductHistoryModal from './components/ProductHistoryModal';
import PurchaseOrdersPanel from './components/PurchaseOrdersPanel';
import PurchaseOrderModal from './components/PurchaseOrderModal';
import { aplicarFiltroRapido, calcularContadoresFiltros } from './utils/quickFilters';

import ProductFormModal from './components/ProductFormModal';
import { ProductsTable } from './components/ProductsTable';

// Product Form Modal Component - Moved to independent file

const ProductsPage: React.FC = () => {
  const [produtos, setProdutos] = useState<Produto[]>([]);
  const [todosProdutos, setTodosProdutos] = useState<Produto[]>([]);
  const [loading, setLoading] = useState(true);
  const [categorias, setCategorias] = useState<string[]>([]);
  const [fornecedores, setFornecedores] = useState<Fornecedor[]>([]);
  const { config } = useConfig();

  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalItems, setTotalItems] = useState(0);

  const [stats, setStats] = useState({
    total_produtos: 0,
    produtos_baixo_estoque: 0,
    produtos_esgotados: 0,
    produtos_normal: 0,
    valor_total_estoque: 0,
    margem_media: 0,
  });

  const [filtros, setFiltros] = useState<ProdutoFiltros>({
    busca: '',
    ativos: true,
    ordenar_por: 'nome',
    direcao: 'asc',
  });
  const [buscaLocal, setBuscaLocal] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [filtroRapido, setFiltroRapido] = useState<string | null>(null);

  const [showProductModal, setShowProductModal] = useState(false);
  const [showStockModal, setShowStockModal] = useState(false);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [showMarkupCalculator, setShowMarkupCalculator] = useState(false);
  const [showProductHistory, setShowProductHistory] = useState(false);
  const [showPurchaseOrders, setShowPurchaseOrders] = useState(false);

  const [selectedProduct, setSelectedProduct] = useState<Produto | null>(null);
  const [selectedProductForOrder, setSelectedProductForOrder] = useState<Produto | null>(null);
  const [editMode, setEditMode] = useState(false);

  const [stockAdjust, setStockAdjust] = useState({
    quantidade: 0,
    operacao: 'entrada' as 'entrada' | 'saida',
    motivo: '',
  });

  const [markupCalc, setMarkupCalc] = useState({
    preco_custo: 0,
    markup: 30,
    preco_venda: 0,
  });

  const [showExpiringProducts, setShowExpiringProducts] = useState(true);

  // Calcular produtos com validade próxima
  const diasAlertaValidade = config?.dias_alerta_validade ?? 30;

  const produtosProximosValidade = useMemo(() => {
    if (!config?.controlar_validade) return [];
    const hoje = new Date();
    hoje.setHours(0, 0, 0, 0);

    return todosProdutos
      .filter(p => p.quantidade > 0 && p.data_validade)
      .map(p => {
        const validade = new Date(p.data_validade!);
        validade.setHours(0, 0, 0, 0);
        const diasRestantes = Math.floor((validade.getTime() - hoje.getTime()) / (1000 * 60 * 60 * 24));
        return { produto: p, diasRestantes };
      })
      .filter(item => item.diasRestantes >= 0 && item.diasRestantes <= diasAlertaValidade)
      .sort((a, b) => a.diasRestantes - b.diasRestantes)
      .slice(0, 10);
  }, [todosProdutos, diasAlertaValidade, config]);

  // Data Loading
  const loadProdutos = useCallback(async () => {
    try {
      setLoading(true);
      const response = await productsService.getAllEstoque(page, 50, filtros);
      setProdutos(response.produtos);
      setTotalPages(response.paginacao.total_paginas);
      setTotalItems(response.paginacao.total_itens);
    } catch (error) {
      console.error('Erro ao carregar produtos:', error);
      toast.error('Erro ao carregar produtos');
    } finally {
      setLoading(false);
    }
  }, [page, filtros]);

  const loadTodosProdutos = useCallback(async () => {
    try {
      const response = await productsService.getAllEstoque(1, 10000, { ativos: true });
      setTodosProdutos(response.produtos);
      const total = response.produtos.length;
      const esgotados = response.produtos.filter(p => p.quantidade <= 0).length;
      const baixo = response.produtos.filter(p => p.quantidade > 0 && p.quantidade <= p.quantidade_minima).length;
      const normal = total - esgotados - baixo;
      const valorTotal = response.produtos.reduce((sum, p) => sum + p.preco_custo * p.quantidade, 0);
      const margemMedia = total > 0 ? response.produtos.reduce((sum, p) => sum + (p.margem_lucro || 0), 0) / total : 0;
      setStats({ total_produtos: total, produtos_esgotados: esgotados, produtos_baixo_estoque: baixo, produtos_normal: normal, valor_total_estoque: valorTotal, margem_media: margemMedia });
    } catch (error) {
      console.error('Erro ao carregar todos os produtos:', error);
    }
  }, []);

  const loadCategorias = useCallback(async () => {
    try {
      const response = await productsService.getCategorias(true);
      setCategorias(response.categorias);
    } catch (error) {
      console.error('Erro ao carregar categorias:', error);
    }
  }, []);

  const loadFornecedores = useCallback(async () => {
    try {
      const response = await apiClient.get<{ fornecedores: Fornecedor[] }>('/fornecedores/', { params: { per_page: 200 } });
      setFornecedores(response.data.fornecedores || []);
    } catch (error) {
      console.error('Erro ao carregar fornecedores:', error);
    }
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => setFiltros(prev => ({ ...prev, busca: buscaLocal })), 500);
    return () => clearTimeout(timer);
  }, [buscaLocal]);

  useEffect(() => { loadProdutos(); }, [loadProdutos]);
  useEffect(() => { loadCategorias(); loadFornecedores(); loadTodosProdutos(); }, []);

  // Handlers
  const handleDelete = async (id: number) => {
    if (!window.confirm('Desativar este produto?')) return;
    try {
      await productsService.delete(id);
      toast.success('Produto desativado!');
      loadProdutos();
      loadTodosProdutos();
    } catch (error) {
      toast.error('Erro ao desativar produto');
    }
  };

  const handleStockAdjust = async () => {
    if (!selectedProduct || !stockAdjust.motivo.trim()) {
      toast.error('Informe o motivo do ajuste');
      return;
    }
    try {
      await productsService.ajustarEstoque(selectedProduct.id, stockAdjust.quantidade, stockAdjust.operacao, stockAdjust.motivo);
      toast.success('Estoque ajustado!');
      setShowStockModal(false);
      loadProdutos();
      loadTodosProdutos();
    } catch (error) {
      toast.error('Erro ao ajustar estoque');
    }
  };

  const handleExportCSV = async () => {
    try {
      const response = await productsService.exportarCSV(true);
      const blob = new Blob([response.csv], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = `produtos_${new Date().toISOString().split('T')[0]}.csv`;
      link.click();
      toast.success(`${response.total_produtos} produtos exportados!`);
    } catch (error) {
      toast.error('Erro ao exportar');
    }
  };

  const openEditModal = (produto: Produto) => {
    setSelectedProduct(produto);
    setEditMode(true);
    setShowProductModal(true);
  };

  const openStockModal = (produto: Produto) => {
    setSelectedProduct(produto);
    setStockAdjust({ quantidade: 0, operacao: 'entrada', motivo: '' });
    setShowStockModal(true);
  };

  const openOrderModal = (produto: Produto) => {
    setSelectedProductForOrder(produto);
    setShowPurchaseOrders(true);
    // Note: We need to pass this state down to PurchaseOrdersPanel -> PurchaseOrderModal
    // Or just open the modal directly if PurchaseOrdersPanel is not the right place.
    // Actually, looking at the code, PurchaseOrdersPanel HAS a PurchaseOrderModal legally.
    // BUT, the implementation plan said to use PurchaseOrderModal directly.
    // Let's check where PurchaseOrderModal is used. It's used at the bottom of ProductsPage if we adding it there.
    // Wait, ProductsPage uses PurchaseOrdersPanel which contains PurchaseOrderModal?
    // Let's check Lines 690: <PurchaseOrdersPanel ... />
    // And Lines 608: <ProductFormModal ... />
    // It seems PurchaseOrderModal IS NOT currently used directly in ProductsPage, only inside PurchaseOrdersPanel?
    // Let's check the file content of ProductsPage again.
    // Line 17: import PurchaseOrdersPanel from './components/PurchaseOrdersPanel';
    // It does NOT import PurchaseOrderModal.
    // I should import PurchaseOrderModal in ProductsPage to use it directly for this feature, 
    // OR create a state in PurchaseOrdersPanel to open it.
    // Direct usage seems easier for "Quick Order".
  };

  const calcularMarkup = () => {
    const precoVenda = markupCalc.preco_custo * (1 + markupCalc.markup / 100);
    setMarkupCalc(prev => ({ ...prev, preco_venda: parseFloat(precoVenda.toFixed(2)) }));
  };

  const handleCardClick = (filterType: string) => {
    if (filterType === 'esgotado') setFiltros(prev => ({ ...prev, estoque_status: 'esgotado' }));
    else if (filterType === 'baixo') setFiltros(prev => ({ ...prev, estoque_status: 'baixo' }));
    else if (filterType === 'normal') setFiltros(prev => ({ ...prev, estoque_status: 'normal' }));
    else setFiltros({ busca: '', ativos: true, ordenar_por: 'nome', direcao: 'asc' });
    setPage(1);
  };

  const produtosFiltrados = useMemo(() => {
    // BUG FIX: When filtering, source from ALL products (todosProdutos) to find items across all pages
    // The table will display the filtered result. Note: Pagination UI might show "Page 1 of 1" correctly if updated,
    // or we might need to handle pagination for the filtered result if it's too large.
    // For now, determining that if a filter is active, we show all matches.
    if (!filtroRapido) return produtos;
    // When filtering, we use valid todosProdutos to ensure we catch everything
    return aplicarFiltroRapido(todosProdutos, filtroRapido, todosProdutos);
  }, [produtos, filtroRapido, todosProdutos]);

  const contadoresFiltros = useMemo(() => calcularContadoresFiltros(todosProdutos, todosProdutos), [todosProdutos]);



  return (
    <div className="space-y-6 p-6">
      <Toaster position="top-right" />

      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-800 dark:text-white">Gestao de Produtos</h1>
          <p className="text-gray-600 dark:text-gray-400">Controle de estoque e catalogo</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button onClick={() => setShowPurchaseOrders(true)} className="px-4 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600 flex items-center gap-2">
            <ShoppingCart className="w-5 h-5" />Pedidos de Compra
          </button>
          <button onClick={() => setShowMarkupCalculator(true)} className="px-4 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 flex items-center gap-2">
            <Calculator className="w-5 h-5" />Markup
          </button>
          <button onClick={handleExportCSV} className="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 flex items-center gap-2">
            <Download className="w-5 h-5" />CSV
          </button>
          <button onClick={() => { setEditMode(false); setSelectedProduct(null); setShowProductModal(true); }} className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 flex items-center gap-2">
            <Plus className="w-5 h-5" />Novo
          </button>
        </div>
      </div>

      {/* Quick Filters */}
      <QuickFiltersPanel activeFilter={filtroRapido} onFilterChange={setFiltroRapido} counts={contadoresFiltros} />

      {/* Produtos com Validade Próxima */}
      {config?.controlar_validade && produtosProximosValidade.length > 0 && (
        <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-xl p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-yellow-600" />
              <h3 className="font-semibold text-yellow-800 dark:text-yellow-200">
                Produtos Próximos da Validade ({produtosProximosValidade.length})
              </h3>
            </div>
            <button onClick={() => setShowExpiringProducts(!showExpiringProducts)} className="text-sm text-yellow-700 dark:text-yellow-300 hover:underline">
              {showExpiringProducts ? 'Ocultar' : 'Mostrar'}
            </button>
          </div>
          {showExpiringProducts && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-3">
              {produtosProximosValidade.map(({ produto, diasRestantes }) => (
                <div key={produto.id} className="bg-white dark:bg-gray-800 rounded-lg p-3 border border-yellow-200 dark:border-yellow-700">
                  <p className="font-medium text-gray-900 dark:text-white truncate text-sm">{produto.nome}</p>
                  <div className="flex items-center justify-between mt-2">
                    <span className="text-xs text-gray-500">Qtd: {produto.quantidade}</span>
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${diasRestantes <= 7 ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'
                      }`}>
                      {diasRestantes === 0 ? 'Vence hoje' : diasRestantes === 1 ? '1 dia' : `${diasRestantes} dias`}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Dashboard */}
      <ProductAnalyticsDashboard produtos={todosProdutos} stats={stats} onCardClick={handleCardClick} />

      {/* Search and Filters */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input type="text" value={buscaLocal} onChange={(e) => setBuscaLocal(e.target.value)} placeholder="Buscar produto..." className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg" />
          </div>
          <button onClick={() => setShowFilters(!showFilters)} className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg flex items-center gap-2">
            <Filter className="w-5 h-5" />Filtros<ChevronDown className={`w-4 h-4 transition-transform ${showFilters ? 'rotate-180' : ''}`} />
          </button>
          <button onClick={loadProdutos} className="px-4 py-2 bg-blue-500 text-white rounded-lg flex items-center gap-2">
            <RefreshCw className="w-5 h-5" />Atualizar
          </button>
        </div>

        {showFilters && (
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4 mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
            <div>
              <label className="block text-sm font-medium mb-1">Categoria</label>
              <select value={filtros.categoria || ''} onChange={(e) => { setFiltros(prev => ({ ...prev, categoria: e.target.value || undefined })); setPage(1); }} className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white">
                <option value="">Todas</option>
                {categorias.map(cat => <option key={cat} value={cat}>{cat}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Fornecedor</label>
              <select value={filtros.fornecedor_id || ''} onChange={(e) => { setFiltros(prev => ({ ...prev, fornecedor_id: e.target.value ? parseInt(e.target.value) : undefined })); setPage(1); }} className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white">
                <option value="">Todos</option>
                {fornecedores.map(f => <option key={f.id} value={f.id}>{f.nome_fantasia}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Status Estoque</label>
              <select value={filtros.estoque_status || ''} onChange={(e) => { setFiltros(prev => ({ ...prev, estoque_status: (e.target.value || undefined) as 'baixo' | 'esgotado' | 'normal' | undefined })); setPage(1); }} className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white">
                <option value="">Todos</option>
                <option value="normal">Normal</option>
                <option value="baixo">Baixo</option>
                <option value="esgotado">Esgotado</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Tipo</label>
              <select value={filtros.tipo || ''} onChange={(e) => { setFiltros(prev => ({ ...prev, tipo: e.target.value || undefined })); setPage(1); }} className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white">
                <option value="">Todos</option>
                <option value="Higiene">Higiene</option>
                <option value="Limpeza">Limpeza</option>
                <option value="Alimentos">Alimentos</option>
                <option value="Bebidas">Bebidas</option>
                <option value="Hortifruti">Hortifruti</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Ordenar por</label>
              <select value={filtros.ordenar_por || 'nome'} onChange={(e) => setFiltros(prev => ({ ...prev, ordenar_por: e.target.value }))} className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white">
                <option value="nome">Nome</option>
                <option value="quantidade">Quantidade</option>
                <option value="preco_venda">Preco</option>
                <option value="margem_lucro">Margem</option>
                <option value="data_validade">Validade</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Direcao</label>
              <select value={filtros.direcao || 'asc'} onChange={(e) => setFiltros(prev => ({ ...prev, direcao: e.target.value as 'asc' | 'desc' }))} className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white">
                <option value="asc">Crescente</option>
                <option value="desc">Decrescente</option>
              </select>
            </div>
          </div>
        )}
      </div>

      {/* Products Table */}
      {/* Products Table */}
      <ProductsTable
        produtos={produtosFiltrados}
        loading={loading}
        totalItems={totalItems}
        page={page}
        totalPages={totalPages}
        onPageChange={setPage}
        onEdit={openEditModal}
        onDelete={handleDelete}
        onStockAdjust={openStockModal}
        onHistory={(p) => { setSelectedProduct(p); setShowProductHistory(true); }}
        onMakeOrder={openOrderModal}
      />

      {/* Product Modal */}
      <ProductFormModal
        show={showProductModal}
        editMode={editMode}
        produto={selectedProduct}
        categorias={categorias}
        fornecedores={fornecedores}
        onClose={() => { setShowProductModal(false); setSelectedProduct(null); setEditMode(false); }}
        onSuccess={() => { setShowProductModal(false); loadProdutos(); loadTodosProdutos(); }}
      />

      {/* Stock Adjustment Modal */}
      {showStockModal && selectedProduct && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-md">
            <div className="flex items-center justify-between p-4 border-b dark:border-gray-700">
              <h3 className="text-lg font-bold">Ajustar Estoque</h3>
              <button onClick={() => setShowStockModal(false)} className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"><X className="w-5 h-5" /></button>
            </div>
            <div className="p-4 space-y-4">
              <div className="bg-gray-50 dark:bg-gray-700 p-3 rounded-lg">
                <p className="font-medium">{selectedProduct.nome}</p>
                <p className="text-sm text-gray-600 dark:text-gray-400">Estoque atual: {selectedProduct.quantidade} {selectedProduct.unidade_medida}</p>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Operacao</label>
                <select value={stockAdjust.operacao} onChange={(e) => setStockAdjust(prev => ({ ...prev, operacao: e.target.value as 'entrada' | 'saida' }))} className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600">
                  <option value="entrada">Entrada</option>
                  <option value="saida">Saida</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Quantidade</label>
                <input type="number" min="1" value={stockAdjust.quantidade} onChange={(e) => setStockAdjust(prev => ({ ...prev, quantidade: parseInt(e.target.value) || 0 }))} className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Motivo *</label>
                <textarea value={stockAdjust.motivo} onChange={(e) => setStockAdjust(prev => ({ ...prev, motivo: e.target.value }))} rows={3} className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600" placeholder="Informe o motivo do ajuste..." />
              </div>
            </div>
            <div className="flex justify-end gap-2 p-4 border-t dark:border-gray-700">
              <button onClick={() => setShowStockModal(false)} className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg">Cancelar</button>
              <button onClick={handleStockAdjust} className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700">Confirmar</button>
            </div>
          </div>
        </div>
      )}

      {/* Markup Calculator Modal */}
      {showMarkupCalculator && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-md">
            <div className="flex items-center justify-between p-4 border-b dark:border-gray-700">
              <h3 className="text-lg font-bold flex items-center gap-2"><Calculator className="w-5 h-5" />Calculadora de Markup</h3>
              <button onClick={() => setShowMarkupCalculator(false)} className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"><X className="w-5 h-5" /></button>
            </div>
            <div className="p-4 space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Preco de Custo</label>
                <input type="number" step="0.01" value={markupCalc.preco_custo} onChange={(e) => setMarkupCalc(prev => ({ ...prev, preco_custo: parseFloat(e.target.value) || 0 }))} className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Markup (%)</label>
                <input type="number" step="0.1" value={markupCalc.markup} onChange={(e) => setMarkupCalc(prev => ({ ...prev, markup: parseFloat(e.target.value) || 0 }))} className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600" />
              </div>
              <button onClick={calcularMarkup} className="w-full py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700">Calcular</button>
              <div className="bg-purple-50 dark:bg-purple-900 p-4 rounded-lg text-center">
                <p className="text-sm text-gray-600 dark:text-gray-400">Preco de Venda Sugerido</p>
                <p className="text-3xl font-bold text-purple-600 dark:text-purple-400">{formatCurrency(markupCalc.preco_venda)}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Product History Modal */}
      {showProductHistory && selectedProduct && (
        <ProductHistoryModal produto={selectedProduct} onClose={() => { setShowProductHistory(false); setSelectedProduct(null); }} />
      )}

      {/* Purchase Orders Panel */}
      <PurchaseOrdersPanel isOpen={showPurchaseOrders} onClose={() => setShowPurchaseOrders(false)} fornecedores={fornecedores} />

      {/* Quick Purchase Order Modal */}
      {selectedProductForOrder && (
        <PurchaseOrderModal
          isOpen={!!selectedProductForOrder}
          onClose={() => setSelectedProductForOrder(null)}
          onSuccess={() => { setSelectedProductForOrder(null); loadProdutos(); }}
          fornecedores={fornecedores}
          initialProduct={selectedProductForOrder}
          initialSupplierId={selectedProductForOrder?.fornecedor_id}
        />
      )}
    </div>
  );
};

export default ProductsPage;
