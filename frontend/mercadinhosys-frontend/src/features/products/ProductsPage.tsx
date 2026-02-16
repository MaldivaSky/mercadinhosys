import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Download,
  Plus,
  ShoppingCart,
  Calculator,
  Search,
  Filter,
  ChevronDown,
  RefreshCw,
  X
} from 'lucide-react';
import { Fornecedor, Produto, ProdutoFiltros } from '../../types';
import { productsService } from './productsService';
import { apiClient } from '../../api/apiClient';
import { Toaster, toast } from 'react-hot-toast';
import { formatCurrency } from '../../utils/formatters';

import ProductAnalyticsDashboard from './components/ProductAnalyticsDashboard';
import QuickFiltersPanel from './components/QuickFiltersPanel';
import ProductHistoryModal from './components/ProductHistoryModal';
import PurchaseOrdersPanel from './components/PurchaseOrdersPanel';
import PurchaseOrderModal from './components/PurchaseOrderModal';


import ProductFormModal from './components/ProductFormModal';
import { ProductsTable } from './components/ProductsTable';
import LotesDisponiveisModal from './components/LotesDisponiveisModal';
import ExpiringProductsModal from './components/ExpiringProductsModal';

const ProductsPage: React.FC = () => {
  const [produtos, setProdutos] = useState<Produto[]>([]);
  // todosProdutos removed in favor of server-side stats
  const [loading, setLoading] = useState(true);
  const [categorias, setCategorias] = useState<string[]>([]);
  const [fornecedores, setFornecedores] = useState<Fornecedor[]>([]);

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
    margem_alta: 0,
    margem_baixa: 0,
    classificacao_abc: { A: 0, B: 0, C: 0 },
    giro_estoque: { rapido: 0, normal: 0, lento: 0 },
    validade: { vencidos: 0, vence_15: 0, vence_30: 0, vence_90: 0 },
    top_produtos_margem: [] as any[],
    produtos_criticos: [] as any[]
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
  // showDetailModal removed
  const [showMarkupCalculator, setShowMarkupCalculator] = useState(false);
  const [showProductHistory, setShowProductHistory] = useState(false);
  const [showPurchaseOrders, setShowPurchaseOrders] = useState(false);
  const [showLotesModal, setShowLotesModal] = useState(false);
  const [showExpiryModal, setShowExpiryModal] = useState(false);
  const [expiryTimeframe, setExpiryTimeframe] = useState<'vencidos' | '15' | '30' | '90'>('30');

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

  const loadStats = useCallback(async () => {
    try {
      const response = await productsService.getEstatisticas(filtros);
      if (response.success && response.estatisticas) {
        setStats({
          ...response.estatisticas,
          margem_alta: response.estatisticas.margem_alta ?? 0,
          margem_baixa: response.estatisticas.margem_baixa ?? 0,
          validade: response.estatisticas.validade || { vencidos: 0, vence_15: 0, vence_30: 0, vence_90: 0 }
        });
      }
    } catch (error) {
      console.error('Erro ao carregar estatísticas:', error);
    }
  }, [filtros]);

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

  useEffect(() => { loadProdutos(); loadStats(); }, [loadProdutos, loadStats]);
  useEffect(() => { loadCategorias(); loadFornecedores(); }, [loadCategorias, loadFornecedores]);

  // Handlers
  const handleDelete = async (id: number) => {
    if (!window.confirm('Desativar este produto?')) return;
    try {
      await productsService.delete(id);
      toast.success('Produto desativado!');
      loadProdutos();
      loadStats();
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
      loadStats();
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
  };

  const calcularMarkup = () => {
    const precoVenda = markupCalc.preco_custo * (1 + markupCalc.markup / 100);
    setMarkupCalc(prev => ({ ...prev, preco_venda: parseFloat(precoVenda.toFixed(2)) }));
  };

  const handleCardClick = (filterType: string) => {
    // Limpa outros filtros ao clicar no dashboard
    setFiltros({ busca: '', ativos: true, ordenar_por: 'nome', direcao: 'asc' });
    setFiltroRapido(null); // Desativar filtro rápido se houver lógica conflitante

    if (filterType === 'esgotado') {
      setFiltros(prev => ({ ...prev, estoque_status: 'esgotado' }));
    } else if (filterType === 'baixo') {
      setFiltros(prev => ({ ...prev, estoque_status: 'baixo' }));
    } else if (filterType === 'normal') {
      setFiltros(prev => ({ ...prev, estoque_status: 'normal' }));
    } else if (filterType === 'valor') {
      // Ordenar por valor total de estoque
      setFiltros(prev => ({ ...prev, ordenar_por: 'valor_total_estoque', direcao: 'desc' }));
    } else if (filterType === 'margem') {
      // Ordenar por margem
      setFiltros(prev => ({ ...prev, ordenar_por: 'margem_lucro', direcao: 'desc' }));
    } else if (filterType === 'vencido' || filterType === 'vence_15' || filterType === 'vence_30' || filterType === 'vence_90') {
      const timeframeMap: Record<string, 'vencidos' | '15' | '30' | '90'> = {
        'vencido': 'vencidos',
        'vence_15': '15',
        'vence_30': '30',
        'vence_90': '90'
      };
      setExpiryTimeframe(timeframeMap[filterType]);
      setShowExpiryModal(true);

      // Também filtra a tabela por consistência
      if (filterType === 'vencido') {
        setFiltros(prev => ({ ...prev, vencidos: true, validade_proxima: false, ordenar_por: 'data_validade', direcao: 'asc' }));
      } else {
        const days = parseInt(filterType.split('_')[1]);
        setFiltros(prev => ({ ...prev, validade_proxima: true, vencidos: false, dias_validade: days, ordenar_por: 'data_validade', direcao: 'asc' }));
      }
    }

    setPage(1);
  };

  const handleQuickFilterChange = (filter: string | null) => {
    setFiltroRapido(filter);

    // Resetar filtros base e aplicar o específico
    const novosFiltros: ProdutoFiltros = { busca: '', ativos: true, ordenar_por: 'nome', direcao: 'asc' };

    if (filter === 'vencimento_proximo') {
      novosFiltros.validade_proxima = true;
      novosFiltros.dias_validade = 30;
      novosFiltros.ordenar_por = 'data_validade';
      novosFiltros.direcao = 'asc';
    } else if (filter === 'vencido') {
      novosFiltros.vencidos = true;
      novosFiltros.ordenar_por = 'data_validade';
      novosFiltros.direcao = 'asc';
    } else if (filter === 'classe_a') {
      // Backend precisa suportar filtro por classe ABC ou ordenamos
      // Como o backend calculate ABC dinamicamente, talvez não tenha filtro direto na query SQL simples.
      // Vamos focar no que funciona: ordenação ou filtro se houver.
      // O backend NÃO tem filtro ABC na query SQL reformulada. 
      // Solução paliativa: Ordenar por valor total vendido (proxy para ABC)
      novosFiltros.ordenar_por = 'total_vendido';
      novosFiltros.direcao = 'desc';
    } else if (filter === 'classe_c') {
      novosFiltros.ordenar_por = 'total_vendido';
      novosFiltros.direcao = 'asc';
    } else if (filter === 'repor_urgente') {
      novosFiltros.estoque_status = 'baixo'; // Backend trata 'baixo' (<= min)
      novosFiltros.ordenar_por = 'quantidade';
      novosFiltros.direcao = 'asc';
    } else if (filter === 'margem_alta') {
      novosFiltros.filtro_rapido = 'margem_alta';
      novosFiltros.ordenar_por = 'margem_lucro';
      novosFiltros.direcao = 'desc';
    } else if (filter === 'margem_baixa') {
      novosFiltros.filtro_rapido = 'margem_baixa';
      novosFiltros.ordenar_por = 'margem_lucro';
      novosFiltros.direcao = 'asc';
    } else if (filter === 'giro_rapido') {
      // Assumindo suporte a ordenação por ultima_venda ou similar
      novosFiltros.ordenar_por = 'ultima_venda';
      novosFiltros.direcao = 'desc';
    } else if (filter === 'giro_lento') {
      novosFiltros.ordenar_por = 'ultima_venda';
      novosFiltros.direcao = 'asc';
    }

    setFiltros(novosFiltros);
    setPage(1);
  };

  const handleSort = (key: string) => {
    setFiltros(prev => ({
      ...prev,
      ordenar_por: key,
      direcao: prev.ordenar_por === key && prev.direcao === 'asc' ? 'desc' : 'asc'
    }));
    setPage(1);
  };

  // Simplificado: Dados vêm direto do estado 'produtos', que é atualizado pelo 'loadProdutos' usando os filtros do server
  const currentTableData = {
    produtos: produtos,
    totalItems: totalItems,
    totalPages: totalPages
  };

  const contadoresFiltros = useMemo(() => ({
    total: stats.total_produtos,
    esgotado: stats.produtos_esgotados,
    baixo: stats.produtos_baixo_estoque,
    normal: stats.produtos_normal,
    classe_a: stats.classificacao_abc?.A || 0,
    classe_c: stats.classificacao_abc?.C || 0,
    giro_rapido: stats.giro_estoque?.rapido || 0,
    giro_lento: stats.giro_estoque?.lento || 0,
    margem_alta: stats.margem_alta ?? 0,
    margem_baixa: stats.margem_baixa ?? 0,
    repor_urgente: stats.produtos_esgotados + stats.produtos_baixo_estoque,
    sem_fornecedor: 0,
    vencimento_proximo: stats.validade?.vence_30 || 0,
    vencido: stats.validade?.vencidos || 0
  }), [stats]);

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

      <QuickFiltersPanel activeFilter={filtroRapido} onFilterChange={handleQuickFilterChange} counts={contadoresFiltros} />

      <ProductAnalyticsDashboard produtos={produtos} stats={stats} onCardClick={handleCardClick} />

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
              <label className="block text-sm font-medium mb-1">Validade</label>
              <select value={filtros.vencidos ? 'vencidos' : (filtros.validade_proxima ? `proxima_${filtros.dias_validade || 30}` : '')}
                onChange={(e) => {
                  const val = e.target.value;
                  const nf: ProdutoFiltros = { ...filtros, vencidos: false, validade_proxima: false, dias_validade: undefined };
                  if (val === 'vencidos') {
                    nf.vencidos = true;
                  } else if (val.startsWith('proxima_')) {
                    nf.validade_proxima = true;
                    nf.dias_validade = parseInt(val.split('_')[1]);
                  }
                  setFiltros(nf);
                  setPage(1);
                }}
                className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              >
                <option value="">Qualquer</option>
                <option value="vencidos">Já Vencidos</option>
                <option value="proxima_15">Vence em 15 dias</option>
                <option value="proxima_30">Vence em 30 dias</option>
                <option value="proxima_90">Vence em 90 dias</option>
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

      <ProductsTable
        produtos={currentTableData.produtos}
        loading={loading}
        totalItems={currentTableData.totalItems}
        page={page}
        totalPages={currentTableData.totalPages}
        onPageChange={setPage}
        onEdit={openEditModal}
        onDelete={handleDelete}
        onStockAdjust={openStockModal}
        onHistory={(p) => { setSelectedProduct(p); setShowProductHistory(true); }}
        onMakeOrder={openOrderModal}
        onViewLotes={(p) => { setSelectedProduct(p); setShowLotesModal(true); }}
        onSort={handleSort}
        sortConfig={{ key: filtros.ordenar_por || 'nome', direction: filtros.direcao || 'asc' }}
      />

      <ProductFormModal
        show={showProductModal}
        editMode={editMode}
        produto={selectedProduct}
        categorias={categorias}
        fornecedores={fornecedores}
        onClose={() => { setShowProductModal(false); setSelectedProduct(null); setEditMode(false); }}
        onSuccess={() => { setShowProductModal(false); loadProdutos(); loadStats(); }}
      />

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

      {showProductHistory && selectedProduct && (
        <ProductHistoryModal produto={selectedProduct} onClose={() => { setShowProductHistory(false); setSelectedProduct(null); }} />
      )}

      <PurchaseOrdersPanel isOpen={showPurchaseOrders} onClose={() => setShowPurchaseOrders(false)} fornecedores={fornecedores} />

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

      {showLotesModal && selectedProduct && (
        <LotesDisponiveisModal
          produtoId={selectedProduct.id}
          produtoNome={selectedProduct.nome}
          onClose={() => { setShowLotesModal(false); setSelectedProduct(null); }}
        />
      )}

      <ExpiringProductsModal
        isOpen={showExpiryModal}
        onClose={() => {
          setShowExpiryModal(false);
          loadStats();
          loadProdutos();
        }}
        timeframe={expiryTimeframe}
      />
    </div>
  );
};

export default ProductsPage;