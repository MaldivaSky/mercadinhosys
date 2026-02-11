import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Package,
  Plus,
  Search,
  Filter,
  Edit,
  Trash2,
  Eye,
  Download,
  TrendingUp,
  AlertTriangle,
  X,
  ChevronDown,
  RefreshCw,
  FileText,
  DollarSign,
  Archive,
  Calculator,
  Percent,
  Check,
  Star,
} from 'lucide-react';
import { Fornecedor, Produto, ProdutoFiltros } from '../../types';
import { productsService } from './productsService';
import { formatCurrency } from '../../utils/formatters';
import { apiClient } from '../../api/apiClient';
import { Toaster, toast } from 'react-hot-toast';
import ProductModal from './ProductModal';
import { useConfig } from '../../contexts/ConfigContext';
import ProductAnalyticsDashboard from './components/ProductAnalyticsDashboard';
import QuickFiltersPanel from './components/QuickFiltersPanel';
import ProductHistoryModal from './components/ProductHistoryModal';
import {
  getClassificacaoABC,
  getDiasDesdeUltimaVenda,
  aplicarFiltroRapido,
  calcularContadoresFiltros,
} from './utils/quickFilters';
import {
  calcularValorInvestido,
  calcularLucroPotencial,
} from './utils/strategicFilters';

interface ProductFormData {
  nome: string;
  codigo_barras: string;
  descricao: string;
  categoria: string;
  marca: string;
  fabricante: string;
  tipo: string;
  unidade_medida: string;
  preco_custo: number;
  preco_venda: number;
  margem_lucro: number;
  quantidade: number;
  quantidade_minima: number;
  fornecedor_id?: number;
  lote?: string;
  data_fabricacao?: string;
  data_validade?: string;
  ativo: boolean;
}

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
  const [showExpiring, setShowExpiring] = useState<boolean>(true);
  const [filtroRapido, setFiltroRapido] = useState<string | null>(null);

  const [showProductModal, setShowProductModal] = useState(false);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [showStockModal, setShowStockModal] = useState(false);
  const [stockMotivoError, setStockMotivoError] = useState(false);
  const [stockNotes, setStockNotes] = useState('');
  const motivosPadrao = useMemo(() => ([
    'ajuste de estoque',
    'antecipacao de pedido junto ao fornecedor',
    'produto com promocao',
    'comprado com o vendedor pronta entrega',
  ]), []);
  const [selectedProduct, setSelectedProduct] = useState<Produto | null>(null);
  const [editMode, setEditMode] = useState(false);

  const [showMarkupCalculator, setShowMarkupCalculator] = useState(false);
  const [showProductHistory, setShowProductHistory] = useState(false);

  const [markupCalc, setMarkupCalc] = useState({
    preco_custo: 0,
    markup: 30,
    preco_venda: 0,
    modo: 'markup' as 'markup' | 'preco_venda'
  });

  const [formData, setFormData] = useState<ProductFormData>({
    nome: '',
    codigo_barras: '',
    descricao: '',
    categoria: '',
    marca: 'Sem Marca',
    fabricante: '',
    tipo: 'Higiene',
    unidade_medida: 'un',
    preco_custo: 0,
    preco_venda: 0,
    margem_lucro: 30,
    quantidade: 0,
    quantidade_minima: 10,
    ativo: true,
  });

  const [stockAdjust, setStockAdjust] = useState({
    quantidade: 0,
    operacao: 'entrada' as 'entrada' | 'saida',
    motivo: '',
  });
  const handleBuscaChange = useCallback((value: string) => {
    setBuscaLocal(value);
  }, []);

  const handlePrecoCustoChange = useCallback((value: string) => {
    const numValue = parseFloat(value) || 0;
    setFormData(prev => ({ ...prev, preco_custo: numValue }));
  }, []);

  const handlePrecoCustoBlur = useCallback(() => {
    setFormData(prev => {
      const custo = prev.preco_custo || 0;
      const margem = prev.margem_lucro || 0;
      const precoVenda = custo * (1 + margem / 100);
      return { ...prev, preco_venda: parseFloat(precoVenda.toFixed(2)) };
    });
  }, []);

  const handlePrecoVendaChange = useCallback((value: string) => {
    const numValue = parseFloat(value) || 0;
    setFormData(prev => ({ ...prev, preco_venda: numValue }));
  }, []);

  const handlePrecoVendaBlur = useCallback(() => {
    setFormData(prev => {
      const venda = prev.preco_venda || 0;
      const custo = prev.preco_custo || 0;
      const margem = custo > 0 ? ((venda - custo) / custo) * 100 : 0;
      return { ...prev, margem_lucro: parseFloat(margem.toFixed(2)) };
    });
  }, []);

  const handleMargemChange = useCallback((value: string) => {
    const numValue = parseFloat(value) || 0;
    setFormData(prev => ({ ...prev, margem_lucro: numValue }));
  }, []);

  const handleMargemBlur = useCallback(() => {
    setFormData(prev => {
      const margem = prev.margem_lucro || 0;
      const custo = prev.preco_custo || 0;
      const precoVenda = custo * (1 + margem / 100);
      return { ...prev, preco_venda: parseFloat(precoVenda.toFixed(2)) };
    });
  }, []);

  const handleNomeChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({ ...prev, nome: e.target.value }));
  }, []);

  const handleCodigoBarrasChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({ ...prev, codigo_barras: e.target.value }));
  }, []);

  const handleCategoriaChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({ ...prev, categoria: e.target.value }));
  }, []);

  const handleMarcaChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({ ...prev, marca: e.target.value }));
  }, []);

  const handleFabricanteChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({ ...prev, fabricante: e.target.value }));
  }, []);

  const handleDescricaoChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setFormData(prev => ({ ...prev, descricao: e.target.value }));
  }, []);

  const handleQuantidadeChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({ ...prev, quantidade: parseFloat(e.target.value) || 0 }));
  }, []);

  const handleQuantidadeMinimaChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({ ...prev, quantidade_minima: parseFloat(e.target.value) || 0 }));
  }, []);

  const handleUnidadeChange = useCallback((e: React.ChangeEvent<HTMLSelectElement>) => {
    setFormData(prev => ({ ...prev, unidade_medida: e.target.value }));
  }, []);

  const handleTipoChange = useCallback((e: React.ChangeEvent<HTMLSelectElement>) => {
    setFormData(prev => ({ ...prev, tipo: e.target.value }));
  }, []);

  const handleFornecedorChange = useCallback((e: React.ChangeEvent<HTMLSelectElement>) => {
    setFormData(prev => ({ ...prev, fornecedor_id: e.target.value ? parseInt(e.target.value) : undefined }));
  }, []);

  const handleAtivoChange = useCallback((checked: boolean) => {
    setFormData(prev => ({ ...prev, ativo: checked }));
  }, []);

  const handleLoteChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({ ...prev, lote: e.target.value }));
  }, []);

  const handleDataFabricacaoChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({ ...prev, data_fabricacao: e.target.value }));
  }, []);

  const handleDataValidadeChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({ ...prev, data_validade: e.target.value }));
  }, []);

  const calcularMarkup = useCallback(() => {
    if (markupCalc.modo === 'markup') {
      const precoVenda = markupCalc.preco_custo * (1 + markupCalc.markup / 100);
      setMarkupCalc(prev => ({ ...prev, preco_venda: parseFloat(precoVenda.toFixed(2)) }));
    } else {
      if (markupCalc.preco_custo > 0) {
        const markup = ((markupCalc.preco_venda - markupCalc.preco_custo) / markupCalc.preco_custo) * 100;
        setMarkupCalc(prev => ({ ...prev, markup: parseFloat(markup.toFixed(2)) }));
      }
    }
  }, [markupCalc]);

  const aplicarMarkupAoProduto = useCallback(() => {
    setFormData(prev => ({
      ...prev,
      preco_custo: markupCalc.preco_custo,
      preco_venda: markupCalc.preco_venda,
      margem_lucro: markupCalc.markup
    }));
    setShowMarkupCalculator(false);
    toast.success('Valores aplicados ao formulario!');
  }, [markupCalc]);

  const openProductHistory = useCallback((produto: Produto) => {
    setSelectedProduct(produto);
    setShowProductHistory(true);
  }, []);

  const getApiError = (error: unknown) => {
    if (typeof error === 'object' && error !== null && 'response' in error) {
      const err = error as { response?: { data?: { error?: string } } };
      return err.response?.data?.error;
    }
    if (error instanceof Error) return error.message;
    return undefined;
  };
  const loadProdutos = useCallback(async () => {
    try {
      setLoading(true);
      const response = await productsService.getAllEstoque(page, 50, filtros);
      setProdutos(response.produtos);
      setTotalPages(response.paginacao.total_paginas);
      setTotalItems(response.paginacao.total_itens);
    } catch (error) {
      console.error('Erro ao carregar produtos:', error);
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
      setStats({
        total_produtos: total,
        produtos_esgotados: esgotados,
        produtos_baixo_estoque: baixo,
        produtos_normal: normal,
        valor_total_estoque: valorTotal,
        margem_media: margemMedia,
      });
    } catch (error) {
      console.error('Erro ao carregar todos os produtos:', error);
    }
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => {
      setFiltros(prev => ({ ...prev, busca: buscaLocal }));
    }, 500);
    return () => clearTimeout(timer);
  }, [buscaLocal]);

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
      const response = await apiClient.get<{ fornecedores: Fornecedor[] }>('/fornecedores/', {
        params: { per_page: 200, ordenar_por: 'nome' },
      });
      setFornecedores(response.data.fornecedores || []);
    } catch (error) {
      console.error('Erro ao carregar fornecedores:', error);
    }
  }, []);

  useEffect(() => {
    loadProdutos();
  }, [loadProdutos]);

  useEffect(() => {
    loadCategorias();
    loadFornecedores();
    loadTodosProdutos();
  }, [loadCategorias, loadFornecedores, loadTodosProdutos]);

  const diasAlertaValidade: number = useMemo(() => {
    return config?.dias_alerta_validade ?? 30;
  }, [config]);

  const calcularDiasRestantes = useCallback((dateStr?: string): number | null => {
    if (!dateStr) return null;
    const hoje = new Date();
    hoje.setHours(0, 0, 0, 0);
    const validade = new Date(dateStr);
    validade.setHours(0, 0, 0, 0);
    const diffMs = validade.getTime() - hoje.getTime();
    const diffDias = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    return diffDias;
  }, []);

  const produtosProximosValidade = useMemo(() => {
    if (!config?.controlar_validade) return [];
    const items = todosProdutos
      .filter(p => p.quantidade > 0)
      .map((p) => ({
        produto: p,
        diasRestantes: calcularDiasRestantes(p.data_validade),
      }))
      .filter((i) => {
        return i.diasRestantes !== null && i.diasRestantes >= 0 && i.diasRestantes <= diasAlertaValidade;
      })
      .sort((a, b) => (a.diasRestantes as number) - (b.diasRestantes as number));
    return items.slice(0, 10);
  }, [todosProdutos, diasAlertaValidade, calcularDiasRestantes, config]);
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editMode && selectedProduct) {
        await productsService.update(selectedProduct.id, formData);
        toast.success('Produto atualizado com sucesso!');
      } else {
        await productsService.create(formData);
        toast.success('Produto criado com sucesso!');
      }
      setShowProductModal(false);
      resetForm();
      loadProdutos();
    } catch (error) {
      console.error('Erro ao salvar produto:', error);
      toast.error(getApiError(error) || 'Erro ao salvar produto');
    }
  };

  const handleDelete = useCallback(async (id: number) => {
    if (!window.confirm('Tem certeza que deseja desativar este produto?')) return;
    try {
      await productsService.delete(id);
      toast.success('Produto desativado com sucesso!');
      loadProdutos();
    } catch (error) {
      console.error('Erro ao excluir produto:', error);
      toast.error('Erro ao excluir produto');
    }
  }, [loadProdutos]);

  const handleStockAdjust = async () => {
    if (!selectedProduct) return;
    try {
      if (!stockAdjust.motivo || stockAdjust.motivo.trim().length === 0) {
        setStockMotivoError(true);
        toast.error('Informe o motivo do ajuste de estoque');
        return;
      }
      await productsService.ajustarEstoque(
        selectedProduct.id,
        stockAdjust.quantidade,
        stockAdjust.operacao,
        stockAdjust.motivo,
        stockNotes
      );
      toast.success('Estoque ajustado com sucesso!');
      setShowStockModal(false);
      loadProdutos();
    } catch (error) {
      console.error('Erro ao ajustar estoque:', error);
      toast.error(getApiError(error) || 'Erro ao ajustar estoque');
    }
  };

  const handleExportCSV = async () => {
    try {
      const response = await productsService.exportarCSV(filtros.ativos ?? true);
      const blob = new Blob([response.csv], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = `produtos_${new Date().toISOString().split('T')[0]}.csv`;
      link.click();
      toast.success(`${response.total_produtos} produtos exportados com sucesso!`);
    } catch (error) {
      console.error('Erro ao exportar CSV:', error);
      toast.error('Erro ao exportar dados');
    }
  };

  const resetForm = () => {
    setFormData({
      nome: '',
      codigo_barras: '',
      descricao: '',
      categoria: '',
      marca: 'Sem Marca',
      fabricante: '',
      tipo: 'Higiene',
      unidade_medida: 'un',
      preco_custo: 0,
      preco_venda: 0,
      margem_lucro: 30,
      quantidade: 0,
      quantidade_minima: 10,
      ativo: true,
    });
    setEditMode(false);
    setSelectedProduct(null);
  };

  const openEditModal = (produto: Produto) => {
    setSelectedProduct(produto);
    setFormData({
      nome: produto.nome,
      codigo_barras: produto.codigo_barras || '',
      descricao: produto.descricao || '',
      categoria: produto.categoria,
      marca: produto.marca || 'Sem Marca',
      fabricante: produto.fabricante || '',
      tipo: produto.tipo || 'Higiene',
      unidade_medida: produto.unidade_medida,
      preco_custo: produto.preco_custo,
      preco_venda: produto.preco_venda,
      margem_lucro: produto.margem_lucro || 30,
      quantidade: produto.quantidade,
      quantidade_minima: produto.quantidade_minima,
      fornecedor_id: produto.fornecedor_id,
      ativo: produto.ativo,
      lote: produto.lote,
      data_fabricacao: produto.data_fabricacao,
      data_validade: produto.data_validade,
    });
    setEditMode(true);
    setShowProductModal(true);
  };

  const openDetailModal = async (id: number) => {
    try {
      const produto = await productsService.getById(id);
      setSelectedProduct(produto);
      setShowDetailModal(true);
    } catch (error) {
      console.error('Erro ao carregar detalhes:', error);
    }
  };

  const openStockModal = useCallback((produto: Produto) => {
    setSelectedProduct(produto);
    setStockAdjust({ quantidade: 0, operacao: 'entrada', motivo: '' });
    setStockNotes('');
    setStockMotivoError(false);
    setShowStockModal(true);
  }, []);

  const getStockBadge = useCallback((produto: Produto) => {
    const status = produto.estoque_status || 'normal';
    const colors = {
      esgotado: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300',
      baixo: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300',
      normal: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
    };
    return colors[status] || colors.normal;
  }, []);

  const handleCardClick = useCallback((filterType: string) => {
    setShowFilters(true);
    switch(filterType) {
      case 'all':
        setFiltros({ busca: '', ativos: true, ordenar_por: 'nome', direcao: 'asc' });
        setBuscaLocal('');
        break;
      case 'normal':
        setFiltros(prev => ({ ...prev, estoque_status: 'normal' }));
        break;
      case 'baixo':
        setFiltros(prev => ({ ...prev, estoque_status: 'baixo' }));
        break;
      case 'esgotado':
        setFiltros(prev => ({ ...prev, estoque_status: 'esgotado' }));
        break;
      case 'valor':
        setFiltros(prev => ({ ...prev, ordenar_por: 'preco_venda', direcao: 'desc' }));
        break;
      case 'margem':
        setFiltros(prev => ({ ...prev, ordenar_por: 'margem_lucro', direcao: 'desc' }));
        break;
    }
    setPage(1);
  }, []);

  const handleFiltroRapidoChange = useCallback((filtro: string | null) => {
    setFiltroRapido(filtro);
    setPage(1);
  }, []);

  const produtosFiltrados = useMemo(() => {
    if (!filtroRapido) return produtos;
    return aplicarFiltroRapido(produtos, filtroRapido, todosProdutos);
  }, [produtos, filtroRapido, todosProdutos]);

  const contadoresFiltros = useMemo(() => {
    return calcularContadoresFiltros(todosProdutos, todosProdutos);
  }, [todosProdutos]);

  const produtosDashboard = useMemo(() => {
    if (!filtroRapido) return todosProdutos;
    return aplicarFiltroRapido(todosProdutos, filtroRapido, todosProdutos);
  }, [todosProdutos, filtroRapido]);

  const analyticsDashboard = useMemo(() => {
    return (
      <ProductAnalyticsDashboard 
        produtos={produtosDashboard}
        stats={stats}
        onCardClick={handleCardClick}
      />
    );
  }, [produtosDashboard, stats, handleCardClick]);
  return (
    <div className="space-y-6 p-6">
      <Toaster position="top-right" />
      
      {/* Cabecalho */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold text-gray-800 dark:text-white mb-2">
            Gestao de Produtos
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Controle completo do estoque e catalogo de produtos
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => setShowMarkupCalculator(true)}
            className="px-4 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 flex items-center gap-2 transition-colors shadow-lg hover:shadow-xl"
            title="Calculadora de Markup"
          >
            <Calculator className="w-5 h-5" />
            <span>Markup</span>
          </button>
          <button
            onClick={handleExportCSV}
            className="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 flex items-center gap-2 transition-colors shadow-lg hover:shadow-xl"
          >
            <Download className="w-5 h-5" />
            <span>Exportar CSV</span>
          </button>
          <button
            onClick={() => {
              resetForm();
              setShowProductModal(true);
            }}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 flex items-center gap-2 transition-colors shadow-lg hover:shadow-xl"
          >
            <Plus className="w-5 h-5" />
            <span>Novo Produto</span>
          </button>
        </div>
      </div>

      {/* Filtros Rapidos */}
      <QuickFiltersPanel
        activeFilter={filtroRapido}
        onFilterChange={handleFiltroRapidoChange}
        counts={contadoresFiltros}
      />

      {/* Indicador de Filtro Ativo */}
      {filtroRapido && (
        <div className="bg-blue-50 dark:bg-blue-900 border border-blue-200 dark:border-blue-700 rounded-lg p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Filter className="w-5 h-5 text-blue-600 dark:text-blue-300" />
            <div>
              <p className="text-sm font-semibold text-blue-900 dark:text-blue-100">Filtro Ativo</p>
              <p className="text-xs text-blue-700 dark:text-blue-300">
                Os cards do dashboard e a tabela estao mostrando apenas produtos do filtro selecionado
              </p>
            </div>
          </div>
          <button
            onClick={() => handleFiltroRapidoChange(null)}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors flex items-center gap-2"
          >
            <X className="w-4 h-4" />
            Limpar Filtro
          </button>
        </div>
      )}

      {/* Dashboard de Estatisticas */}
      {analyticsDashboard}

      {/* Filtros e Busca */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
        <div className="flex flex-col gap-4">
          {/* Validades Proximas */}
          {config?.controlar_validade && (
            <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5 text-yellow-600" />
                  <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-200">
                    Produtos proximos a validade
                  </h3>
                  <span className="ml-2 inline-flex items-center px-2 py-0.5 text-xs rounded-full bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200">
                    {produtosProximosValidade.length}
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => setShowExpiring(!showExpiring)}
                  className="text-xs px-2 py-1 border rounded-md border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                >
                  {showExpiring ? 'Esconder' : 'Mostrar'}
                </button>
              </div>
              {showExpiring && produtosProximosValidade.length > 0 && (
                <div className="mt-3 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                  {produtosProximosValidade.map(({ produto, diasRestantes }) => (
                    <div
                      key={produto.id}
                      className="flex items-center justify-between p-3 rounded-md border border-gray-200 dark:border-gray-700"
                    >
                      <div className="min-w-0">
                        <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                          {produto.nome}
                        </p>
                        <p className="text-xs text-gray-600 dark:text-gray-400">
                          Validade: {produto.data_validade || 'N/A'}
                        </p>
                      </div>
                      <div className="text-right">
                        <span
                          className={`inline-flex items-center px-2 py-0.5 text-xs rounded-full ${
                            diasRestantes !== null && diasRestantes <= 0
                              ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                              : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
                          }`}
                        >
                          {diasRestantes !== null ? `${diasRestantes}d` : '-'}
                        </span>
                        <div className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                          Qtd: {produto.quantidade}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
              {showExpiring && produtosProximosValidade.length === 0 && (
                <p className="mt-2 text-xs text-gray-600 dark:text-gray-400">
                  Nenhum produto dentro do limite de {diasAlertaValidade} dias.
                </p>
              )}
            </div>
          )}

          {/* Linha 1: Busca e acoes */}
          <div className="flex flex-col md:flex-row gap-3">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                value={buscaLocal}
                onChange={(e) => handleBuscaChange(e.target.value)}
                placeholder="Buscar por nome, codigo de barras, marca ou categoria..."
                className="w-full pl-10 pr-4 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setShowFilters(!showFilters)}
                className="px-4 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg flex items-center gap-2 hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors relative"
              >
                <Filter className="w-5 h-5" />
                <span>Filtros</span>
                <ChevronDown
                  className={`w-4 h-4 transition-transform ${showFilters ? 'rotate-180' : ''}`}
                />
              </button>
              <button
                onClick={loadProdutos}
                className="px-4 py-2.5 bg-blue-500 text-white rounded-lg hover:bg-blue-600 flex items-center gap-2 transition-colors"
              >
                <RefreshCw className="w-5 h-5" />
                <span>Atualizar</span>
              </button>
            </div>
          </div>
          {/* Filtros Avancados */}
          {showFilters && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4 pt-4 border-t border-gray-200 dark:border-gray-700">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Categoria
                </label>
                <input
                  type="text"
                  value={filtros.categoria || ''}
                  onChange={(e) => {
                    setFiltros({ ...filtros, categoria: e.target.value || undefined });
                    setPage(1);
                  }}
                  list="categorias-list-filtro"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="Ex: Refrigerantes"
                />
                <datalist id="categorias-list-filtro">
                  {categorias.map((cat) => (
                    <option key={cat} value={cat} />
                  ))}
                </datalist>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Tipo de Produto
                </label>
                <select
                  value={filtros.tipo || ''}
                  onChange={(e) => {
                    setFiltros({ ...filtros, tipo: e.target.value || undefined });
                    setPage(1);
                  }}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Todos</option>
                  <option value="Higiene">Higiene</option>
                  <option value="Limpeza">Limpeza</option>
                  <option value="Hortifruti">Hortifruti</option>
                  <option value="Padaria">Padaria</option>
                  <option value="Carnes">Carnes (Acougue)</option>
                  <option value="Frios e Laticinios">Frios e Laticinios</option>
                  <option value="Mercearia">Mercearia</option>
                  <option value="Bebidas Nao Alcoolicas">Bebidas Nao Alcoolicas</option>
                  <option value="Bebidas Alcoolicas">Bebidas Alcoolicas</option>
                  <option value="Congelados">Congelados</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Fornecedor
                </label>
                <select
                  value={filtros.fornecedor_id || ''}
                  onChange={(e) => {
                    setFiltros({ ...filtros, fornecedor_id: e.target.value ? Number(e.target.value) : undefined });
                    setPage(1);
                  }}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Todos</option>
                  {fornecedores.map((fornecedor) => (
                    <option key={fornecedor.id} value={fornecedor.id}>
                      {fornecedor.nome}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Status Estoque
                </label>
                <select
                  value={filtros.estoque_status || ''}
                  onChange={(e) => {
                    setFiltros({ ...filtros, estoque_status: (e.target.value || undefined) as ProdutoFiltros['estoque_status'] });
                    setPage(1);
                  }}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Todos</option>
                  <option value="normal">Normal</option>
                  <option value="baixo">Baixo</option>
                  <option value="esgotado">Esgotado</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Ordenar Por
                </label>
                <select
                  value={filtros.ordenar_por || 'nome'}
                  onChange={(e) => {
                    setFiltros({ ...filtros, ordenar_por: e.target.value });
                    setPage(1);
                  }}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="nome">Nome</option>
                  <option value="preco_venda">Preco</option>
                  <option value="quantidade">Quantidade</option>
                  <option value="created_at">Data Cadastro</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Direcao
                </label>
                <select
                  value={filtros.direcao || 'asc'}
                  onChange={(e) => {
                    setFiltros({ ...filtros, direcao: e.target.value as 'asc' | 'desc' });
                    setPage(1);
                  }}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="asc">Crescente</option>
                  <option value="desc">Decrescente</option>
                </select>
              </div>
              <div className="md:col-span-2 lg:col-span-3 xl:col-span-6 flex justify-end">
                <button
                  onClick={() => {
                    setFiltros({ busca: '', ativos: true, ordenar_por: 'nome', direcao: 'asc' });
                    setBuscaLocal('');
                    setPage(1);
                  }}
                  className="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors flex items-center gap-2"
                >
                  <X className="w-4 h-4" />
                  Limpar Filtros
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
      {/* Tabela de Produtos */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-700">
              <tr>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Produto
                </th>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Codigo
                </th>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Categoria
                </th>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Classificacao
                </th>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Estoque
                </th>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Fornecedor
                </th>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Precos
                </th>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Acoes
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {loading ? (
                <tr>
                  <td colSpan={9} className="px-6 py-12 text-center">
                    <div className="flex justify-center">
                      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
                    </div>
                  </td>
                </tr>
              ) : produtos.length === 0 ? (
                <tr>
                  <td colSpan={9} className="px-6 py-12 text-center">
                    <div className="flex flex-col items-center">
                      <Package className="w-16 h-16 text-gray-300 dark:text-gray-600 mb-4" />
                      <p className="text-gray-500 dark:text-gray-400 text-lg">
                        Nenhum produto encontrado
                      </p>
                      <p className="text-gray-400 dark:text-gray-500 text-sm mt-2">
                        Tente ajustar os filtros ou adicione um novo produto
                      </p>
                    </div>
                  </td>
                </tr>
              ) : (
                produtosFiltrados.map((produto) => (
                  <tr
                    key={produto.id}
                    className="hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                  >
                    <td className="px-6 py-4">
                      <div className="flex items-center">
                        <div className="flex-shrink-0 h-12 w-12 bg-gradient-to-br from-blue-100 to-blue-200 dark:from-blue-900 dark:to-blue-800 rounded-lg flex items-center justify-center">
                          {produto.imagem_url ? (
                            <img
                              src={produto.imagem_url}
                              alt={produto.nome}
                              className="h-12 w-12 rounded-lg object-cover"
                            />
                          ) : (
                            <Package className="w-6 h-6 text-blue-600 dark:text-blue-300" />
                          )}
                        </div>
                        <div className="ml-4">
                          <div className="text-sm font-semibold text-gray-900 dark:text-white">
                            {produto.nome}
                          </div>
                          <div className="text-xs text-gray-500 dark:text-gray-400">
                            {produto.marca || 'Sem marca'}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className="text-sm text-gray-900 dark:text-white font-mono">
                        {produto.codigo_barras || 'N/A'}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className="px-2.5 py-1 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-300">
                        {produto.categoria}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="space-y-1">
                        {(() => {
                          const abc = getClassificacaoABC(produto, todosProdutos);
                          const colors = {
                            A: 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-300',
                            B: 'bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-300',
                            C: 'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-300',
                          };
                          return (
                            <span className={`px-2 py-0.5 inline-flex items-center gap-1 text-xs font-semibold rounded-full ${colors[abc]}`}>
                              <Star className="w-3 h-3" />
                              {abc}
                            </span>
                          );
                        })()}
                        <div className="text-xs text-gray-600 dark:text-gray-400">
                          {(() => {
                            const dias = getDiasDesdeUltimaVenda(produto);
                            if (dias === null) return 'Nunca vendeu';
                            if (dias === 0) return 'Vendeu hoje';
                            if (dias <= 7) return `${dias}d atras`;
                            if (dias <= 30) return `${dias}d atras`;
                            return `${dias}d parado`;
                          })()}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm">
                        <div className="font-semibold text-gray-900 dark:text-white">
                          {produto.quantidade} {produto.unidade_medida}
                        </div>
                        <div className="text-xs text-gray-500 dark:text-gray-400">
                          Min: {produto.quantidade_minima}
                        </div>
                        <span
                          className={`mt-1 px-2 py-0.5 inline-flex text-xs leading-4 font-semibold rounded-full ${getStockBadge(produto)}`}
                        >
                          {produto.estoque_status || 'normal'}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="space-y-1">
                        <div className="text-sm">
                          {produto.fornecedor_nome ? (
                            <span className="text-gray-900 dark:text-white font-medium truncate max-w-[150px]">
                              {produto.fornecedor_nome}
                            </span>
                          ) : (
                            <div className="flex items-center gap-1">
                              <AlertTriangle className="w-4 h-4 text-red-600 dark:text-red-400" />
                              <span className="text-red-600 dark:text-red-400 text-xs font-semibold">
                                Sem fornecedor
                              </span>
                            </div>
                          )}
                        </div>
                        <div className="text-xs text-gray-500 dark:text-gray-400">
                          <span className="text-gray-600 dark:text-gray-400">Investido: </span>
                          <span className="font-semibold text-blue-600 dark:text-blue-400">
                            {formatCurrency(calcularValorInvestido(produto))}
                          </span>
                        </div>
                        <div className="text-xs text-gray-500 dark:text-gray-400">
                          <span className="text-gray-600 dark:text-gray-400">Lucro: </span>
                          <span className="font-semibold text-green-600 dark:text-green-400">
                            {formatCurrency(calcularLucroPotencial(produto))}
                          </span>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm">
                        <div className="font-semibold text-green-600 dark:text-green-400">
                          Venda: {formatCurrency(produto.preco_venda)}
                        </div>
                        <div className="text-gray-500 dark:text-gray-400">
                          Custo: {formatCurrency(produto.preco_custo)}
                        </div>
                        <div
                          className={`text-xs font-semibold ${
                            (produto.margem_lucro || 0) >= 50
                              ? 'text-green-600'
                              : 'text-yellow-600'
                          }`}
                        >
                          Margem: {produto.margem_lucro?.toFixed(1) || 0}%
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span
                        className={`px-2.5 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
                          produto.ativo
                            ? 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-300'
                            : 'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-300'
                        }`}
                      >
                        {produto.ativo ? 'Ativo' : 'Inativo'}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex gap-1">
                        <button
                          onClick={() => openProductHistory(produto)}
                          className="p-2 text-indigo-600 hover:text-indigo-800 hover:bg-indigo-50 dark:hover:bg-indigo-900 rounded-lg transition-colors font-semibold"
                          title="Ver Historico"
                        >
                          <TrendingUp className="w-5 h-5" />
                        </button>
                        <button
                          onClick={() => openDetailModal(produto.id)}
                          className="p-2 text-blue-500 hover:text-blue-700 hover:bg-blue-50 dark:hover:bg-blue-900 rounded-lg transition-colors"
                          title="Ver detalhes"
                        >
                          <Eye className="w-5 h-5" />
                        </button>
                        <button
                          onClick={() => openEditModal(produto)}
                          className="p-2 text-yellow-500 hover:text-yellow-700 hover:bg-yellow-50 dark:hover:bg-yellow-900 rounded-lg transition-colors"
                          title="Editar"
                        >
                          <Edit className="w-5 h-5" />
                        </button>
                        <button
                          onClick={() => openStockModal(produto)}
                          className={`p-2 text-purple-500 hover:text-purple-700 hover:bg-purple-50 dark:hover:bg-purple-900 rounded-lg transition-colors ${
                            (produto.estoque_status === 'esgotado' || produto.estoque_status === 'baixo')
                              ? 'animate-pulse ring-2 ring-offset-2 ring-purple-400'
                              : ''
                          }`}
                          title="Ajustar estoque"
                        >
                          <Archive className="w-5 h-5" />
                        </button>
                        <button
                          onClick={() => handleDelete(produto.id)}
                          className="p-2 text-red-500 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900 rounded-lg transition-colors"
                          title="Excluir"
                        >
                          <Trash2 className="w-5 h-5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        {/* Paginacao */}
        {totalPages > 1 && (
          <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-750">
            <div className="flex flex-col md:flex-row items-center justify-between gap-4">
              <div className="text-sm text-gray-700 dark:text-gray-300">
                Mostrando <span className="font-semibold">{produtosFiltrados.length}</span> de{' '}
                <span className="font-semibold">{totalItems}</span> produtos
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPage(1)}
                  disabled={page === 1}
                  className="px-3 py-1.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg disabled:opacity-50 hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors"
                >
                  Primeira
                </button>
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="px-4 py-1.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg disabled:opacity-50 hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors"
                >
                  Anterior
                </button>
                <div className="px-4 py-1.5 text-sm text-gray-700 dark:text-gray-300">
                  Pagina <span className="font-semibold">{page}</span> de{' '}
                  <span className="font-semibold">{totalPages}</span>
                </div>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="px-4 py-1.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg disabled:opacity-50 hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors"
                >
                  Proxima
                </button>
                <button
                  onClick={() => setPage(totalPages)}
                  disabled={page === totalPages}
                  className="px-3 py-1.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg disabled:opacity-50 hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors"
                >
                  Ultima
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* MODAL DE CADASTRO/EDICAO */}
      <ProductModal
        show={showProductModal}
        editMode={editMode}
        formData={formData}
        categorias={categorias}
        fornecedores={fornecedores}
        onClose={() => {
          setShowProductModal(false);
          resetForm();
        }}
        onSubmit={handleSubmit}
        onNomeChange={handleNomeChange}
        onCodigoBarrasChange={handleCodigoBarrasChange}
        onCategoriaChange={handleCategoriaChange}
        onMarcaChange={handleMarcaChange}
        onFabricanteChange={handleFabricanteChange}
        onDescricaoChange={handleDescricaoChange}
        onFornecedorChange={handleFornecedorChange}
        onTipoChange={handleTipoChange}
        onUnidadeChange={handleUnidadeChange}
        onPrecoCustoChange={handlePrecoCustoChange}
        onPrecoCustoBlur={handlePrecoCustoBlur}
        onPrecoVendaChange={handlePrecoVendaChange}
        onPrecoVendaBlur={handlePrecoVendaBlur}
        onMargemChange={handleMargemChange}
        onMargemBlur={handleMargemBlur}
        onQuantidadeChange={handleQuantidadeChange}
        onQuantidadeMinimaChange={handleQuantidadeMinimaChange}
        onAtivoChange={handleAtivoChange}
        onLoteChange={handleLoteChange}
        onDataFabricacaoChange={handleDataFabricacaoChange}
        onDataValidadeChange={handleDataValidadeChange}
      />

      {/* MODAL DE DETALHES */}
      {showDetailModal && selectedProduct && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl max-w-3xl w-full">
            <div className="bg-gradient-to-r from-blue-500 to-blue-600 px-6 py-4 flex justify-between items-center rounded-t-xl">
              <h2 className="text-2xl font-bold text-white">Detalhes do Produto</h2>
              <button
                onClick={() => setShowDetailModal(false)}
                className="text-white hover:text-gray-200"
              >
                <X className="w-6 h-6" />
              </button>
            </div>
            <div className="p-6 max-h-[70vh] overflow-y-auto">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold text-gray-800 dark:text-white border-b pb-2">
                    Informacoes Basicas
                  </h3>
                  <div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">Nome</p>
                    <p className="text-base font-semibold text-gray-900 dark:text-white">
                      {selectedProduct.nome}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">Codigo de Barras</p>
                    <p className="text-base font-mono text-gray-900 dark:text-white">
                      {selectedProduct.codigo_barras || 'N/A'}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">Categoria</p>
                    <p className="text-base text-gray-900 dark:text-white">
                      {selectedProduct.categoria}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">Fornecedor</p>
                    <p className="text-base text-gray-900 dark:text-white">
                      {selectedProduct.fornecedor_nome || 'Nao informado'}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">Marca</p>
                    <p className="text-base text-gray-900 dark:text-white">
                      {selectedProduct.marca || 'N/A'}
                    </p>
                  </div>
                </div>
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold text-gray-800 dark:text-white border-b pb-2">
                    Estoque e Precos
                  </h3>
                  <div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">Quantidade em Estoque</p>
                    <p className="text-base font-semibold text-gray-900 dark:text-white">
                      {selectedProduct.quantidade} {selectedProduct.unidade_medida}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">Estoque Minimo</p>
                    <p className="text-base text-gray-900 dark:text-white">
                      {selectedProduct.quantidade_minima}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">Preco de Custo</p>
                    <p className="text-base font-semibold text-gray-900 dark:text-white">
                      {formatCurrency(selectedProduct.preco_custo)}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">Preco de Venda</p>
                    <p className="text-base font-semibold text-green-600 dark:text-green-400">
                      {formatCurrency(selectedProduct.preco_venda)}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">Margem de Lucro</p>
                    <p className="text-base font-semibold text-blue-600 dark:text-blue-400">
                      {selectedProduct.margem_lucro?.toFixed(1) || 0}%
                    </p>
                  </div>
                </div>
              </div>
            </div>
            <div className="border-t border-gray-200 dark:border-gray-700 px-6 py-4 flex justify-end">
              <button
                onClick={() => setShowDetailModal(false)}
                className="px-6 py-2.5 bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-white rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
              >
                Fechar
              </button>
            </div>
          </div>
        </div>
      )}
      {/* MODAL DE AJUSTE DE ESTOQUE */}
      {showStockModal && selectedProduct && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl max-w-md w-full">
            <div className="bg-gradient-to-r from-purple-500 to-purple-600 px-6 py-4 flex justify-between items-center rounded-t-xl">
              <h2 className="text-2xl font-bold text-white">Ajustar Estoque</h2>
              <button
                onClick={() => setShowStockModal(false)}
                className="text-white hover:text-gray-200"
              >
                <X className="w-6 h-6" />
              </button>
            </div>
            <div className="p-6">
              <div className="mb-4 p-4 bg-blue-50 dark:bg-blue-900 rounded-lg">
                <p className="text-sm text-gray-700 dark:text-gray-300">
                  <span className="font-semibold">Produto:</span> {selectedProduct.nome}
                </p>
                <p className="text-sm text-gray-700 dark:text-gray-300 mt-1">
                  <span className="font-semibold">Estoque Atual:</span>{' '}
                  {selectedProduct.quantidade} {selectedProduct.unidade_medida}
                </p>
              </div>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Tipo de Operacao
                  </label>
                  <select
                    value={stockAdjust.operacao}
                    onChange={(e) =>
                      setStockAdjust({
                        ...stockAdjust,
                        operacao: e.target.value as 'entrada' | 'saida',
                      })
                    }
                    className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="entrada">Entrada (Adicionar)</option>
                    <option value="saida">Saida (Remover)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Quantidade
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0.01"
                    value={stockAdjust.quantidade}
                    onChange={(e) =>
                      setStockAdjust({
                        ...stockAdjust,
                        quantidade: parseFloat(e.target.value) || 0,
                      })
                    }
                    className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="0.00"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Motivo
                  </label>
                  <select
                    value={stockAdjust.motivo}
                    onChange={(e) => {
                      setStockAdjust({ ...stockAdjust, motivo: e.target.value });
                      setStockMotivoError(false);
                    }}
                    className={`w-full px-4 py-2.5 border ${
                      stockMotivoError ? 'border-red-500' : 'border-gray-300'
                    } dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500`}
                  >
                    <option value="">Selecione um motivo</option>
                    {motivosPadrao.map(m => (
                      <option key={m} value={m}>{m}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Notas (opcional)
                  </label>
                  <textarea
                    value={stockNotes}
                    onChange={(e) => setStockNotes(e.target.value)}
                    rows={3}
                    className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="Detalhes adicionais..."
                  />
                </div>
                <div className="p-4 bg-yellow-50 dark:bg-yellow-900 rounded-lg">
                  <p className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                    Novo Estoque Previsto:
                  </p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">
                    {stockAdjust.operacao === 'entrada'
                      ? selectedProduct.quantidade + stockAdjust.quantidade
                      : selectedProduct.quantidade - stockAdjust.quantidade}{' '}
                    {selectedProduct.unidade_medida}
                  </p>
                </div>
              </div>
            </div>
            <div className="border-t border-gray-200 dark:border-gray-700 px-6 py-4 flex justify-end gap-3">
              <button
                onClick={() => setShowStockModal(false)}
                className="px-6 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors"
              >
                Cancelar
              </button>
              <button
                onClick={handleStockAdjust}
                disabled={stockAdjust.quantidade <= 0}
                className="px-6 py-2.5 bg-purple-500 text-white rounded-lg hover:bg-purple-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
              >
                <FileText className="w-5 h-5" />
                Confirmar Ajuste
              </button>
            </div>
          </div>
        </div>
      )}

      {/* MODAL DE HISTORICO */}
      {showProductHistory && selectedProduct && (
        <ProductHistoryModal
          produto={selectedProduct}
          onClose={() => {
            setShowProductHistory(false);
            setSelectedProduct(null);
          }}
        />
      )}