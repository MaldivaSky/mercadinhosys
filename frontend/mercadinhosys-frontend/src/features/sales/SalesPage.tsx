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
import { showToast } from "../../utils/toast";

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

// Interfaces para tipagem
interface Venda {
    id: number;
    codigo: string;
    cliente?: {
        id?: number;
        nome: string;
        telefone?: string;
        cpf?: string;
    };
    funcionario?: {
        id?: number;
        nome: string;
        email?: string;
    };
    subtotal: number;
    desconto: number;
    total: number;
    forma_pagamento: string;
    valor_recebido: number;
    troco: number;
    data: string;
    data_formatada: string;
    status: string;
    quantidade_itens: number;
    observacoes?: string;
}

interface ItemVenda {
    id: number;
    produto_nome: string;
    quantidade: number;
    preco_unitario: number;
    total_item: number;
    desconto_item: number;
}

interface VendaDetalhada extends Venda {
    itens: ItemVenda[];
}

interface FormaPagamento {
    quantidade: number;
    total: number;
}

interface Estatisticas {
    total_vendas: number;
    quantidade_vendas: number;
    ticket_medio: number;
    total_descontos: number;
    total_valor_recebido: number;
    total_itens: number;
    formas_pagamento: Record<string, FormaPagamento>;
}

interface Paginacao {
    estatisticas: Estatisticas;
    pagina_atual: number;
    total_paginas: number;
    total_itens: number;
    itens_por_pagina: number;
    tem_anterior: boolean;
    tem_proxima: boolean;
}

function formatCurrency(value: number) {
    return value.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

// Função utilitária para obter data local no formato YYYY-MM-DD (Evita erro de UTC/ISO)
function getLocalDateISO(date: Date = new Date()) {
    const d = new Date(date);
    d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
    return d.toISOString().split('T')[0];
}

export default function SalesPage() {
    const [vendas, setVendas] = useState<Venda[]>([]);
    const [loading, setLoading] = useState<boolean>(true);
    const [erro, setErro] = useState<string | null>(null);
    const [estatisticas, setEstatisticas] = useState<Estatisticas>({
        total_vendas: 0,
        quantidade_vendas: 0,
        ticket_medio: 0,
        total_descontos: 0,
        total_valor_recebido: 0,
        total_itens: 0,
        formas_pagamento: {},
    });
    const [filtros, setFiltros] = useState({
        data_inicio: getLocalDateISO(new Date(Date.now() - 90 * 24 * 60 * 60 * 1000)),
        data_fim: getLocalDateISO(),
        search: "",
        status: "",
        forma_pagamento: "",
        funcionario_id: "",
        cliente_id: "",
        min_total: "",
        max_total: "",
        page: 1,
        per_page: 20,
    });
    const [paginacao, setPaginacao] = useState<Paginacao | null>(null);
    const [modalDetalhesAberto, setModalDetalhesAberto] = useState(false);
    const [detalhesVenda, setDetalhesVenda] = useState<VendaDetalhada | null>(null);
    const [loadingDetalhes, setLoadingDetalhes] = useState(false);

    // Estados para análises
    const [analisesData, setAnalisesData] = useState<any>(null);
    const [loadingAnalises, setLoadingAnalises] = useState(false);
    const [menuExportarAberto, setMenuExportarAberto] = useState(false);

    // ✅ Estado para controlar expansão das análises e Filtro Ativo
    const [analisesExpandidas, setAnalisesExpandidas] = useState(false);
    const [activeFilterLabel, setActiveFilterLabel] = useState<string>("");

    // ✅ Debounce para carregamento de dados (evitar múltiplas requisições ao digitar)
    useEffect(() => {
        const timer = setTimeout(() => {
            if (filtros.page === 1) {
                // Carregar ambos em paralelo para melhor UX, 
                // mas dar prioridade visual para a listagem de vendas
                carregarVendas();

                // Pequeno atraso para as análises (que são mais pesadas) 
                // para não travar o worker do backend simultaneamente
                setTimeout(() => {
                    carregarAnalises();
                }, 100);
            }
        }, 600); // 600ms de debounce

        return () => clearTimeout(timer);
    }, [filtros.data_inicio, filtros.data_fim, filtros.search, filtros.status, filtros.forma_pagamento, filtros.funcionario_id, filtros.cliente_id]);

    // Carregar vendas quando apenas a página muda (sem recarregar análises, sem debounce necessário)
    useEffect(() => {
        if (filtros.page > 1) {
            carregarVendasApenas();
        }
    }, [filtros.page]);

    // Fechar menu de exportação ao clicar fora
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

    async function carregarAnalises() {
        setLoadingAnalises(true);
        try {
            const params: any = {};
            if (filtros.data_inicio) params.data_inicio = filtros.data_inicio;
            if (filtros.data_fim) params.data_fim = filtros.data_fim;
            if (filtros.forma_pagamento) params.forma_pagamento = filtros.forma_pagamento;
            if (filtros.funcionario_id) params.funcionario_id = filtros.funcionario_id;
            if (filtros.cliente_id) params.cliente_id = filtros.cliente_id;
            if (filtros.status) params.status = filtros.status;

            const response = await apiClient.get("/vendas/estatisticas", { params });
            console.log("📈 Análises carregadas:", response.data);
            setAnalisesData(response.data);
        } catch (err: any) {
            console.error("❌ Erro ao carregar análises:", err);
        } finally {
            setLoadingAnalises(false);
        }
    }

    async function carregarVendas() {
        setLoading(true);
        setErro(null);

        try {
            const params: any = {
                page: filtros.page,
                per_page: filtros.per_page,
            };

            // Adicionar filtros apenas se tiverem valor
            if (filtros.search) params.search = filtros.search;
            if (filtros.data_inicio) params.data_inicio = filtros.data_inicio;
            if (filtros.data_fim) params.data_fim = filtros.data_fim;
            if (filtros.status) params.status = filtros.status;
            if (filtros.forma_pagamento) params.forma_pagamento = filtros.forma_pagamento;
            if (filtros.funcionario_id) params.funcionario_id = filtros.funcionario_id;
            if (filtros.cliente_id) params.cliente_id = filtros.cliente_id;
            if (filtros.min_total) params.min_total = filtros.min_total;
            if (filtros.max_total) params.max_total = filtros.max_total;

            const response = await apiClient.get("/vendas", { params });
            console.log("📊 Resposta da API de vendas:", response.data);

            setVendas(response.data.vendas || []);

            const estatisticasFromApi = response.data.paginacao?.estatisticas || {
                total_vendas: 0,
                quantidade_vendas: 0,
                ticket_medio: 0,
                total_descontos: 0,
                total_valor_recebido: 0,
                total_itens: 0,
                formas_pagamento: {},
            };

            setEstatisticas(estatisticasFromApi);
            setPaginacao(response.data.paginacao || null);
        } catch (err: unknown) {
            console.error("❌ Erro ao carregar vendas:", err);
            const mensagemErro = (err as { response?: { data?: { error?: string } } }).response?.data?.error || (err as Error).message || "Erro desconhecido";
            setErro(`Erro ao carregar vendas: ${mensagemErro}`);
        } finally {
            setLoading(false);
        }
    }

    // ✅ Nova função: carregar apenas vendas (para paginação)
    async function carregarVendasApenas() {
        setLoading(true);
        setErro(null);

        try {
            const params: any = {
                page: filtros.page,
                per_page: filtros.per_page,
            };

            if (filtros.search) params.search = filtros.search;
            if (filtros.data_inicio) params.data_inicio = filtros.data_inicio;
            if (filtros.data_fim) params.data_fim = filtros.data_fim;
            if (filtros.status) params.status = filtros.status;
            if (filtros.forma_pagamento) params.forma_pagamento = filtros.forma_pagamento;
            if (filtros.funcionario_id) params.funcionario_id = filtros.funcionario_id;
            if (filtros.cliente_id) params.cliente_id = filtros.cliente_id;
            if (filtros.min_total) params.min_total = filtros.min_total;
            if (filtros.max_total) params.max_total = filtros.max_total;

            const response = await apiClient.get("/vendas", { params });

            setVendas(response.data.vendas || []);
            setPaginacao(response.data.paginacao || null);

            // Scroll suave para o topo da tabela
            document.getElementById('tabela-vendas')?.scrollIntoView({ behavior: 'smooth' });
        } catch (err: unknown) {
            console.error("❌ Erro ao carregar vendas:", err);
            const mensagemErro = (err as { response?: { data?: { error?: string } } }).response?.data?.error || (err as Error).message || "Erro desconhecido";
            setErro(`Erro ao carregar vendas: ${mensagemErro}`);
        } finally {
            setLoading(false);
        }
    }

    // Handlers de filtro
    function handleFiltroChange(e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) {
        if (e.target.name === "data_inicio" || e.target.name === "data_fim") {
            setActiveFilterLabel(""); // Desmarca botão rápido se digitar input manual
        }
        setFiltros((prev) => ({
            ...prev,
            [e.target.name]: e.target.value,
            page: 1, // Resetar página ao filtrar
        }));
    }

    function limparFiltros() {
        setActiveFilterLabel("");
        setFiltros({
            data_inicio: getLocalDateISO(new Date(Date.now() - 90 * 24 * 60 * 60 * 1000)),
            data_fim: getLocalDateISO(),
            search: "",
            status: "",
            forma_pagamento: "",
            funcionario_id: "",
            cliente_id: "",
            min_total: "",
            max_total: "",
            page: 1,
            per_page: 20,
        });
    }

    // Paginação
    function mudarPagina(novaPagina: number) {
        setFiltros((prev) => ({ ...prev, page: novaPagina }));
    }

    // Abrir modal de detalhes
    async function abrirDetalhes(venda: Venda) {
        setLoadingDetalhes(true);
        setModalDetalhesAberto(true);

        try {
            const response = await apiClient.get(`/vendas/${venda.id}`);
            console.log("📋 Detalhes da venda:", response.data);
            setDetalhesVenda(response.data.venda);
        } catch (err: any) {
            console.error("❌ Erro ao carregar detalhes:", err);
            showToast.error(`Erro ao carregar detalhes da venda: ${err.response?.data?.error || err.message}`);
            setModalDetalhesAberto(false);
        } finally {
            setLoadingDetalhes(false);
        }
    }

    // Cancelar venda
    async function cancelarVenda(vendaId: number) {
        if (!confirm("Tem certeza que deseja cancelar esta venda? Os produtos serão devolvidos ao estoque.")) return;

        try {
            await showToast.promise(apiClient.post(`/vendas/${vendaId}/cancelar`, {
                motivo: "Cancelamento via painel de vendas"
            }), {
                loading: 'Cancelando venda...',
                success: 'Venda cancelada com sucesso!',
                error: (err: any) => `Erro ao cancelar venda: ${err.response?.data?.error || err.message}`
            });
            carregarVendas();
        } catch (error) {
            // Erro tratado pelo promise
        }
    }

    // Funções de exportação
    function exportarCSV() {
        try {
            const headers = [
                "Código", "Cliente", "Funcionário", "Subtotal", "Desconto", "Total",
                "Forma Pagamento", "Valor Recebido", "Troco", "Data", "Status", "Qtd Itens"
            ];

            const rows = vendas.map(v => [
                v.codigo,
                v.cliente?.nome || "Consumidor Final",
                v.funcionario?.nome || "Não Informado",
                v.subtotal.toFixed(2),
                v.desconto.toFixed(2),
                v.total.toFixed(2),
                v.forma_pagamento.replace(/_/g, " "),
                v.valor_recebido.toFixed(2),
                v.troco.toFixed(2),
                v.data_formatada,
                v.status,
                v.quantidade_itens
            ]);

            const csvContent = [
                headers.join(","),
                ...rows.map(row => row.map(cell => `"${cell}"`).join(","))
            ].join("\n");

            const blob = new Blob(["\ufeff" + csvContent], { type: "text/csv;charset=utf-8;" });
            const link = document.createElement("a");
            const url = URL.createObjectURL(blob);
            link.setAttribute("href", url);
            link.setAttribute("download", `vendas-${new Date().toISOString().split('T')[0]}.csv`);
            link.style.visibility = "hidden";
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

            setMenuExportarAberto(false);
            showToast.success("CSV exportado com sucesso!");
        } catch (err: any) {
            console.error("❌ Erro ao exportar CSV:", err);
            showToast.error(`Erro ao exportar CSV: ${err.message}`);
        }
    }

    async function exportarExcel() {
        try {
            const dados = vendas.map(v => ({
                "Código": v.codigo,
                "Cliente": v.cliente?.nome || "Consumidor Final",
                "CPF": v.cliente?.cpf || "-",
                "Funcionário": v.funcionario?.nome || "Não Informado",
                "Subtotal": v.subtotal,
                "Desconto": v.desconto,
                "Total": v.total,
                "Forma Pagamento": v.forma_pagamento.replace(/_/g, " ").toUpperCase(),
                "Valor Recebido": v.valor_recebido,
                "Troco": v.troco,
                "Data": v.data_formatada,
                "Status": v.status.toUpperCase(),
                "Qtd Itens": v.quantidade_itens,
                "Observações": v.observacoes || "-"
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
            link.setAttribute("download", `vendas-${new Date().toISOString().split('T')[0]}.xls`);
            link.style.visibility = "hidden";
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

            setMenuExportarAberto(false);
            showToast.success("Excel exportado com sucesso!");
        } catch (err: any) {
            console.error("❌ Erro ao exportar Excel:", err);
            showToast.error(`Erro ao exportar Excel: ${err.message}`);
        }
    }

    async function exportarJSON() {
        try {
            const response = await apiClient.get("/vendas/relatorio-diario");
            const dataStr = JSON.stringify(response.data, null, 2);
            const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr);
            const exportFileDefaultName = `relatorio-vendas-${new Date().toISOString().split('T')[0]}.json`;
            const linkElement = document.createElement('a');
            linkElement.setAttribute('href', dataUri);
            linkElement.setAttribute('download', exportFileDefaultName);
            linkElement.click();

            setMenuExportarAberto(false);
            showToast.success("JSON exportado com sucesso!");
        } catch (err: any) {
            console.error("❌ Erro ao exportar JSON:", err);
            showToast.error(`Erro ao exportar JSON: ${err.response?.data?.error || err.message}`);
        }
    }

    return (
        <div className="p-4 md:p-8 max-w-[1600px] mx-auto bg-[#F8FAFC] dark:bg-slate-950 min-h-screen font-sans transition-colors duration-300">
            {/* Cabeçalho Premium */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
                <div>
                    <h1 className="text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight transition-colors">Painel de Vendas</h1>
                    <p className="text-sm text-slate-500 dark:text-slate-400 mt-1 font-medium transition-colors">Acompanhe e analise o faturamento da sua loja</p>
                </div>
                <div className="flex gap-3">
                    {/* Menu de Exportação */}
                    <div className="relative export-menu-container">
                        <button
                            onClick={() => setMenuExportarAberto(!menuExportarAberto)}
                            className="bg-indigo-600 text-white px-5 py-2.5 rounded-xl font-medium hover:bg-indigo-700 hover:shadow-lg hover:shadow-indigo-200 transition-all flex items-center gap-2"
                        >
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                            Exportar
                            <svg className={`w-4 h-4 transition-transform ${menuExportarAberto ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                            </svg>
                        </button>

                        {/* Dropdown Menu */}
                        {menuExportarAberto && (
                            <div className="absolute right-0 mt-2 w-56 bg-white rounded-lg shadow-xl border border-gray-200 z-50 overflow-hidden">
                                <div className="py-1">
                                    <button
                                        onClick={exportarExcel}
                                        className="w-full text-left px-4 py-3 hover:bg-green-50 transition-colors flex items-center gap-3 text-gray-700"
                                    >
                                        <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                        </svg>
                                        <div>
                                            <div className="font-medium">Excel (.xls)</div>
                                            <div className="text-xs text-gray-500">Planilha editável</div>
                                        </div>
                                    </button>

                                    <button
                                        onClick={exportarCSV}
                                        className="w-full text-left px-4 py-3 hover:bg-blue-50 transition-colors flex items-center gap-3 text-gray-700"
                                    >
                                        <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                                        </svg>
                                        <div>
                                            <div className="font-medium">CSV (.csv)</div>
                                            <div className="text-xs text-gray-500">Dados separados por vírgula</div>
                                        </div>
                                    </button>

                                    <button
                                        onClick={exportarJSON}
                                        className="w-full text-left px-4 py-3 hover:bg-purple-50 transition-colors flex items-center gap-3 text-gray-700"
                                    >
                                        <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                                        </svg>
                                        <div>
                                            <div className="font-medium">JSON (.json)</div>
                                            <div className="text-xs text-gray-500">Relatório completo</div>
                                        </div>
                                    </button>
                                </div>

                                <div className="border-t border-gray-200 px-4 py-2 bg-gray-50">
                                    <p className="text-xs text-gray-600">
                                        📊 {vendas.length} vendas • {formatCurrency(estatisticas.total_vendas)}
                                    </p>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Filtros Inteligentes */}
            <div className="bg-white dark:bg-slate-900 p-5 md:p-6 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 mb-8 transition-colors">
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-4 border-b border-slate-100 dark:border-slate-800/60 pb-4">
                    <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100 flex items-center gap-2 transition-colors">
                        <div className="p-2 bg-indigo-50 dark:bg-indigo-500/10 rounded-lg text-indigo-600 dark:text-indigo-400 transition-colors">
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
                            </svg>
                        </div>
                        Filtros Avançados
                    </h2>

                    <div className="flex flex-wrap items-center gap-2">
                        {[
                            { label: "Hoje", days: 0 },
                            { label: "Ontem", days: 1 },
                            { label: "7 Dias", days: 7 },
                            { label: "30 Dias", days: 30 },
                            { label: "Este Mês", type: "month" },
                        ].map((filtro, idx) => {
                            const isActive = activeFilterLabel === filtro.label;
                            return (
                                <button
                                    key={idx}
                                    onClick={() => {
                                        let start = new Date();
                                        let end = new Date();

                                        if (filtro.type === "month") {
                                            start = new Date(new Date().getFullYear(), new Date().getMonth(), 1);
                                            end = new Date(new Date().getFullYear(), new Date().getMonth() + 1, 0);
                                        } else if (filtro.days === 1) {
                                            start.setDate(start.getDate() - 1);
                                            end.setDate(end.getDate() - 1);
                                        } else {
                                            start.setDate(start.getDate() - (filtro.days || 0));
                                        }

                                        setActiveFilterLabel(filtro.label);

                                        setFiltros(prev => ({
                                            ...prev,
                                            data_inicio: getLocalDateISO(start),
                                            data_fim: getLocalDateISO(end),
                                            page: 1
                                        }));
                                    }}
                                    className={`px-4 py-2 text-sm font-semibold rounded-xl transition-all duration-200 border ${isActive
                                        ? "bg-indigo-600 text-white border-indigo-600 shadow-md shadow-indigo-200 dark:shadow-indigo-900/50 ring-2 ring-indigo-600 dark:ring-indigo-500 ring-offset-2 dark:ring-offset-slate-900"
                                        : "bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700 hover:border-slate-300"
                                        }`}
                                >
                                    {filtro.label}
                                </button>
                            );
                        })}

                        <button
                            onClick={limparFiltros}
                            className="text-sm text-red-600 hover:text-red-700 hover:bg-red-50 px-4 py-2 rounded-xl transition-colors font-semibold flex items-center gap-1 border border-transparent hover:border-red-100 ml-1"
                        >
                            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                            </svg>
                            Limpar
                        </button>
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
                    {/* Período */}
                    <div className="col-span-1 md:col-span-2 grid grid-cols-2 gap-4 bg-[#F8FAFC] dark:bg-slate-800/40 p-4 rounded-xl border border-slate-100 dark:border-slate-700/50 transition-colors">
                        <div>
                            <label className="block text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-widest mb-1.5 transition-colors">Data Início</label>
                            <input
                                type="date"
                                name="data_inicio"
                                value={filtros.data_inicio}
                                onChange={handleFiltroChange}
                                className="w-full px-4 py-2.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-slate-800 dark:text-slate-200 text-sm font-medium focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 focus:border-indigo-500 transition-all shadow-sm outline-none color-scheme-dark"
                            />
                        </div>
                        <div>
                            <label className="block text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-widest mb-1.5 transition-colors">Data Fim</label>
                            <input
                                type="date"
                                name="data_fim"
                                value={filtros.data_fim}
                                onChange={handleFiltroChange}
                                className="w-full px-4 py-2.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-slate-800 dark:text-slate-200 text-sm font-medium focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 focus:border-indigo-500 transition-all shadow-sm outline-none color-scheme-dark"
                            />
                        </div>
                    </div>

                    <div>
                        <label className="block text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-widest mb-1.5 transition-colors">Status</label>
                        <select
                            name="status"
                            value={filtros.status}
                            onChange={handleFiltroChange}
                            className="w-full px-4 py-2.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-slate-800 dark:text-slate-200 text-sm font-medium focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 focus:border-indigo-500 transition-all shadow-sm outline-none cursor-pointer"
                        >
                            <option value="">Status Geral</option>
                            <option value="finalizada">✅ Finalizada</option>
                            <option value="cancelada">❌ Cancelada</option>
                            <option value="em_andamento">⏳ Em Andamento</option>
                        </select>
                    </div>

                    <div className="self-end pb-1 lg:pb-0 lg:self-auto">
                        <label className="block text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-widest mb-1.5 lg:mt-0 transition-colors">Formas de Pagamento</label>
                        <select
                            name="forma_pagamento"
                            value={filtros.forma_pagamento}
                            onChange={handleFiltroChange}
                            className="w-full px-4 py-2.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-slate-800 dark:text-slate-200 text-sm font-medium focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 focus:border-indigo-500 transition-all shadow-sm outline-none cursor-pointer"
                        >
                            <option value="">Qualquer Forma</option>
                            <option value="dinheiro">💵 Dinheiro</option>
                            <option value="cartao_credito">💳 Crédito</option>
                            <option value="cartao_debito">💳 Débito</option>
                            <option value="pix">💠 PIX</option>
                            <option value="fiado">📝 Fiado</option>
                        </select>
                    </div>

                    <div className="col-span-1 md:col-span-2 lg:col-span-4 mt-2">
                        <label className="block text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-widest mb-1.5 transition-colors">Buscar Inteligente</label>
                        <div className="relative border-t border-slate-100 dark:border-slate-800/80 pt-4">
                            <input
                                type="text"
                                name="search"
                                placeholder="Digite nome do cliente, funcionário, CPF, código da venda..."
                                value={filtros.search}
                                onChange={handleFiltroChange}
                                className="w-full pl-11 pr-4 py-3 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-slate-800 dark:text-slate-200 text-sm font-medium focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 focus:border-indigo-500 transition-all shadow-sm outline-none"
                            />
                            <div className="absolute inset-y-0 top-4 left-0 flex items-center pl-4 pointer-events-none">
                                <svg className="w-5 h-5 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                                </svg>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* KPIs Principais em Grid Dinâmico (Distribuídos em 4 Colunas Equilibradas) */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5 mb-8">
                {/* 1. Total Vendido (Destaque Principal) */}
                <div className="bg-gradient-to-br from-indigo-500 to-indigo-700 dark:from-indigo-600 dark:to-indigo-800 p-6 rounded-2xl shadow-lg relative overflow-hidden group hover:-translate-y-1 transition-all duration-300">
                    <div className="absolute -right-4 -top-4 opacity-10 transform group-hover:scale-110 transition-transform duration-500 pointer-events-none">
                        <svg className="w-32 h-32 text-indigo-100" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z" />
                        </svg>
                    </div>
                    <div className="flex items-center gap-3 mb-2 relative z-10">
                        <div className="p-2 bg-white/20 rounded-xl text-white backdrop-blur-md">
                            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                        </div>
                        <div className="text-xs font-bold text-indigo-50 uppercase tracking-widest">Total Faturado</div>
                    </div>
                    <div className="text-3xl font-black text-white mt-1 mb-2 relative z-10">
                        {formatCurrency(estatisticas.total_vendas)}
                    </div>
                    {analisesData?.vendas_por_dia?.length >= 2 && (
                        <div className="mt-1 flex items-center gap-1 text-[11px]">
                            {(() => {
                                const hoje = analisesData.vendas_por_dia[analisesData.vendas_por_dia.length - 1]?.total || 0;
                                const ontem = analisesData.vendas_por_dia[analisesData.vendas_por_dia.length - 2]?.total || 0;
                                const diff = ontem > 0 ? ((hoje - ontem) / ontem * 100) : 0;
                                return diff > 0 ? (
                                    <span className="text-emerald-300 font-bold flex items-center bg-emerald-500/20 px-2 py-0.5 rounded-md">↑ {diff.toFixed(1)}% <span className="font-normal text-indigo-100/80 ml-1">vs ontem</span></span>
                                ) : diff < 0 ? (
                                    <span className="text-rose-300 font-bold flex items-center bg-rose-500/20 px-2 py-0.5 rounded-md">↓ {Math.abs(diff).toFixed(1)}% <span className="font-normal text-indigo-100/80 ml-1">vs ontem</span></span>
                                ) : <span className="text-indigo-200 bg-indigo-500/20 px-2 py-0.5 rounded-md">Estável</span>;
                            })()}
                        </div>
                    )}
                </div>

                {/* 2. Lucro Real */}
                <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 hover:shadow-md hover:-translate-y-1 transition-all duration-300 relative overflow-hidden group flex flex-col justify-center">
                    <div className="absolute -right-4 -top-4 opacity-[0.03] dark:opacity-[0.05] transform group-hover:scale-110 transition-transform duration-500 pointer-events-none">
                        <svg className="w-32 h-32 text-emerald-500" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M4 4a2 2 0 00-2 2v4a2 2 0 002 2V6h10a2 2 0 00-2-2H4zm2 6a2 2 0 012-2h8a2 2 0 012 2v4a2 2 0 01-2 2H8a2 2 0 01-2-2v-4zm6 4a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" />
                        </svg>
                    </div>
                    <div className="flex flex-wrap items-center justify-between mb-2 gap-2">
                        <div className="flex items-center gap-3">
                            <div className="p-2.5 bg-emerald-100 dark:bg-emerald-500/10 rounded-xl text-emerald-600 dark:text-emerald-400">
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                            </div>
                            <div className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-widest">Lucro</div>
                        </div>
                        <div className="text-[10px] sm:text-xs font-bold text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-500/10 px-2 py-1 rounded-md border border-emerald-100 dark:border-emerald-500/20 whitespace-nowrap self-start sm:self-auto">
                            Margem: {analisesData?.estatisticas_gerais?.total_valor
                                ? (((Number(analisesData.estatisticas_gerais.total_lucro ?? 0) / Number(analisesData.estatisticas_gerais.total_valor)) * 100).toFixed(1) + "%")
                                : "--"}
                        </div>
                    </div>
                    <div className="text-2xl lg:text-3xl font-black text-slate-800 dark:text-slate-100 mt-2">
                        {analisesData?.estatisticas_gerais
                            ? formatCurrency(Number(analisesData.estatisticas_gerais.total_lucro ?? 0))
                            : <span className="text-lg text-slate-400 font-medium animate-pulse flex items-center gap-2">
                                <span className="w-2 h-2 bg-slate-300 rounded-full animate-bounce"></span>
                                Computando
                            </span>
                        }
                    </div>
                </div>

                {/* 3. Ticket Médio */}
                <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 hover:shadow-md hover:-translate-y-1 transition-all duration-300 relative overflow-hidden group flex flex-col justify-center">
                    <div className="flex items-center gap-3 mb-3">
                        <div className="p-2.5 bg-sky-100 dark:bg-sky-500/10 rounded-xl text-sky-600 dark:text-sky-400">
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                            </svg>
                        </div>
                        <div className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-widest">Tkt Médio</div>
                    </div>
                    <div className="text-2xl lg:text-3xl font-black text-slate-800 dark:text-slate-100 group-hover:text-sky-600 dark:group-hover:text-sky-400 transition-colors">
                        {formatCurrency(estatisticas.ticket_medio)}
                    </div>
                    <div className="text-[11px] text-slate-400 mt-1 font-medium select-none">Valor por transação</div>
                </div>

                {/* 4. Itens por Venda */}
                <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 hover:shadow-md hover:-translate-y-1 transition-all duration-300 relative overflow-hidden group flex flex-col justify-center">
                    <div className="flex items-center gap-3 mb-3">
                        <div className="p-2.5 bg-amber-100 dark:bg-amber-500/10 rounded-xl text-amber-600 dark:text-amber-400">
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" />
                            </svg>
                        </div>
                        <div className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-widest">Vol / Venda</div>
                    </div>
                    <div className="text-2xl lg:text-3xl font-black text-slate-800 dark:text-slate-100 group-hover:text-amber-600 dark:group-hover:text-amber-400 transition-colors">
                        {estatisticas.quantidade_vendas > 0
                            ? (estatisticas.total_itens / estatisticas.quantidade_vendas).toFixed(1)
                            : "0.0"} <span className="text-sm text-slate-400 font-medium">un</span>
                    </div>
                    <div className="text-[11px] text-slate-400 mt-1 font-medium select-none">Média de Itens</div>
                </div>
            </div>

            {/* ✅ ANÁLISES EM BLOCO EXPANSÍVEL */}
            <details className="mb-8 bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 overflow-hidden group transition-colors duration-300" open={analisesExpandidas}>
                <summary
                    className="bg-gradient-to-r from-slate-800 to-slate-900 dark:from-slate-800/80 dark:to-slate-950 text-white p-5 md:p-6 cursor-pointer flex items-center justify-between hover:from-slate-700 hover:to-slate-800 dark:hover:from-slate-800 dark:hover:to-slate-900 transition-all shadow-sm list-none select-none outline-none border-b border-transparent dark:border-slate-800"
                    onClick={(e) => {
                        e.preventDefault(); // Controllamos via state
                        setAnalisesExpandidas(!analisesExpandidas);
                    }}
                >
                    <div className="flex items-center gap-4">
                        <div className="p-3 bg-white/10 rounded-xl backdrop-blur-sm">
                            <svg className="w-7 h-7 text-indigo-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                            </svg>
                        </div>
                        <div>
                            <h2 className="font-bold text-xl tracking-tight text-white">Análises Inteligentes e Previsões</h2>
                            <p className="text-sm text-slate-400 mt-1 font-medium">Gráficos de tendência, top produtos e métricas do período</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-3">
                        {!analisesExpandidas && (
                            <span className="hidden md:inline-block text-xs font-semibold bg-white/10 px-3 py-1.5 rounded-lg text-slate-300">
                                {analisesData?.vendas_por_dia?.length || 0} dias faturados
                            </span>
                        )}
                        <div className={`p-2 rounded-full bg-white/5 transition-transform duration-300 ${analisesExpandidas ? 'rotate-180 bg-white/20' : ''}`}>
                            <svg className="w-5 h-5 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                            </svg>
                        </div>
                    </div>
                </summary>

                <div className="p-6">
                    {loadingAnalises ? (
                        <div className="text-center py-12">
                            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
                            <p className="mt-4 text-gray-700">Carregando análises...</p>
                        </div>
                    ) : analisesData && (
                        <div className="space-y-6">
                            {/* Cards de Comparação Rápida */}
                            {analisesData.vendas_por_dia && analisesData.vendas_por_dia.length > 0 && (
                                <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
                                    {/* Hoje vs Ontem */}
                                    <div className="bg-gradient-to-br from-indigo-500 to-blue-600 rounded-2xl p-6 text-white shadow-md relative overflow-hidden group hover:-translate-y-1 transition-transform">
                                        <div className="absolute -right-4 -top-4 opacity-10 transform group-hover:scale-110 transition-transform duration-500">
                                            <svg className="w-24 h-24 text-white" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M12 7a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0V8.414l-4.293 4.293a1 1 0 01-1.414 0L8 10.414l-4.293 4.293a1 1 0 01-1.414-1.414l5-5a1 1 0 011.414 0L11 10.586 14.586 7H12z" clipRule="evenodd" /></svg>
                                        </div>
                                        <div className="flex items-center justify-between mb-3 relative z-10">
                                            <span className="text-sm font-bold uppercase tracking-widest text-indigo-100">Hoje vs Ontem</span>
                                            {(() => {
                                                const hoje = analisesData.vendas_por_dia[analisesData.vendas_por_dia.length - 1]?.total || 0;
                                                const ontem = analisesData.vendas_por_dia[analisesData.vendas_por_dia.length - 2]?.total || 0;
                                                const diff = ontem > 0 ? ((hoje - ontem) / ontem * 100) : 0;
                                                return diff >= 0 ? (
                                                    <span className="text-emerald-300 text-xs font-bold bg-emerald-500/20 px-2 py-1 rounded-md">+{diff.toFixed(1)}%</span>
                                                ) : (
                                                    <span className="text-rose-300 text-xs font-bold bg-rose-500/20 px-2 py-1 rounded-md">{diff.toFixed(1)}%</span>
                                                );
                                            })()}
                                        </div>
                                        <div className="text-3xl font-black relative z-10">
                                            {formatCurrency(analisesData.vendas_por_dia[analisesData.vendas_por_dia.length - 1]?.total || 0)}
                                        </div>
                                        <div className="text-xs font-medium text-indigo-200 mt-2 relative z-10">
                                            Ontem: {formatCurrency(analisesData.vendas_por_dia[analisesData.vendas_por_dia.length - 2]?.total || 0)}
                                        </div>
                                    </div>

                                    {/* Esta Semana */}
                                    <div className="bg-gradient-to-br from-emerald-500 to-teal-600 rounded-2xl p-6 text-white shadow-md relative overflow-hidden group hover:-translate-y-1 transition-transform">
                                        <div className="absolute -right-4 -top-4 opacity-10 transform group-hover:scale-110 transition-transform duration-500">
                                            <svg className="w-24 h-24 text-white" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clipRule="evenodd" /></svg>
                                        </div>
                                        <div className="flex items-center justify-between mb-3 relative z-10">
                                            <span className="text-sm font-bold uppercase tracking-widest text-emerald-100">Esta Semana</span>
                                        </div>
                                        <div className="text-3xl font-black relative z-10">
                                            {formatCurrency(analisesData.vendas_por_dia.slice(-7).reduce((sum: number, v: any) => sum + v.total, 0))}
                                        </div>
                                        <div className="text-xs font-medium text-emerald-200 mt-2 relative z-10">Faturamento últimos 7 dias</div>
                                    </div>

                                    {/* Previsão */}
                                    {analisesData.previsao_vendas && analisesData.previsao_vendas.length > 0 && (
                                        <div className="bg-gradient-to-br from-purple-500 to-fuchsia-600 rounded-2xl p-6 text-white shadow-md relative overflow-hidden group hover:-translate-y-1 transition-transform">
                                            <div className="absolute -right-4 -top-4 opacity-10 transform group-hover:scale-110 transition-transform duration-500">
                                                <svg className="w-24 h-24 text-white" fill="currentColor" viewBox="0 0 20 20"><path d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM14 15a4 4 0 00-8 0v3h8v-3zM6 8a2 2 0 11-4 0 2 2 0 014 0zM16 18v-3a5.972 5.972 0 00-.75-2.906A3.005 3.005 0 0119 15v3h-3zM4.75 12.094A5.973 5.973 0 004 15v3H1v-3a3 3 0 013.75-2.906z" /></svg>
                                            </div>
                                            <div className="flex items-center justify-between mb-3 relative z-10">
                                                <span className="text-sm font-bold uppercase tracking-widest text-purple-100">Previsão 7 Dias</span>
                                                <span className="text-xs font-bold bg-white/20 px-2 py-1 rounded-md backdrop-blur-sm">🤖 IA</span>
                                            </div>
                                            <div className="text-3xl font-black relative z-10">
                                                {formatCurrency(analisesData.previsao_vendas.reduce((sum: number, v: any) => sum + v.total, 0))}
                                            </div>
                                            <div className="text-xs font-medium text-purple-200 mt-2 relative z-10">
                                                Média Estimada: {formatCurrency(analisesData.previsao_vendas.reduce((sum: number, v: any) => sum + v.total, 0) / 7)}/dia
                                            </div>
                                        </div>
                                    )}

                                    {/* Melhor Dia */}
                                    <div className="bg-gradient-to-br from-amber-500 to-orange-500 rounded-2xl p-6 text-white shadow-md relative overflow-hidden group hover:-translate-y-1 transition-transform">
                                        <div className="absolute -right-4 -top-4 opacity-[0.15] transform group-hover:scale-110 transition-transform duration-500">
                                            <svg className="w-24 h-24 text-white" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" clipRule="evenodd" /></svg>
                                        </div>
                                        <div className="flex items-center justify-between mb-3 relative z-10">
                                            <span className="text-sm font-bold uppercase tracking-widest text-amber-100">Melhor Dia</span>
                                            <span className="text-xl">🏆</span>
                                        </div>
                                        <div className="text-3xl font-black relative z-10">
                                            {formatCurrency(Math.max(...analisesData.vendas_por_dia.map((v: any) => v.total)))}
                                        </div>
                                        <div className="text-xs font-medium text-amber-100 mt-2 relative z-10">
                                            Módulo Campeão: {(() => {
                                                const melhorDia = analisesData.vendas_por_dia.reduce((max: any, v: any) => v.total > max.total ? v : max);
                                                const data = new Date(melhorDia.data);
                                                return `${String(data.getDate()).padStart(2, '0')}/${String(data.getMonth() + 1).padStart(2, '0')}`;
                                            })()}
                                        </div>
                                    </div>

                                    {/* Melhor Cliente */}
                                    {analisesData.vendas_por_cliente && analisesData.vendas_por_cliente.length > 0 && (
                                        <div className="bg-gradient-to-br from-rose-500 to-pink-600 rounded-2xl p-6 text-white shadow-md relative overflow-hidden group hover:-translate-y-1 transition-transform">
                                            <div className="absolute -right-4 -top-4 opacity-10 transform group-hover:scale-110 transition-transform duration-500">
                                                <svg className="w-24 h-24 text-white" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" /></svg>
                                            </div>
                                            <div className="flex items-center justify-between mb-3 relative z-10">
                                                <span className="text-sm font-bold uppercase tracking-widest text-rose-100">Melhor Cliente</span>
                                                <span className="text-xl">👑</span>
                                            </div>
                                            <div className="text-2xl font-black relative z-10 truncate" title={analisesData.vendas_por_cliente[0]?.cliente}>
                                                {analisesData.vendas_por_cliente[0]?.cliente || "Consumidor Final"}
                                            </div>
                                            <div className="text-xs font-medium text-rose-200 mt-2 relative z-10 flex items-center gap-1">
                                                <span>Total Comprado: {formatCurrency(analisesData.vendas_por_cliente[0]?.total || 0)}</span>
                                            </div>
                                        </div>
                                    )}

                                    {/* Melhor Horário */}
                                    {analisesData.vendas_por_hora && analisesData.vendas_por_hora.length > 0 && (
                                        <div className="bg-gradient-to-br from-indigo-500 to-cyan-600 rounded-2xl p-6 text-white shadow-md relative overflow-hidden group hover:-translate-y-1 transition-transform">
                                            <div className="absolute -right-4 -top-4 opacity-10 transform group-hover:scale-110 transition-transform duration-500">
                                                <svg className="w-24 h-24 text-white" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" /></svg>
                                            </div>
                                            <div className="flex items-center justify-between mb-3 relative z-10">
                                                <span className="text-sm font-bold uppercase tracking-widest text-indigo-100">Melhor Horário</span>
                                                <span className="text-xl">⏰</span>
                                            </div>
                                            <div className="text-3xl font-black relative z-10">
                                                {(() => {
                                                    const melhorHora = analisesData.vendas_por_hora.reduce((max: any, v: any) => v.total > max.total ? v : max);
                                                    return `${melhorHora.hora}h às ${melhorHora.hora + 1}h`;
                                                })()}
                                            </div>
                                            <div className="text-xs font-medium text-indigo-200 mt-2 relative z-10">
                                                Pico: {formatCurrency(analisesData.vendas_por_hora.reduce((max: any, v: any) => v.total > max.total ? v : max)?.total || 0)}
                                            </div>
                                        </div>
                                    )}

                                    {/* Melhor Produto */}
                                    {analisesData.produtos_mais_vendidos && analisesData.produtos_mais_vendidos.length > 0 && (
                                        <div className="bg-gradient-to-br from-violet-500 to-purple-700 rounded-2xl p-6 text-white shadow-md relative overflow-hidden group hover:-translate-y-1 transition-transform">
                                            <div className="absolute -right-4 -top-4 opacity-10 transform group-hover:scale-110 transition-transform duration-500">
                                                <svg className="w-24 h-24 text-white" fill="currentColor" viewBox="0 0 20 20"><path d="M3 1a1 1 0 000 2h1.22l.305 1.222a.997.997 0 00.01.042l1.358 5.43-.893.892C3.74 11.846 4.632 14 6.414 14H15a1 1 0 000-2H6.414l1-1H14a1 1 0 00.894-.553l3-6A1 1 0 0017 3H6.28l-.31-1.243A1 1 0 005 1H3zM16 16.5a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0zM6.5 18a1.5 1.5 0 100-3 1.5 1.5 0 000 3z" /></svg>
                                            </div>
                                            <div className="flex items-center justify-between mb-3 relative z-10">
                                                <span className="text-sm font-bold uppercase tracking-widest text-violet-100">Melhor Produto</span>
                                                <span className="text-xl">🌟</span>
                                            </div>
                                            <div className="text-xl font-black relative z-10 truncate" title={analisesData.produtos_mais_vendidos[0]?.nome}>
                                                {analisesData.produtos_mais_vendidos[0]?.nome || "Nenhum"}
                                            </div>
                                            <div className="text-xs font-medium text-violet-200 mt-2 relative z-10">
                                                Total Vendido: {formatCurrency(analisesData.produtos_mais_vendidos[0]?.total || 0)}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            )}

                            {/* Gráfico de Tendência */}
                            {analisesData.vendas_por_dia && analisesData.vendas_por_dia.length > 0 && (
                                <div className="bg-white p-6 rounded-lg border border-gray-200">
                                    <h3 className="text-lg font-semibold text-gray-900 mb-4">📈 Histórico e Previsão de Vendas</h3>
                                    <div className="h-80">
                                        <Line
                                            data={{
                                                labels: analisesData.vendas_por_dia.map((v: any) => {
                                                    const date = new Date(v.data);
                                                    return `${date.getDate()}/${date.getMonth() + 1}`;
                                                }),
                                                datasets: [
                                                    {
                                                        label: "Vendas",
                                                        data: analisesData.vendas_por_dia.map((v: any) => v.total),
                                                        borderColor: "#3B82F6",
                                                        backgroundColor: "rgba(59, 130, 246, 0.1)",
                                                        fill: true,
                                                        tension: 0.4,
                                                        pointRadius: 4,
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
                                                            label: (context) => formatCurrency(context.parsed.y || 0),
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
                            )}

                            {/* Grid de Gráficos */}
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                                {/* Formas de Pagamento */}
                                {analisesData.formas_pagamento && analisesData.formas_pagamento.length > 0 && (
                                    <div className="bg-white p-6 rounded-lg border border-gray-200">
                                        <h3 className="text-lg font-semibold text-gray-900 mb-4">💳 Formas de Pagamento</h3>
                                        <div className="h-64 flex items-center justify-center">
                                            <Doughnut
                                                data={{
                                                    labels: analisesData.formas_pagamento.map((f: any) => f.forma.replace(/_/g, " ").toUpperCase()),
                                                    datasets: [{
                                                        data: analisesData.formas_pagamento.map((f: any) => f.total),
                                                        backgroundColor: ["#3B82F6", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6"],
                                                        borderWidth: 0,
                                                    }],
                                                }}
                                                options={{
                                                    responsive: true,
                                                    maintainAspectRatio: false,
                                                    cutout: '60%',
                                                    plugins: {
                                                        legend: { position: "bottom" },
                                                        tooltip: {
                                                            callbacks: {
                                                                label: (context) => formatCurrency(context.parsed || 0),
                                                            },
                                                        },
                                                    },
                                                }}
                                            />
                                        </div>
                                    </div>
                                )}

                                {/* Vendas por Hora */}
                                {analisesData.vendas_por_hora && analisesData.vendas_por_hora.length > 0 && (
                                    <div className="bg-white p-6 rounded-lg border border-gray-200">
                                        <h3 className="text-lg font-semibold text-gray-900 mb-4">🕐 Vendas por Horário</h3>
                                        <div className="h-64">
                                            <Bar
                                                data={{
                                                    labels: analisesData.vendas_por_hora.map((v: any) => `${v.hora}h`),
                                                    datasets: [{
                                                        label: "Vendas",
                                                        data: analisesData.vendas_por_hora.map((v: any) => v.quantidade),
                                                        backgroundColor: "#EC4899",
                                                        borderRadius: 4,
                                                    }],
                                                }}
                                                options={{
                                                    responsive: true,
                                                    maintainAspectRatio: false,
                                                    plugins: { legend: { display: false } },
                                                    scales: {
                                                        y: { beginAtZero: true },
                                                    },
                                                }}
                                            />
                                        </div>
                                    </div>
                                )}
                            </div>

                            {/* Top Produtos */}
                            {analisesData.produtos_mais_vendidos && analisesData.produtos_mais_vendidos.length > 0 && (
                                <div className="bg-white p-6 rounded-lg border border-gray-200">
                                    <h3 className="text-lg font-semibold text-gray-900 mb-4">🛍️ Top 10 Produtos Mais Vendidos</h3>
                                    <div className="h-64">
                                        <Bar
                                            data={{
                                                labels: analisesData.produtos_mais_vendidos.slice(0, 10).map((p: any) => p.nome.substring(0, 20)),
                                                datasets: [{
                                                    label: "Quantidade",
                                                    data: analisesData.produtos_mais_vendidos.slice(0, 10).map((p: any) => p.quantidade),
                                                    backgroundColor: "#10B981",
                                                    borderRadius: 4,
                                                }],
                                            }}
                                            options={{
                                                indexAxis: "y",
                                                responsive: true,
                                                maintainAspectRatio: false,
                                                plugins: { legend: { display: false } },
                                            }}
                                        />
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </details>

            {/* Tabela de Vendas Premium */}
            <div id="tabela-vendas" className="bg-white dark:bg-slate-900 rounded-2xl shadow-[0_2px_10px_-3px_rgba(6,81,237,0.1)] border border-slate-200 dark:border-slate-800 overflow-hidden mb-8 transition-colors duration-300">
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center p-6 border-b border-slate-100 dark:border-slate-800/60 gap-4">
                    <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2 transition-colors">
                        <div className="w-2 h-6 bg-indigo-500 rounded-full"></div>
                        Lista de Vendas
                    </h2>
                    {paginacao && (
                        <div className="flex items-center gap-4 text-sm">
                            <span className="text-slate-500 dark:text-slate-400 font-medium transition-colors">Exibindo registros da loja</span>
                            <span className="bg-indigo-50 dark:bg-indigo-500/10 text-indigo-700 dark:text-indigo-400 px-3 py-1 rounded-full font-bold transition-colors">
                                {paginacao.total_itens} vendas encontradas
                            </span>
                        </div>
                    )}
                </div>
                {loading ? (
                    <div className="text-center py-16">
                        <div className="inline-block animate-spin rounded-full h-10 w-10 border-4 border-indigo-200 border-t-indigo-600 mb-4"></div>
                        <p className="text-slate-500 font-medium">Buscando registros refinados...</p>
                    </div>
                ) : erro ? (
                    <div className="text-center py-16 px-4">
                        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-red-100 text-red-500 mb-4">
                            <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                        </div>
                        <div className="text-red-600 font-bold mb-2">Erro na comunicação com o banco</div>
                        <p className="text-slate-500 mb-6">{erro}</p>
                        <button
                            onClick={carregarVendas}
                            className="bg-red-500 text-white px-6 py-2.5 rounded-xl font-semibold hover:bg-red-600 transition-colors shadow-sm"
                        >
                            Tentar Novamente
                        </button>
                    </div>
                ) : vendas.length === 0 ? (
                    <div className="text-center py-16 px-4">
                        <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-slate-50 text-slate-300 mb-4 ring-8 ring-slate-50">
                            <svg className="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
                            </svg>
                        </div>
                        <h3 className="text-lg font-bold text-slate-700 mb-1">Nenhum registro encontrado</h3>
                        <p className="text-sm text-slate-500 max-w-sm mx-auto">
                            {filtros.search || filtros.status || filtros.forma_pagamento
                                ? "Não encontramos vendas para a combinação atual de filtros. Tente limpar os filtros e buscar novamente."
                                : "Ainda não existem vendas registradas para este período selecionado."}
                        </p>
                    </div>
                ) : (
                    <>
                        <div className="overflow-x-auto">
                            <table className="min-w-full text-sm text-left border-collapse whitespace-nowrap">
                                <thead className="bg-[#F8FAFC] dark:bg-slate-800/40">
                                    <tr>
                                        <th className="p-4 text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider border-b border-slate-200 dark:border-slate-700/50">Ref / Código</th>
                                        <th className="p-4 text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider border-b border-slate-200 dark:border-slate-700/50">Cliente</th>
                                        <th className="p-4 text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider border-b border-slate-200 dark:border-slate-700/50">Vendedor</th>
                                        <th className="p-4 text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider border-b border-slate-200 dark:border-slate-700/50 text-right">Subtotal</th>
                                        <th className="p-4 text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider border-b border-slate-200 dark:border-slate-700/50 text-right">Desconto</th>
                                        <th className="p-4 text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider border-b border-slate-200 dark:border-slate-700/50 text-right">Total Final</th>
                                        <th className="p-4 text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider border-b border-slate-200 dark:border-slate-700/50">Transação</th>
                                        <th className="p-4 text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider border-b border-slate-200 dark:border-slate-700/50">Data</th>
                                        <th className="p-4 text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider border-b border-slate-200 dark:border-slate-700/50 text-center">Situação</th>
                                        <th className="p-4 text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider border-b border-slate-200 dark:border-slate-700/50 text-right">Ações</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {vendas.map((venda, index) => (
                                        <tr key={venda.id} className={`border-b border-slate-100 dark:border-slate-800/60 hover:bg-indigo-50/50 dark:hover:bg-indigo-500/5 transition-colors group ${index % 2 === 0 ? 'bg-white dark:bg-slate-900' : 'bg-slate-50/30 dark:bg-slate-800/20'}`}>
                                            <td className="p-4 font-mono text-xs text-slate-400 font-medium group-hover:text-indigo-500 dark:group-hover:text-indigo-400 transition-colors">{venda.codigo.split('-')[0].toUpperCase()}</td>
                                            <td className="p-4 font-semibold text-slate-800 dark:text-slate-200 transition-colors">{venda.cliente?.nome || <span className="text-slate-400 dark:text-slate-500 font-normal italic">Consumidor Padrão</span>}</td>
                                            <td className="p-4 text-slate-600 dark:text-slate-400 transition-colors">{venda.funcionario?.nome || "-"}</td>
                                            <td className="p-4 text-right text-slate-500 dark:text-slate-400">{formatCurrency(venda.subtotal)}</td>
                                            <td className="p-4 text-right">
                                                {venda.desconto > 0 ? (
                                                    <span className="text-rose-500 font-medium bg-rose-50 dark:bg-rose-500/10 px-2 py-0.5 rounded-md">-{formatCurrency(venda.desconto)}</span>
                                                ) : <span className="text-slate-300 dark:text-slate-600">-</span>}
                                            </td>
                                            <td className="p-4 text-right font-bold text-slate-900 dark:text-slate-100 transition-colors">{formatCurrency(venda.total)}</td>
                                            <td className="p-4">
                                                <div className="flex items-center gap-1.5 text-slate-600 dark:text-slate-300 capitalize font-medium transition-colors">
                                                    {venda.forma_pagamento === 'dinheiro' && <span className="text-emerald-500 bg-emerald-50/50 dark:bg-emerald-500/10 p-1 rounded-md">💵</span>}
                                                    {venda.forma_pagamento.includes('cartao') && <span className="text-blue-500 bg-blue-50/50 dark:bg-blue-500/10 p-1 rounded-md">💳</span>}
                                                    {venda.forma_pagamento === 'pix' && <span className="text-teal-400 bg-teal-50/50 dark:bg-teal-500/10 p-1 rounded-md">💠</span>}
                                                    {venda.forma_pagamento === 'fiado' && <span className="text-orange-500 bg-orange-50/50 dark:bg-orange-500/10 p-1 rounded-md">📝</span>}
                                                    <span className="ml-1">{venda.forma_pagamento.replace(/_/g, " ")}</span>
                                                </div>
                                            </td>
                                            <td className="p-4 text-slate-500 dark:text-slate-400 text-xs font-medium transition-colors">{venda.data_formatada.replace(',', ' -')}</td>
                                            <td className="p-4 text-center">
                                                <span
                                                    className={`px-3 py-1 rounded-full text-[11px] font-bold tracking-wider uppercase ${venda.status === "finalizada"
                                                        ? "bg-emerald-100/80 text-emerald-700 border border-emerald-200"
                                                        : venda.status === "cancelada"
                                                            ? "bg-rose-100/80 text-rose-700 border border-rose-200"
                                                            : "bg-amber-100/80 text-amber-700 border border-amber-200"
                                                        }`}
                                                >
                                                    {venda.status === "finalizada" ? "Finalizada" :
                                                        venda.status === "cancelada" ? "Cancelada" : "Andamento"}
                                                </span>
                                            </td>
                                            <td className="p-4 text-right">
                                                <div className="flex items-center justify-end gap-2 opacity-80 group-hover:opacity-100 transition-opacity">
                                                    <button
                                                        onClick={() => abrirDetalhes(venda)}
                                                        className="p-1.5 text-indigo-600 hover:bg-indigo-100 rounded-lg transition-colors tooltip-trigger"
                                                        title="Ver Detalhes"
                                                    >
                                                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" /></svg>
                                                    </button>
                                                    {venda.status === "finalizada" && (
                                                        <button
                                                            onClick={() => cancelarVenda(venda.id)}
                                                            className="p-1.5 text-rose-500 hover:bg-rose-100 rounded-lg transition-colors tooltip-trigger"
                                                            title="Estornar Venda"
                                                        >
                                                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                                                        </button>
                                                    )}
                                                </div>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                        {/* Paginação */}
                        {paginacao && paginacao.total_paginas > 1 && (
                            <div className="flex flex-col md:flex-row justify-between items-center p-6 bg-white dark:bg-slate-900 border-t border-slate-100 dark:border-slate-800/60 gap-4 transition-colors">
                                <div className="text-sm text-slate-500 dark:text-slate-400 font-medium">
                                    Mostrando <span className="font-bold text-slate-800 dark:text-slate-200">{((paginacao.pagina_atual - 1) * paginacao.itens_por_pagina) + 1}</span> a{" "}
                                    <span className="font-bold text-slate-800 dark:text-slate-200">{Math.min(paginacao.pagina_atual * paginacao.itens_por_pagina, paginacao.total_itens)}</span> de{" "}
                                    <span className="font-bold text-slate-800 dark:text-slate-200">{paginacao.total_itens}</span>
                                </div>
                                <div className="flex items-center space-x-2">
                                    <button
                                        onClick={() => mudarPagina(filtros.page - 1)}
                                        disabled={!paginacao.tem_anterior}
                                        className="px-4 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-600 dark:text-slate-300 font-semibold hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-sm"
                                    >
                                        &larr; Anterior
                                    </button>
                                    <span className="px-4 py-2 text-indigo-600 dark:text-indigo-400 font-bold bg-indigo-50 dark:bg-indigo-500/10 rounded-lg shadow-sm">
                                        Pág {paginacao.pagina_atual} de {paginacao.total_paginas}
                                    </span>
                                    <button
                                        onClick={() => mudarPagina(filtros.page + 1)}
                                        disabled={!paginacao.tem_proxima}
                                        className="px-4 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-600 dark:text-slate-300 font-semibold hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-sm"
                                    >
                                        Próxima &rarr;
                                    </button>
                                </div>
                            </div>
                        )}
                    </>
                )}
            </div>

            {/* Modal de Detalhes Premium */}
            {modalDetalhesAberto && (
                <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center z-50 p-4 transition-all opacity-100">
                    <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] flex flex-col overflow-hidden transform transition-all scale-100 border border-transparent dark:border-slate-800">
                        {/* Header do Modal */}
                        <div className="flex justify-between items-center px-8 py-6 border-b border-slate-100 dark:border-slate-800/60 bg-slate-50/50 dark:bg-slate-800/40 transition-colors">
                            <div>
                                <h3 className="text-2xl font-black text-slate-800 dark:text-slate-100 tracking-tight flex items-center gap-3 transition-colors">
                                    <span className="p-2 bg-indigo-100 dark:bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 rounded-lg">
                                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                                    </span>
                                    Detalhes da Venda
                                </h3>
                                <p className="text-sm text-slate-500 dark:text-slate-400 font-medium mt-1 ml-11 transition-colors">
                                    {detalhesVenda ? `Ref: ${detalhesVenda.codigo}` : 'Carregando...'}
                                </p>
                            </div>
                            <button
                                onClick={() => setModalDetalhesAberto(false)}
                                className="w-10 h-10 flex items-center justify-center rounded-full bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700 hover:text-slate-800 dark:hover:text-slate-200 transition-colors focus:ring-2 focus:ring-slate-400 outline-none"
                            >
                                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                            </button>
                        </div>

                        {/* Corpo do Modal */}
                        <div className="p-8 overflow-y-auto custom-scrollbar flex-1 bg-white dark:bg-slate-900 transition-colors">
                            {loadingDetalhes ? (
                                <div className="text-center py-20 flex flex-col items-center justify-center">
                                    <div className="w-16 h-16 border-4 border-indigo-100 border-t-indigo-600 rounded-full animate-spin mb-6"></div>
                                    <p className="text-xl font-bold text-slate-700">Recuperando informações detalhadas</p>
                                    <p className="text-slate-500 mt-2 font-medium">Por favor, aguarde um instante...</p>
                                </div>
                            ) : detalhesVenda ? (
                                <div className="space-y-8 animate-fade-in">
                                    {/* Grip de Status e Info Básica */}
                                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                                        <div className="bg-slate-50 dark:bg-slate-800/50 p-5 rounded-2xl border border-slate-100 dark:border-slate-700/50 transition-colors">
                                            <p className="text-[11px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-widest mb-2 flex items-center gap-1.5"><svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>Situação</p>
                                            <span
                                                className={`inline-flex px-3 py-1.5 rounded-lg text-sm font-bold uppercase tracking-wider ${detalhesVenda.status === "finalizada"
                                                    ? "bg-emerald-100/80 dark:bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-500/20 shadow-sm"
                                                    : detalhesVenda.status === "cancelada"
                                                        ? "bg-rose-100/80 dark:bg-rose-500/10 text-rose-700 dark:text-rose-400 border border-rose-200 dark:border-rose-500/20 shadow-sm"
                                                        : "bg-amber-100/80 dark:bg-amber-500/10 text-amber-700 dark:text-amber-400 border border-amber-200 dark:border-amber-500/20 shadow-sm"
                                                    }`}
                                            >
                                                {detalhesVenda.status === "finalizada" ? "Finalizada" :
                                                    detalhesVenda.status === "cancelada" ? "Cancelada" : "Andamento"}
                                            </span>
                                        </div>
                                        <div className="bg-slate-50 dark:bg-slate-800/50 p-5 rounded-2xl border border-slate-100 dark:border-slate-700/50 transition-colors">
                                            <p className="text-[11px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-widest mb-2 flex items-center gap-1.5"><svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>Data da Transação</p>
                                            <p className="font-bold text-slate-800 dark:text-slate-200 text-base">{detalhesVenda.data_formatada}</p>
                                        </div>
                                        <div className="bg-slate-50 dark:bg-slate-800/50 p-5 rounded-2xl border border-slate-100 dark:border-slate-700/50 transition-colors">
                                            <p className="text-[11px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-widest mb-2 flex items-center gap-1.5"><svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg>Cliente Vinculado</p>
                                            <p className="font-bold text-slate-800 dark:text-slate-200 text-base truncate" title={detalhesVenda.cliente?.nome || "Consumidor Padrão"}>{detalhesVenda.cliente?.nome || <span className="text-slate-400 dark:text-slate-500 italic font-normal">Consumidor Padrão</span>}</p>
                                        </div>
                                        <div className="bg-slate-50 dark:bg-slate-800/50 p-5 rounded-2xl border border-slate-100 dark:border-slate-700/50 transition-colors">
                                            <p className="text-[11px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-widest mb-2 flex items-center gap-1.5"><svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>Vendedor</p>
                                            <p className="font-bold text-slate-800 dark:text-slate-200 text-base truncate" title={detalhesVenda.funcionario?.nome || "Não Informado"}>{detalhesVenda.funcionario?.nome || <span className="text-slate-400 dark:text-slate-500">-</span>}</p>
                                        </div>
                                    </div>

                                    {/* Seção Tabela de Itens */}
                                    <div className="pt-4">
                                        <h4 className="flex items-center gap-3 text-lg font-bold text-slate-800 dark:text-slate-100 mb-4 transition-colors">
                                            <div className="w-1.5 h-6 bg-indigo-500 rounded-full"></div>
                                            Itens Registrados no Fechamento
                                        </h4>
                                        <div className="border border-slate-200 dark:border-slate-700/50 rounded-2xl overflow-hidden shadow-[0_2px_10px_-3px_rgba(6,81,237,0.05)] transition-colors">
                                            <table className="min-w-full text-sm text-left">
                                                <thead className="bg-[#F8FAFC] dark:bg-slate-800/40 transition-colors">
                                                    <tr>
                                                        <th className="px-6 py-4 text-[11px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-widest border-b border-slate-200 dark:border-slate-700/50">Produto</th>
                                                        <th className="px-6 py-4 text-[11px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-widest border-b border-slate-200 dark:border-slate-700/50 text-center">Unidades</th>
                                                        <th className="px-6 py-4 text-[11px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-widest border-b border-slate-200 dark:border-slate-700/50 text-right">Preço Unitário</th>
                                                        <th className="px-6 py-4 text-[11px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-widest border-b border-slate-200 dark:border-slate-700/50 text-right">Valor Total</th>
                                                    </tr>
                                                </thead>
                                                <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60">
                                                    {detalhesVenda.itens?.map((item: ItemVenda, idx: number) => (
                                                        <tr key={item.id} className={`${idx % 2 === 0 ? 'bg-white dark:bg-slate-900' : 'bg-slate-50/30 dark:bg-slate-800/20'} hover:bg-indigo-50/30 dark:hover:bg-indigo-500/5 transition-colors`}>
                                                            <td className="px-6 py-4 font-semibold text-slate-800 dark:text-slate-200 transition-colors">{item.produto_nome}</td>
                                                            <td className="px-6 py-4 text-center font-bold">
                                                                <span className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 px-3 py-1 rounded-lg text-slate-700 dark:text-slate-200 shadow-sm inline-flex items-center justify-center min-w-[3rem] transition-colors">
                                                                    {item.quantidade}x
                                                                </span>
                                                            </td>
                                                            <td className="px-6 py-4 text-right text-slate-500 dark:text-slate-400 transition-colors">{formatCurrency(item.preco_unitario)}</td>
                                                            <td className="px-6 py-4 text-right font-black text-slate-800 dark:text-slate-100 transition-colors">{formatCurrency(item.total_item)}</td>
                                                        </tr>
                                                    ))}
                                                </tbody>
                                            </table>
                                        </div>
                                    </div>

                                    {/* Grid de Resumo Financeiro */}
                                    <div className="pt-2">
                                        <div className="grid grid-cols-1 md:grid-cols-12 gap-8 bg-gradient-to-br from-[#F8FAFC] to-slate-50 dark:from-slate-800/40 dark:to-slate-900/40 p-8 rounded-2xl border border-slate-200 dark:border-slate-800 relative overflow-hidden transition-colors">
                                            {/* Watermark decora o fundo */}
                                            <svg className="absolute right-0 bottom-0 text-slate-100 dark:text-slate-800/50 h-64 w-64 transform translate-x-1/4 translate-y-1/4 transition-colors" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1.41 16.09V20h-2.67v-1.93c-1.71-.36-3.16-1.46-3.27-3.4h1.96c.1 1.05.82 1.87 2.65 1.87 1.96 0 2.4-.98 2.4-1.59 0-.83-.44-1.61-2.67-2.14-2.48-.6-4.18-1.62-4.18-3.67 0-1.72 1.39-2.84 3.11-3.21V4h2.67v1.95c1.86.45 2.79 1.86 2.85 3.39H14.3c-.05-1.11-.64-1.87-2.22-1.87-1.5 0-2.4.68-2.4 1.64 0 .84.65 1.39 2.67 1.91s4.18 1.39 4.18 3.91c-.01 1.83-1.38 2.83-3.12 3.16z" /></svg>

                                            <div className="md:col-span-6 flex flex-col justify-center space-y-6 relative z-10">
                                                <div>
                                                    <p className="text-[11px] font-bold text-slate-400 uppercase tracking-widest mb-2 flex items-center gap-1.5"><svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" /></svg>Forma de Pagamento Base</p>
                                                    <div className="flex items-center gap-3">
                                                        <span className="text-3xl text-slate-800 dark:text-slate-100 bg-white dark:bg-slate-800 p-2 rounded-xl border border-slate-100 dark:border-slate-700 shadow-sm transition-colors">
                                                            {detalhesVenda.forma_pagamento === 'dinheiro' ? '💵' :
                                                                detalhesVenda.forma_pagamento.includes('cartao') ? '💳' :
                                                                    detalhesVenda.forma_pagamento === 'pix' ? '💠' : '📝'}
                                                        </span>
                                                        <p className="font-black text-xl text-slate-800 dark:text-slate-100 uppercase tracking-widest transition-colors">
                                                            {detalhesVenda.forma_pagamento.replace(/_/g, " ")}
                                                        </p>
                                                    </div>
                                                </div>
                                                <div>
                                                    <p className="text-[11px] font-bold text-slate-400 uppercase tracking-widest mb-1">Valor Informado / Recebido</p>
                                                    <p className="font-bold text-slate-600 dark:text-slate-300 text-lg transition-colors">{formatCurrency(detalhesVenda.valor_recebido)}</p>
                                                </div>
                                            </div>

                                            {/* Divisor Visual */}
                                            <div className="hidden md:block md:col-span-1 border-l border-dashed border-slate-300 dark:border-slate-600 mx-auto h-full relative z-10 transition-colors"></div>

                                            <div className="md:col-span-5 space-y-3 flex flex-col justify-center relative z-10">
                                                <div className="flex justify-between items-center text-slate-600 dark:text-slate-300 pb-2 border-b border-slate-200 dark:border-slate-700 transition-colors">
                                                    <span className="font-semibold text-sm uppercase tracking-wide">Subtotal</span>
                                                    <span className="font-bold text-slate-800 dark:text-slate-100">{formatCurrency(detalhesVenda.subtotal)}</span>
                                                </div>
                                                <div className="flex justify-between items-center bg-rose-50 dark:bg-rose-500/10 -mx-4 px-4 py-2.5 rounded-xl text-rose-600 dark:text-rose-400 border border-rose-100 dark:border-rose-500/20 transition-colors">
                                                    <span className="font-bold text-sm tracking-wide flex items-center gap-2"><svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 11l5-5m0 0l5 5m-5-5v12" /></svg>Desconto Aplicado</span>
                                                    <span className="font-bold font-mono text-base">
                                                        {detalhesVenda.desconto > 0 ? `-${formatCurrency(detalhesVenda.desconto)}` : formatCurrency(0)}
                                                    </span>
                                                </div>
                                                <div className="pt-4 mt-2 flex justify-between items-end">
                                                    <div className="flex flex-col">
                                                        <span className="text-[11px] font-bold uppercase tracking-widest text-slate-400 mb-1">Total Final da Venda</span>
                                                    </div>
                                                    <span className="text-4xl font-black text-indigo-600 dark:text-indigo-400 transition-colors">{formatCurrency(detalhesVenda.total)}</span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            ) : (
                                <div className="text-center py-24 flex flex-col items-center justify-center text-rose-500 bg-rose-50 rounded-2xl border border-rose-100">
                                    <div className="w-20 h-20 rounded-full bg-rose-100 flex items-center justify-center mb-6">
                                        <svg className="w-10 h-10 text-rose-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
                                    </div>
                                    <h3 className="text-2xl font-bold tracking-tight text-rose-700">Falha de Integridade</h3>
                                    <p className="text-rose-600/80 mt-2 max-w-sm">Os dados detalhados desta venda não puderam ser recuperados do servidor. Tente novamente mais tarde.</p>
                                    <button onClick={() => setModalDetalhesAberto(false)} className="mt-8 px-6 py-2 bg-rose-600 hover:bg-rose-700 text-white font-bold rounded-xl transition-colors">Voltar</button>
                                </div>
                            )}
                        </div>

                        {/* Footer do Modal */}
                        <div className="bg-[#F8FAFC] dark:bg-slate-900 border-t border-slate-200 dark:border-slate-800/60 px-8 py-5 flex items-center justify-between gap-4 flex-shrink-0 transition-colors">
                            <span className="text-xs font-bold text-slate-400 uppercase tracking-widest hidden md:block">Sistema PDV Inteligente</span>
                            <div className="flex gap-3 w-full md:w-auto justify-end">
                                <button
                                    onClick={() => setModalDetalhesAberto(false)}
                                    className="px-6 py-3 rounded-xl font-bold text-slate-600 dark:text-slate-300 hover:bg-white dark:hover:bg-slate-800 border border-transparent hover:border-slate-300 dark:hover:border-slate-600 hover:shadow-sm transition-all focus:ring-2 focus:ring-slate-200 dark:focus:ring-slate-700 outline-none"
                                >
                                    Voltar para Lista
                                </button>
                                {detalhesVenda?.status === "finalizada" && (
                                    <button
                                        onClick={() => {
                                            setModalDetalhesAberto(false);
                                            cancelarVenda(detalhesVenda.id);
                                        }}
                                        className="px-6 py-3 rounded-xl font-bold bg-white dark:bg-slate-800 text-rose-600 dark:text-rose-400 border border-rose-200 dark:border-rose-500/30 hover:bg-rose-600 dark:hover:bg-rose-600 hover:text-white dark:hover:text-white transition-all shadow-sm flex items-center justify-center gap-2 group overflow-hidden relative"
                                    >
                                        <span className="absolute inset-0 w-full h-full bg-rose-600 group-hover:bg-rose-700 transform origin-left scale-x-0 group-hover:scale-x-100 transition-transform duration-300 ease-out z-0"></span>
                                        <svg className="w-5 h-5 group-hover:-rotate-180 transition-transform duration-500 z-10 relative" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                                        <span className="z-10 relative">Estornar Transação</span>
                                    </button>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}