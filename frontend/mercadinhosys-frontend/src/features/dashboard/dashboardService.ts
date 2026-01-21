// dashboardService.ts - CIENTISTA DE DADOS BASEADO NO BACKEND
import { apiClient } from '../../api/apiClient';
import { ApiResponse } from '../../types';

// ==================== INTERFACES EXATAS DO BACKEND ====================

interface DashboardResumoResponse {
    success: boolean;
    timestamp: string;
    usuario: {
        nome: string;
        role: string;
        estabelecimento_id: number;
    };
    periodos: {
        dia: string;
        mes: string;
        analise: string;
    };
    metricas: {
        dia: {
            total_vendas: number;
            quantidade_vendas: number;
            ticket_medio: number | null;
            unidade: string;
        };
        mes: {
            total_vendas: number;
            total_despesas: number;
            lucro_estimado: number;
            margem_lucro: number | null;
            categorias_despesas: Array<{
                categoria: string;
                total: number;
                quantidade: number;
                percentual: number;
            }>;
        };
    };
    analises: {
        produtos_estrela: Array<{
            id: number;
            nome: string;
            categoria: string;
            preco_custo: number;
            preco_venda: number;
            quantidade_estoque: number;
            quantidade_minima: number;
            quantidade_vendida: number;
            valor_total_vendido: number;
            margem_lucro: number | null;
            frequencia_venda: number | null;
            rotacao_estoque: number | null;
            score_estrela?: number;
            criterios_atingidos?: string[];
            classificacao?: string;
        }>;
        alertas_estoque: {
            estoque_baixo: number;
            validade_proxima: number;
            margem_baixa: number;
            sem_venda: number;
        };
        insights_priorizados: Array<{
            id: string;
            titulo: string;
            descricao: string;
            acao: string;
            impacto: string;
            prioridade: number;
            categoria: string;
        }>;
    };
    metadados: {
        base_calculo: string;
        configuracoes: {
            margem_lucro_alvo: number;
            dias_alerta_validade: number;
            estoque_minimo_dias: number;
        };
        observacoes: string[];
    };
}

interface TendenciaResponse {
    success: boolean;
    analise: {
        tipo: string;
        periodo_dias: number;
        dias_analisados: number;
        validacao_estatistica: {
            minimo_dias_atingido: boolean;
            variacao_detectada: boolean;
            dados_suficientes: boolean;
        };
    };
    dados: {
        datas: string[];
        valores: number[];
        medias_moveis: {
            "7_dias": (number | null)[];
            "14_dias": (number | null)[];
        };
    };
    resultados: {
        tendencia: {
            inclinacao: number;
            intercepto: number;
            r2: number;
            confianca: string;
            direcao: string;
            magnitude: number;
        } | null;
        crescimento_7d: number | null;
        estatisticas: {
            media: number;
            maximo: number;
            minimo: number;
            variacao: number;
        };
    };
    interpretacao: {
        direcao: string;
        confianca: string;
        recomendacao: string | null;
    };
}

interface ProdutosAnaliseResponse {
    success: boolean;
    periodo_analise: number;
    resumo: {
        total_produtos: number;
        produtos_com_venda: number;
        produtos_ativos: number;
        valor_total_estoque: number;
        valor_total_vendido: number;
    };
    classificacoes: {
        estrela: {
            quantidade: number;
            valor_contribuicao: number;
            produtos: Array<{
                id: number;
                nome: string;
                categoria: string;
                preco_custo: number;
                preco_venda: number;
                quantidade_estoque: number;
                quantidade_minima: number;
                quantidade_vendida: number;
                valor_total_vendido: number;
                margem_lucro: number | null;
                frequencia_venda: number | null;
                rotacao_estoque: number | null;
                score_estrela?: number;
                criterios_atingidos?: string[];
                classificacao?: string;
            }>;
        };
        abc: {
            A: Array<{
                id: number;
                nome: string;
                valor_total_vendido: number;
                participacao: number;
                acumulado: number;
            }>;
            B: Array<{
                id: number;
                nome: string;
                valor_total_vendido: number;
                participacao: number;
                acumulado: number;
            }>;
            C: Array<{
                id: number;
                nome: string;
                valor_total_vendido: number;
                participacao: number;
                acumulado: number;
            }>;
        };
        problemas: {
            [key: string]: number;
        };
    };
    metricas_setor: {
        [categoria: string]: {
            quantidade_produtos: number;
            total_vendido: number;
            media_margem: number;
            media_rotacao: number;
        };
    };
    recomendacoes: string[];
}

interface ComparativoResponse {
    success: boolean;
    metadados: {
        base_comparacao: string;
        periodo_referencia: string;
        observacao: string;
    };
    periodos: {
        esta_semana: PeriodoComparativo;
        semana_passada: PeriodoComparativo;
        este_mes: PeriodoComparativo;
        mes_passado: PeriodoComparativo;
    };
    crescimentos: {
        semanal: number | null;
        mensal: number | null;
    };
    analise_comparativa: {
        tendencia_curto_prazo: string;
        tendencia_longo_prazo: string;
        alertas: string[];
        oportunidades: string[];
    };
}

interface PeriodoComparativo {
    total: number;
    quantidade_vendas: number;
    ticket_medio: number | null;
    dias: number;
    media_diaria: number;
}

// ==================== TIPOS PARA O DASHBOARDPAGE EXISTENTE ====================
interface DashboardPageData {
    metrics: {
        total_vendas_hoje: number;
        ticket_medio: number;
        lucro_mes: number;
        total_vendas_mes: number;
    };
    vendasPorCategoria: Array<{
        categoria: string;
        total: number;
    }>;
    vendasUltimos7Dias: Array<{
        data: string;
        total: number;
    }>;
    alertas: {
        estoque_baixo: number;
        validade_proxima: number;
    };
}

// ==================== SERVIÇO PRINCIPAL ====================
export const dashboardService = {
    // 1. Endpoint principal /dashboard/resumo
    getResumoDashboard: async (): Promise<DashboardResumoResponse> => {
        try {
            const response = await apiClient.get<ApiResponse<DashboardResumoResponse>>('/dashboard/resumo');

            if (!response.data.success) {
                throw new Error(response.data.message || 'Erro ao buscar resumo do dashboard');
            }

            if (!response.data.data) {
                throw new Error('Dados do resumo ausentes');
            }

            return response.data.data;
        } catch (error) {
            console.error('Erro ao buscar resumo do dashboard:', error);
            throw error;
        }
    },

    // 2. Análise de tendência /dashboard/tendencia
    getAnaliseTendencia: async (dias: number = 30): Promise<TendenciaResponse> => {
        try {
            const response = await apiClient.get<ApiResponse<TendenciaResponse>>('/dashboard/tendencia', {
                params: { dias: Math.min(Math.max(dias, 7), 365) }
            });

            if (!response.data.success) {
                throw new Error(response.data.message || 'Erro ao buscar análise de tendência');
            }

            if (!response.data.data) {
                throw new Error('Dados de tendência ausentes');
            }

            return response.data.data;
        } catch (error) {
            console.error('Erro ao buscar análise de tendência:', error);
            throw error;
        }
    },

    // 3. Análise de produtos /dashboard/produtos/analise
    getAnaliseProdutos: async (periodoDias: number = 90): Promise<ProdutosAnaliseResponse> => {
        try {
            const response = await apiClient.get<ApiResponse<ProdutosAnaliseResponse>>('/dashboard/produtos/analise', {
                params: { periodo: Math.min(Math.max(periodoDias, 30), 365) }
            });

            if (!response.data.success) {
                throw new Error(response.data.message || 'Erro ao buscar análise de produtos');
            }

            if (!response.data.data) {
                throw new Error('Dados de análise de produtos ausentes');
            }

            return response.data.data;
        } catch (error) {
            console.error('Erro ao buscar análise de produtos:', error);
            throw error;
        }
    },

    // 4. Comparativo de períodos /dashboard/comparativo
    getComparativoPeriodos: async (): Promise<ComparativoResponse> => {
        try {
            const response = await apiClient.get<ApiResponse<ComparativoResponse>>('/dashboard/comparativo');

            if (!response.data.success) {
                throw new Error(response.data.message || 'Erro ao buscar comparativo');
            }

            if (!response.data.data) {
                throw new Error('Dados comparativos ausentes');
            }

            return response.data.data;
        } catch (error) {
            console.error('Erro ao buscar comparativo:', error);
            throw error;
        }
    },

    // 5. Dashboard completo para o DashboardPage.tsx (MÉTODO QUE VOCÊ PRECISA)
    getDashboardCompleto: async (): Promise<DashboardPageData> => {
        try {
            console.log('🔍 DashboardService: Iniciando coleta de dados do backend...');

            // Coletar todos os dados em paralelo
            const [resumo, tendencia, produtosAnalise, comparativo] = await Promise.all([
                dashboardService.getResumoDashboard(),
                dashboardService.getAnaliseTendencia(7), // Últimos 7 dias
                dashboardService.getAnaliseProdutos(90),
                dashboardService.getComparativoPeriodos()
            ]);

            console.log('✅ DashboardService: Dados coletados com sucesso');
            console.log('📊 Resumo:', resumo.metricas.dia.total_vendas);
            console.log('📈 Tendência:', tendencia.dados.valores.length, 'dias');
            console.log('🏷️ Produtos:', produtosAnalise.resumo.total_produtos);
            console.log('📅 Comparativo:', comparativo.crescimentos.semanal);

            // Transformar dados para o formato esperado pelo DashboardPage.tsx
            const result: DashboardPageData = {
                metrics: {
                    total_vendas_hoje: resumo.metricas.dia.total_vendas,
                    ticket_medio: resumo.metricas.dia.ticket_medio || 0,
                    lucro_mes: resumo.metricas.mes.lucro_estimado,
                    total_vendas_mes: resumo.metricas.mes.total_vendas
                },
                vendasPorCategoria: Object.entries(produtosAnalise.metricas_setor).map(([categoria, dados]) => ({
                    categoria,
                    total: dados.total_vendido
                })).sort((a, b) => b.total - a.total).slice(0, 10), // Top 10 categorias
                vendasUltimos7Dias: tendencia.dados.datas.map((data, index) => ({
                    data: data,
                    total: tendencia.dados.valores[index] || 0
                })).slice(-7), // Últimos 7 dias
                alertas: {
                    estoque_baixo: resumo.analises.alertas_estoque.estoque_baixo,
                    validade_proxima: resumo.analises.alertas_estoque.validade_proxima
                }
            };

            console.log('🎯 DashboardService: Dados transformados:', result);
            return result;

        } catch (error) {
            console.error('❌ DashboardService: Erro ao buscar dashboard completo:', error);

            // Em caso de erro, retornar estrutura vazia para não quebrar o frontend
            return {
                metrics: {
                    total_vendas_hoje: 0,
                    ticket_medio: 0,
                    lucro_mes: 0,
                    total_vendas_mes: 0
                },
                vendasPorCategoria: [],
                vendasUltimos7Dias: [],
                alertas: {
                    estoque_baixo: 0,
                    validade_proxima: 0
                }
            };
        }
    },

    // 6. Métricas simplificadas para cards rápidos
    getMetricasRapidas: async () => {
        try {
            const resumo = await dashboardService.getResumoDashboard();

            return {
                vendasHoje: resumo.metricas.dia.total_vendas,
                vendasHojeQuantidade: resumo.metricas.dia.quantidade_vendas,
                ticketMedioHoje: resumo.metricas.dia.ticket_medio,
                vendasMes: resumo.metricas.mes.total_vendas,
                despesasMes: resumo.metricas.mes.total_despesas,
                lucroEstimadoMes: resumo.metricas.mes.lucro_estimado,
                margemLucroMes: resumo.metricas.mes.margem_lucro,
                alertasEstoque: resumo.analises.alertas_estoque,
                produtosEstrela: resumo.analises.produtos_estrela.length,
                insightsPriorizados: resumo.analises.insights_priorizados
            };
        } catch (error) {
            console.error('Erro ao buscar métricas rápidas:', error);
            throw error;
        }
    },

    // 7. Dados para gráfico de tendência (Últimos 30 dias)
    getDadosGraficoTendencia: async (dias: number = 30) => {
        try {
            const tendencia = await dashboardService.getAnaliseTendencia(dias);

            return {
                datas: tendencia.dados.datas,
                valores: tendencia.dados.valores,
                mediasMoveis7d: tendencia.dados.medias_moveis["7_dias"],
                mediasMoveis14d: tendencia.dados.medias_moveis["14_dias"],
                tendenciaAtual: tendencia.resultados.tendencia,
                crescimento7d: tendencia.resultados.crescimento_7d,
                estatisticas: tendencia.resultados.estatisticas,
                interpretacao: tendencia.interpretacao
            };
        } catch (error) {
            console.error('Erro ao buscar dados para gráfico de tendência:', error);
            throw error;
        }
    },

    // 8. Dados para gráfico de categorias
    getDadosCategorias: async () => {
        try {
            const produtosAnalise = await dashboardService.getAnaliseProdutos(90);

            return {
                categorias: Object.entries(produtosAnalise.metricas_setor).map(([categoria, dados]) => ({
                    categoria,
                    totalVendido: dados.total_vendido,
                    quantidadeProdutos: dados.quantidade_produtos,
                    mediaMargem: dados.media_margem,
                    mediaRotacao: dados.media_rotacao
                })),
                resumo: produtosAnalise.resumo,
                classificacaoABC: produtosAnalise.classificacoes.abc
            };
        } catch (error) {
            console.error('Erro ao buscar dados de categorias:', error);
            throw error;
        }
    },

    // 9. Produtos com alertas detalhados
    getAlertasDetalhados: async () => {
        try {
            const produtosAnalise = await dashboardService.getAnaliseProdutos(90);
            const resumo = await dashboardService.getResumoDashboard();

            return {
                estoqueBaixo: produtosAnalise.classificacoes.problemas.estoque_baixo || 0,
                validadeProxima: produtosAnalise.classificacoes.problemas.validade_proxima || 0,
                margemBaixa: produtosAnalise.classificacoes.problemas.margem_baixa || 0,
                semVenda: produtosAnalise.classificacoes.problemas.sem_venda || 0,
                configuracoes: resumo.metadados.configuracoes,
                dataConsulta: new Date().toISOString()
            };
        } catch (error) {
            console.error('Erro ao buscar alertas detalhados:', error);
            throw error;
        }
    }
};

// ==================== FUNÇÕES DE FORMATAÇÃO ====================
export const formatarMoeda = (valor: number | null): string => {
    if (valor === null || valor === undefined) return 'R$ 0,00';
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(valor);
};

export const formatarPorcentagem = (valor: number | null, casasDecimais: number = 1): string => {
    if (valor === null || valor === undefined) return '0,0%';
    return valor.toFixed(casasDecimais).replace('.', ',') + '%';
};

export const formatarData = (dataString: string): string => {
    try {
        const data = new Date(dataString);
        return data.toLocaleDateString('pt-BR');
    } catch {
        return dataString;
    }
};

export const formatarDataHora = (dataString: string): string => {
    try {
        const data = new Date(dataString);
        return data.toLocaleDateString('pt-BR') + ' ' + data.toLocaleTimeString('pt-BR', {
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch {
        return dataString;
    }
};

// ==================== FUNÇÕES DE ANÁLISE ====================
export const calcularTendenciaTexto = (inclinacao: number, confianca: string): string => {
    if (Math.abs(inclinacao) < 0.1) return 'Estável';
    if (inclinacao > 0) return 'Em Crescimento';
    return 'Em Queda';
};

export const classificarPrioridade = (prioridade: number): { texto: string, cor: string } => {
    switch (prioridade) {
        case 1: return { texto: 'Crítico', cor: 'bg-red-500' };
        case 2: return { texto: 'Alta', cor: 'bg-orange-500' };
        case 3: return { texto: 'Média', cor: 'bg-yellow-500' };
        default: return { texto: 'Baixa', cor: 'bg-green-500' };
    }
};

export const analisarPerformance = (
    valorAtual: number,
    valorAnterior: number,
    tipo: 'vendas' | 'lucro' | 'ticket'
): { status: 'positivo' | 'negativo' | 'neutro', percentual: number } => {
    if (valorAnterior === 0) return { status: 'neutro', percentual: 0 };

    const percentual = ((valorAtual - valorAnterior) / Math.abs(valorAnterior)) * 100;

    let status: 'positivo' | 'negativo' | 'neutro' = 'neutro';

    if (tipo === 'vendas' || tipo === 'lucro') {
        status = percentual >= 0 ? 'positivo' : 'negativo';
    } else if (tipo === 'ticket') {
        status = percentual >= 5 ? 'positivo' : percentual <= -5 ? 'negativo' : 'neutro';
    }

    return { status, percentual: Math.abs(percentual) };
};

// Exportar tipos para uso em componentes
export type {
    DashboardResumoResponse,
    TendenciaResponse,
    ProdutosAnaliseResponse,
    ComparativoResponse,
    PeriodoComparativo,
    DashboardPageData
};