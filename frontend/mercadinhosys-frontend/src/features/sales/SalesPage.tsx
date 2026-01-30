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
        formas_pagamento: {},
    });
    const [filtros, setFiltros] = useState({
        data_inicio: "",
        data_fim: "",
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
    
    // Novos estados para análises
    const [mostrarAnalises, setMostrarAnalises] = useState(true);
    const [analisesData, setAnalisesData] = useState<any>(null);
    const [loadingAnalises, setLoadingAnalises] = useState(false);
    const [menuExportarAberto, setMenuExportarAberto] = useState(false);

    // Carregar vendas e estatísticas
    useEffect(() => {
        carregarVendas();
        if (mostrarAnalises) {
            carregarAnalises();
        }
    }, [filtros]);

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

            const response = await apiClient.get("/vendas", { params });
            
            console.log("📊 Resposta da API de vendas:", response.data);
            
            setVendas(response.data.vendas || []);
            
            const estatisticasFromApi = response.data.paginacao?.estatisticas || {
                total_vendas: 0,
                quantidade_vendas: 0,
                ticket_medio: 0,
                total_descontos: 0,
                total_valor_recebido: 0,
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

    // Handlers de filtro
    function handleFiltroChange(e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) {
        setFiltros((prev) => ({
            ...prev,
            [e.target.name]: e.target.value,
            page: 1, // Resetar página ao filtrar
        }));
    }

    function limparFiltros() {
        setFiltros({
            data_inicio: "",
            data_fim: "",
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
            alert(`Erro ao carregar detalhes da venda: ${err.response?.data?.error || err.message}`);
            setModalDetalhesAberto(false);
        } finally {
            setLoadingDetalhes(false);
        }
    }

    // Cancelar venda
    async function cancelarVenda(vendaId: number) {
        if (!confirm("Tem certeza que deseja cancelar esta venda? Os produtos serão devolvidos ao estoque.")) return;
        
        try {
            await apiClient.post(`/vendas/${vendaId}/cancelar`, { 
                motivo: "Cancelamento via painel de vendas" 
            });
            alert("Venda cancelada com sucesso!");
            carregarVendas(); // Recarregar vendas
        } catch (err: any) {
            console.error("❌ Erro ao cancelar venda:", err);
            alert(`Erro ao cancelar venda: ${err.response?.data?.error || err.message}`);
        }
    }

    // Funções de exportação
    function exportarCSV() {
        try {
            // Cabeçalhos do CSV
            const headers = [
                "Código",
                "Cliente",
                "Funcionário",
                "Subtotal",
                "Desconto",
                "Total",
                "Forma Pagamento",
                "Valor Recebido",
                "Troco",
                "Data",
                "Status",
                "Qtd Itens"
            ];

            // Converter vendas para linhas CSV
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

            // Criar conteúdo CSV
            const csvContent = [
                headers.join(","),
                ...rows.map(row => row.map(cell => `"${cell}"`).join(","))
            ].join("\n");

            // Download
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
            alert("✅ CSV exportado com sucesso!");
        } catch (err: any) {
            console.error("❌ Erro ao exportar CSV:", err);
            alert(`Erro ao exportar CSV: ${err.message}`);
        }
    }

    async function exportarExcel() {
        try {
            // Preparar dados para Excel
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

            // Criar worksheet
            const ws_data = [
                Object.keys(dados[0] || {}),
                ...dados.map(obj => Object.values(obj))
            ];

            // Converter para CSV (Excel pode abrir CSV)
            const csvContent = ws_data.map(row => 
                row.map(cell => `"${cell}"`).join(",")
            ).join("\n");

            // Download como Excel-compatible CSV
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
            alert("✅ Excel exportado com sucesso!");
        } catch (err: any) {
            console.error("❌ Erro ao exportar Excel:", err);
            alert(`Erro ao exportar Excel: ${err.message}`);
        }
    }

    async function exportarJSON() {
        try {
            const response = await apiClient.get("/vendas/relatorio-diario");
            const dataStr = JSON.stringify(response.data, null, 2);
            const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
            const exportFileDefaultName = `relatorio-vendas-${new Date().toISOString().split('T')[0]}.json`;
            const linkElement = document.createElement('a');
            linkElement.setAttribute('href', dataUri);
            linkElement.setAttribute('download', exportFileDefaultName);
            linkElement.click();
            
            setMenuExportarAberto(false);
            alert("✅ JSON exportado com sucesso!");
        } catch (err: any) {
            console.error("❌ Erro ao exportar JSON:", err);
            alert(`Erro ao exportar JSON: ${err.response?.data?.error || err.message}`);
        }
    }

    function exportarPDF() {
        alert("📄 Exportação para PDF será implementada em breve!\n\nPor enquanto, use CSV ou Excel e converta para PDF.");
        setMenuExportarAberto(false);
    }

    return (
        <div className="p-6 max-w-7xl mx-auto bg-gray-50 min-h-screen">
            <div className="flex justify-between items-center mb-6">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900">Vendas</h1>
                    <p className="text-sm text-gray-600 mt-1">Análise completa e histórico de vendas</p>
                </div>
                <div className="flex gap-3">
                    <button
                        onClick={() => setMostrarAnalises(!mostrarAnalises)}
                        className={`px-4 py-2 rounded transition-colors flex items-center gap-2 ${
                            mostrarAnalises
                                ? "bg-blue-500 text-white hover:bg-blue-600"
                                : "bg-white text-gray-700 border border-gray-300 hover:bg-gray-50"
                        }`}
                    >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                        </svg>
                        {mostrarAnalises ? "Ocultar Análises" : "Mostrar Análises"}
                    </button>
                    
                    {/* Menu de Exportação */}
                    <div className="relative export-menu-container">
                        <button
                            onClick={() => setMenuExportarAberto(!menuExportarAberto)}
                            className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600 transition-colors flex items-center gap-2"
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
                                    
                                    <button
                                        onClick={exportarPDF}
                                        className="w-full text-left px-4 py-3 hover:bg-red-50 transition-colors flex items-center gap-3 text-gray-700"
                                    >
                                        <svg className="w-5 h-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                                        </svg>
                                        <div>
                                            <div className="font-medium">PDF (.pdf)</div>
                                            <div className="text-xs text-gray-500">Em breve</div>
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

            {/* Métricas */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
                    <div className="flex items-center gap-3 mb-2">
                        <div className="p-2 bg-green-100 rounded-lg text-green-600">
                            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                        </div>
                        <div className="text-sm font-medium text-gray-500">Total Vendido</div>
                    </div>
                    <div className="text-2xl font-bold text-gray-900">{formatCurrency(estatisticas.total_vendas)}</div>
                </div>
                
                <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
                    <div className="flex items-center gap-3 mb-2">
                        <div className="p-2 bg-blue-100 rounded-lg text-blue-600">
                            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
                            </svg>
                        </div>
                        <div className="text-sm font-medium text-gray-500">Qtd. Vendas</div>
                    </div>
                    <div className="text-2xl font-bold text-gray-900">{estatisticas.quantidade_vendas}</div>
                </div>

                <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
                    <div className="flex items-center gap-3 mb-2">
                        <div className="p-2 bg-purple-100 rounded-lg text-purple-600">
                            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                            </svg>
                        </div>
                        <div className="text-sm font-medium text-gray-500">Ticket Médio</div>
                    </div>
                    <div className="text-2xl font-bold text-gray-900">{formatCurrency(estatisticas.ticket_medio)}</div>
                </div>

                <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
                    <div className="flex items-center gap-3 mb-2">
                        <div className="p-2 bg-red-100 rounded-lg text-red-600">
                            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                        </div>
                        <div className="text-sm font-medium text-gray-500">Descontos</div>
                    </div>
                    <div className="text-2xl font-bold text-gray-900">{formatCurrency(estatisticas.total_descontos)}</div>
                </div>
            </div>

            {/* Seção de Análises Avançadas */}
            {mostrarAnalises && (
                loadingAnalises ? (
                    <div className="bg-white p-12 rounded-lg shadow-md border mb-6 text-center">
                        <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
                        <p className="mt-4 text-gray-700">Carregando análises...</p>
                    </div>
                ) : analisesData && (
                <div className="space-y-6 mb-6">
                    {/* Gráfico de Tendência */}
                    {analisesData.vendas_por_dia && analisesData.vendas_por_dia.length > 0 && (
                        <div className="bg-white p-6 rounded-lg shadow-md border">
                            <h3 className="text-lg font-semibold mb-4 text-gray-900 flex items-center gap-2">
                                <span>📈</span> Tendência de Vendas
                                <span className="text-sm font-normal text-gray-500">
                                    ({analisesData.vendas_por_dia.length} {analisesData.vendas_por_dia.length === 1 ? 'dia' : 'dias'})
                                </span>
                            </h3>
                            <div className="h-80">
                                <Line
                                    data={{
                                        labels: analisesData.vendas_por_dia.map((v: any) => {
                                            const date = new Date(v.data);
                                            return analisesData.vendas_por_dia.length === 1 
                                                ? 'Hoje'
                                                : `${date.getDate()}/${date.getMonth() + 1}`;
                                        }),
                                        datasets: [
                                            {
                                                label: "Vendas (R$)",
                                                data: analisesData.vendas_por_dia.map((v: any) => v.total),
                                                borderColor: "#3B82F6", // Blue-500
                                                backgroundColor: (context) => {
                                                    const ctx = context.chart.ctx;
                                                    const gradient = ctx.createLinearGradient(0, 0, 0, 300);
                                                    gradient.addColorStop(0, "rgba(59, 130, 246, 0.5)");
                                                    gradient.addColorStop(1, "rgba(59, 130, 246, 0.0)");
                                                    return gradient;
                                                },
                                                fill: true,
                                                tension: 0.4,
                                                pointRadius: 4,
                                                pointHoverRadius: 6,
                                                pointBackgroundColor: "#3B82F6",
                                                pointBorderColor: "#fff",
                                                pointBorderWidth: 2,
                                                borderWidth: 3,
                                            },
                                        ],
                                    }}
                                    options={{
                                        responsive: true,
                                        maintainAspectRatio: false,
                                        interaction: {
                                            mode: 'index',
                                            intersect: false,
                                        },
                                        plugins: {
                                            legend: { display: false },
                                            tooltip: {
                                                backgroundColor: 'rgba(255, 255, 255, 0.9)',
                                                titleColor: '#1F2937',
                                                bodyColor: '#4B5563',
                                                borderColor: '#E5E7EB',
                                                borderWidth: 1,
                                                padding: 10,
                                                displayColors: false,
                                                callbacks: {
                                                    label: (context) => `Vendas: ${formatCurrency(context.parsed.y || 0)}`,
                                                    afterLabel: (context) => {
                                                        const item = analisesData.vendas_por_dia[context.dataIndex];
                                                        return `Quantidade: ${item.quantidade} vendas`;
                                                    }
                                                },
                                            },
                                        },
                                        scales: {
                                            y: {
                                                beginAtZero: true,
                                                grid: {
                                                    color: '#F3F4F6',
                                                },
                                                ticks: {
                                                    callback: (value) => formatCurrency(Number(value) || 0),
                                                    font: {
                                                        family: "'Inter', sans-serif",
                                                        size: 11
                                                    },
                                                    color: '#6B7280'
                                                },
                                                border: {
                                                    display: false
                                                }
                                            },
                                            x: {
                                                grid: {
                                                    display: false
                                                },
                                                ticks: {
                                                    font: {
                                                        family: "'Inter', sans-serif",
                                                        size: 11
                                                    },
                                                    color: '#6B7280'
                                                },
                                                border: {
                                                    display: false
                                                }
                                            }
                                        },
                                    }}
                                />
                            </div>
                            {analisesData.vendas_por_dia.length === 1 && (
                                <p className="text-sm text-gray-500 mt-3 text-center">
                                    💡 Dica: Aplique filtros de data para ver a tendência ao longo do tempo
                                </p>
                            )}
                        </div>
                    )}

                    {/* Grid de 2 colunas - Top Produtos */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {/* Top Produtos */}
                        {analisesData.produtos_mais_vendidos && analisesData.produtos_mais_vendidos.length > 0 && (
                            <div className="bg-white p-6 rounded-lg shadow-md border">
                                <h3 className="text-lg font-semibold mb-4 text-gray-900 flex items-center gap-2">
                                    <span>🛍️</span> Top 10 Produtos Mais Vendidos
                                </h3>
                                <div className="h-80">
                                    <Bar
                                        data={{
                                            labels: analisesData.produtos_mais_vendidos.slice(0, 10).map((p: any) => p.nome),
                                            datasets: [
                                                {
                                                    label: "Quantidade Vendida",
                                                    data: analisesData.produtos_mais_vendidos.slice(0, 10).map((p: any) => p.quantidade),
                                                    backgroundColor: "#10B981",
                                                    borderRadius: 4,
                                                    barThickness: 20,
                                                },
                                            ],
                                        }}
                                        options={{
                                            indexAxis: "y",
                                            responsive: true,
                                            maintainAspectRatio: false,
                                            plugins: {
                                                legend: { display: false },
                                                tooltip: {
                                                    backgroundColor: 'rgba(255, 255, 255, 0.9)',
                                                    titleColor: '#1F2937',
                                                    bodyColor: '#4B5563',
                                                    borderColor: '#E5E7EB',
                                                    borderWidth: 1,
                                                    padding: 10,
                                                    displayColors: false,
                                                    callbacks: {
                                                        label: (context) => `${context.parsed.x} unidades`,
                                                        afterLabel: (context) => {
                                                            const item = analisesData.produtos_mais_vendidos[context.dataIndex];
                                                            return `Total: ${formatCurrency(item.total || 0)}`;
                                                        },
                                                    },
                                                },
                                            },
                                            scales: {
                                                x: {
                                                    beginAtZero: true,
                                                    grid: {
                                                        color: '#F3F4F6',
                                                    },
                                                    ticks: {
                                                        stepSize: 1,
                                                        font: {
                                                            family: "'Inter', sans-serif",
                                                            size: 11
                                                        },
                                                        color: '#6B7280'
                                                    },
                                                    border: {
                                                        display: false
                                                    }
                                                },
                                                y: {
                                                    grid: {
                                                        display: false
                                                    },
                                                    ticks: {
                                                        font: {
                                                            family: "'Inter', sans-serif",
                                                            size: 11
                                                        },
                                                        color: '#6B7280'
                                                    },
                                                    border: {
                                                        display: false
                                                    }
                                                }
                                            },
                                        }}
                                    />
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Grid de 2 colunas - Top Clientes e Top Fornecedores */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {/* Top Clientes */}
                        {analisesData.vendas_por_cliente && analisesData.vendas_por_cliente.length > 0 && (
                            <div className="bg-white p-6 rounded-lg shadow-md border">
                                <h3 className="text-lg font-semibold mb-4 text-gray-900 flex items-center gap-2">
                                    <span>🏅</span> Top 10 Clientes
                                </h3>
                                <div className="h-80">
                                    <Bar
                                        data={{
                                            labels: analisesData.vendas_por_cliente.slice(0, 10).map((c: any) => c.cliente),
                                            datasets: [
                                                {
                                                    label: "Total Gasto (R$)",
                                                    data: analisesData.vendas_por_cliente.slice(0, 10).map((c: any) => c.total),
                                                    backgroundColor: "#8B5CF6",
                                                    borderRadius: 4,
                                                    barThickness: 20,
                                                },
                                            ],
                                        }}
                                        options={{
                                            indexAxis: "y",
                                            responsive: true,
                                            maintainAspectRatio: false,
                                            plugins: {
                                                legend: { display: false },
                                                tooltip: {
                                                    backgroundColor: 'rgba(255, 255, 255, 0.9)',
                                                    titleColor: '#1F2937',
                                                    bodyColor: '#4B5563',
                                                    borderColor: '#E5E7EB',
                                                    borderWidth: 1,
                                                    padding: 10,
                                                    displayColors: false,
                                                    callbacks: {
                                                        label: (context) => `Total: ${formatCurrency(context.parsed.x || 0)}`,
                                                        afterLabel: (context) => {
                                                            const item = analisesData.vendas_por_cliente[context.dataIndex];
                                                            return item.quantidade ? `${item.quantidade} compras` : '';
                                                        }
                                                    },
                                                },
                                            },
                                            scales: {
                                                x: {
                                                    beginAtZero: true,
                                                    grid: {
                                                        color: '#F3F4F6',
                                                    },
                                                    ticks: {
                                                        callback: (value) => formatCurrency(Number(value) || 0),
                                                        font: {
                                                            family: "'Inter', sans-serif",
                                                            size: 11
                                                        },
                                                        color: '#6B7280'
                                                    },
                                                    border: {
                                                        display: false
                                                    }
                                                },
                                                y: {
                                                    grid: {
                                                        display: false
                                                    },
                                                    ticks: {
                                                        font: {
                                                            family: "'Inter', sans-serif",
                                                            size: 11
                                                        },
                                                        color: '#6B7280'
                                                    },
                                                    border: {
                                                        display: false
                                                    }
                                                }
                                            },
                                        }}
                                    />
                                </div>
                            </div>
                        )}

                        {/* Top Fornecedores */}
                        {analisesData.vendas_por_fornecedor && analisesData.vendas_por_fornecedor.length > 0 && (
                            <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
                                <h3 className="text-lg font-bold mb-6 text-gray-900 flex items-center gap-2">
                                    <div className="p-2 bg-orange-100 rounded-lg text-orange-600">
                                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                                        </svg>
                                    </div>
                                    Top 10 Fornecedores
                                </h3>
                                <div className="h-80">
                                    <Bar
                                        data={{
                                            labels: analisesData.vendas_por_fornecedor.slice(0, 10).map((f: any) => f.fornecedor),
                                            datasets: [
                                                {
                                                    label: "Total Vendido (R$)",
                                                    data: analisesData.vendas_por_fornecedor.slice(0, 10).map((f: any) => f.total),
                                                    backgroundColor: "#F97316", // Orange-500
                                                    borderRadius: 4,
                                                    barThickness: 20,
                                                },
                                            ],
                                        }}
                                        options={{
                                            indexAxis: "y",
                                            responsive: true,
                                            maintainAspectRatio: false,
                                            plugins: {
                                                legend: { display: false },
                                                tooltip: {
                                                    backgroundColor: 'rgba(255, 255, 255, 0.9)',
                                                    titleColor: '#1F2937',
                                                    bodyColor: '#4B5563',
                                                    borderColor: '#E5E7EB',
                                                    borderWidth: 1,
                                                    padding: 10,
                                                    displayColors: false,
                                                    callbacks: {
                                                        label: (context) => `Total: ${formatCurrency(context.parsed.x || 0)}`,
                                                        afterLabel: (context) => {
                                                            const item = analisesData.vendas_por_fornecedor[context.dataIndex];
                                                            return `${item.quantidade_vendas} vendas`;
                                                        }
                                                    },
                                                },
                                            },
                                            scales: {
                                                x: {
                                                    beginAtZero: true,
                                                    grid: {
                                                        color: '#F3F4F6',
                                                    },
                                                    ticks: {
                                                        callback: (value) => formatCurrency(Number(value) || 0),
                                                        font: {
                                                            family: "'Inter', sans-serif",
                                                            size: 11
                                                        },
                                                        color: '#6B7280'
                                                    },
                                                    border: {
                                                        display: false
                                                    }
                                                },
                                                y: {
                                                    grid: {
                                                        display: false
                                                    },
                                                    ticks: {
                                                        font: {
                                                            family: "'Inter', sans-serif",
                                                            size: 11
                                                        },
                                                        color: '#6B7280'
                                                    },
                                                    border: {
                                                        display: false
                                                    }
                                                }
                                            },
                                        }}
                                    />
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Grid de 2 colunas - Formas de Pagamento e Horários */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {/* Formas de Pagamento */}
                        {analisesData.formas_pagamento && analisesData.formas_pagamento.length > 0 && (
                            <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
                                <h3 className="text-lg font-bold mb-6 text-gray-900 flex items-center gap-2">
                                    <div className="p-2 bg-indigo-100 rounded-lg text-indigo-600">
                                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
                                        </svg>
                                    </div>
                                    Distribuição por Forma de Pagamento
                                </h3>
                                <div className="h-80 flex items-center justify-center">
                                    <Doughnut
                                        data={{
                                            labels: analisesData.formas_pagamento.map((f: any) => f.forma.replace(/_/g, " ").toUpperCase()),
                                            datasets: [
                                                {
                                                    data: analisesData.formas_pagamento.map((f: any) => f.total),
                                                    backgroundColor: [
                                                        "#3B82F6", // Blue
                                                        "#10B981", // Emerald
                                                        "#F59E0B", // Amber
                                                        "#EF4444", // Red
                                                        "#8B5CF6", // Violet
                                                    ],
                                                    borderWidth: 0,
                                                    hoverOffset: 4,
                                                },
                                            ],
                                        }}
                                        options={{
                                            responsive: true,
                                            maintainAspectRatio: false,
                                            cutout: '70%',
                                            plugins: {
                                                legend: { 
                                                    position: "bottom",
                                                    labels: {
                                                        font: {
                                                            family: "'Inter', sans-serif",
                                                            size: 11
                                                        },
                                                        usePointStyle: true,
                                                        padding: 20
                                                    }
                                                },
                                                tooltip: {
                                                    backgroundColor: 'rgba(255, 255, 255, 0.9)',
                                                    titleColor: '#1F2937',
                                                    bodyColor: '#4B5563',
                                                    borderColor: '#E5E7EB',
                                                    borderWidth: 1,
                                                    padding: 10,
                                                    callbacks: {
                                                        label: (context) => {
                                                            const label = context.label || "";
                                                            const value = context.parsed || 0;
                                                            return ` ${label}: ${formatCurrency(value)}`;
                                                        },
                                                        afterLabel: (context) => {
                                                            const item = analisesData.formas_pagamento[context.dataIndex];
                                                            return `${item.quantidade} vendas (${item.percentual.toFixed(1)}%)`;
                                                        }
                                                    },
                                                },
                                            },
                                        }}
                                    />
                                </div>
                            </div>
                        )}

                        {/* Horários de Pico */}
                        {analisesData.vendas_por_hora && analisesData.vendas_por_hora.length > 0 && (
                            <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
                                <h3 className="text-lg font-bold mb-6 text-gray-900 flex items-center gap-2">
                                    <div className="p-2 bg-pink-100 rounded-lg text-pink-600">
                                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                                        </svg>
                                    </div>
                                    Vendas por Horário
                                    <span className="text-sm font-normal text-gray-500 ml-auto">
                                        ({analisesData.vendas_por_hora.length} {analisesData.vendas_por_hora.length === 1 ? 'horário' : 'horários'})
                                    </span>
                                </h3>
                                <div className="h-80">
                                    <Bar
                                        data={{
                                            labels: analisesData.vendas_por_hora.map((v: any) => `${v.hora}h`),
                                            datasets: [
                                                {
                                                    label: "Quantidade de Vendas",
                                                    data: analisesData.vendas_por_hora.map((v: any) => v.quantidade),
                                                    backgroundColor: "#EC4899", // Pink-500
                                                    borderRadius: 4,
                                                    maxBarThickness: 40,
                                                },
                                            ],
                                        }}
                                        options={{
                                            responsive: true,
                                            maintainAspectRatio: false,
                                            plugins: {
                                                legend: { display: false },
                                                tooltip: {
                                                    backgroundColor: 'rgba(255, 255, 255, 0.9)',
                                                    titleColor: '#1F2937',
                                                    bodyColor: '#4B5563',
                                                    borderColor: '#E5E7EB',
                                                    borderWidth: 1,
                                                    padding: 10,
                                                    displayColors: false,
                                                    callbacks: {
                                                        label: (context) => `${context.parsed.y} vendas`,
                                                        afterLabel: (context) => {
                                                            const item = analisesData.vendas_por_hora[context.dataIndex];
                                                            return `Total: ${formatCurrency(item.total)}`;
                                                        },
                                                    },
                                                },
                                            },
                                            scales: {
                                                y: {
                                                    beginAtZero: true,
                                                    grid: {
                                                        color: '#F3F4F6',
                                                    },
                                                    ticks: {
                                                        stepSize: 1,
                                                        font: {
                                                            family: "'Inter', sans-serif",
                                                            size: 11
                                                        },
                                                        color: '#6B7280'
                                                    },
                                                    border: {
                                                        display: false
                                                    }
                                                },
                                                x: {
                                                    grid: {
                                                        display: false
                                                    },
                                                    ticks: {
                                                        font: {
                                                            family: "'Inter', sans-serif",
                                                            size: 11
                                                        },
                                                        color: '#6B7280'
                                                    },
                                                    border: {
                                                        display: false
                                                    }
                                                }
                                            },
                                        }}
                                    />
                                </div>
                                {analisesData.vendas_por_hora.length === 1 && (
                                    <p className="text-sm text-gray-500 mt-3 text-center flex items-center justify-center gap-2">
                                        <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                        </svg>
                                        Dica: Vendas em diferentes horários aparecerão como barras separadas
                                    </p>
                                )}
                            </div>
                        )}
                    </div>

                    {/* Top Funcionários */}
                    {analisesData.vendas_por_funcionario && analisesData.vendas_por_funcionario.length > 0 && (
                        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
                            <h3 className="text-lg font-bold mb-6 text-gray-900 flex items-center gap-2">
                                <div className="p-2 bg-yellow-100 rounded-lg text-yellow-600">
                                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                    </svg>
                                </div>
                                Ranking de Funcionários
                            </h3>
                            <div className="space-y-4">
                                {analisesData.vendas_por_funcionario.slice(0, 5).map((func: any, index: number) => (
                                    <div
                                        key={index}
                                        className={`flex items-center justify-between p-4 bg-white rounded-xl border transition-all hover:shadow-md ${
                                            index === 0 ? 'border-yellow-200 ring-1 ring-yellow-100' :
                                            index === 1 ? 'border-gray-200' :
                                            index === 2 ? 'border-orange-200' : 'border-gray-100'
                                        }`}
                                    >
                                        <div className="flex items-center gap-4">
                                            <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-lg ${
                                                index === 0 ? 'bg-yellow-100 text-yellow-700' :
                                                index === 1 ? 'bg-gray-100 text-gray-700' :
                                                index === 2 ? 'bg-orange-100 text-orange-700' : 'bg-blue-50 text-blue-600'
                                            }`}>
                                                {index + 1}º
                                            </div>
                                            <div>
                                                <p className="font-bold text-gray-900">{func.funcionario}</p>
                                                <p className="text-sm text-gray-500 flex items-center gap-2">
                                                    <span>{func.quantidade} vendas</span>
                                                    <span className="w-1 h-1 bg-gray-300 rounded-full"></span>
                                                    <span>Ticket médio: {formatCurrency(func.total / func.quantidade)}</span>
                                                </p>
                                            </div>
                                        </div>
                                        <div className="text-right">
                                            <p className="font-bold text-lg text-gray-900">
                                                {formatCurrency(func.total)}
                                            </p>
                                            <div className="flex items-center justify-end gap-1 text-xs text-gray-500">
                                                <div className="w-16 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                                                    <div 
                                                        className="h-full bg-green-500 rounded-full"
                                                        style={{ width: `${(func.total / analisesData.estatisticas_gerais.total_valor) * 100}%` }}
                                                    ></div>
                                                </div>
                                                <span>{((func.total / analisesData.estatisticas_gerais.total_valor) * 100).toFixed(1)}%</span>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
                )
            )}

            {/* Filtros */}
            <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 mb-6">
                <div className="flex justify-between items-center mb-6">
                    <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                        <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
                        </svg>
                        Filtros de Busca
                    </h2>
                    <button
                        onClick={limparFiltros}
                        className="text-sm text-red-600 hover:text-red-800 hover:bg-red-50 px-3 py-1.5 rounded-lg transition-colors font-medium flex items-center gap-1"
                    >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                        Limpar Filtros
                    </button>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
                    <div>
                        <label className="block text-sm font-semibold text-gray-700 mb-2">Data Início</label>
                        <input
                            type="date"
                            name="data_inicio"
                            value={filtros.data_inicio}
                            onChange={handleFiltroChange}
                            className="w-full px-4 py-2.5 bg-white border border-gray-200 rounded-lg text-gray-900 font-medium focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all shadow-sm"
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-semibold text-gray-700 mb-2">Data Fim</label>
                        <input
                            type="date"
                            name="data_fim"
                            value={filtros.data_fim}
                            onChange={handleFiltroChange}
                            className="w-full px-4 py-2.5 bg-white border border-gray-200 rounded-lg text-gray-900 font-medium focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all shadow-sm"
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-semibold text-gray-700 mb-2">Status</label>
                        <div className="relative">
                            <select
                                name="status"
                                value={filtros.status}
                                onChange={handleFiltroChange}
                                className="w-full px-4 py-2.5 bg-white border border-gray-200 rounded-lg text-gray-900 font-medium focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all shadow-sm appearance-none"
                            >
                                <option value="">Todos</option>
                                <option value="finalizada">Finalizada</option>
                                <option value="cancelada">Cancelada</option>
                                <option value="em_andamento">Em Andamento</option>
                            </select>
                            <div className="absolute inset-y-0 right-0 flex items-center px-2 pointer-events-none">
                                <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                </svg>
                            </div>
                        </div>
                    </div>
                    <div>
                        <label className="block text-sm font-semibold text-gray-700 mb-2">Forma de Pagamento</label>
                        <div className="relative">
                            <select
                                name="forma_pagamento"
                                value={filtros.forma_pagamento}
                                onChange={handleFiltroChange}
                                className="w-full px-4 py-2.5 bg-white border border-gray-200 rounded-lg text-gray-900 font-medium focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all shadow-sm appearance-none"
                            >
                                <option value="">Todas</option>
                                <option value="dinheiro">Dinheiro</option>
                                <option value="cartao_credito">Cartão de Crédito</option>
                                <option value="cartao_debito">Cartão de Débito</option>
                                <option value="pix">PIX</option>
                                <option value="fiado">Fiado</option>
                            </select>
                            <div className="absolute inset-y-0 right-0 flex items-center px-2 pointer-events-none">
                                <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                </svg>
                            </div>
                        </div>
                    </div>
                    <div>
                        <label className="block text-sm font-semibold text-gray-700 mb-2">Busca</label>
                        <div className="relative">
                            <input
                                type="text"
                                name="search"
                                placeholder="Código, cliente..."
                                value={filtros.search}
                                onChange={handleFiltroChange}
                                className="w-full pl-10 pr-4 py-2.5 bg-white border border-gray-200 rounded-lg text-gray-900 font-medium focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all shadow-sm"
                            />
                            <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
                                <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                                </svg>
                            </div>
                        </div>
                    </div>
                </div>
            </div>


            {/* Tabela de Vendas */}
            <div className="bg-white p-4 rounded-lg shadow-md border">
                <div className="flex justify-between items-center mb-4">
                    <h2 className="text-lg font-semibold text-gray-900">Lista de Vendas</h2>
                    {paginacao && (
                        <span className="text-sm text-gray-600">
                            Total: {paginacao.total_itens} vendas
                        </span>
                    )}
                </div>
                {loading ? (
                    <div className="text-center py-12">
                        <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
                        <p className="mt-4 text-gray-700">Carregando vendas...</p>
                    </div>
                ) : erro ? (
                    <div className="text-center py-12">
                        <div className="text-red-600 font-medium mb-2">❌ {erro}</div>
                        <button
                            onClick={carregarVendas}
                            className="mt-4 bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
                        >
                            Tentar Novamente
                        </button>
                    </div>
                ) : vendas.length === 0 ? (
                    <div className="text-center py-12">
                        <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        <p className="mt-4 text-gray-700 font-medium">Nenhuma venda encontrada</p>
                        <p className="text-sm text-gray-500 mt-2">
                            {filtros.search || filtros.data_inicio || filtros.data_fim || filtros.status || filtros.forma_pagamento
                                ? "Tente ajustar os filtros para ver mais resultados"
                                : "Realize vendas através do PDV para visualizá-las aqui"}
                        </p>
                    </div>
                ) : (
                    <>
                        <div className="overflow-x-auto">
                            <table className="min-w-full text-sm border-collapse">
                                <thead className="bg-gray-100">
                                    <tr>
                                        <th className="text-left p-3 text-gray-700 font-medium border-b">Código</th>
                                        <th className="text-left p-3 text-gray-700 font-medium border-b">Cliente</th>
                                        <th className="text-left p-3 text-gray-700 font-medium border-b">Funcionário</th>
                                        <th className="text-right p-3 text-gray-700 font-medium border-b">Subtotal</th>
                                        <th className="text-right p-3 text-gray-700 font-medium border-b">Desconto</th>
                                        <th className="text-right p-3 text-gray-700 font-medium border-b">Total</th>
                                        <th className="text-left p-3 text-gray-700 font-medium border-b">Forma Pgto</th>
                                        <th className="text-left p-3 text-gray-700 font-medium border-b">Data</th>
                                        <th className="text-center p-3 text-gray-700 font-medium border-b">Itens</th>
                                        <th className="text-center p-3 text-gray-700 font-medium border-b">Status</th>
                                        <th className="text-center p-3 text-gray-700 font-medium border-b">Ações</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {vendas.map((venda) => (
                                        <tr key={venda.id} className="border-b hover:bg-gray-50 transition-colors">
                                            <td className="p-3 text-gray-900 font-mono text-xs">{venda.codigo}</td>
                                            <td className="p-3 text-gray-900">{venda.cliente?.nome || "Consumidor Final"}</td>
                                            <td className="p-3 text-gray-900">{venda.funcionario?.nome || "Não Informado"}</td>
                                            <td className="p-3 text-right text-gray-900">{formatCurrency(venda.subtotal)}</td>
                                            <td className="p-3 text-right text-red-600">
                                                {venda.desconto > 0 ? `-${formatCurrency(venda.desconto)}` : "-"}
                                            </td>
                                            <td className="p-3 font-semibold text-right text-gray-900">{formatCurrency(venda.total)}</td>
                                            <td className="p-3 text-gray-900 capitalize">
                                                {venda.forma_pagamento.replace(/_/g, " ")}
                                            </td>
                                            <td className="p-3 text-gray-900 text-xs">{venda.data_formatada}</td>
                                            <td className="p-3 text-center">
                                                <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-blue-100 text-blue-800 text-xs font-medium">
                                                    {venda.quantidade_itens}
                                                </span>
                                            </td>
                                            <td className="p-3 text-center">
                                                <span
                                                    className={`px-2 py-1 rounded text-xs font-medium ${
                                                        venda.status === "finalizada"
                                                            ? "bg-green-100 text-green-800"
                                                            : venda.status === "cancelada"
                                                            ? "bg-red-100 text-red-800"
                                                            : "bg-yellow-100 text-yellow-800"
                                                    }`}
                                                >
                                                    {venda.status === "finalizada" ? "Finalizada" : 
                                                     venda.status === "cancelada" ? "Cancelada" : "Em Andamento"}
                                                </span>
                                            </td>
                                            <td className="p-3 text-center">
                                                <div className="flex gap-2 justify-center">
                                                    <button
                                                        onClick={() => abrirDetalhes(venda)}
                                                        className="bg-blue-500 text-white px-3 py-1 rounded text-xs hover:bg-blue-600 transition-colors"
                                                        title="Ver detalhes"
                                                    >
                                                        Detalhes
                                                    </button>
                                                    {venda.status === "finalizada" && (
                                                        <button
                                                            onClick={() => cancelarVenda(venda.id)}
                                                            className="bg-red-500 text-white px-3 py-1 rounded text-xs hover:bg-red-600 transition-colors"
                                                            title="Cancelar venda"
                                                        >
                                                            Cancelar
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
                            <div className="flex justify-between items-center mt-6">
                                <div className="text-sm text-gray-600">
                                    Mostrando {((paginacao.pagina_atual - 1) * paginacao.itens_por_pagina) + 1} a{" "}
                                    {Math.min(paginacao.pagina_atual * paginacao.itens_por_pagina, paginacao.total_itens)} de{" "}
                                    {paginacao.total_itens} vendas
                                </div>
                                <div className="flex space-x-2">
                                    <button
                                        onClick={() => mudarPagina(filtros.page - 1)}
                                        disabled={!paginacao.tem_anterior}
                                        className="px-4 py-2 border border-gray-300 rounded text-gray-700 hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                                    >
                                        ← Anterior
                                    </button>
                                    <span className="px-4 py-2 text-gray-700 font-medium">
                                        Página {paginacao.pagina_atual} de {paginacao.total_paginas}
                                    </span>
                                    <button
                                        onClick={() => mudarPagina(filtros.page + 1)}
                                        disabled={!paginacao.tem_proxima}
                                        className="px-4 py-2 border border-gray-300 rounded text-gray-700 hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                                    >
                                        Próxima →
                                    </button>
                                </div>
                            </div>
                        )}
                    </>
                )}
            </div>

            {/* Modal de Detalhes */}
            {modalDetalhesAberto && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white p-6 rounded-lg shadow-xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
                        <div className="flex justify-between items-center mb-6">
                            <h3 className="text-2xl font-bold text-gray-900">Detalhes da Venda</h3>
                            <button
                                onClick={() => setModalDetalhesAberto(false)}
                                className="text-gray-500 hover:text-gray-700 text-2xl"
                            >
                                ×
                            </button>
                        </div>
                        
                        {loadingDetalhes ? (
                            <div className="text-center py-12">
                                <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
                                <p className="mt-4 text-gray-700">Carregando detalhes...</p>
                            </div>
                        ) : detalhesVenda ? (
                            <div>
                                {/* Informações Gerais */}
                                <div className="grid grid-cols-2 gap-4 mb-6 p-4 bg-gray-50 rounded-lg">
                                    <div>
                                        <p className="text-sm text-gray-600">Código</p>
                                        <p className="font-mono font-semibold text-gray-900">{detalhesVenda.codigo}</p>
                                    </div>
                                    <div>
                                        <p className="text-sm text-gray-600">Status</p>
                                        <span
                                            className={`inline-block px-3 py-1 rounded text-sm font-medium ${
                                                detalhesVenda.status === "finalizada"
                                                    ? "bg-green-100 text-green-800"
                                                    : detalhesVenda.status === "cancelada"
                                                    ? "bg-red-100 text-red-800"
                                                    : "bg-yellow-100 text-yellow-800"
                                            }`}
                                        >
                                            {detalhesVenda.status === "finalizada" ? "Finalizada" : 
                                             detalhesVenda.status === "cancelada" ? "Cancelada" : "Em Andamento"}
                                        </span>
                                    </div>
                                    <div>
                                        <p className="text-sm text-gray-600">Cliente</p>
                                        <p className="font-semibold text-gray-900">{detalhesVenda.cliente?.nome || "Consumidor Final"}</p>
                                        {detalhesVenda.cliente?.cpf && (
                                            <p className="text-sm text-gray-600">CPF: {detalhesVenda.cliente.cpf}</p>
                                        )}
                                    </div>
                                    <div>
                                        <p className="text-sm text-gray-600">Funcionário</p>
                                        <p className="font-semibold text-gray-900">{detalhesVenda.funcionario?.nome || "Não Informado"}</p>
                                    </div>
                                    <div>
                                        <p className="text-sm text-gray-600">Data</p>
                                        <p className="font-semibold text-gray-900">{detalhesVenda.data_formatada}</p>
                                    </div>
                                    <div>
                                        <p className="text-sm text-gray-600">Forma de Pagamento</p>
                                        <p className="font-semibold text-gray-900 capitalize">
                                            {detalhesVenda.forma_pagamento.replace(/_/g, " ")}
                                        </p>
                                    </div>
                                </div>

                                {/* Valores */}
                                <div className="grid grid-cols-2 gap-4 mb-6 p-4 bg-blue-50 rounded-lg">
                                    <div>
                                        <p className="text-sm text-gray-600">Subtotal</p>
                                        <p className="text-lg font-semibold text-gray-900">{formatCurrency(detalhesVenda.subtotal)}</p>
                                    </div>
                                    <div>
                                        <p className="text-sm text-gray-600">Desconto</p>
                                        <p className="text-lg font-semibold text-red-600">
                                            {detalhesVenda.desconto > 0 ? `-${formatCurrency(detalhesVenda.desconto)}` : formatCurrency(0)}
                                        </p>
                                    </div>
                                    <div>
                                        <p className="text-sm text-gray-600">Total</p>
                                        <p className="text-2xl font-bold text-green-600">{formatCurrency(detalhesVenda.total)}</p>
                                    </div>
                                    <div>
                                        <p className="text-sm text-gray-600">Valor Recebido</p>
                                        <p className="text-lg font-semibold text-gray-900">{formatCurrency(detalhesVenda.valor_recebido)}</p>
                                        {detalhesVenda.troco > 0 && (
                                            <p className="text-sm text-gray-600">Troco: {formatCurrency(detalhesVenda.troco)}</p>
                                        )}
                                    </div>
                                </div>

                                {/* Itens da Venda */}
                                <div className="mb-6">
                                    <h4 className="text-lg font-semibold mb-3 text-gray-900">Itens da Venda</h4>
                                    <div className="border rounded-lg overflow-hidden">
                                        <table className="min-w-full text-sm">
                                            <thead className="bg-gray-100">
                                                <tr>
                                                    <th className="text-left p-3 text-gray-700 font-medium">Produto</th>
                                                    <th className="text-center p-3 text-gray-700 font-medium">Qtd</th>
                                                    <th className="text-right p-3 text-gray-700 font-medium">Preço Unit.</th>
                                                    <th className="text-right p-3 text-gray-700 font-medium">Desconto</th>
                                                    <th className="text-right p-3 text-gray-700 font-medium">Total</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {detalhesVenda.itens?.map((item: ItemVenda) => (
                                                    <tr key={item.id} className="border-t hover:bg-gray-50">
                                                        <td className="p-3 text-gray-900">{item.produto_nome}</td>
                                                        <td className="p-3 text-center text-gray-900">{item.quantidade}</td>
                                                        <td className="p-3 text-right text-gray-900">{formatCurrency(item.preco_unitario)}</td>
                                                        <td className="p-3 text-right text-red-600">
                                                            {item.desconto_item > 0 ? `-${formatCurrency(item.desconto_item)}` : "-"}
                                                        </td>
                                                        <td className="p-3 text-right font-semibold text-gray-900">{formatCurrency(item.total_item)}</td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>

                                {/* Observações */}
                                {detalhesVenda.observacoes && (
                                    <div className="mb-6 p-4 bg-yellow-50 rounded-lg">
                                        <p className="text-sm text-gray-600 mb-1">Observações</p>
                                        <p className="text-gray-900">{detalhesVenda.observacoes}</p>
                                    </div>
                                )}

                                {/* Botões de Ação */}
                                <div className="flex justify-end gap-3">
                                    <button
                                        onClick={() => setModalDetalhesAberto(false)}
                                        className="bg-gray-500 text-white px-6 py-2 rounded hover:bg-gray-600 transition-colors"
                                    >
                                        Fechar
                                    </button>
                                    {detalhesVenda.status === "finalizada" && (
                                        <button
                                            onClick={() => {
                                                setModalDetalhesAberto(false);
                                                cancelarVenda(detalhesVenda.id);
                                            }}
                                            className="bg-red-500 text-white px-6 py-2 rounded hover:bg-red-600 transition-colors"
                                        >
                                            Cancelar Venda
                                        </button>
                                    )}
                                </div>
                            </div>
                        ) : (
                            <div className="text-center py-12 text-red-600">
                                Erro ao carregar detalhes da venda.
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}