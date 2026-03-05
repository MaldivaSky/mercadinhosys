import { useState, useCallback, useEffect } from 'react';
import { Produto, Cliente } from '../types';
import { pdvService, ConfiguracoesPDV, CaixaPDV } from '../features/pdv/pdvService';
import { showToast } from '../utils/toast';

export interface ItemCarrinho {
    produto: Produto;
    quantidade: number;
    precoUnitario: number;
    desconto: number;
    descontoPercentual: boolean;
    total: number;
}

export interface FormaPagamento {
    tipo: string;
    label: string;
    taxa: number;
    permite_troco: boolean;
}

export interface PDVSession {
    id: string;
    carrinho: ItemCarrinho[];
    cliente: Cliente | null;
    emailRecibo: string;
    formaPagamentoSelecionada: string;
    valorRecebido: number;
    observacoes: string;
    descontoGeral: number;
    descontoPercentual: boolean;
}

const createInitialSession = (): PDVSession => ({
    id: Date.now().toString(),
    carrinho: [],
    cliente: null,
    emailRecibo: '',
    formaPagamentoSelecionada: 'dinheiro',
    valorRecebido: 0,
    observacoes: '',
    descontoGeral: 0,
    descontoPercentual: false,
});

export const usePDV = () => {
    // Configurações e permissões globais
    const [configuracoes, setConfiguracoes] = useState<ConfiguracoesPDV | null>(null);
    const [formasPagamento, setFormasPagamento] = useState<FormaPagamento[]>([]);
    const [loading, setLoading] = useState(false);
    const [caixaAberto, setCaixaAberto] = useState<CaixaPDV | null>(null);

    // Múltiplas Sessões do PDV
    const [sessoes, setSessoes] = useState<PDVSession[]>([createInitialSession()]);
    const [sessaoAtivaId, setSessaoAtivaId] = useState<string>(sessoes[0].id);

    const sessaoAtiva = sessoes.find(s => s.id === sessaoAtivaId) || sessoes[0];

    // Getters da sessão atual
    const carrinho = sessaoAtiva.carrinho;
    const cliente = sessaoAtiva.cliente;
    const emailRecibo = sessaoAtiva.emailRecibo;
    const formaPagamentoSelecionada = sessaoAtiva.formaPagamentoSelecionada;
    const valorRecebido = sessaoAtiva.valorRecebido;
    const observacoes = sessaoAtiva.observacoes;
    const descontoGeral = sessaoAtiva.descontoGeral;
    const descontoPercentual = sessaoAtiva.descontoPercentual;

    const updateSessao = useCallback((updates: Partial<PDVSession>) => {
        setSessoes(prev => prev.map(s => s.id === sessaoAtivaId ? { ...s, ...updates } : s));
    }, [sessaoAtivaId]);

    const setCarrinho = useCallback((value: ItemCarrinho[] | ((prev: ItemCarrinho[]) => ItemCarrinho[])) => {
        setSessoes(prev => prev.map(s => {
            if (s.id !== sessaoAtivaId) return s;
            const newValue = typeof value === 'function' ? value(s.carrinho) : value;
            return { ...s, carrinho: newValue };
        }));
    }, [sessaoAtivaId]);

    const setCliente = useCallback((c: Cliente | null) => {
        setSessoes(prev => prev.map(s => {
            if (s.id !== sessaoAtivaId) return s;
            return { ...s, cliente: c, emailRecibo: c?.email || '' };
        }));
    }, [sessaoAtivaId]);

    const setEmailRecibo = useCallback((e: string) => updateSessao({ emailRecibo: e }), [updateSessao]);
    const setFormaPagamentoSelecionada = useCallback((f: string) => updateSessao({ formaPagamentoSelecionada: f }), [updateSessao]);
    const setValorRecebido = useCallback((v: number | ((prev: number) => number)) => {
        setSessoes(prev => prev.map(s => {
            if (s.id !== sessaoAtivaId) return s;
            const n = typeof v === 'function' ? v(s.valorRecebido) : v;
            return { ...s, valorRecebido: n };
        }));
    }, [sessaoAtivaId]);
    const setObservacoes = useCallback((o: string) => updateSessao({ observacoes: o }), [updateSessao]);
    const setDescontoGeral = useCallback((d: number | ((prev: number) => number)) => {
        setSessoes(prev => prev.map(s => {
            if (s.id !== sessaoAtivaId) return s;
            const n = typeof d === 'function' ? d(s.descontoGeral) : d;
            return { ...s, descontoGeral: n };
        }));
    }, [sessaoAtivaId]);
    const setDescontoPercentual = useCallback((dp: boolean | ((prev: boolean) => boolean)) => {
        setSessoes(prev => prev.map(s => {
            if (s.id !== sessaoAtivaId) return s;
            const n = typeof dp === 'function' ? dp(s.descontoPercentual) : dp;
            return { ...s, descontoPercentual: n };
        }));
    }, [sessaoAtivaId]);

    // Gestão de Sessões
    const adicionarSessao = useCallback(() => {
        const nova = createInitialSession();
        setSessoes(prev => [...prev, nova]);
        setSessaoAtivaId(nova.id);
    }, []);

    const alternarSessao = useCallback((id: string) => {
        setSessaoAtivaId(id);
    }, []);

    const removerSessao = useCallback((id: string) => {
        setSessoes(prev => {
            if (prev.length <= 1) {
                const nova = createInitialSession();
                setSessaoAtivaId(nova.id);
                return [nova];
            }
            const novas = prev.filter(s => s.id !== id);
            if (sessaoAtivaId === id && novas.length > 0) {
                setSessaoAtivaId(novas[novas.length - 1].id);
            }
            return novas;
        });
    }, [sessaoAtivaId]);

    // Carregar configurações do PDV
    useEffect(() => {
        const carregarConfiguracoes = async () => {
            try {
                const config = await pdvService.getConfiguracoes();
                setConfiguracoes(config);
                setFormasPagamento(config.formas_pagamento);

                // Verificar Caixa Aberto
                const caixa = await pdvService.getCaixaAtual();
                setCaixaAberto(caixa);
            } catch (error) {
                console.error('Erro ao carregar configurações/caixa do PDV:', error);
            }
        };
        carregarConfiguracoes();
    }, []);

    // Help: Precisão decimal rigorosa para operações financeiras
    const round = useCallback((val: number) => Math.round((val + Number.EPSILON) * 100) / 100, []);

    // Cálculos em tempo real memoizados para performance de elite
    const subtotal = round(carrinho.reduce((sum, item) => sum + (item.precoUnitario * item.quantidade), 0));
    const descontoItens = round(carrinho.reduce((sum, item) => sum + item.desconto, 0));

    const descontoGeralCalculado = round(descontoPercentual
        ? (subtotal - descontoItens) * (descontoGeral / 100)
        : descontoGeral);

    const descontoTotal = round(descontoItens + descontoGeralCalculado);
    const total = Math.max(0, round(subtotal - descontoTotal));

    const troco = (() => {
        const formaPg = formasPagamento.find(f => f.tipo === formaPagamentoSelecionada);
        return (formaPg?.permite_troco && valorRecebido > total)
            ? round(valorRecebido - total)
            : 0;
    })();

    // Adicionar produto ao carrinho
    const adicionarProduto = useCallback((produto: Produto, quantidade: number = 1) => {
        const controlarValidade = configuracoes?.controlar_validade ?? true;

        if (controlarValidade && produto.data_validade) {
            let y, m, d;
            if (produto.data_validade.includes('-')) {
                [y, m, d] = produto.data_validade.split('-').map(Number);
            } else {
                [d, m, y] = produto.data_validade.split('/').map(Number);
            }

            const dataValidade = new Date(y, m - 1, d);
            const hoje = new Date();
            hoje.setHours(0, 0, 0, 0);

            if (dataValidade < hoje) {
                showToast.error(`BLOQUEIO: O produto ${produto.nome} está VENCIDO!`, {
                    duration: 8000,
                    icon: '🚫'
                });
            } else {
                const diasAlerta = configuracoes?.dias_alerta_validade ?? 30;
                const dataLimiteAlerta = new Date(hoje);
                dataLimiteAlerta.setDate(hoje.getDate() + diasAlerta);

                if (dataValidade <= dataLimiteAlerta) {
                    const diffTime = dataValidade.getTime() - hoje.getTime();
                    const diasRestantes = Math.round(diffTime / (1000 * 3600 * 24));

                    if (diasRestantes >= 0) {
                        showToast.warning(`AVISO: ${produto.nome} vence em ${diasRestantes === 0 ? 'hoje' : diasRestantes + ' dias'}`, {
                            duration: 5000,
                            icon: '⚠️'
                        });
                    }
                }
            }
        }

        setCarrinho(prev => {
            const itemExistente = prev.find(item => item.produto.id === produto.id);
            const estoqueDisponivel = produto.estoque_atual ?? 0;

            if (itemExistente) {
                const novaQuantidade = itemExistente.quantidade + quantidade;
                const permiteSemEstoque = configuracoes?.permitir_venda_sem_estoque ?? false;

                if (!permiteSemEstoque && novaQuantidade > estoqueDisponivel) {
                    showToast.warning(`Estoque insuficiente para ${produto.nome}`);
                    const qtdPermitida = Math.max(0, estoqueDisponivel);
                    if (itemExistente.quantidade >= qtdPermitida) return prev;

                    return prev.map(item =>
                        item.produto.id === produto.id
                            ? {
                                ...item,
                                quantidade: qtdPermitida,
                                total: round(qtdPermitida * item.precoUnitario - item.desconto),
                            }
                            : item
                    );
                }

                return prev.map(item =>
                    item.produto.id === produto.id
                        ? {
                            ...item,
                            quantidade: novaQuantidade,
                            total: round(novaQuantidade * item.precoUnitario - item.desconto),
                        }
                        : item
                );
            } else {
                const preco = (produto as any).preco_venda_efetivo ?? produto.preco_venda;
                const permiteSemEstoque = configuracoes?.permitir_venda_sem_estoque ?? false;

                let qtdPedida = quantidade;
                if (!permiteSemEstoque) {
                    qtdPedida = Math.min(quantidade, Math.max(0, estoqueDisponivel));
                }

                if (!permiteSemEstoque && qtdPedida <= 0 && estoqueDisponivel <= 0) {
                    showToast.error(`Produto ${produto.nome} sem estoque disponível`);
                    return prev;
                }

                const novoItem: ItemCarrinho = {
                    produto,
                    quantidade: qtdPedida,
                    precoUnitario: preco,
                    desconto: 0,
                    descontoPercentual: false,
                    total: round(preco * qtdPedida),
                };
                return [...prev, novoItem];
            }
        });
    }, [configuracoes, round, setCarrinho]);

    const removerProduto = useCallback((produtoId: number) => {
        setCarrinho(prev => prev.filter(item => item.produto.id !== produtoId));
    }, [setCarrinho]);

    const atualizarQuantidade = useCallback((produtoId: number, quantidade: number) => {
        if (quantidade <= 0) {
            removerProduto(produtoId);
            return;
        }

        setCarrinho(prev =>
            prev.map(item => {
                if (item.produto.id === produtoId) {
                    const estoqueMax = item.produto.estoque_atual ?? 0;
                    const permiteSemEstoque = configuracoes?.permitir_venda_sem_estoque ?? false;

                    const qtdValida = permiteSemEstoque
                        ? (quantidade > 0 ? quantidade : 1)
                        : Math.min(quantidade, Math.max(1, estoqueMax));

                    return {
                        ...item,
                        quantidade: qtdValida,
                        total: round(qtdValida * item.precoUnitario - item.desconto),
                    };
                }
                return item;
            })
        );
    }, [removerProduto, configuracoes, round, setCarrinho]);

    const aplicarDescontoItem = useCallback((produtoId: number, desconto: number, percentual: boolean = false) => {
        setCarrinho(prev =>
            prev.map(item => {
                if (item.produto.id === produtoId) {
                    const descontoValor = percentual
                        ? item.precoUnitario * item.quantidade * (desconto / 100)
                        : desconto;

                    return {
                        ...item,
                        desconto: descontoValor,
                        descontoPercentual: percentual,
                        total: item.precoUnitario * item.quantidade - descontoValor,
                    };
                }
                return item;
            })
        );
    }, [setCarrinho]);

    const validarDescontoPermitido = useCallback((valorDesconto: number): boolean => {
        if (!configuracoes) return false;
        if (configuracoes.funcionario.role === 'ADMIN') return true;

        const percentualDesconto = (valorDesconto / subtotal) * 100;
        const limiteDesconto = configuracoes.funcionario.limite_desconto || 0;
        return percentualDesconto <= limiteDesconto;
    }, [configuracoes, subtotal]);

    const limparCarrinho = useCallback(() => {
        updateSessao({
            carrinho: [],
            cliente: null,
            emailRecibo: '',
            formaPagamentoSelecionada: 'dinheiro',
            valorRecebido: 0,
            observacoes: '',
            descontoGeral: 0,
            descontoPercentual: false,
        });
    }, [updateSessao]);

    const finalizarVenda = async (extraData?: { data_vencimento_fiado?: string }) => {
        if (carrinho.length === 0) {
            throw new Error('Adicione produtos ao carrinho');
        }

        const permiteVendaSemCliente = configuracoes?.permite_venda_sem_cliente ?? true;
        if (!permiteVendaSemCliente && !cliente) {
            throw new Error('Selecione um cliente para continuar');
        }

        const formaPg = formasPagamento.find(f => f.tipo === formaPagamentoSelecionada);

        if (formaPg?.permite_troco) {
            if (valorRecebido < (total - 0.01)) {
                throw new Error(`Valor recebido insuficiente. Faltam R$ ${(total - valorRecebido).toFixed(2)}`);
            }
        }

        setLoading(true);

        try {
            const vendaData = {
                items: carrinho.map(item => ({
                    id: item.produto.id,
                    quantity: item.quantidade,
                    discount: item.desconto,
                    price: item.precoUnitario
                })),
                subtotal,
                desconto: descontoTotal,
                total,
                paymentMethod: formaPagamentoSelecionada,
                valor_recebido: formaPg?.permite_troco ? valorRecebido : total,
                troco,
                cliente_id: cliente?.id ? Number(cliente.id) : null,
                email_destino: emailRecibo.trim() || undefined,
                observacoes: observacoes.trim() || undefined,
                ...(extraData || {}),
            };

            const venda = await pdvService.finalizarVenda(vendaData);

            // ── Alerta de Sangria ──────────────────────────────────────────
            // Se a venda foi em dinheiro, verifica o saldo no caixa
            const LIMITE_SANGRIA = 500; // R$ — ajuste conforme política da loja
            if (formaPagamentoSelecionada === 'dinheiro') {
                try {
                    const resumo = await pdvService.getResumoCaixa();
                    const saldoDinheiro = resumo?.por_forma?.dinheiro ?? resumo?.saldo_atual ?? 0;
                    if (saldoDinheiro > LIMITE_SANGRIA) {
                        showToast.warning(
                            `💰 Sangria recomendada! Dinheiro no caixa: R$ ${saldoDinheiro.toFixed(2).replace('.', ',')}. Limite: R$ ${LIMITE_SANGRIA},00`,
                            { duration: 8000, icon: '🔔' }
                        );
                    }
                } catch {
                    // Alerta de sangria é não-crítico — não bloqueia o fluxo
                }
            }

            return venda;
        } catch (error: any) {
            console.error("Erro ao finalizar venda:", error);
            throw error;
        } finally {
            setLoading(false);
        }
    };

    return {
        // Multi-Session Utilities
        sessoes,
        sessaoAtivaId,
        adicionarSessao,
        alternarSessao,
        removerSessao,

        // Current Session Data
        carrinho,
        cliente,
        setCliente,
        emailRecibo,
        setEmailRecibo,
        formasPagamento,
        formaPagamentoSelecionada,
        setFormaPagamentoSelecionada,
        valorRecebido,
        setValorRecebido,
        observacoes,
        setObservacoes,
        descontoGeral,
        setDescontoGeral,
        descontoPercentual,
        setDescontoPercentual,
        configuracoes,
        loading,
        subtotal,
        descontoItens,
        descontoGeralCalculado,
        descontoTotal,
        total,
        troco,
        adicionarProduto,
        removerProduto,
        atualizarQuantidade,
        aplicarDescontoItem,
        validarDescontoPermitido,
        limparCarrinho,
        finalizarVenda,
        caixaAberto,
        setCaixaAberto
    };
};