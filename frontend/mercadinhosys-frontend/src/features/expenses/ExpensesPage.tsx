import React, { useEffect, useState, useCallback } from "react";
import { Bar, Line, Doughnut } from "react-chartjs-2";
import {
    Chart as ChartJS, BarElement, CategoryScale, LinearScale,
    PointElement, LineElement, ArcElement, Tooltip, Legend, Filler,
} from "chart.js";
import { apiClient } from "../../api/apiClient";
import { showToast } from "../../utils/toast";
import {
    Wallet, TrendingUp, TrendingDown, DollarSign, Calendar,
    Download, Plus, Edit2, Trash2, Eye, X, AlertCircle,
    FileText, Clock, BarChart2,
    RefreshCw, ChevronLeft, ChevronRight, Tag, Layers,
} from "lucide-react";
import BoletosAVencerPanel from "./components/BoletosAVencerPanel";
import ResumoFinanceiroPanel from "./components/ResumoFinanceiroPanel";

ChartJS.register(BarElement, CategoryScale, LinearScale, PointElement,
    LineElement, ArcElement, Tooltip, Legend, Filler);

// ─── Interfaces ────────────────────────────────────────────────────────────
interface Despesa {
    id: number;
    descricao: string;
    categoria: string;
    tipo: "fixa" | "variavel";
    valor: number;
    data_despesa: string;
    forma_pagamento?: string;
    recorrente: boolean;
    fornecedor?: { id: number; nome: string };
    observacoes?: string;
    created_at: string;
}

interface CategoriaStat {
    categoria: string;
    total: number;
    quantidade: number;
    percentual: number;
}

interface EvolucaoMes {
    mes: string;
    total: number;
    mes_nome: string;
}

interface Estatisticas {
    total_despesas: number;
    soma_total: number;
    soma_periodo: number;
    media_valor: number;
    despesas_hoje: number;
    despesas_ontem: number;
    despesas_semana: number;
    despesas_mes_atual: number;
    despesas_mes_anterior: number;
    variacao_percentual: number;
    despesas_recorrentes: number;
    despesas_nao_recorrentes: number;
    despesas_por_categoria: CategoriaStat[];
    evolucao_mensal: EvolucaoMes[];
}

// ─── Categorias de negócio ─────────────────────────────────────────────────
const CATEGORIAS = [
    { value: "aluguel", label: "🏠 Aluguel", cor: "#6366f1", tipo: "fixa", grupo: "Infraestrutura & Imóvel" },
    { value: "energia_eletrica", label: "⚡ Energia Elétrica", cor: "#f59e0b", tipo: "fixa", grupo: "Contas (Consumo diário)" },
    { value: "agua", label: "💧 Água", cor: "#06b6d4", tipo: "fixa", grupo: "Contas (Consumo diário)" },
    { value: "telefone", label: "📱 Telefone", cor: "#8b5cf6", tipo: "fixa", grupo: "Contas (Consumo diário)" },
    { value: "internet", label: "🌐 Internet", cor: "#3b82f6", tipo: "fixa", grupo: "Contas (Consumo diário)" },
    { value: "boleto_mercadoria", label: "📦 Boleto de Mercadoria", cor: "#ef4444", tipo: "variavel", grupo: "Fornecedores & Compras" },
    { value: "salarios", label: "👥 Salários", cor: "#10b981", tipo: "fixa", grupo: "Recursos Humanos & Pessoal" },
    { value: "beneficios", label: "🎁 Benefícios (VT/VA/Plano)", cor: "#14b8a6", tipo: "fixa", grupo: "Recursos Humanos & Pessoal" },
    { value: "marketing", label: "📣 Marketing / Campanhas", cor: "#f97316", tipo: "variavel", grupo: "Operacional & Excepcionais" },
    { value: "material_escritorio", label: "🖊️ Material de Escritório", cor: "#a78bfa", tipo: "variavel", grupo: "Operacional & Excepcionais" },
    { value: "manutencao", label: "🔧 Manutenção", cor: "#78716c", tipo: "variavel", grupo: "Operacional & Excepcionais" },
    { value: "fiado", label: "📋 Fiado (Dívida Clientes)", cor: "#fb7185", tipo: "variavel", grupo: "Operacional & Excepcionais" },
    { value: "impostos", label: "🏛️ Impostos / Taxas", cor: "#64748b", tipo: "fixa", grupo: "Infraestrutura & Imóvel" },
    { value: "outros", label: "📌 Outros", cor: "#94a3b8", tipo: "variavel", grupo: "Operacional & Excepcionais" },
];

const GRUPOS_CATEGORIAS = Array.from(new Set(CATEGORIAS.map(c => c.grupo)));

const COR_POR_CATEGORIA: Record<string, string> = Object.fromEntries(
    CATEGORIAS.map(c => [c.value, c.cor])
);

const FORMAS_PAGAMENTO = ["Dinheiro", "PIX", "Cartão de Crédito", "Cartão de Débito", "Boleto", "Transferência", "Débito em Conta"];

// ─── Utilitários ──────────────────────────────────────────────────────────
function fmt(v: number) {
    return (v || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}
function fmtDate(s: string) {
    return new Date(s + "T00:00:00").toLocaleDateString("pt-BR");
}
function firstDayOfMonth(d = new Date()) {
    return new Date(d.getFullYear(), d.getMonth(), 1).toISOString().split("T")[0];
}
function today() { return new Date().toISOString().split("T")[0]; }
function daysAgo(n: number) {
    const d = new Date(); d.setDate(d.getDate() - n);
    return d.toISOString().split("T")[0];
}

// ─── Período preset ────────────────────────────────────────────────────────
const PERIODOS = [
    { label: "Hoje", value: "hoje" },
    { label: "7 dias", value: "7d" },
    { label: "Este mês", value: "mes" },
    { label: "Mês anterior", value: "mes_ant" },
    { label: "90 dias", value: "90d" },
    { label: "Periodo", value: "custom" },
];

function getPeriodoDates(v: string): { inicio: string; fim: string } {
    const t = today();
    const d = new Date();
    switch (v) {
        case "hoje": return { inicio: t, fim: t };
        case "7d": return { inicio: daysAgo(6), fim: t };
        case "mes": return { inicio: firstDayOfMonth(), fim: t };
        case "mes_ant": {
            const ant = new Date(d.getFullYear(), d.getMonth() - 1, 1);
            const ultAnt = new Date(d.getFullYear(), d.getMonth(), 0);
            return {
                inicio: ant.toISOString().split("T")[0],
                fim: ultAnt.toISOString().split("T")[0],
            };
        }
        case "90d": return { inicio: daysAgo(89), fim: t };
        default: return { inicio: firstDayOfMonth(), fim: t };
    }
}

// ─── Skeleton loader ──────────────────────────────────────────────────────
function Skeleton({ cls = "" }: { cls?: string }) {
    return <div className={`animate-pulse bg-gray-200 dark:bg-gray-700 rounded-lg ${cls}`} />;
}

// ─── Badge Categoria ──────────────────────────────────────────────────────
function CategoriaBadge({ cat }: { cat: string }) {
    const cor = COR_POR_CATEGORIA[cat] || "#94a3b8";
    return (
        <span className="px-2 py-0.5 text-xs font-semibold rounded-full text-white"
            style={{ backgroundColor: cor }}>
            {cat}
        </span>
    );
}

// ══════════════════════════════════════════════════════════════════════════
export default function ExpensesPage() {
    // ─── State ─────────────────────────────────────────────────────────────
    const [despesas, setDespesas] = useState<Despesa[]>([]);
    const [loading, setLoading] = useState(true);
    const [loadingStats, setLoadingStats] = useState(true);
    const [erro, setErro] = useState<string | null>(null);
    const [stats, setStats] = useState<Estatisticas | null>(null);
    const [paginacao, setPaginacao] = useState({ total: 0, paginas: 1 });

    const [período, setPeriodo] = useState("mes");
    const [filtros, setFiltros] = useState({
        inicio: firstDayOfMonth(),
        fim: today(),
        categoria: "",
        tipo: "",
        recorrente: "",
        busca: "",
        pagina: 1,
        por_pagina: 20,
    });

    // Modais
    const [modalAberto, setModalAberto] = useState(false);
    const [modalDetalhes, setModalDetalhes] = useState(false);
    const [despesaSel, setDespesaSel] = useState<Despesa | null>(null);
    const [modoEdicao, setModoEdicao] = useState(false);
    const [mostrarGraficos, setMostrarGraficos] = useState(true);
    const [menuExportar, setMenuExportar] = useState(false);

    const [formData, setFormData] = useState({
        descricao: "", categoria: "", tipo: "variavel" as "fixa" | "variavel",
        valor: "", data_despesa: today(), data_emissao: "", data_vencimento: "",
        forma_pagamento: "", recorrente: false, observacoes: "",
    });

    // ─── Loaders ───────────────────────────────────────────────────────────
    const carregarDespesas = useCallback(async () => {
        setLoading(true); setErro(null);
        try {
            const params: any = { pagina: filtros.pagina, por_pagina: filtros.por_pagina };
            if (filtros.busca) params.busca = filtros.busca;
            if (filtros.inicio) params.inicio = filtros.inicio;
            if (filtros.fim) params.fim = filtros.fim;
            if (filtros.categoria) params.categoria = filtros.categoria;
            if (filtros.tipo) params.tipo = filtros.tipo;
            if (filtros.recorrente) params.recorrente = filtros.recorrente;
            const res = await apiClient.get("/despesas", { params });
            if (res.data.success) {
                setDespesas(res.data.data || []);
                setPaginacao({
                    total: res.data.paginacao?.total_itens ?? 0,
                    paginas: res.data.paginacao?.total_paginas ?? 1,
                });
            } else { setDespesas([]); }
        } catch (e: any) {
            setErro(`Erro ao carregar despesas: ${e.response?.data?.error || e.message}`);
        } finally { setLoading(false); }
    }, [filtros]);

    const carregarEstatisticas = useCallback(async () => {
        setLoadingStats(true);
        try {
            const res = await apiClient.get("/despesas/estatisticas", {
                params: { inicio: filtros.inicio, fim: filtros.fim },
            });
            if (res.data.success && res.data.estatisticas) {
                setStats(res.data.estatisticas);
            }
        } catch (e: any) {
            showToast.error("Não foi possível carregar as estatísticas.");
        } finally { setLoadingStats(false); }
    }, [filtros.inicio, filtros.fim]);

    useEffect(() => { carregarDespesas(); }, [carregarDespesas]);
    useEffect(() => { carregarEstatisticas(); }, [carregarEstatisticas]);

    // Click-outside menu exportar
    useEffect(() => {
        const fn = (e: MouseEvent) => {
            if (!(e.target as HTMLElement).closest(".export-menu"))
                setMenuExportar(false);
        };
        document.addEventListener("mousedown", fn);
        return () => document.removeEventListener("mousedown", fn);
    }, []);

    // ─── Período Preset ────────────────────────────────────────────────────
    function aplicarPeriodo(pre: string) {
        setPeriodo(pre);
        if (pre !== "custom") {
            const { inicio, fim } = getPeriodoDates(pre);
            setFiltros(f => ({ ...f, inicio, fim, pagina: 1 }));
        }
    }

    // ─── Modais ────────────────────────────────────────────────────────────
    function abrirNovo() {
        setModoEdicao(false); setDespesaSel(null);
        setFormData({ descricao: "", categoria: "", tipo: "variavel", valor: "", data_despesa: today(), data_emissao: "", data_vencimento: "", forma_pagamento: "", recorrente: false, observacoes: "" });
        setModalAberto(true);
    }
    function abrirEdicao(d: Despesa) {
        setModoEdicao(true); setDespesaSel(d);
        setFormData({ descricao: d.descricao, categoria: d.categoria, tipo: d.tipo, valor: String(d.valor), data_despesa: d.data_despesa, data_emissao: (d as any).data_emissao || "", data_vencimento: (d as any).data_vencimento || "", forma_pagamento: d.forma_pagamento || "", recorrente: d.recorrente, observacoes: d.observacoes || "" });
        setModalAberto(true);
    }

    async function salvar() {
        const dados = { ...formData, valor: parseFloat(formData.valor) };
        const prom = modoEdicao && despesaSel
            ? apiClient.put(`/despesas/${despesaSel.id}`, dados)
            : apiClient.post("/despesas", dados);
        await showToast.promise(prom, {
            loading: modoEdicao ? "Atualizando..." : "Criando despesa...",
            success: modoEdicao ? "Despesa atualizada!" : "Despesa criada!",
            error: "Erro ao salvar despesa",
        });
        setModalAberto(false);
        carregarDespesas(); carregarEstatisticas();
    }

    async function excluir(id: number) {
        if (!confirm("Excluir esta despesa?")) return;
        await showToast.promise(apiClient.delete(`/despesas/${id}`), {
            loading: "Excluindo...", success: "Despesa excluída!", error: "Erro ao excluir",
        });
        carregarDespesas(); carregarEstatisticas();
    }

    // ─── Export CSV ────────────────────────────────────────────────────────
    function exportarCSV() {
        const h = ["Descrição", "Categoria", "Tipo", "Valor", "Data", "Pagamento", "Recorrente"];
        const rows = despesas.map(d => [d.descricao, d.categoria, d.tipo, d.valor.toFixed(2), fmtDate(d.data_despesa), d.forma_pagamento || "-", d.recorrente ? "Sim" : "Não"]);
        const csv = [h, ...rows].map(r => r.map(c => `"${c}"`).join(",")).join("\n");
        const blob = new Blob(["\ufeff" + csv], { type: "text/csv;charset=utf-8;" });
        const a = document.createElement("a"); a.href = URL.createObjectURL(blob);
        a.download = `despesas-${today()}.csv`; a.click();
        setMenuExportar(false); showToast.success("CSV exportado!");
    }

    // ─── Chart data (Professional Monochromatic Palettes) ─────────────────

    // Palette: Indigo Professional
    const indigoPalette = [
        "rgba(99, 102, 241, 0.9)",  // indigo-500
        "rgba(79, 70, 229, 0.85)", // indigo-600
        "rgba(67, 56, 202, 0.8)",  // indigo-700
        "rgba(55, 48, 163, 0.75)", // indigo-800
        "rgba(49, 46, 129, 0.7)",  // indigo-900
        "rgba(129, 140, 248, 0.9)", // indigo-400
        "rgba(165, 180, 252, 0.9)", // indigo-300
    ];

    // Palette: Emerald/Cyan Professional
    const emeraldPalette = [
        "rgba(16, 185, 129, 0.9)",  // emerald-500
        "rgba(5, 150, 105, 0.85)",  // emerald-600
        "rgba(4, 120, 87, 0.8)",    // emerald-700
        "rgba(6, 95, 70, 0.75)",    // emerald-800
        "rgba(20, 184, 166, 0.9)",  // teal-500
        "rgba(13, 148, 136, 0.85)", // teal-600
        "rgba(45, 212, 191, 0.9)",  // teal-400
    ];

    const doughnutChartCores = stats?.despesas_por_categoria.map((_, i) => indigoPalette[i % indigoPalette.length]) || [];
    const barChartCores = stats?.despesas_por_categoria.map((_, i) => emeraldPalette[i % emeraldPalette.length]) || [];

    const donutData = {
        labels: stats?.despesas_por_categoria.map(c => c.categoria) || [],
        datasets: [{
            data: stats?.despesas_por_categoria.map(c => c.total) || [],
            backgroundColor: doughnutChartCores,
            hoverBackgroundColor: doughnutChartCores.map(c => c.replace("0.9", "1").replace("0.85", "1").replace("0.8", "1")),
            borderWidth: 2,
            borderColor: "rgba(15, 23, 42, 0.8)",
            hoverOffset: 15,
        }],
    };

    const barData = {
        labels: stats?.despesas_por_categoria.map(c => c.categoria) || [],
        datasets: [{
            label: "Total Gasto",
            data: stats?.despesas_por_categoria.map(c => c.total) || [],
            backgroundColor: barChartCores,
            borderRadius: 8,
            borderSkipped: false,
            hoverBackgroundColor: "rgba(16, 185, 129, 1)",
        }],
    };

    const lineData = {
        labels: stats?.evolucao_mensal.map(e => e.mes_nome) || [],
        datasets: [{
            label: "Despesas",
            data: stats?.evolucao_mensal.map(e => e.total) || [],
            borderColor: "#ef4444",
            backgroundColor: "rgba(239,68,68,0.12)",
            fill: true, tension: 0.4,
            pointRadius: 5, pointHoverRadius: 7,
            pointBackgroundColor: "#ef4444", pointBorderColor: "#fff", pointBorderWidth: 2,
        }],
    };

    const chartOpts: any = {
        responsive: true,
        maintainAspectRatio: false,
        animation: {
            duration: 2000,
            easing: "easeOutQuart",
        },
        plugins: {
            legend: {
                display: false
            },
            tooltip: {
                backgroundColor: "rgba(15, 23, 42, 0.9)",
                titleFont: { size: 14, weight: "bold" },
                bodyFont: { size: 13 },
                padding: 12,
                cornerRadius: 12,
                displayColors: true,
                callbacks: {
                    label: (ctx: any) => ` ${fmt(ctx.parsed.y ?? ctx.parsed)}`
                }
            },
        },
        scales: {
            y: {
                beginAtZero: true,
                ticks: {
                    callback: (v: any) => fmt(Number(v)),
                    color: "rgba(148, 163, 184, 0.7)",
                    font: { size: 10 }
                },
                grid: {
                    color: "rgba(255,255,255,0.03)",
                    drawBorder: false
                }
            },
            x: {
                ticks: {
                    color: "rgba(148, 163, 184, 0.7)",
                    font: { size: 10 }
                },
                grid: { display: false }
            },
        },
    };

    // ─── Render ────────────────────────────────────────────────────────────
    const varPct = stats?.variacao_percentual ?? 0;

    return (
        <div style={{ background: "linear-gradient(135deg,#0f172a 0%,#1e1b4b 50%,#0f172a 100%)", minHeight: "100vh" }}
            className="p-4 md:p-6">

            {/* ═══ HEADER ═══════════════════════════════════════════════════ */}
            <div className="flex flex-col md:flex-row md:items-center gap-4 mb-6">
                <div className="flex items-center gap-4 flex-1">
                    <div className="p-3 rounded-2xl shadow-xl" style={{ background: "linear-gradient(135deg,#10b981,#06b6d4)" }}>
                        <Wallet className="w-8 h-8 text-white" />
                    </div>
                    <div>
                        <h1 className="text-3xl font-black text-white tracking-tight">Gestão de Despesas</h1>
                        <p className="text-sm text-slate-300 mt-0.5 font-medium">ERP · Controle financeiro inteligente de saídas</p>
                    </div>
                </div>
                <div className="flex items-center gap-2 flex-wrap">
                    <button onClick={() => { carregarDespesas(); carregarEstatisticas(); }}
                        className="p-2.5 rounded-xl bg-slate-800 border border-slate-700 text-slate-300 hover:text-white hover:border-slate-500 transition-all">
                        <RefreshCw className="w-4 h-4" />
                    </button>
                    <button onClick={() => setMostrarGraficos(!mostrarGraficos)}
                        className={`px-4 py-2.5 rounded-xl font-semibold text-sm transition-all flex items-center gap-2 ${mostrarGraficos ? "bg-indigo-600 text-white shadow-lg shadow-indigo-500/30" : "bg-slate-800 text-slate-300 border border-slate-700"}`}>
                        <BarChart2 className="w-4 h-4" /> Analytics
                    </button>
                    <div className="relative export-menu">
                        <button onClick={() => setMenuExportar(!menuExportar)}
                            className="px-4 py-2.5 rounded-xl bg-emerald-600 text-white font-semibold text-sm hover:bg-emerald-500 transition-all flex items-center gap-2 shadow-lg shadow-emerald-500/30">
                            <Download className="w-4 h-4" /> Exportar
                        </button>
                        {menuExportar && (
                            <div className="absolute right-0 mt-2 w-48 bg-slate-800 border border-slate-700 rounded-xl shadow-2xl z-50 overflow-hidden">
                                <button onClick={exportarCSV} className="w-full text-left px-4 py-3 text-sm text-slate-200 hover:bg-slate-700 flex items-center gap-2">
                                    <FileText className="w-4 h-4 text-emerald-400" /> Export CSV
                                </button>
                            </div>
                        )}
                    </div>
                    <button onClick={abrirNovo}
                        className="px-5 py-2.5 rounded-xl font-bold text-sm flex items-center gap-2 shadow-xl transition-all text-white"
                        style={{ background: "linear-gradient(135deg,#6366f1,#8b5cf6)", boxShadow: "0 4px 20px rgba(99,102,241,0.4)" }}>
                        <Plus className="w-4 h-4" /> Nova Despesa
                    </button>
                </div>
            </div>

            {/* ═══ PAINÉIS EXTERNOS ════════════════════════════════════════ */}
            <ResumoFinanceiroPanel className="mb-5" />

            {/* ═══ SELETOR DE PERÍODO ══════════════════════════════════════ */}
            <div className="flex items-center gap-2 mb-5 flex-wrap">
                <span className="text-xs font-black text-slate-300 uppercase tracking-widest mr-1">Período:</span>
                {PERIODOS.map(p => (
                    <button key={p.value} onClick={() => aplicarPeriodo(p.value)}
                        className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all border ${período === p.value
                            ? "bg-indigo-600 text-white border-indigo-500 shadow-md shadow-indigo-500/30"
                            : "bg-slate-800 text-slate-400 border-slate-700 hover:border-slate-500 hover:text-white"}`}>
                        {p.label}
                    </button>
                ))}
                {período === "custom" && (
                    <div className="flex items-center gap-2 ml-2">
                        <input type="date" value={filtros.inicio}
                            onChange={e => setFiltros(f => ({ ...f, inicio: e.target.value, pagina: 1 }))}
                            className="px-2 py-1.5 text-xs rounded-lg bg-slate-800 border border-slate-600 text-white focus:outline-none focus:ring-1 focus:ring-indigo-500" />
                        <span className="text-slate-500 text-xs">até</span>
                        <input type="date" value={filtros.fim}
                            onChange={e => setFiltros(f => ({ ...f, fim: e.target.value, pagina: 1 }))}
                            className="px-2 py-1.5 text-xs rounded-lg bg-slate-800 border border-slate-600 text-white focus:outline-none focus:ring-1 focus:ring-indigo-500" />
                    </div>
                )}
            </div>

            {/* ═══ KPI CARDS ═══════════════════════════════════════════════ */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                <KpiCard icon={<Clock className="w-5 h-5" />} label="Hoje" value={loadingStats ? null : (stats?.despesas_hoje ?? 0)} cor="from-rose-500 to-pink-600" />
                <KpiCard icon={<Calendar className="w-5 h-5" />} label="Este Mês" value={loadingStats ? null : (stats?.despesas_mes_atual ?? 0)}
                    cor="from-orange-500 to-amber-500"
                    sub={stats ? (
                        <span className={`flex items-center gap-1 text-xs font-semibold ${varPct > 0 ? "text-rose-400" : "text-emerald-400"}`}>
                            {varPct > 0 ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                            {Math.abs(varPct).toFixed(1)}% vs mês ant.
                        </span>
                    ) : null} />
                <KpiCard icon={<BarChart2 className="w-5 h-5" />} label="Semana (7d)" value={loadingStats ? null : (stats?.despesas_semana ?? 0)} cor="from-violet-500 to-indigo-600" />
                <KpiCard icon={<RefreshCw className="w-5 h-5" />} label="Recorrentes" value={loadingStats ? null : (stats?.despesas_recorrentes ?? 0)} cor="from-teal-500 to-cyan-600"
                    sub={stats && stats.soma_total > 0 ? (
                        <span className="text-xs text-slate-400">{((stats.despesas_recorrentes / stats.soma_total) * 100).toFixed(1)}% do total geral</span>
                    ) : null} />
            </div>

            {/* ═══ BOLETOS ═════════════════════════════════════════════════ */}
            <BoletosAVencerPanel className="mb-5" />

            {/* ═══ ANALYTICS ═══════════════════════════════════════════════ */}
            {mostrarGraficos && (
                <div className="space-y-5 mb-6">
                    {/* Evolução Mensal (linha) */}
                    <div className="rounded-2xl border border-slate-700/60 p-5" style={{ background: "rgba(15,23,42,0.6)", backdropFilter: "blur(12px)" }}>
                        <h3 className="text-base font-bold text-white mb-4 flex items-center gap-2">
                            <TrendingUp className="w-5 h-5 text-rose-400" /> Evolução de Despesas — 6 Meses
                        </h3>
                        <div className="h-64">
                            {loadingStats
                                ? <Skeleton cls="h-full w-full" />
                                : <Line data={lineData} options={{ ...chartOpts, plugins: { ...chartOpts.plugins, legend: { display: false } } }} />}
                        </div>
                    </div>

                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
                        {/* Barras por categoria */}
                        <div className="rounded-2xl border border-slate-700/60 p-5" style={{ background: "rgba(15,23,42,0.6)", backdropFilter: "blur(12px)" }}>
                            <h3 className="text-base font-bold text-white mb-4 flex items-center gap-2">
                                <Tag className="w-5 h-5 text-indigo-400" /> Por Categoria (período)
                            </h3>
                            <div className="h-64">
                                {loadingStats
                                    ? <Skeleton cls="h-full w-full" />
                                    : stats?.despesas_por_categoria.length
                                        ? <Bar data={barData} options={chartOpts} />
                                        : <EmptyChart />}
                            </div>
                        </div>

                        {/* Donut distribuição */}
                        <div className="rounded-2xl border border-slate-700/60 p-5" style={{ background: "rgba(15,23,42,0.6)", backdropFilter: "blur(12px)" }}>
                            <h3 className="text-base font-bold text-white mb-4 flex items-center gap-2">
                                <Layers className="w-5 h-5 text-cyan-400" /> Distribuição
                            </h3>
                            <div className="h-64 flex items-center justify-center">
                                {loadingStats
                                    ? <Skeleton cls="h-full w-full" />
                                    : stats?.despesas_por_categoria.length
                                        ? <Doughnut data={donutData} options={{ responsive: true, maintainAspectRatio: false, plugins: { legend: { position: "right", labels: { color: "#94a3b8", boxWidth: 12, font: { size: 11 } } }, tooltip: { callbacks: { label: (ctx: any) => `${ctx.label}: ${fmt(ctx.parsed)} (${stats.despesas_por_categoria[ctx.dataIndex]?.percentual.toFixed(1)}%)` } } } }} />
                                        : <EmptyChart />}
                            </div>
                        </div>
                    </div>

                    {/* Tabela de categorias com barra de progresso */}
                    {(stats?.despesas_por_categoria.length ?? 0) > 0 && (
                        <div className="rounded-2xl border border-slate-700/60 p-5" style={{ background: "rgba(15,23,42,0.6)", backdropFilter: "blur(12px)" }}>
                            <h3 className="text-base font-bold text-white mb-4 flex items-center gap-2">
                                <DollarSign className="w-5 h-5 text-emerald-400" /> Ranking de Categorias no Período
                            </h3>
                            <div className="space-y-3">
                                {stats!.despesas_por_categoria.map(c => (
                                    <div key={c.categoria} className="group">
                                        <div className="flex items-center justify-between mb-1">
                                            <div className="flex items-center gap-2">
                                                <CategoriaBadge cat={c.categoria} />
                                                <span className="text-xs text-slate-400">{c.quantidade} lançamento{c.quantidade !== 1 ? "s" : ""}</span>
                                            </div>
                                            <div className="flex items-center gap-3">
                                                <span className="text-sm font-bold text-white">{fmt(c.total)}</span>
                                                <span className="text-xs text-slate-400 w-10 text-right">{c.percentual.toFixed(1)}%</span>
                                            </div>
                                        </div>
                                        <div className="w-full bg-slate-700 rounded-full h-1.5">
                                            <div className="h-1.5 rounded-full transition-all duration-500"
                                                style={{ width: `${c.percentual}%`, backgroundColor: COR_POR_CATEGORIA[c.categoria] || "#6366f1" }} />
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            )}

            {/* ═══ ABAS LISTA ══════════════════════════════════════════════ */}
            <div className="rounded-2xl border border-slate-700/60 overflow-hidden" style={{ background: "rgba(15,23,42,0.7)", backdropFilter: "blur(12px)" }}>
                {/* Filtros da tabela */}
                <div className="p-4 border-b border-slate-700/60">
                    <div className="flex flex-wrap gap-3 items-center">
                        <div className="flex-1 min-w-[180px]">
                            <input type="text" placeholder="🔍 Buscar despesa..." value={filtros.busca}
                                onChange={e => setFiltros(f => ({ ...f, busca: e.target.value, pagina: 1 }))}
                                className="w-full px-3 py-2 text-sm rounded-xl bg-slate-800 border border-slate-600 text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500" />
                        </div>
                        <select value={filtros.categoria} onChange={e => setFiltros(f => ({ ...f, categoria: e.target.value, pagina: 1 }))}
                            className="px-3 py-2 text-sm rounded-xl bg-slate-800 border border-slate-600 text-white focus:outline-none focus:ring-1 focus:ring-indigo-500">
                            <option value="">Todas categorias</option>
                            {GRUPOS_CATEGORIAS.map(grupo => (
                                <optgroup key={grupo} label={grupo} className="bg-slate-700 text-indigo-300 font-bold">
                                    {CATEGORIAS.filter(c => c.grupo === grupo).map(c => (
                                        <option key={c.value} value={c.value} className="text-white bg-slate-800">{c.label}</option>
                                    ))}
                                </optgroup>
                            ))}
                        </select>
                        <select value={filtros.tipo} onChange={e => setFiltros(f => ({ ...f, tipo: e.target.value, pagina: 1 }))}
                            className="px-3 py-2 text-sm rounded-xl bg-slate-800 border border-slate-600 text-white focus:outline-none focus:ring-1 focus:ring-indigo-500">
                            <option value="">Todos os tipos</option>
                            <option value="fixa">Fixas</option>
                            <option value="variavel">Variáveis</option>
                        </select>
                        <select value={filtros.recorrente} onChange={e => setFiltros(f => ({ ...f, recorrente: e.target.value, pagina: 1 }))}
                            className="px-3 py-2 text-sm rounded-xl bg-slate-800 border border-slate-600 text-white focus:outline-none focus:ring-1 focus:ring-indigo-500">
                            <option value="">Recorrência</option>
                            <option value="true">Recorrentes</option>
                            <option value="false">Pontuais</option>
                        </select>
                        {(filtros.busca || filtros.categoria || filtros.tipo || filtros.recorrente) && (
                            <button onClick={() => setFiltros(f => ({ ...f, busca: "", categoria: "", tipo: "", recorrente: "", pagina: 1 }))}
                                className="text-xs text-rose-400 hover:text-rose-300 flex items-center gap-1">
                                <X className="w-3 h-3" /> Limpar
                            </button>
                        )}
                        <div className="ml-auto flex items-center gap-2">
                            <span className="text-xs text-slate-400 font-semibold">{paginacao.total} registro{paginacao.total !== 1 ? "s" : ""}</span>
                        </div>
                    </div>
                </div>

                {/* Tabela */}
                <div className="overflow-x-auto">
                    {loading ? (
                        <div className="p-10 space-y-3">
                            {[...Array(5)].map((_, i) => <Skeleton key={i} cls="h-10 w-full" />)}
                        </div>
                    ) : erro ? (
                        <div className="p-12 text-center">
                            <AlertCircle className="w-12 h-12 text-rose-400 mx-auto mb-3" />
                            <p className="text-rose-300 text-sm">{erro}</p>
                        </div>
                    ) : despesas.length === 0 ? (
                        <div className="p-12 text-center">
                            <FileText className="w-12 h-12 text-slate-600 mx-auto mb-3" />
                            <p className="text-slate-400">Nenhuma despesa encontrada</p>
                            <button onClick={abrirNovo} className="mt-4 px-5 py-2 rounded-xl bg-indigo-600 text-white text-sm font-semibold hover:bg-indigo-500 transition-all">
                                Adicionar primeira despesa
                            </button>
                        </div>
                    ) : (
                        <table className="w-full text-sm">
                            <thead>
                                <tr className="border-b border-slate-700">
                                    <th className="px-4 py-3 text-left text-xs font-bold text-slate-400 uppercase tracking-wider">Descrição</th>
                                    <th className="px-4 py-3 text-left text-xs font-bold text-slate-400 uppercase tracking-wider">Categoria</th>
                                    <th className="px-4 py-3 text-left text-xs font-bold text-slate-400 uppercase tracking-wider">Tipo</th>
                                    <th className="px-4 py-3 text-right text-xs font-bold text-slate-400 uppercase tracking-wider">Valor</th>
                                    <th className="px-4 py-3 text-left text-xs font-bold text-slate-400 uppercase tracking-wider">Data</th>
                                    <th className="px-4 py-3 text-left text-xs font-bold text-slate-400 uppercase tracking-wider">Pagamento</th>
                                    <th className="px-4 py-3 text-center text-xs font-bold text-slate-400 uppercase tracking-wider">Ações</th>
                                </tr>
                            </thead>
                            <tbody>
                                {despesas.map(d => (
                                    <tr key={d.id} className="border-b border-slate-800 hover:bg-slate-800/40 transition-colors">
                                        <td className="px-4 py-3">
                                            <div className="font-semibold text-white">{d.descricao}</div>
                                            {d.fornecedor && <div className="text-xs text-slate-500">{d.fornecedor.nome}</div>}
                                            {d.recorrente && (
                                                <span className="inline-flex items-center gap-1 text-[10px] font-bold text-cyan-400 mt-0.5">
                                                    <RefreshCw className="w-2.5 h-2.5" /> Recorrente
                                                </span>
                                            )}
                                        </td>
                                        <td className="px-4 py-3"><CategoriaBadge cat={d.categoria} /></td>
                                        <td className="px-4 py-3">
                                            <span className={`px-2 py-0.5 text-xs font-semibold rounded-full ${d.tipo === "fixa" ? "bg-violet-900/60 text-violet-300" : "bg-orange-900/60 text-orange-300"}`}>
                                                {d.tipo === "fixa" ? "Fixa" : "Variável"}
                                            </span>
                                        </td>
                                        <td className="px-4 py-3 text-right font-bold text-rose-400">{fmt(d.valor)}</td>
                                        <td className="px-4 py-3 text-slate-300">{fmtDate(d.data_despesa)}</td>
                                        <td className="px-4 py-3 text-slate-400 text-xs">{d.forma_pagamento || "—"}</td>
                                        <td className="px-4 py-3">
                                            <div className="flex items-center justify-center gap-2">
                                                <button onClick={() => { setDespesaSel(d); setModalDetalhes(true); }}
                                                    className="p-1.5 rounded-lg text-slate-400 hover:text-cyan-400 hover:bg-slate-700 transition-all" title="Ver detalhes">
                                                    <Eye className="w-4 h-4" />
                                                </button>
                                                <button onClick={() => abrirEdicao(d)}
                                                    className="p-1.5 rounded-lg text-slate-400 hover:text-amber-400 hover:bg-slate-700 transition-all" title="Editar">
                                                    <Edit2 className="w-4 h-4" />
                                                </button>
                                                <button onClick={() => excluir(d.id)}
                                                    className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-slate-700 transition-all" title="Excluir">
                                                    <Trash2 className="w-4 h-4" />
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
                {!loading && !erro && paginacao.paginas > 1 && (
                    <div className="px-4 py-3 border-t border-slate-700 flex items-center justify-between">
                        <span className="text-xs text-slate-400">
                            Página {filtros.pagina} de {paginacao.paginas} · {paginacao.total} registros
                        </span>
                        <div className="flex items-center gap-2">
                            <button disabled={filtros.pagina === 1}
                                onClick={() => setFiltros(f => ({ ...f, pagina: f.pagina - 1 }))}
                                className="p-1.5 rounded-lg bg-slate-800 border border-slate-700 text-slate-300 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed transition-all">
                                <ChevronLeft className="w-4 h-4" />
                            </button>
                            <button disabled={filtros.pagina >= paginacao.paginas}
                                onClick={() => setFiltros(f => ({ ...f, pagina: f.pagina + 1 }))}
                                className="p-1.5 rounded-lg bg-slate-800 border border-slate-700 text-slate-300 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed transition-all">
                                <ChevronRight className="w-4 h-4" />
                            </button>
                        </div>
                    </div>
                )}
            </div>

            {/* ═══ MODAL FORM ══════════════════════════════════════════════ */}
            {modalAberto && (
                <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                    <div className="w-full max-w-2xl rounded-2xl border border-slate-700 shadow-2xl overflow-hidden max-h-[90vh] flex flex-col"
                        style={{ background: "linear-gradient(135deg,#0f172a,#1e1b4b)" }}>
                        <div className="p-6 border-b border-slate-700 flex items-center justify-between">
                            <h2 className="text-xl font-black text-white">{modoEdicao ? "✏️ Editar Despesa" : "➕ Nova Despesa"}</h2>
                            <button onClick={() => setModalAberto(false)} className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-700 transition-all">
                                <X className="w-5 h-5" />
                            </button>
                        </div>
                        <div className="p-6 space-y-4 overflow-y-auto flex-1">
                            <div>
                                <label className="block text-xs font-bold text-slate-300 mb-1.5 uppercase tracking-wider">Descrição *</label>
                                <input type="text" value={formData.descricao}
                                    onChange={e => setFormData(f => ({ ...f, descricao: e.target.value }))}
                                    className="w-full px-4 py-2.5 rounded-xl bg-slate-800 border border-slate-600 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
                                    placeholder="Ex: Conta de energia de março" />
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-xs font-bold text-slate-300 mb-1.5 uppercase tracking-wider">Categoria *</label>
                                    <select value={formData.categoria}
                                        onChange={e => {
                                            const cat = CATEGORIAS.find(c => c.value === e.target.value);
                                            setFormData(f => ({ ...f, categoria: e.target.value, tipo: (cat?.tipo as any) || f.tipo }));
                                        }}
                                        className="w-full px-4 py-2.5 rounded-xl bg-slate-800 border border-slate-600 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm">
                                        <option value="">Selecione...</option>
                                        {GRUPOS_CATEGORIAS.map(grupo => (
                                            <optgroup key={grupo} label={grupo} className="bg-slate-700 text-indigo-300 font-bold">
                                                {CATEGORIAS.filter(c => c.grupo === grupo).map(c => (
                                                    <option key={c.value} value={c.value} className="text-white bg-slate-800 font-normal">{c.label}</option>
                                                ))}
                                            </optgroup>
                                        ))}
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-xs font-bold text-slate-300 mb-1.5 uppercase tracking-wider">Tipo</label>
                                    <select value={formData.tipo}
                                        onChange={e => setFormData(f => ({ ...f, tipo: e.target.value as any }))}
                                        className="w-full px-4 py-2.5 rounded-xl bg-slate-800 border border-slate-600 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm">
                                        <option value="fixa">Fixa (mensal)</option>
                                        <option value="variavel">Variável (pontual)</option>
                                    </select>
                                </div>
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-xs font-bold text-slate-300 mb-1.5 uppercase tracking-wider">Valor (R$) *</label>
                                    <input type="number" step="0.01" min="0" value={formData.valor}
                                        onChange={e => setFormData(f => ({ ...f, valor: e.target.value }))}
                                        className="w-full px-4 py-2.5 rounded-xl bg-slate-800 border border-slate-600 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
                                        placeholder="0,00" />
                                </div>
                                <div>
                                    <label className="block text-xs font-bold text-slate-300 mb-1.5 uppercase tracking-wider">Data da Despesa *</label>
                                    <input type="date" value={formData.data_despesa}
                                        onChange={e => setFormData(f => ({ ...f, data_despesa: e.target.value }))}
                                        className="w-full px-4 py-2.5 rounded-xl bg-slate-800 border border-slate-600 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm" />
                                </div>
                            </div>

                            {/* Datas de documento (ERP) */}
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-xs font-bold text-slate-300 mb-1.5 uppercase tracking-wider">
                                        📄 Data de Emissão
                                        <span className="ml-1 text-slate-500 normal-case font-normal">(nota/boleto)</span>
                                    </label>
                                    <input type="date" value={formData.data_emissao}
                                        onChange={e => setFormData(f => ({ ...f, data_emissao: e.target.value }))}
                                        className="w-full px-4 py-2.5 rounded-xl bg-slate-800 border border-slate-600 text-white focus:outline-none focus:ring-2 focus:ring-amber-500 text-sm" />
                                </div>
                                <div>
                                    <label className="block text-xs font-bold text-rose-400 mb-1.5 uppercase tracking-wider">
                                        ⏰ Data de Vencimento
                                        <span className="ml-1 text-slate-500 normal-case font-normal text-slate-300">(prazo pag.)</span>
                                    </label>
                                    <input type="date" value={formData.data_vencimento}
                                        onChange={e => setFormData(f => ({ ...f, data_vencimento: e.target.value }))}
                                        className="w-full px-4 py-2.5 rounded-xl bg-slate-800 border border-rose-600/60 text-white focus:outline-none focus:ring-2 focus:ring-rose-500 text-sm" />
                                </div>
                            </div>
                            <div>
                                <label className="block text-xs font-bold text-slate-300 mb-1.5 uppercase tracking-wider">Forma de Pagamento</label>
                                <select value={formData.forma_pagamento}
                                    onChange={e => setFormData(f => ({ ...f, forma_pagamento: e.target.value }))}
                                    className="w-full px-4 py-2.5 rounded-xl bg-slate-800 border border-slate-600 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm">
                                    <option value="">Selecione...</option>
                                    {FORMAS_PAGAMENTO.map(fp => <option key={fp} value={fp}>{fp}</option>)}
                                </select>
                            </div>
                            <label className="flex items-center gap-3 cursor-pointer p-3 rounded-xl border border-slate-700 hover:border-indigo-500 transition-all">
                                <input type="checkbox" checked={formData.recorrente}
                                    onChange={e => setFormData(f => ({ ...f, recorrente: e.target.checked }))}
                                    className="w-4 h-4 accent-indigo-500" />
                                <div>
                                    <span className="text-sm font-semibold text-white">Despesa Recorrente</span>
                                    <p className="text-xs text-slate-400">Cobrada mensalmente (aluguel, salário, contas fixas)</p>
                                </div>
                            </label>
                            <div>
                                <label className="block text-xs font-bold text-slate-300 mb-1.5 uppercase tracking-wider">Observações</label>
                                <textarea value={formData.observacoes}
                                    onChange={e => setFormData(f => ({ ...f, observacoes: e.target.value }))}
                                    rows={2} placeholder="Informações complementares..."
                                    className="w-full px-4 py-2.5 rounded-xl bg-slate-800 border border-slate-600 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm resize-none" />
                            </div>
                        </div>
                        <div className="p-5 border-t border-slate-700 flex justify-end gap-3">
                            <button onClick={() => setModalAberto(false)}
                                className="px-5 py-2.5 rounded-xl border border-slate-600 text-slate-300 hover:text-white hover:border-slate-400 text-sm font-semibold transition-all">
                                Cancelar
                            </button>
                            <button onClick={salvar}
                                className="px-6 py-2.5 rounded-xl text-white text-sm font-bold transition-all shadow-lg"
                                style={{ background: "linear-gradient(135deg,#6366f1,#8b5cf6)", boxShadow: "0 4px 15px rgba(99,102,241,0.4)" }}>
                                {modoEdicao ? "Atualizar" : "Salvar Despesa"}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* ═══ MODAL DETALHES ══════════════════════════════════════════ */}
            {modalDetalhes && despesaSel && (
                <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                    <div className="w-full max-w-lg rounded-2xl border border-slate-700 shadow-2xl"
                        style={{ background: "linear-gradient(135deg,#0f172a,#1e1b4b)" }}>
                        <div className="p-6 border-b border-slate-700 flex items-center justify-between">
                            <h2 className="text-xl font-black text-white">Detalhes da Despesa</h2>
                            <button onClick={() => setModalDetalhes(false)} className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-700 transition-all">
                                <X className="w-5 h-5" />
                            </button>
                        </div>
                        <div className="p-6 space-y-4">
                            <div className="flex items-start justify-between">
                                <div>
                                    <p className="text-xs text-slate-400 mb-1">Descrição</p>
                                    <p className="text-lg font-black text-white">{despesaSel.descricao}</p>
                                </div>
                                <div className="text-right">
                                    <p className="text-xs text-slate-400 mb-1">Valor</p>
                                    <p className="text-2xl font-black text-rose-400">{fmt(despesaSel.valor)}</p>
                                </div>
                            </div>
                            <div className="grid grid-cols-2 gap-4 pt-2 border-t border-slate-700">
                                <DetailItem label="Categoria"><CategoriaBadge cat={despesaSel.categoria} /></DetailItem>
                                <DetailItem label="Tipo">
                                    <span className={`px-2 py-0.5 text-xs font-bold rounded-full ${despesaSel.tipo === "fixa" ? "bg-violet-900/60 text-violet-300" : "bg-orange-900/60 text-orange-300"}`}>
                                        {despesaSel.tipo === "fixa" ? "Fixa" : "Variável"}
                                    </span>
                                </DetailItem>
                                <DetailItem label="Data">{fmtDate(despesaSel.data_despesa)}</DetailItem>
                                <DetailItem label="Pagamento">{despesaSel.forma_pagamento || "—"}</DetailItem>
                                <DetailItem label="Recorrente">{despesaSel.recorrente ? "✅ Sim" : "❌ Não"}</DetailItem>
                                {despesaSel.fornecedor && <DetailItem label="Fornecedor">{despesaSel.fornecedor.nome}</DetailItem>}
                            </div>
                            {despesaSel.observacoes && (
                                <div className="pt-3 border-t border-slate-700">
                                    <p className="text-xs text-slate-400 mb-1">Observações</p>
                                    <p className="text-sm text-slate-300 bg-slate-800 p-3 rounded-xl">{despesaSel.observacoes}</p>
                                </div>
                            )}
                        </div>
                        <div className="p-5 border-t border-slate-700 flex justify-end gap-3">
                            <button onClick={() => setModalDetalhes(false)}
                                className="px-5 py-2.5 rounded-xl border border-slate-600 text-slate-300 hover:text-white text-sm font-semibold transition-all">
                                Fechar
                            </button>
                            <button onClick={() => { setModalDetalhes(false); abrirEdicao(despesaSel); }}
                                className="px-5 py-2.5 rounded-xl bg-amber-600 text-white text-sm font-bold hover:bg-amber-500 transition-all flex items-center gap-2">
                                <Edit2 className="w-4 h-4" /> Editar
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

// ─── Sub-componentes locais ───────────────────────────────────────────────
function KpiCard({ icon, label, value, cor, sub }: {
    icon: React.ReactNode; label: string; value: number | null; cor: string; sub?: React.ReactNode;
}) {
    return (
        <div className="rounded-2xl border border-slate-700/60 p-5 relative overflow-hidden transition-all hover:border-slate-500/80"
            style={{ background: "rgba(15,23,42,0.6)", backdropFilter: "blur(12px)" }}>
            <div className={`absolute top-0 right-0 w-24 h-24 rounded-bl-full opacity-10 bg-gradient-to-bl ${cor}`} />
            <div className={`inline-flex p-2 rounded-xl bg-gradient-to-br ${cor} text-white mb-3 shadow-lg`}>
                {icon}
            </div>
            <p className="text-xs font-black text-slate-300 uppercase tracking-widest mb-1">{label}</p>
            {value === null ? (
                <Skeleton cls="h-7 w-32 mt-1" />
            ) : (
                <p className="text-2xl font-black text-white leading-tight">{fmt(value)}</p>
            )}
            {sub && <div className="mt-1">{sub}</div>}
        </div>
    );
}

function DetailItem({ label, children }: { label: string; children: React.ReactNode }) {
    return (
        <div>
            <p className="text-xs text-slate-400 mb-1">{label}</p>
            <div className="text-sm font-semibold text-white">{children}</div>
        </div>
    );
}

function EmptyChart() {
    return (
        <div className="h-full flex flex-col items-center justify-center text-slate-400">
            <BarChart2 className="w-10 h-10 mb-2 opacity-60" />
            <p className="text-sm font-bold">Sem dados no período selecionado</p>
        </div>
    );
}
