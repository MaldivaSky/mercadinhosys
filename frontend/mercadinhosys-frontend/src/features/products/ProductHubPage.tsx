import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { productsService } from './productsService';
import { formatCurrency } from '../../utils/formatters';
import {
    AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
    ComposedChart, Bar, Line, Legend
} from 'recharts';
import { ArrowLeft, TrendingUp, DollarSign, Activity, Truck, AlertTriangle, Percent, Clock, Package, CheckCircle } from 'lucide-react';
import { showToast } from '../../utils/toast';
import './ProductHubPage.css';

export default function ProductHubPage() {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    
    const [loading, setLoading] = useState(true);
    const [hubData, setHubData] = useState<any>(null);
    const [error, setError] = useState('');
    const [periodo, setPeriodo] = useState('all');
    const [vendasHistorico, setVendasHistorico] = useState<any[]>([]);

    useEffect(() => {
        if (!id) return;
        
        setLoading(true);
        productsService.getProductHubData(parseInt(id), periodo)
            .then(data => {
                if (data.success) {
                    setHubData(data);
                } else {
                    setError('Falha ao carregar dados do produto.');
                }
            })
            .catch(err => {
                console.error(err);
                setError('Erro ao comunicar com o servidor.');
            })
            .finally(() => {
                setLoading(false);
            });
            
        // Fetch vendas histórico
        let dias = 30;
        if (periodo === '7d') dias = 7;
        else if (periodo === '90d') dias = 90;
        else if (periodo === '1y') dias = 365;
        else if (periodo === 'all') dias = 365 * 2; // Máximo 2 anos para evitar sobrecarga no gráfico

        productsService.getProductSalesHistory(parseInt(id), dias)
            .then(data => {
                if (data.success && data.historico) {
                    const vendasFormatadas = data.historico.map((v: any) => ({
                        data: v.data,
                        quantidade_total: v.quantidade,
                        preco_medio: v.quantidade > 0 ? (v.valor_total / v.quantidade).toFixed(2) : 0,
                        custo_estimado: hubData?.produto?.preco_custo || 0 // Usando custo atual como proxy simples
                    }));
                    setVendasHistorico(vendasFormatadas);
                }
            })
            .catch(err => console.error('Erro ao carregar histórico de vendas:', err));
    }, [id, periodo, hubData?.produto?.preco_custo]);

    if (loading) {
        return (
            <div className="product-hub-container" style={{ alignItems: 'center', justifyContent: 'center' }}>
                <Activity className="animate-spin text-blue-500" size={48} />
                <h2 style={{ marginTop: '16px', color: '#64748b' }}>Carregando Hub do Produto...</h2>
            </div>
        );
    }

    if (error || !hubData) {
        return (
            <div className="product-hub-container" style={{ alignItems: 'center', justifyContent: 'center' }}>
                <AlertTriangle className="text-red-500" size={48} />
                <h2 style={{ marginTop: '16px', color: '#ef4444' }}>{error || 'Produto não encontrado'}</h2>
                <button className="btn-secondary" style={{ marginTop: '24px' }} onClick={() => navigate('/products')}>
                    Voltar para Produtos
                </button>
            </div>
        );
    }

    const { produto, estatisticas, historico_precos, lotes, pedidos_pendentes } = hubData;

    // Calcular KPIs Avançados
    const margemReal = estatisticas?.valor_total_vendido > 0 && produto?.preco_custo > 0
        ? ((produto.preco_venda - produto.preco_custo) / produto.preco_custo) * 100
        : (produto.margem_lucro || 0);

    let diasPeriodo = 30;
    if (periodo === '7d') diasPeriodo = 7;
    else if (periodo === '30d') diasPeriodo = 30;
    else if (periodo === '90d') diasPeriodo = 90;
    else if (periodo === '1y') diasPeriodo = 365;
    else if (periodo === 'all') {
        const dataCadastro = new Date(estatisticas?.primeira_venda || produto?.data_cadastro || produto?.created_at || new Date().getTime() - (365*24*60*60*1000));
        const diasDesdeCadastro = Math.max(1, Math.ceil((new Date().getTime() - dataCadastro.getTime()) / (1000 * 3600 * 24)));
        diasPeriodo = diasDesdeCadastro;
    }

    const vmd = (produto?.quantidade_vendida || 0) / diasPeriodo;
    const coberturaDias = vmd > 0 ? Math.round(produto.quantidade / vmd) : 0;

    // Preparar dados do gráfico (Histórico de Preços cruzado com Lotes)
    const chartData: any[] = [];
    const reversedHistory = (historico_precos || []).slice(0, 15).reverse();

    if (reversedHistory.length > 0) {
        const firstHp = reversedHistory[0];
        chartData.push({
            data: 'Inicial',
            Custo: firstHp.preco_custo_anterior || produto.preco_custo,
            Venda: firstHp.preco_venda_anterior || produto.preco_venda,
            Margem: margemReal,
            Fornecedor: 'Cadastro Inicial'
        });
    }

    reversedHistory.forEach((hp: any) => {
        // Encontrar lote que tenha a data de entrada próxima ou custo correspondente
        const dataAlteracao = new Date(hp.data_alteracao || hp.created_at);
        const dataStr = dataAlteracao.toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' });
        
        let fornecedorNome = 'Ajuste Manual / Sem Lote';
        if (lotes && lotes.length > 0) {
            // Tenta achar lote que causou esse custo
            const loteRelacionado = lotes.find((l: any) => Math.abs(l.preco_custo_unitario - hp.preco_custo_novo) < 0.1 || new Date(l.data_entrada).getTime() <= dataAlteracao.getTime());
            if (loteRelacionado && loteRelacionado.fornecedor?.nome_fantasia) {
                fornecedorNome = loteRelacionado.fornecedor.nome_fantasia;
            } else if (loteRelacionado && loteRelacionado.fornecedor?.razao_social) {
                fornecedorNome = loteRelacionado.fornecedor.razao_social;
            } else if (produto.fornecedor?.nome_fantasia) {
                fornecedorNome = produto.fornecedor.nome_fantasia;
            }
        } else if (produto.fornecedor?.nome_fantasia) {
            fornecedorNome = produto.fornecedor.nome_fantasia;
        }

        chartData.push({
            data: dataStr,
            Custo: hp.preco_custo_novo,
            Venda: hp.preco_venda_novo,
            Margem: hp.margem_nova,
            Fornecedor: fornecedorNome
        });
    });

    // Se não houver histórico de preços, cria um ponto inicial falso para o gráfico não ficar vazio
    if (chartData.length === 0) {
        chartData.push({
            data: new Date().toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' }),
            Custo: produto.preco_custo,
            Venda: produto.preco_venda,
            Margem: margemReal,
            Fornecedor: produto.fornecedor?.nome_fantasia || produto.fornecedor?.razao_social || 'Fornecedor Principal'
        });
    }

    // Custom Tooltip para o Gráfico
    const CustomTooltip = ({ active, payload, label }: any) => {
        if (active && payload && payload.length) {
            return (
                <div style={{ background: '#fff', padding: '12px', border: '1px solid #e2e8f0', borderRadius: '8px', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)' }}>
                    <p style={{ margin: '0 0 8px', fontWeight: 'bold', color: '#1e293b' }}>{label}</p>
                    {payload.map((entry: any, index: number) => (
                        <p key={index} style={{ margin: '4px 0', color: entry.color, fontSize: '0.9rem' }}>
                            {entry.name}: {formatCurrency(entry.value)}
                        </p>
                    ))}
                    {payload[0]?.payload?.Margem !== undefined && (
                        <p style={{ margin: '4px 0', color: '#10b981', fontSize: '0.9rem' }}>
                            Margem: {payload[0].payload.Margem.toFixed(2)}%
                        </p>
                    )}
                    {payload[0]?.payload?.Fornecedor && (
                        <div style={{ marginTop: '8px', paddingTop: '8px', borderTop: '1px solid #e2e8f0' }}>
                            <p style={{ margin: '0', fontSize: '0.85rem', color: '#64748b', display: 'flex', alignItems: 'center', gap: '4px' }}>
                                <Truck size={12} /> {payload[0].payload.Fornecedor}
                            </p>
                        </div>
                    )}
                </div>
            );
        }
        return null;
    };

    return (
        <div className="product-hub-container">
            {/* Cabeçalho do Produto */}
            <header className="hub-header">
                <div className="product-title-group">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
                        <button onClick={() => navigate('/products')} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#64748b' }}>
                            <ArrowLeft size={24} />
                        </button>
                        <span className="meta-badge" style={{ background: produto.ativo ? '#dcfce7' : '#fee2e2', color: produto.ativo ? '#166534' : '#991b1b' }}>
                            {produto.ativo ? 'Ativo' : 'Inativo'}
                        </span>
                        <span className="meta-badge" style={{ background: '#e0e7ff', color: '#3730a3' }}>
                            {produto.categoria?.nome || 'Sem Categoria'}
                        </span>
                    </div>
                    <h1 className="product-title">{produto.nome}</h1>
                    <div className="product-subtitle">
                        Código: {produto.codigo_interno} | Barras: {produto.codigo_barras || 'N/A'} | Curva ABC: <strong style={{color: '#3b82f6'}}>Classe {produto.classificacao_abc || 'C'}</strong>
                    </div>
                    {produto.descricao && (
                        <div style={{ marginTop: '8px', fontSize: '0.9rem', color: '#64748b', fontStyle: 'italic' }}>
                            Descrição: {produto.descricao}
                        </div>
                    )}
                </div>

                {/* Status Rápido */}
                <div className="quick-status">
                    <div className="status-item" style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                        <span className="status-label">Estoque Atual</span>
                        <span className="status-value" style={{ color: produto.quantidade <= (produto.quantidade_minima || 0) ? '#ef4444' : 'var(--text-color, inherit)' }}>
                            {produto.quantidade} {produto.unidade_medida}
                        </span>
                    </div>
                    <div className="status-item" style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                        <span className="status-label">Preço de Venda</span>
                        <span className="status-value highlight">{formatCurrency(produto.preco_venda)}</span>
                    </div>
                    <div className="status-item" style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                        <span className="status-label">Margem Base</span>
                        <span className="status-value highlight-green">{margemReal.toFixed(2)}%</span>
                    </div>
                    {lotes && lotes.length > 0 && (
                        <div className="status-item" style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                            <span className="status-label">Próx. Validade</span>
                            <span className="status-value highlight-green">
                                {new Date(Math.min(...lotes.filter((l: any) => l.data_validade).map((l: any) => new Date(l.data_validade).getTime()))).toLocaleDateString('pt-BR')}
                            </span>
                        </div>
                    )}
                </div>
            </header>

            {/* Ações Rápidas Integradas */}
            <div className="hub-actions-wrapper">
                <button 
                    onClick={() => navigate('/products', { state: { openEditFor: produto.id, returnTo: `/products/${produto.id}` } })}
                    className="btn-primary" 
                    style={{ background: '#0284c7', color: 'white', display: 'flex', alignItems: 'center', gap: '8px', padding: '10px 16px', borderRadius: '12px', fontWeight: 'bold' }}
                >
                    <Package size={18} />
                    Editar Produto
                </button>
                <button 
                    onClick={async () => {
                        const confirmMsg = produto.ativo 
                            ? 'Deseja realmente inativar este produto? Ele não aparecerá nas listagens padrão.' 
                            : 'Deseja reativar este produto?';
                        if (window.confirm(confirmMsg)) {
                            try {
                                await productsService.toggleProductStatus(produto.id, !produto.ativo);
                                showToast.success(produto.ativo ? 'Produto inativado com sucesso.' : 'Produto reativado com sucesso.');
                                setHubData((prev: any) => prev ? { ...prev, produto: { ...prev.produto, ativo: !prev.produto.ativo } } : prev);
                            } catch (e) {
                                showToast.error('Erro ao alterar status do produto.');
                            }
                        }
                    }}
                    className="btn-secondary" 
                    style={{ background: produto.ativo ? '#fff1f2' : '#f0fdf4', color: produto.ativo ? '#be123c' : '#15803d', display: 'flex', alignItems: 'center', gap: '8px', padding: '10px 16px', borderRadius: '12px', fontWeight: 'bold', border: `1px solid ${produto.ativo ? '#fecdd3' : '#bbf7d0'}` }}
                >
                    {produto.ativo ? <AlertTriangle size={18} /> : <CheckCircle size={18} />}
                    {produto.ativo ? 'Inativar Produto' : 'Reativar Produto'}
                </button>
                <button 
                    onClick={() => navigate('/products', { state: { openHistoryFor: produto.id, returnTo: `/products/${produto.id}` } })}
                    className="btn-primary" 
                    style={{ background: '#4f46e5', color: 'white', display: 'flex', alignItems: 'center', gap: '8px', padding: '10px 16px', borderRadius: '12px', fontWeight: 'bold' }}
                >
                    <Clock size={18} />
                    Histórico & Movimentações
                </button>
                <button 
                    onClick={() => navigate('/products', { state: { openAdjustFor: produto.id } })}
                    className="btn-secondary" 
                    style={{ background: '#f1f5f9', color: '#334155', display: 'flex', alignItems: 'center', gap: '8px', padding: '10px 16px', borderRadius: '12px', fontWeight: 'bold', border: '1px solid #cbd5e1' }}
                >
                    <Package size={18} />
                    Ajustar Estoque
                </button>
                <button 
                    onClick={() => navigate('/products', { state: { openDiscardFor: produto.id } })}
                    className="btn-secondary" 
                    style={{ background: '#fef2f2', color: '#b91c1c', display: 'flex', alignItems: 'center', gap: '8px', padding: '10px 16px', borderRadius: '12px', fontWeight: 'bold', border: '1px solid #fecaca' }}
                >
                    <AlertTriangle size={18} />
                    Descartar Perda/Vencido
                </button>
                <button 
                    onClick={() => {
                        if (window.confirm('ATENÇÃO! Esta ação é irreversível e excluirá definitivamente este produto. Deseja continuar?')) {
                            productsService.delete(produto.id, true).then(() => {
                                alert('Produto excluído com sucesso.');
                                navigate('/products');
                            }).catch(() => alert('Erro ao excluir produto.'));
                        }
                    }}
                    className="btn-secondary" 
                    style={{ background: '#fff1f2', color: '#e11d48', display: 'flex', alignItems: 'center', gap: '8px', padding: '10px 16px', borderRadius: '12px', fontWeight: 'bold', border: '1px solid #fda4af', marginLeft: 'auto' }}
                >
                    <AlertTriangle size={18} />
                    Excluir Definitivamente
                </button>
            </div>

            {/* Filtros e KPIs Principais */}
            <div className="hub-controls-wrapper">
                <select 
                    value={periodo} 
                    onChange={(e) => setPeriodo(e.target.value)}
                    style={{ padding: '8px 12px', borderRadius: '6px', border: '1px solid #e2e8f0', background: '#fff', color: '#1e293b', fontWeight: '500', cursor: 'pointer' }}
                >
                    <option value="all">Faturamento Histórico (Todo o Período)</option>
                    <option value="7d">Últimos 7 dias</option>
                    <option value="30d">Últimos 30 dias</option>
                    <option value="90d">Últimos 90 dias</option>
                    <option value="1y">Este Ano</option>
                </select>
            </div>
            
            <section className="kpi-grid">
                <div className="kpi-card">
                    <div className="kpi-icon-wrapper blue">
                        <DollarSign size={24} />
                    </div>
                    <div className="kpi-label">Faturamento Histórico</div>
                    <div className="kpi-value">{formatCurrency(estatisticas?.valor_total_vendido || 0)}</div>
                    <div className="kpi-trend positive">
                        {produto.quantidade_vendida} unidades vendidas
                    </div>
                </div>

                <div className="kpi-card">
                    <div className="kpi-icon-wrapper green">
                        <Percent size={24} />
                    </div>
                    <div className="kpi-label">Lucro Bruto (Aprox.)</div>
                    <div className="kpi-value">{formatCurrency(estatisticas?.lucro_total_estimado || 0)}</div>
                    <div className="kpi-trend positive">
                        Média de margem: {margemReal.toFixed(2)}%
                    </div>
                </div>

                <div className="kpi-card">
                    <div className="kpi-icon-wrapper purple">
                        <Clock size={24} />
                    </div>
                    <div className="kpi-label">Última Venda</div>
                    <div className="kpi-value" style={{ fontSize: '1.2rem' }}>
                        {produto.ultima_venda ? new Date(produto.ultima_venda).toLocaleDateString('pt-BR') : 'Sem vendas'}
                    </div>
                    <div className="kpi-trend neutral">
                        {estatisticas?.dias_sem_venda !== undefined ? `${estatisticas.dias_sem_venda} dias atrás` : '---'}
                    </div>
                </div>

                <div className="kpi-card">
                    <div className="kpi-icon-wrapper orange">
                        <TrendingUp size={24} />
                    </div>
                    <div className="kpi-label">Cobertura de Estoque</div>
                    <div className="kpi-value">{coberturaDias > 999 ? '∞' : coberturaDias} <span style={{ fontSize: '1rem', color: '#64748b', fontWeight: '500' }}>Dias</span></div>
                    <div className="kpi-trend neutral">
                        VMD: {vmd.toFixed(2)} un/dia
                    </div>
                </div>
            </section>

            {/* Área de Conteúdo */}
            <section className="hub-content-grid">
                {/* Gráfico de Inteligência: Giro vs Margem */}
                <div className="content-panel" style={{ gridColumn: '1 / -1' }}>
                    <div className="panel-header">
                        <h3 className="panel-title"><Activity size={20} color="#10b981" /> Inteligência de Produtos: Giro vs Preço/Margem</h3>
                    </div>
                    <p style={{ color: '#64748b', fontSize: '0.9rem', lineHeight: '1.5' }}>
                        Analise o volume de vendas (Giro) em relação às mudanças de preço e custo médio do período.
                    </p>
                    <div style={{ width: '100%', height: 350, marginTop: '20px' }}>
                        {vendasHistorico.length > 0 ? (
                            <ResponsiveContainer>
                                <ComposedChart data={vendasHistorico} margin={{ top: 20, right: 30, left: 0, bottom: 0 }}>
                                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                                    <XAxis dataKey="data" stroke="#94a3b8" fontSize={12} tickFormatter={(val) => {
                                        const d = new Date(val);
                                        return d.toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' });
                                    }} />
                                    <YAxis yAxisId="left" stroke="#3b82f6" fontSize={12} orientation="left" />
                                    <YAxis yAxisId="right" stroke="#10b981" fontSize={12} orientation="right" tickFormatter={(val) => `R$${val}`} />
                                    <Tooltip 
                                        formatter={(value: any, name: string) => {
                                            if (name === 'Volume (Giro)') return [value, name];
                                            return [formatCurrency(value), name];
                                        }}
                                        labelFormatter={(label) => new Date(label).toLocaleDateString('pt-BR')}
                                    />
                                    <Legend />
                                    <Bar yAxisId="left" dataKey="quantidade_total" name="Volume (Giro)" fill="#3b82f6" radius={[4, 4, 0, 0]} barSize={20} />
                                    <Line yAxisId="right" type="monotone" dataKey="preco_medio" name="Preço Médio Praticado" stroke="#10b981" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 6 }} />
                                    <Line yAxisId="right" type="monotone" dataKey="custo_estimado" name="Custo Médio" stroke="#94a3b8" strokeWidth={2} strokeDasharray="5 5" dot={false} />
                                </ComposedChart>
                            </ResponsiveContainer>
                        ) : (
                            <div style={{ display: 'flex', height: '100%', alignItems: 'center', justifyContent: 'center', color: '#94a3b8', background: '#f8fafc', borderRadius: '8px' }}>
                                Nenhum dado de venda no período selecionado para cruzar com preço/margem.
                            </div>
                        )}
                    </div>
                </div>

                {/* Gráfico de Evolução de Preços */}
                <div className="content-panel">
                    <div className="panel-header">
                        <h3 className="panel-title"><TrendingUp size={20} color="#6366f1" /> Histórico de Preço e Custo</h3>
                    </div>
                    <div style={{ width: '100%', height: 350, marginTop: '20px' }}>
                        <ResponsiveContainer>
                            <AreaChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                                <defs>
                                    <linearGradient id="colorVenda" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3}/>
                                        <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                                    </linearGradient>
                                    <linearGradient id="colorCusto" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#94a3b8" stopOpacity={0.3}/>
                                        <stop offset="95%" stopColor="#94a3b8" stopOpacity={0}/>
                                    </linearGradient>
                                </defs>
                                <XAxis dataKey="data" stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
                                <YAxis stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(val) => `R$${val}`} domain={['auto', 'auto']} />
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                                <Tooltip content={<CustomTooltip />} />
                                <Area type="monotone" dataKey="Venda" stroke="#6366f1" strokeWidth={3} fillOpacity={1} fill="url(#colorVenda)" />
                                <Area type="monotone" dataKey="Custo" stroke="#94a3b8" strokeWidth={3} fillOpacity={1} fill="url(#colorCusto)" />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Radar de Fornecedores */}
                <div className="content-panel">
                    <div className="panel-header">
                        <h3 className="panel-title"><Truck size={20} color="#f97316" /> Radar de Fornecedores</h3>
                    </div>
                    <p style={{ color: '#64748b', fontSize: '0.9rem', lineHeight: '1.5' }}>
                        Comparativo baseado no histórico de ordens de compra e preços recebidos.
                    </p>
                    
                    <div className="supplier-list">
                        {/* Lista de Fornecedores baseada nos lotes */}
                        {(() => {
                            const lotesForRadar = lotes && lotes.length > 0 ? lotes : [];
                            if (lotesForRadar.length === 0 && produto?.fornecedor) {
                                lotesForRadar.push({
                                    fornecedor: produto.fornecedor,
                                    numero_lote: 'Padrão (Cadastro Inicial)',
                                    quantidade: produto.quantidade || 0,
                                    preco_custo_unitario: produto.preco_custo
                                });
                            }

                            return lotesForRadar.length > 0 ? (
                                lotesForRadar.map((lote: any, idx: number) => {
                                    if (!lote.fornecedor) return null;
                                    return (
                                        <div 
                                            key={idx}
                                            className="supplier-item best-price" 
                                            style={{ cursor: 'pointer', transition: 'all 0.2s ease', border: '1px solid transparent', marginBottom: '8px' }}
                                            onMouseOver={(e) => e.currentTarget.style.borderColor = '#3b82f6'}
                                            onMouseOut={(e) => e.currentTarget.style.borderColor = 'transparent'}
                                            onClick={() => navigate(`/suppliers/${lote.fornecedor.id}`)}
                                        >
                                            <div className="supplier-info">
                                                <span className="supplier-name">{lote.fornecedor.nome_fantasia || lote.fornecedor.razao_social}</span>
                                                <div style={{ display: 'flex', gap: '12px', fontSize: '0.85rem', color: '#94a3b8', marginTop: '4px' }}>
                                                    Lote: {lote.numero_lote} | Qtd: {lote.quantidade}
                                                </div>
                                            </div>
                                            <div className="supplier-metrics" style={{ alignSelf: 'center', textAlign: 'right' }}>
                                                <span className="supplier-price">{formatCurrency(lote.preco_custo_unitario)}</span>
                                            </div>
                                        </div>
                                    );
                                }).filter(Boolean)
                            ) : (
                                <div style={{ padding: '20px', textAlign: 'center', color: '#94a3b8', background: '#f8fafc', borderRadius: '8px' }}>
                                    Nenhum fornecedor registrado.
                                </div>
                            );
                        })()}
                        
                        {pedidos_pendentes && pedidos_pendentes.length > 0 && (
                            <div style={{ marginTop: '16px', padding: '12px', background: '#fff7ed', borderRadius: '8px', border: '1px solid #ffedd5' }}>
                                <h4 style={{ color: '#c2410c', fontWeight: '600', fontSize: '0.9rem', marginBottom: '8px' }}>Pedidos Pendentes</h4>
                                {pedidos_pendentes.map((ped: any) => (
                                    <div key={ped.id} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', color: '#9a3412' }}>
                                        <span>Pedido #{ped.pedido_numero}</span>
                                        <span>{ped.quantidade_solicitada} un @ {formatCurrency(ped.preco_unitario)}</span>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>

                {/* Tabela de Lotes */}
                <div className="content-panel" style={{ gridColumn: '1 / -1' }}>
                    <div className="panel-header">
                        <h3 className="panel-title"><Clock size={20} color="#8b5cf6" /> Controle de Lotes e Validade</h3>
                    </div>
                    <div style={{ marginTop: '16px', overflowX: 'auto' }}>
                        {lotes && lotes.length > 0 ? (
                            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.9rem' }}>
                                <thead>
                                    <tr style={{ borderBottom: '1px solid #e2e8f0', color: '#64748b' }}>
                                        <th style={{ padding: '12px' }}>Nº Lote</th>
                                        <th style={{ padding: '12px' }}>Data Entrada (Compra)</th>
                                        <th style={{ padding: '12px' }}>Fabricação</th>
                                        <th style={{ padding: '12px' }}>Validade</th>
                                        <th style={{ padding: '12px', textAlign: 'right' }}>Qtd Atual</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {lotes.map((lote: any) => {
                                        const diasValidade = Math.ceil((new Date(lote.data_validade).getTime() - new Date().getTime()) / (1000 * 3600 * 24));
                                        const isVencido = diasValidade < 0;
                                        const isProximo = diasValidade >= 0 && diasValidade <= 30;
                                        return (
                                            <tr key={lote.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                                                <td style={{ padding: '12px', fontWeight: '500' }}>{lote.numero_lote}</td>
                                                <td style={{ padding: '12px' }}>{new Date(lote.data_entrada).toLocaleDateString('pt-BR')}</td>
                                                <td style={{ padding: '12px' }}>{lote.data_fabricacao ? new Date(lote.data_fabricacao).toLocaleDateString('pt-BR') : '---'}</td>
                                                <td style={{ padding: '12px', color: isVencido ? '#ef4444' : (isProximo ? '#f59e0b' : '#10b981'), fontWeight: isVencido || isProximo ? 'bold' : 'normal' }}>
                                                    {new Date(lote.data_validade).toLocaleDateString('pt-BR')}
                                                    {isVencido && ' (Vencido)'}
                                                    {isProximo && ` (${diasValidade} dias)`}
                                                </td>
                                                <td style={{ padding: '12px', textAlign: 'right', fontWeight: 'bold' }}>{lote.quantidade}</td>
                                            </tr>
                                        );
                                    })}
                                </tbody>
                            </table>
                        ) : (
                            <div style={{ padding: '20px', textAlign: 'center', color: '#94a3b8', background: '#f8fafc', borderRadius: '8px' }}>
                                Não há lotes registrados ou em estoque para este produto.
                            </div>
                        )}
                    </div>
                </div>
            </section>
        </div>
    );
}
