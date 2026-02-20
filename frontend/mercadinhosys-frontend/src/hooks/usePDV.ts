import { useState, useCallback, useEffect } from 'react';
import { Produto, Cliente } from '../types';
import { pdvService, ConfiguracoesPDV } from '../features/pdv/pdvService';
import { showToast } from '../utils/toast';

interface ItemCarrinho {
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

export const usePDV = () => {
    // Estado do PDV
    const [carrinho, setCarrinho] = useState<ItemCarrinho[]>([]);
    const [cliente, setCliente] = useState<Cliente | null>(null);
    const [emailRecibo, setEmailRecibo] = useState<string>('');
    const [formasPagamento, setFormasPagamento] = useState<FormaPagamento[]>([]);
    const [formaPagamentoSelecionada, setFormaPagamentoSelecionada] = useState<string>('dinheiro');
    const [valorRecebido, setValorRecebido] = useState<number>(0);
    const [observacoes, setObservacoes] = useState<string>('');
    const [descontoGeral, setDescontoGeral] = useState<number>(0);
    const [descontoPercentual, setDescontoPercentual] = useState<boolean>(false);

    // Configurações e permissões
    const [configuracoes, setConfiguracoes] = useState<ConfiguracoesPDV | null>(null);
    const [loading, setLoading] = useState(false);

    // Carregar configurações do PDV
    useEffect(() => {
        const carregarConfiguracoes = async () => {
            try {
                const config = await pdvService.getConfiguracoes();
                setConfiguracoes(config);
                setFormasPagamento(config.formas_pagamento);
            } catch (error) {
                console.error('Erro ao carregar configurações do PDV:', error);
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
        // Inteligência de Validade (Elite Accuracy - Timezone Shield)
        const controlarValidade = configuracoes?.controlar_validade ?? true;

        if (controlarValidade && produto.data_validade) {
            // Parse robusto: suporta YYYY-MM-DD e DD/MM/YYYY
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
                // Produto REALMENTE vencido (data anterior a hoje)
                showToast.error(`BLOQUEIO: O produto ${produto.nome} está VENCIDO!`, {
                    duration: 8000,
                    icon: '🚫'
                });
            } else {
                // Verificar se está próximo ao vencimento conforme config
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
    }, [configuracoes, round]);

    const removerProduto = useCallback((produtoId: number) => {
        setCarrinho(prev => prev.filter(item => item.produto.id !== produtoId));
    }, []);

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
    }, [removerProduto, configuracoes, round]);

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
    }, []);

    const validarDescontoPermitido = useCallback((valorDesconto: number): boolean => {
        if (!configuracoes) return false;

        if (configuracoes.funcionario.role === 'ADMIN') {
            return true;
        }

        const percentualDesconto = (valorDesconto / subtotal) * 100;
        const limiteDesconto = configuracoes.funcionario.limite_desconto || 0;

        if (percentualDesconto > limiteDesconto) {
            return false;
        }

        return true;
    }, [configuracoes, subtotal]);

    const limparCarrinho = useCallback(() => {
        setCarrinho([]);
        setCliente(null);
        setEmailRecibo('');
        setValorRecebido(0);
        setDescontoGeral(0);
        setDescontoPercentual(false);
        setObservacoes('');
        setFormaPagamentoSelecionada('dinheiro');
    }, []);

    const finalizarVenda = async () => {
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
                cliente_id: cliente?.id,
                email_destino: emailRecibo.trim() || undefined,
                observacoes: observacoes.trim() || undefined,
            };

            const venda = await pdvService.finalizarVenda(vendaData);
            return venda;
        } catch (error: any) {
            console.error("Erro ao finalizar venda:", error);
            throw error;
        } finally {
            setLoading(false);
        }
    };

    return {
        carrinho,
        cliente,
        setCliente: (c: Cliente | null) => {
            setCliente(c);
            if (c?.email) setEmailRecibo(c.email);
        },
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
    };
};