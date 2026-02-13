import React, { useEffect, useState } from "react";
import { Bar, Line, Doughnut } from "react-chartjs-2";
import {
    Chart as ChartJS,
    BarElement,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    ArcElement,
    Tooltip,
    Legend,
    Filler,
} from "chart.js";
import { apiClient } from "../../api/apiClient";
import { FileText, TrendingUp, TrendingDown, DollarSign, Calendar, Filter, Download, Plus, Edit2, Trash2, Eye, X, AlertCircle, CheckCircle, Wallet } from "lucide-react";
import BoletosAVencerPanel from "./components/BoletosAVencerPanel";
import ResumoFinanceiroPanel from "./components/ResumoFinanceiroPanel";

ChartJS.register(
    BarElement,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    ArcElement,
    Tooltip,
    Legend,
    Filler
);

// Interfaces
interface Despesa {
    id: number;
    descricao: string;
    categoria: string;
    tipo: 'fixa' | 'variavel';
    valor: number;
    data_despesa: string;
    forma_pagamento?: string;
    recorrente: boolean;
    fornecedor?: {
        id: number;
        nome: string;
    };
    observacoes?: string;
    created_at: string;
}

interface Estatisticas {
    total_despesas: number;
    soma_total: number;
    media_valor: number;
    despesas_mes_atual: number;
    despesas_mes_anterior: number;
    variacao_percentual: number;
    despesas_recorrentes: number;
    despesas_nao_recorrentes: number;
    despesas_por_categoria: Array<{
        categoria: string;
        total: number;
        quantidade: number;
        percentual: number;
    }>;
    evolucao_mensal?: Array<{
        mes: string;
        total: number;
        mes_nome: string;
    }>;
}

const CATEGORIAS = [
    "Salários",
    "Aluguel",
    "Energia",
    "Água",
    "Telefone",
    "Internet",
    "Impostos",
    "Fornecedores",
    "Marketing",
    "Manutenção",
    "Transporte",
    "Alimentação",
    "Outros"
];

const FORMAS_PAGAMENTO = [
    "Dinheiro",
    "PIX",
    "Cartão de Crédito",
    "Cartão de Débito",
    "Boleto",
    "Transferência",
    "Cheque"
];

function formatCurrency(value: number) {
    return value.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function formatDate(dateString: string) {
    const date = new Date(dateString);
    return date.toLocaleDateString("pt-BR");
}

export default function ExpensesPage() {
    const [despesas, setDespesas] = useState<Despesa[]>([]);
    const [loading, setLoading] = useState(true);
    const [erro, setErro] = useState<string | null>(null);
    const [estatisticas, setEstatisticas] = useState<Estatisticas | null>(null);
    
    // Filtros
    const [filtros, setFiltros] = useState({
        inicio: "",
        fim: "",
        categoria: "",
        tipo: "",
        recorrente: "",
        busca: "",
        pagina: 1,
        por_pagina: 20,
    });

    // Modais
    const [modalAberto, setModalAberto] = useState(false);
    const [modalDetalhesAberto, setModalDetalhesAberto] = useState(false);
    const [despesaSelecionada, setDespesaSelecionada] = useState<Despesa | null>(null);
    const [modoEdicao, setModoEdicao] = useState(false);

    // Form
    const [formData, setFormData] = useState({
        descricao: "",
        categoria: "",
        tipo: "variavel" as 'fixa' | 'variavel',
        valor: "",
        data_despesa: new Date().toISOString().split('T')[0],
        forma_pagamento: "",
        recorrente: false,
        observacoes: "",
    });

    // Analytics
    const [menuExportarAberto, setMenuExportarAberto] = useState(false);

    // Toast notifications
    const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

    useEffect(() => {
        if (toast) {
            const timer = setTimeout(() => setToast(null), 3000);
            return () => clearTimeout(timer);
        }
    }, [toast]);

    const showToast = (message: string, type: 'success' | 'error' = 'success') => {
        setToast({ message, type });
    };

    useEffect(() => {
        carregarDespesas();
        carregarEstatisticas();
    }, [filtros]);

    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            const target = event.target as HTMLElement;
            if (menuExportarAberto && !target.closest('.export-menu-container')) {
                setMenuExportarAberto(false);
            }
        }
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, [menuExportarAberto]);

    async function carregarDespesas() {
        setLoading(true);
        setErro(null);
        
        try {
            const params: any = {
                pagina: filtros.pagina,
                por_pagina: filtros.por_pagina,
            };

            if (filtros.busca) params.busca = filtros.busca;
            if (filtros.inicio) params.inicio = filtros.inicio;
            if (filtros.fim) params.fim = filtros.fim;
            if (filtros.categoria) params.categoria = filtros.categoria;
            if (filtros.tipo) params.tipo = filtros.tipo;
            if (filtros.recorrente) params.recorrente = filtros.recorrente;

            const response = await apiClient.get("/despesas", { params });
            console.log("📊 Despesas carregadas:", response.data);
            
            if (response.data.success) {
                setDespesas(response.data.data || []);
                console.log(`✅ ${response.data.data?.length || 0} despesas carregadas`);
            } else {
                console.warn("⚠️ Resposta sem sucesso:", response.data);
                setDespesas([]);
            }
        } catch (err: any) {
            console.error("❌ Erro ao carregar despesas:", err);
            setErro(`Erro ao carregar despesas: ${err.response?.data?.error || err.message}`);
        } finally {
            setLoading(false);
        }
    }

    async function carregarEstatisticas() {
        try {
            const params: any = {};
            if (filtros.inicio) params.inicio = filtros.inicio;
            if (filtros.fim) params.fim = filtros.fim;

            const response = await apiClient.get("/despesas/estatisticas", { params });
            console.log("📈 Estatísticas carregadas:", response.data);
            
            if (response.data.success && response.data.estatisticas) {
                setEstatisticas(response.data.estatisticas);
                console.log("✅ Estatísticas definidas:", response.data.estatisticas);
            } else {
                console.warn("⚠️ Resposta sem estatísticas:", response.data);
            }
        } catch (err: any) {
            console.error("❌ Erro ao carregar estatísticas:", err);
            console.error("❌ Detalhes do erro:", err.response?.data);
        }
    }

    function handleFiltroChange(e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) {
        setFiltros((prev) => ({
            ...prev,
            [e.target.name]: e.target.value,
            pagina: 1, // Resetar para primeira página ao filtrar
        }));
    }

    function limparFiltros() {
        setFiltros({
            inicio: "",
            fim: "",
            categoria: "",
            tipo: "",
            recorrente: "",
            busca: "",
            pagina: 1,
            por_pagina: 20,
        });
    }

    function abrirModalNovo() {
        setModoEdicao(false);
        setDespesaSelecionada(null);
        setFormData({
            descricao: "",
            categoria: "",
            tipo: "variavel",
            valor: "",
            data_despesa: new Date().toISOString().split('T')[0],
            forma_pagamento: "",
            recorrente: false,
            observacoes: "",
        });
        setModalAberto(true);
    }

    function abrirModalEdicao(despesa: Despesa) {
        setModoEdicao(true);
        setDespesaSelecionada(despesa);
        setFormData({
            descricao: despesa.descricao,
            categoria: despesa.categoria,
            tipo: despesa.tipo,
            valor: despesa.valor.toString(),
            data_despesa: despesa.data_despesa,
            forma_pagamento: despesa.forma_pagamento || "",
            recorrente: despesa.recorrente,
            observacoes: despesa.observacoes || "",
        });
        setModalAberto(true);
    }

    function abrirDetalhes(despesa: Despesa) {
        setDespesaSelecionada(despesa);
        setModalDetalhesAberto(true);
    }

    async function salvarDespesa() {
        try {
            const dados = {
                ...formData,
                valor: parseFloat(formData.valor),
            };

            if (modoEdicao && despesaSelecionada) {
                await apiClient.put(`/despesas/${despesaSelecionada.id}`, dados);
                showToast("Despesa atualizada com sucesso!");
            } else {
                await apiClient.post("/despesas", dados);
                showToast("Despesa criada com sucesso!");
            }

            setModalAberto(false);
            carregarDespesas();
            carregarEstatisticas();
        } catch (err: any) {
            console.error("❌ Erro ao salvar despesa:", err);
            showToast(`Erro ao salvar despesa: ${err.response?.data?.error || err.message}`, 'error');
        }
    }

    async function excluirDespesa(id: number) {
        if (!confirm("Tem certeza que deseja excluir esta despesa?")) return;

        try {
            await apiClient.delete(`/despesas/${id}`);
            showToast("Despesa excluída com sucesso!");
            carregarDespesas();
            carregarEstatisticas();
        } catch (err: any) {
            console.error("❌ Erro ao excluir despesa:", err);
            showToast(`Erro ao excluir despesa: ${err.response?.data?.error || err.message}`, 'error');
        }
    }

    function exportarCSV() {
        try {
            const headers = ["Descrição", "Categoria", "Tipo", "Valor", "Data", "Forma Pagamento", "Recorrente"];
            const rows = despesas.map(d => [
                d.descricao,
                d.categoria,
                d.tipo,
                d.valor.toFixed(2),
                formatDate(d.data_despesa),
                d.forma_pagamento || "-",
                d.recorrente ? "Sim" : "Não"
            ]);

            const csvContent = [
                headers.join(","),
                ...rows.map(row => row.map(cell => `"${cell}"`).join(","))
            ].join("\n");

            const blob = new Blob(["\ufeff" + csvContent], { type: "text/csv;charset=utf-8;" });
            const link = document.createElement("a");
            const url = URL.createObjectURL(blob);
            link.setAttribute("href", url);
            link.setAttribute("download", `despesas-${new Date().toISOString().split('T')[0]}.csv`);
            link.style.visibility = "hidden";
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            setMenuExportarAberto(false);
            showToast("CSV exportado com sucesso!");
        } catch (err: any) {
            console.error("❌ Erro ao exportar CSV:", err);
            showToast(`Erro ao exportar CSV: ${err.message}`, 'error');
        }
    }

    function exportarExcel() {
        try {
            const dados = despesas.map(d => ({
                "Descrição": d.descricao,
                "Categoria": d.categoria,
                "Tipo": d.tipo.toUpperCase(),
                "Valor": d.valor,
                "Data": formatDate(d.data_despesa),
                "Forma Pagamento": d.forma_pagamento || "-",
                "Recorrente": d.recorrente ? "Sim" : "Não",
                "Observações": d.observacoes || "-"
            }));

            const ws_data = [
                Object.keys(dados[0] || {}),
                ...dados.map(obj => Object.values(obj))
            ];

            const csvContent = ws_data.map(row => 
                row.map(cell => `"${cell}"`).join(",")
            ).join("\n");

            const blob = new Blob(["\ufeff" + csvContent], { type: "application/vnd.ms-excel;charset=utf-8;" });
            const link = document.createElement("a");
            const url = URL.createObjectURL(blob);
            link.setAttribute("href", url);
            link.setAttribute("download", `despesas-${new Date().toISOString().split('T')[0]}.xls`);
            link.style.visibility = "hidden";
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            setMenuExportarAberto(false);
            showToast("Excel exportado com sucesso!");
        } catch (err: any) {
            console.error("❌ Erro ao exportar Excel:", err);
            showToast(`Erro ao exportar Excel: ${err.message}`, 'error');
        }
    }

    return (
        <div className="p-6 max-w-7xl mx-auto bg-gray-50 dark:bg-gray-900 min-h-screen">
            {/* Toast Notification */}
            {toast && (
                <div className={`fixed top-4 right-4 z-50 px-6 py-3 rounded-lg shadow-lg flex items-center gap-2 animate-slide-in ${
                    toast.type === 'success' 
                        ? 'bg-green-500 text-white' 
                        : 'bg-red-500 text-white'
                }`}>
                    {toast.type === 'success' ? (
                        <CheckCircle className="w-5 h-5" />
                    ) : (
                        <AlertCircle className="w-5 h-5" />
                    )}
                    <span>{toast.message}</span>
                </div>
            )}
            
            {/* Header */}
            <div className="mb-8">
                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                    <div className="flex items-center space-x-4">
                        <div className="p-3 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-xl shadow-lg">
                            <Wallet className="w-8 h-8 text-white" />
                        </div>
                        <div>
                            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                                Financeiro
                            </h1>
                            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                                Despesas, boletos, contas a pagar e receber — visao completa ERP
                            </p>
                        </div>
                    </div>
                    <div className="flex flex-wrap gap-3">
                                                
                        {/* Menu Exportar */}
                        <div className="relative export-menu-container">
                            <button
                                onClick={() => setMenuExportarAberto(!menuExportarAberto)}
                                className="bg-green-500 text-white px-4 py-2.5 rounded-lg hover:bg-green-600 transition-all flex items-center gap-2 shadow-md font-medium"
                            >
                                <Download className="w-5 h-5" />
                                Exportar
                            </button>
                            
                            {menuExportarAberto && (
                                <div className="absolute right-0 mt-2 w-56 bg-white dark:bg-gray-800 rounded-xl shadow-2xl border border-gray-200 dark:border-gray-700 z-50 overflow-hidden">
                                    <div className="py-1">
                                        <button
                                            onClick={exportarExcel}
                                            className="w-full text-left px-4 py-3 hover:bg-green-50 dark:hover:bg-gray-700 transition-colors flex items-center gap-3 text-gray-700 dark:text-gray-300"
                                        >
                                            <FileText className="w-5 h-5 text-green-600" />
                                            <div>
                                                <div className="font-medium">Excel (.xls)</div>
                                                <div className="text-xs text-gray-500">Planilha editável</div>
                                            </div>
                                        </button>
                                        
                                        <button
                                            onClick={exportarCSV}
                                            className="w-full text-left px-4 py-3 hover:bg-blue-50 dark:hover:bg-gray-700 transition-colors flex items-center gap-3 text-gray-700 dark:text-gray-300"
                                        >
                                            <FileText className="w-5 h-5 text-blue-600" />
                                            <div>
                                                <div className="font-medium">CSV (.csv)</div>
                                                <div className="text-xs text-gray-500">Dados separados</div>
                                            </div>
                                        </button>
                                    </div>
                                    
                                    <div className="border-t border-gray-200 dark:border-gray-700 px-4 py-2 bg-gray-50 dark:bg-gray-900">
                                        <p className="text-xs text-gray-600 dark:text-gray-400">
                                            📊 {despesas.length} despesas • {estatisticas ? formatCurrency(estatisticas.soma_total) : "R$ 0,00"}
                                        </p>
                                    </div>
                                </div>
                            )}
                        </div>

                        <button
                            onClick={abrirModalNovo}
                            className="bg-gradient-to-r from-blue-500 to-blue-600 text-white px-6 py-2.5 rounded-lg hover:from-blue-600 hover:to-blue-700 transition-all flex items-center gap-2 shadow-lg font-medium"
                        >
                            <Plus className="w-5 h-5" />
                            Nova Despesa
                        </button>
                    </div>
                </div>
            </div>

            {/* Painel Financeiro ERP (Resumo Consolidado) */}
            <ResumoFinanceiroPanel className="mb-6" />

            {/* Métricas KPI */}
            {estatisticas && (
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                    <div className="bg-gradient-to-br from-red-50 to-red-100 dark:from-red-900/20 dark:to-red-800/20 p-6 rounded-xl shadow-md border border-red-200 dark:border-red-800">
                        <div className="flex items-center justify-between mb-2">
                            <div className="text-sm text-red-700 dark:text-red-300 font-medium">Total Despesas</div>
                            <DollarSign className="w-5 h-5 text-red-600 dark:text-red-400" />
                        </div>
                        <div className="text-2xl font-bold text-red-600 dark:text-red-400">{formatCurrency(estatisticas.soma_total)}</div>
                        <div className="text-xs text-red-600 dark:text-red-400 mt-1">{estatisticas.total_despesas} registros</div>
                    </div>

                    <div className="bg-gradient-to-br from-orange-50 to-orange-100 dark:from-orange-900/20 dark:to-orange-800/20 p-6 rounded-xl shadow-md border border-orange-200 dark:border-orange-800">
                        <div className="flex items-center justify-between mb-2">
                            <div className="text-sm text-orange-700 dark:text-orange-300 font-medium">Mês Atual</div>
                            <Calendar className="w-5 h-5 text-orange-600 dark:text-orange-400" />
                        </div>
                        <div className="text-2xl font-bold text-orange-600 dark:text-orange-400">{formatCurrency(estatisticas.despesas_mes_atual)}</div>
                        <div className={`text-xs mt-1 flex items-center gap-1 ${estatisticas.variacao_percentual > 0 ? 'text-red-600' : 'text-green-600'}`}>
                            {estatisticas.variacao_percentual > 0 ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                            {Math.abs(estatisticas.variacao_percentual).toFixed(1)}% vs mês anterior
                        </div>
                    </div>

                    <div className="bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/20 dark:to-purple-800/20 p-6 rounded-xl shadow-md border border-purple-200 dark:border-purple-800">
                        <div className="flex items-center justify-between mb-2">
                            <div className="text-sm text-purple-700 dark:text-purple-300 font-medium">Média por Despesa</div>
                            <TrendingUp className="w-5 h-5 text-purple-600 dark:text-purple-400" />
                        </div>
                        <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">{formatCurrency(estatisticas.media_valor)}</div>
                        <div className="text-xs text-purple-600 dark:text-purple-400 mt-1">Ticket médio</div>
                    </div>

                    <div className="bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 p-6 rounded-xl shadow-md border border-blue-200 dark:border-blue-800">
                        <div className="flex items-center justify-between mb-2">
                            <div className="text-sm text-blue-700 dark:text-blue-300 font-medium">Despesas Recorrentes</div>
                            <CheckCircle className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                        </div>
                        <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">{formatCurrency(estatisticas.despesas_recorrentes)}</div>
                        <div className="text-xs text-blue-600 dark:text-blue-400 mt-1">
                            {((estatisticas.despesas_recorrentes / estatisticas.soma_total) * 100).toFixed(1)}% do total
                        </div>
                    </div>
                </div>
            )}

            {/* Painel de Boletos a Vencer */}
            <BoletosAVencerPanel className="mb-6" />

            {/* Análises e Gráficos */}
            {mostrarAnalises && (
                <div className="space-y-6 mb-6">
                    {!estatisticas ? (
                        <div className="bg-white dark:bg-gray-800 p-12 rounded-xl shadow-md border border-gray-200 dark:border-gray-700 text-center">
                            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
                            <p className="text-gray-700 dark:text-gray-300">Carregando análises...</p>
                        </div>
                    ) : (
                        <>
                            {console.log("🎨 Renderizando análises:", { 
                                mostrarAnalises, 
                                temEstatisticas: !!estatisticas,
                                categorias: estatisticas?.despesas_por_categoria?.length,
                                evolucao: estatisticas?.evolucao_mensal?.length 
                            })}
                            
                            {/* Evolução Mensal */}
                            {estatisticas.evolucao_mensal && estatisticas.evolucao_mensal.length > 0 && (
                        <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md border border-gray-200 dark:border-gray-700">
                            <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white flex items-center gap-2">
                                <span>📈</span> Evolução Mensal de Despesas
                            </h3>
                            <div className="h-80">
                                <Line
                                    data={{
                                        labels: estatisticas.evolucao_mensal.map((e: any) => e.mes_nome),
                                        datasets: [
                                            {
                                                label: "Despesas (R$)",
                                                data: estatisticas.evolucao_mensal.map((e: any) => e.total),
                                                borderColor: "rgb(239, 68, 68)",
                                                backgroundColor: "rgba(239, 68, 68, 0.1)",
                                                fill: true,
                                                tension: 0.4,
                                                pointRadius: 6,
                                                pointHoverRadius: 8,
                                                pointBackgroundColor: "rgb(239, 68, 68)",
                                                pointBorderColor: "#fff",
                                                pointBorderWidth: 2,
                                            },
                                        ],
                                    }}
                                    options={{
                                        responsive: true,
                                        maintainAspectRatio: false,
                                        plugins: {
                                            legend: { display: false },
                                            tooltip: {
                                                callbacks: {
                                                    label: (context: any) => `Despesas: ${formatCurrency(context.parsed.y || 0)}`,
                                                }
                                            },
                                        },
                                        scales: {
                                            y: {
                                                beginAtZero: true,
                                                ticks: {
                                                    callback: (value: any) => formatCurrency(Number(value) || 0),
                                                },
                                            },
                                        },
                                    }}
                                />
                            </div>
                        </div>
                    )}

                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {/* Gráfico de Categorias - Barras */}
                        {estatisticas.despesas_por_categoria && estatisticas.despesas_por_categoria.length > 0 ? (
                            <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md border border-gray-200 dark:border-gray-700">
                                <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white flex items-center gap-2">
                                    <span>📊</span> Despesas por Categoria
                                </h3>
                                <div className="h-80">
                                    <Bar
                                    data={{
                                        labels: estatisticas.despesas_por_categoria.map(c => c.categoria),
                                        datasets: [
                                            {
                                                label: "Valor (R$)",
                                                data: estatisticas.despesas_por_categoria.map(c => c.total),
                                                backgroundColor: "rgba(239, 68, 68, 0.7)",
                                                borderColor: "rgb(239, 68, 68)",
                                                borderWidth: 2,
                                            },
                                        ],
                                    }}
                                    options={{
                                        responsive: true,
                                        maintainAspectRatio: false,
                                        plugins: {
                                            legend: { display: false },
                                            tooltip: {
                                                callbacks: {
                                                    label: (context) => `Valor: ${formatCurrency(context.parsed.y || 0)}`,
                                                    afterLabel: (context) => {
                                                        const item = estatisticas.despesas_por_categoria[context.dataIndex];
                                                        return `Quantidade: ${item.quantidade} despesas\nPercentual: ${item.percentual.toFixed(1)}%`;
                                                    }
                                                },
                                            },
                                        },
                                        scales: {
                                            y: {
                                                beginAtZero: true,
                                                ticks: {
                                                    callback: (value) => formatCurrency(Number(value) || 0),
                                                },
                                            },
                                        },
                                    }}
                                />
                            </div>
                        </div>
                        ) : (
                            <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md border border-gray-200 dark:border-gray-700">
                                <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white flex items-center gap-2">
                                    <span>📊</span> Despesas por Categoria
                                </h3>
                                <div className="h-80 flex items-center justify-center">
                                    <div className="text-center text-gray-500 dark:text-gray-400">
                                        <FileText className="w-16 h-16 mx-auto mb-4 opacity-50" />
                                        <p>Nenhuma despesa nos últimos 30 dias</p>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Gráfico de Pizza - Distribuição */}
                        {estatisticas.despesas_por_categoria && estatisticas.despesas_por_categoria.length > 0 ? (
                            <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md border border-gray-200 dark:border-gray-700">
                                <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white flex items-center gap-2">
                                    <span>🥧</span> Distribuição por Categoria
                                </h3>
                                <div className="h-80 flex items-center justify-center">
                                    <Doughnut
                                    data={{
                                        labels: estatisticas.despesas_por_categoria.map(c => c.categoria),
                                        datasets: [
                                            {
                                                data: estatisticas.despesas_por_categoria.map(c => c.total),
                                                backgroundColor: [
                                                    'rgba(239, 68, 68, 0.8)',
                                                    'rgba(249, 115, 22, 0.8)',
                                                    'rgba(234, 179, 8, 0.8)',
                                                    'rgba(34, 197, 94, 0.8)',
                                                    'rgba(59, 130, 246, 0.8)',
                                                    'rgba(168, 85, 247, 0.8)',
                                                    'rgba(236, 72, 153, 0.8)',
                                                    'rgba(20, 184, 166, 0.8)',
                                                    'rgba(251, 146, 60, 0.8)',
                                                    'rgba(132, 204, 22, 0.8)',
                                                ],
                                                borderWidth: 2,
                                                borderColor: '#fff',
                                            },
                                        ],
                                    }}
                                    options={{
                                        responsive: true,
                                        maintainAspectRatio: false,
                                        plugins: {
                                            legend: {
                                                position: 'right',
                                                labels: {
                                                    boxWidth: 15,
                                                    padding: 10,
                                                    font: { size: 11 }
                                                }
                                            },
                                            tooltip: {
                                                callbacks: {
                                                    label: (context) => {
                                                        const item = estatisticas.despesas_por_categoria[context.dataIndex];
                                                        return `${item.categoria}: ${formatCurrency(item.total)} (${item.percentual.toFixed(1)}%)`;
                                                    }
                                                },
                                            },
                                        },
                                    }}
                                />
                            </div>
                        </div>
                        ) : (
                            <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md border border-gray-200 dark:border-gray-700">
                                <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white flex items-center gap-2">
                                    <span>🥧</span> Distribuição por Categoria
                                </h3>
                                <div className="h-80 flex items-center justify-center">
                                    <div className="text-center text-gray-500 dark:text-gray-400">
                                        <FileText className="w-16 h-16 mx-auto mb-4 opacity-50" />
                                        <p>Nenhuma despesa nos últimos 30 dias</p>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </>
            )}
        </div>
            )}

            {/* Filtros */}
            <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md border border-gray-200 dark:border-gray-700 mb-6">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                        <Filter className="w-5 h-5" />
                        Filtros
                    </h3>
                    <button
                        onClick={limparFiltros}
                        className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
                    >
                        Limpar Filtros
                    </button>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-900 dark:text-white mb-2">
                            Buscar
                        </label>
                        <input
                            type="text"
                            name="busca"
                            value={filtros.busca}
                            onChange={handleFiltroChange}
                            placeholder="Buscar descrição..."
                            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                        />
                    </div>
                    
                    <div>
                        <label className="block text-sm font-medium text-gray-900 dark:text-white mb-2">
                            Categoria
                        </label>
                        <select
                            name="categoria"
                            value={filtros.categoria}
                            onChange={handleFiltroChange}
                            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                        >
                            <option value="">Todas as Categorias</option>
                            {CATEGORIAS.map(cat => (
                                <option key={cat} value={cat}>{cat}</option>
                            ))}
                        </select>
                    </div>
                    
                    <div>
                        <label className="block text-sm font-medium text-gray-900 dark:text-white mb-2">
                            Tipo
                        </label>
                        <select
                            name="tipo"
                            value={filtros.tipo}
                            onChange={handleFiltroChange}
                            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                        >
                            <option value="">Todos os Tipos</option>
                            <option value="fixa">Fixa</option>
                            <option value="variavel">Variável</option>
                        </select>
                    </div>
                    
                    <div>
                        <label className="block text-sm font-medium text-gray-900 dark:text-white mb-2">
                            Recorrência
                        </label>
                        <select
                            name="recorrente"
                            value={filtros.recorrente}
                            onChange={handleFiltroChange}
                            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                        >
                            <option value="">Todas</option>
                            <option value="true">Recorrentes</option>
                            <option value="false">Não Recorrentes</option>
                        </select>
                    </div>
                    
                    <div>
                        <label className="block text-sm font-medium text-gray-900 dark:text-white mb-2">
                            Data Início
                        </label>
                        <input
                            type="date"
                            name="inicio"
                            value={filtros.inicio}
                            onChange={handleFiltroChange}
                            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                        />
                    </div>
                    
                    <div>
                        <label className="block text-sm font-medium text-gray-900 dark:text-white mb-2">
                            Data Fim
                        </label>
                        <input
                            type="date"
                            name="fim"
                            value={filtros.fim}
                            onChange={handleFiltroChange}
                            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                        />
                    </div>
                </div>
            </div>

            {/* Tabela de Despesas */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md border border-gray-200 dark:border-gray-700 overflow-hidden">
                <div className="overflow-x-auto">
                    {loading ? (
                        <div className="p-12 text-center">
                            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
                            <p className="mt-4 text-gray-700 dark:text-gray-300">Carregando despesas...</p>
                        </div>
                    ) : erro ? (
                        <div className="p-12 text-center">
                            <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
                            <p className="text-red-600 dark:text-red-400">{erro}</p>
                        </div>
                    ) : despesas.length === 0 ? (
                        <div className="p-12 text-center">
                            <FileText className="w-16 h-16 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
                            <h3 className="text-xl font-semibold text-gray-700 dark:text-gray-300 mb-2">
                                Nenhuma despesa encontrada
                            </h3>
                            <p className="text-gray-500 dark:text-gray-400 mb-4">
                                Comece adicionando sua primeira despesa
                            </p>
                            <button
                                onClick={abrirModalNovo}
                                className="bg-blue-500 text-white px-6 py-2 rounded-lg hover:bg-blue-600 transition-colors"
                            >
                                Adicionar Despesa
                            </button>
                        </div>
                    ) : (
                        <table className="w-full">
                            <thead className="bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                                        Descrição
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                                        Categoria
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                                        Tipo
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                                        Valor
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                                        Data
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                                        Status
                                    </th>
                                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                                        Ações
                                    </th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                                {despesas.map((despesa) => (
                                    <tr key={despesa.id} className="hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div className="text-sm font-medium text-gray-900 dark:text-white">
                                                {despesa.descricao}
                                            </div>
                                            {despesa.fornecedor && (
                                                <div className="text-xs text-gray-500 dark:text-gray-400">
                                                    {despesa.fornecedor.nome}
                                                </div>
                                            )}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <span className="px-2 py-1 text-xs font-medium rounded-full bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200">
                                                {despesa.categoria}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                                                despesa.tipo === 'fixa' 
                                                    ? 'bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-200' 
                                                    : 'bg-orange-100 dark:bg-orange-900 text-orange-800 dark:text-orange-200'
                                            }`}>
                                                {despesa.tipo === 'fixa' ? 'Fixa' : 'Variável'}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div className="text-sm font-bold text-red-600 dark:text-red-400">
                                                {formatCurrency(despesa.valor)}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700 dark:text-gray-300">
                                            {formatDate(despesa.data_despesa)}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            {despesa.recorrente && (
                                                <span className="px-2 py-1 text-xs font-medium rounded-full bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200">
                                                    Recorrente
                                                </span>
                                            )}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                            <div className="flex items-center justify-end gap-2">
                                                <button
                                                    onClick={() => abrirDetalhes(despesa)}
                                                    className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300"
                                                    title="Ver detalhes"
                                                >
                                                    <Eye className="w-5 h-5" />
                                                </button>
                                                <button
                                                    onClick={() => abrirModalEdicao(despesa)}
                                                    className="text-yellow-600 dark:text-yellow-400 hover:text-yellow-800 dark:hover:text-yellow-300"
                                                    title="Editar"
                                                >
                                                    <Edit2 className="w-5 h-5" />
                                                </button>
                                                <button
                                                    onClick={() => excluirDespesa(despesa.id)}
                                                    className="text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-300"
                                                    title="Excluir"
                                                >
                                                    <Trash2 className="w-5 h-5" />
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </div>
                
                {/* Paginação */}
                {!loading && !erro && despesas.length > 0 && (
                    <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700 flex items-center justify-between">
                        <div className="text-sm text-gray-700 dark:text-gray-300">
                            Mostrando <span className="font-medium">{despesas.length}</span> despesas
                        </div>
                        <div className="flex items-center gap-2">
                            <button
                                onClick={() => setFiltros(prev => ({ ...prev, pagina: Math.max(1, prev.pagina - 1) }))}
                                disabled={filtros.pagina === 1}
                                className="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded-lg text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                            >
                                Anterior
                            </button>
                            <span className="text-sm text-gray-700 dark:text-gray-300">
                                Página {filtros.pagina}
                            </span>
                            <button
                                onClick={() => setFiltros(prev => ({ ...prev, pagina: prev.pagina + 1 }))}
                                disabled={despesas.length < filtros.por_pagina}
                                className="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded-lg text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                            >
                                Próxima
                            </button>
                        </div>
                    </div>
                )}
            </div>

            {/* Modal de Criação/Edição */}
            {modalAberto && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
                        <div className="p-6 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
                            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                                {modoEdicao ? "Editar Despesa" : "Nova Despesa"}
                            </h2>
                            <button
                                onClick={() => setModalAberto(false)}
                                className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                            >
                                <X className="w-6 h-6" />
                            </button>
                        </div>
                        
                        <div className="p-6 space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                    Descrição *
                                </label>
                                <input
                                    type="text"
                                    value={formData.descricao}
                                    onChange={(e) => setFormData({ ...formData, descricao: e.target.value })}
                                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                                    placeholder="Ex: Conta de energia"
                                    required
                                />
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                        Categoria *
                                    </label>
                                    <select
                                        value={formData.categoria}
                                        onChange={(e) => setFormData({ ...formData, categoria: e.target.value })}
                                        className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                                        required
                                    >
                                        <option value="">Selecione...</option>
                                        {CATEGORIAS.map(cat => (
                                            <option key={cat} value={cat}>{cat}</option>
                                        ))}
                                    </select>
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                        Tipo *
                                    </label>
                                    <select
                                        value={formData.tipo}
                                        onChange={(e) => setFormData({ ...formData, tipo: e.target.value as 'fixa' | 'variavel' })}
                                        className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                                        required
                                    >
                                        <option value="variavel">Variável</option>
                                        <option value="fixa">Fixa</option>
                                    </select>
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                        Valor (R$) *
                                    </label>
                                    <input
                                        type="number"
                                        step="0.01"
                                        value={formData.valor}
                                        onChange={(e) => setFormData({ ...formData, valor: e.target.value })}
                                        className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                                        placeholder="0.00"
                                        required
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                        Data *
                                    </label>
                                    <input
                                        type="date"
                                        value={formData.data_despesa}
                                        onChange={(e) => setFormData({ ...formData, data_despesa: e.target.value })}
                                        className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                                        required
                                    />
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                    Forma de Pagamento
                                </label>
                                <select
                                    value={formData.forma_pagamento}
                                    onChange={(e) => setFormData({ ...formData, forma_pagamento: e.target.value })}
                                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                                >
                                    <option value="">Selecione...</option>
                                    {FORMAS_PAGAMENTO.map(forma => (
                                        <option key={forma} value={forma}>{forma}</option>
                                    ))}
                                </select>
                            </div>

                            <div>
                                <label className="flex items-center gap-2 cursor-pointer">
                                    <input
                                        type="checkbox"
                                        checked={formData.recorrente}
                                        onChange={(e) => setFormData({ ...formData, recorrente: e.target.checked })}
                                        className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                                    />
                                    <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                                        Despesa Recorrente
                                    </span>
                                </label>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                    Observações
                                </label>
                                <textarea
                                    value={formData.observacoes}
                                    onChange={(e) => setFormData({ ...formData, observacoes: e.target.value })}
                                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                                    rows={3}
                                    placeholder="Informações adicionais..."
                                />
                            </div>
                        </div>

                        <div className="p-6 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-3">
                            <button
                                onClick={() => setModalAberto(false)}
                                className="px-6 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                            >
                                Cancelar
                            </button>
                            <button
                                onClick={salvarDespesa}
                                className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
                            >
                                {modoEdicao ? "Atualizar" : "Salvar"}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Modal de Detalhes */}
            {modalDetalhesAberto && despesaSelecionada && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl max-w-2xl w-full">
                        <div className="p-6 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
                            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                                Detalhes da Despesa
                            </h2>
                            <button
                                onClick={() => setModalDetalhesAberto(false)}
                                className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                            >
                                <X className="w-6 h-6" />
                            </button>
                        </div>
                        
                        <div className="p-6 space-y-4">
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                                        Descrição
                                    </label>
                                    <p className="text-lg font-semibold text-gray-900 dark:text-white">
                                        {despesaSelecionada.descricao}
                                    </p>
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                                        Valor
                                    </label>
                                    <p className="text-lg font-bold text-red-600 dark:text-red-400">
                                        {formatCurrency(despesaSelecionada.valor)}
                                    </p>
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                                        Categoria
                                    </label>
                                    <span className="inline-block px-3 py-1 text-sm font-medium rounded-full bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200">
                                        {despesaSelecionada.categoria}
                                    </span>
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                                        Tipo
                                    </label>
                                    <span className={`inline-block px-3 py-1 text-sm font-medium rounded-full ${
                                        despesaSelecionada.tipo === 'fixa' 
                                            ? 'bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-200' 
                                            : 'bg-orange-100 dark:bg-orange-900 text-orange-800 dark:text-orange-200'
                                    }`}>
                                        {despesaSelecionada.tipo === 'fixa' ? 'Fixa' : 'Variável'}
                                    </span>
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                                        Data
                                    </label>
                                    <p className="text-gray-900 dark:text-white">
                                        {formatDate(despesaSelecionada.data_despesa)}
                                    </p>
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                                        Forma de Pagamento
                                    </label>
                                    <p className="text-gray-900 dark:text-white">
                                        {despesaSelecionada.forma_pagamento || "Não informado"}
                                    </p>
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                                    Status
                                </label>
                                {despesaSelecionada.recorrente && (
                                    <span className="inline-block px-3 py-1 text-sm font-medium rounded-full bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200">
                                        Recorrente
                                    </span>
                                )}
                                {!despesaSelecionada.recorrente && (
                                    <span className="inline-block px-3 py-1 text-sm font-medium rounded-full bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200">
                                        Única
                                    </span>
                                )}
                            </div>

                            {despesaSelecionada.fornecedor && (
                                <div>
                                    <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                                        Fornecedor
                                    </label>
                                    <p className="text-gray-900 dark:text-white">
                                        {despesaSelecionada.fornecedor.nome}
                                    </p>
                                </div>
                            )}

                            {despesaSelecionada.observacoes && (
                                <div>
                                    <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                                        Observações
                                    </label>
                                    <p className="text-gray-900 dark:text-white bg-gray-50 dark:bg-gray-700 p-3 rounded-lg">
                                        {despesaSelecionada.observacoes}
                                    </p>
                                </div>
                            )}

                            <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                                <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                                    Criado em
                                </label>
                                <p className="text-sm text-gray-600 dark:text-gray-400">
                                    {formatDate(despesaSelecionada.created_at)}
                                </p>
                            </div>
                        </div>

                        <div className="p-6 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-3">
                            <button
                                onClick={() => setModalDetalhesAberto(false)}
                                className="px-6 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                            >
                                Fechar
                            </button>
                            <button
                                onClick={() => {
                                    setModalDetalhesAberto(false);
                                    abrirModalEdicao(despesaSelecionada);
                                }}
                                className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors flex items-center gap-2"
                            >
                                <Edit2 className="w-4 h-4" />
                                Editar
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
