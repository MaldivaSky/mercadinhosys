import React, { useState, useEffect } from 'react';
import { showToast } from '../../utils/toast';
import {
    ShoppingCart,
    Printer,
    X,
    Check,
    CreditCard,
    DollarSign,
    Smartphone,
    TrendingUp,
    Tag,
    AlertTriangle
} from 'lucide-react';
import ProdutoSearch from './components/ProdutoSearch';
import CarrinhoItem from './components/CarrinhoItem';
import ClienteSelect from './components/ClienteSelect';
import CaixaHeader from './components/CaixaHeader';
import GerenteAuthModal from './components/GerenteAuthModal';
import NotaFiscalModal from './components/NotaFiscalModal';
import { usePDV } from '../../hooks/usePDV';
import { Produto } from '../../types';
import { formatCurrency } from '../../utils/formatters';
import { pdvService } from './pdvService';

const PDVPage: React.FC = () => {
    const TOAST_IDS = {
        descontoAutorizacao: 'pdv-desconto-autorizacao',
        estoqueIndisponivel: 'pdv-estoque-indisponivel',
        estoqueInsuficiente: 'pdv-estoque-insuficiente',
        produtoVencido: 'pdv-produto-vencido',
        validadeProxima: 'pdv-validade-proxima',
        estoqueBaixo: 'pdv-estoque-baixo',
        itemAdicionado: 'pdv-item-adicionado',
        vendaFinalizada: 'pdv-venda-finalizada',
        erroFinalizacao: 'pdv-erro-finalizacao',
        emailInvalido: 'pdv-email-invalido',
        erroEmail: 'pdv-erro-email',
    } as const;
    const {
        carrinho,
        cliente,
        setCliente,
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
    } = usePDV();

    const [formaPagamentoAberta, setFormaPagamentoAberta] = useState(false);
    const [mostrarAutorizacao, setMostrarAutorizacao] = useState(false);
    const [descontoAprovado, setDescontoAprovado] = useState(false);
    const [ultimaVendaId, setUltimaVendaId] = useState<number | null>(null);
    const [enviandoEmail, setEnviandoEmail] = useState(false);
    const [mostrarModalNotaFiscal, setMostrarModalNotaFiscal] = useState(false);
    const [ultimoComprovante, setUltimoComprovante] = useState<any | null>(null);

    // Validar desconto ao alterar
    useEffect(() => {
        if (descontoGeral > 0 && !descontoAprovado) {
            const permitido = validarDescontoPermitido(descontoGeralCalculado);
            if (!permitido) {
                showToast.warning(
                    `Desconto de ${formatCurrency(descontoGeralCalculado)} requer autorização de gerente`,
                    { id: TOAST_IDS.descontoAutorizacao }
                );
            }
        }
    }, [descontoGeral, descontoGeralCalculado, descontoAprovado, validarDescontoPermitido]);

    const handleProdutoSelecionado = (produto: Produto) => {
        // 1. Validação de Estoque (Bloqueante)
        if (!produto.quantidade_estoque || produto.quantidade_estoque <= 0) {
            showToast.error(`PRODUTO INDISPONÍVEL: ${produto.nome} está sem estoque!`, { id: TOAST_IDS.estoqueIndisponivel });
            return;
        }

        // Verificar quantidade já no carrinho
        const itemCarrinho = carrinho.find(item => item.produto.id === produto.id);
        const qtdAtual = itemCarrinho ? itemCarrinho.quantidade : 0;

        if (qtdAtual + 1 > produto.quantidade_estoque) {
            showToast.error(`ESTOQUE INSUFICIENTE: Disponível: ${produto.quantidade_estoque} un.`, { id: TOAST_IDS.estoqueInsuficiente });
            return;
        }

        // 2. Validação de Validade (Alerta Crítico ou Aviso)
        if (produto.data_validade) {
            const hoje = new Date();
            hoje.setHours(0, 0, 0, 0);

            // Tratamento fuso horário simples (considerando data string YYYY-MM-DD)
            const partesData = produto.data_validade.split('-');
            const validade = new Date(
                parseInt(partesData[0]),
                parseInt(partesData[1]) - 1,
                parseInt(partesData[2])
            );

            const diffTime = validade.getTime() - hoje.getTime();
            const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

            if (diffDays < 0) {
                showToast.error(`⛔ PRODUTO VENCIDO! Validade expirou em ${validade.toLocaleDateString('pt-BR')}`, {
                    duration: 6000,
                    id: TOAST_IDS.produtoVencido
                });
                // Opcional: Bloquear venda de produto vencido
                // return; 
            } else if (diffDays <= 30) {
                showToast.warning(`⚠️ ATENÇÃO: Validade próxima! Vence em ${diffDays} dias (${validade.toLocaleDateString('pt-BR')})`, {
                    duration: 5000,
                    id: TOAST_IDS.validadeProxima
                });
            }
        }

        // 3. Alerta de Estoque Baixo (Aviso)
        // Se a quantidade atual no carrinho + 1 atingir ou baixar do mínimo
        const estoqueRestante = produto.quantidade_estoque - (qtdAtual + 1);
        if (produto.quantidade_minima && estoqueRestante <= produto.quantidade_minima && estoqueRestante >= 0) {
            showToast.warning(`📉 ESTOQUE BAIXO: Restarão apenas ${estoqueRestante} unidades após esta venda.`, {
                duration: 4000,
                id: TOAST_IDS.estoqueBaixo
            });
        }

        adicionarProduto(produto);
        // Feedback de sucesso mais curto para não poluir se houver outros alertas
        if (!itemCarrinho) {
            showToast.success(`${produto.nome} adicionado!`, { id: TOAST_IDS.itemAdicionado });
        }
    };

    const handleAplicarDesconto = () => {
        if (descontoGeral > 0) {
            const permitido = validarDescontoPermitido(descontoGeralCalculado);

            if (!permitido && !descontoAprovado) {
                setMostrarAutorizacao(true);
            }
        }
    };

    const handleAutorizacaoAprovada = () => {
        setDescontoAprovado(true);
        setMostrarAutorizacao(false);
        showToast.success('Desconto autorizado pelo gerente');
    };

    const handleFinalizarVenda = async () => {
        try {
            // Validar desconto antes de finalizar
            if (descontoGeral > 0) {
                const permitido = validarDescontoPermitido(descontoGeralCalculado);
                if (!permitido && !descontoAprovado) {
                    setMostrarAutorizacao(true);
                    return;
                }
            }

            const venda = await finalizarVenda();
            setUltimaVendaId(venda.id);
            try {
                const comprovante = await pdvService.obterComprovante(venda.id);
                setUltimoComprovante(comprovante);
            } catch (err) {
                console.error('Erro ao buscar comprovante da venda:', err);
                setUltimoComprovante(null);
            }

            showToast.success(
                `✅ VENDA ${venda.codigo} FINALIZADA! Total: ${formatCurrency(venda.total)}`,
                { duration: 5000, id: TOAST_IDS.vendaFinalizada }
            );

            setDescontoAprovado(false);

            // Sempre mostrar modal de nota fiscal após finalizar
            setMostrarModalNotaFiscal(true);

        } catch (error: unknown) {
            console.error('❌ ERRO AO FINALIZAR:', error);
            let errorMessage = 'Erro ao finalizar venda';
            interface ErrorWithResponse {
                response?: {
                    data?: {
                        error?: string;
                    };
                };
                message?: string;
            }
            const err = error as ErrorWithResponse;
            if (typeof error === 'object' && error !== null) {
                if ('response' in err && typeof err.response?.data?.error === 'string') {
                    errorMessage = err.response!.data!.error!;
                } else if ('message' in err && typeof err.message === 'string') {
                    errorMessage = err.message;
                }
            }
            showToast.error(errorMessage, { id: TOAST_IDS.erroFinalizacao });
        }
    };

    const abrirNotaEmNovaTela = (imprimirAutomaticamente = false) => {
        if (!ultimoComprovante) {
            showToast.error('Comprovante ainda não carregado');
            return;
        }

        const { venda, comprovante, estabelecimento } = ultimoComprovante;
        const itensHtml = (comprovante.itens || [])
            .map((item: any) => `
                <tr>
                    <td class="item-desc">${item.nome}</td>
                </tr>
                <tr>
                    <td class="item-details">
                        ${item.quantidade} x R$ ${Number(item.preco_unitario || 0).toFixed(2)} 
                        <span style="float:right;">R$ ${Number(item.total || 0).toFixed(2)}</span>
                    </td>
                </tr>
            `)
            .join('');

        const html = `
            <!doctype html>
            <html>
                <head>
                    <meta charset="utf-8" />
                    <title>Comprovante - ${venda.codigo}</title>
                    <style>
                        body {
                            margin: 0;
                            padding: 0;
                            font-family: 'Consolas', 'Courier New', monospace;
                            font-size: 12px;
                            color: #000;
                            line-height: 1.2;
                        }
                        .page {
                            width: 302px; /* ~80mm */
                            margin: 0 auto;
                            padding: 10px 0;
                        }
                        .text-center { text-align: center; }
                        .text-right { text-align: right; }
                        .fw-bold { font-weight: bold; }
                        .divider { border-top: 1px dashed #000; margin: 8px 0; }
                        .header { margin-bottom: 10px; }
                        .logo { max-width: 120px; max-height: 80px; margin-bottom: 5px; }
                        table { width: 100%; border-collapse: collapse; }
                        .item-desc { font-weight: bold; padding-top: 4px; }
                        .item-details { padding-bottom: 4px; font-size: 11px; }
                        .totals { margin-top: 10px; }
                        .footer { margin-top: 20px; font-size: 10px; text-align: center; }
                        
                        @media print {
                            @page { margin: 0; }
                            body { margin: 0; }
                        }
                    </style>
                </head>
                <body onload="${imprimirAutomaticamente ? 'window.print()' : ''}">
                    <div class="page">
                        <div class="text-center header">
                            ${comprovante.logo_url ?
                `<img src="${comprovante.logo_url}" class="logo" />` :
                // SVG Fallback Simples (Carrinho)
                `<svg class="logo" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" xmlns="http://www.w3.org/2000/svg"><circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/></svg>`
            }
                            <div class="fw-bold" style="font-size: 14px;">${estabelecimento?.nome_fantasia || 'MercadinhoSys'}</div>
                            <div>${estabelecimento?.razao_social || ''}</div>
                            <div>CNPJ: ${estabelecimento?.cnpj || 'Não informado'}</div>
                            <div>${estabelecimento?.endereco || ''}</div>
                            <div>Tel: ${estabelecimento?.telefone || ''}</div>
                        </div>

                        <div class="divider"></div>

                        <div>
                            <div><strong>Venda:</strong> ${venda.codigo}</div>
                            <div><strong>Data:</strong> ${venda.data}</div>
                            <div><strong>Cliente:</strong> ${comprovante.cliente}</div>
                            <div><strong>Operador:</strong> ${comprovante.funcionario}</div>
                        </div>

                        <div class="divider"></div>

                        <table>
                            ${itensHtml}
                        </table>

                        <div class="divider"></div>

                        <div class="totals">
                            <div style="display:flex; justify-content:space-between;">
                                <span>Qtd Itens:</span>
                                <span>${(comprovante.itens || []).length}</span>
                            </div>
                            <div style="display:flex; justify-content:space-between;">
                                <span>Subtotal:</span>
                                <span>R$ ${Number(comprovante.subtotal || 0).toFixed(2)}</span>
                            </div>
                            ${comprovante.desconto > 0 ? `
                                <div style="display:flex; justify-content:space-between;">
                                    <span>Desconto:</span>
                                    <span>- R$ ${Number(comprovante.desconto || 0).toFixed(2)}</span>
                                </div>
                            ` : ''}
                            <div style="display:flex; justify-content:space-between; font-weight:bold; font-size: 16px; margin-top: 5px;">
                                <span>TOTAL:</span>
                                <span>R$ ${Number(comprovante.total || 0).toFixed(2)}</span>
                            </div>
                        </div>

                        <div class="divider"></div>

                        <div>
                            <div style="display:flex; justify-content:space-between;">
                                <span>Forma Pagto:</span>
                                <span>${comprovante.forma_pagamento}</span>
                            </div>
                            <div style="display:flex; justify-content:space-between;">
                                <span>Valor Recebido:</span>
                                <span>R$ ${Number(comprovante.valor_recebido || 0).toFixed(2)}</span>
                            </div>
                            <div style="display:flex; justify-content:space-between;">
                                <span>Troco:</span>
                                <span>R$ ${Number(comprovante.troco || 0).toFixed(2)}</span>
                            </div>
                        </div>

                        <div class="divider"></div>

                        <div class="footer">
                            ${comprovante.rodape || 'Obrigado pela preferência!'}<br/>
                            *** Documento Não Fiscal ***<br/>
                            Sistema: MercadinhoSys
                        </div>
                    </div>
                </body>
            </html>
        `;

        const novaJanela = window.open('', '_blank');
        if (!novaJanela) {
            showToast.error('Nao foi possivel abrir a visualizacao da nota');
            return;
        }
        novaJanela.document.write(html);
        novaJanela.document.close();

        if (imprimirAutomaticamente) {
            novaJanela.focus();
            setTimeout(() => novaJanela.print(), 300);
        }
    };

    const handleEnviarEmail = async (email: string) => {
        if (!ultimaVendaId || !email) {
            showToast.error('Email inválido', { id: TOAST_IDS.emailInvalido });
            return;
        }

        try {
            setEnviandoEmail(true);
            await pdvService.enviarCupomFiscal(ultimaVendaId, email);

            showToast.success(`Nota fiscal enviada para ${email}!`);

            // Fechar modal e limpar após sucesso
            setMostrarModalNotaFiscal(false);
            setTimeout(() => {
                limparCarrinho();
                setUltimaVendaId(null);
            }, 1500);

        } catch (error: unknown) {
            console.error('❌ ERRO AO ENVIAR EMAIL:', error);
            const err = error as { response?: { data?: { error?: string; details?: string; message?: string } } };
            const detalhe = err.response?.data?.details || err.response?.data?.error || err.response?.data?.message;
            showToast.error(`❌ Falha ao enviar email${detalhe ? `: ${detalhe}` : '. Tente novamente.'}`, {
                duration: 5000,
                id: TOAST_IDS.erroEmail
            });
        } finally {
            setEnviandoEmail(false);
        }
    };

    const handleImprimirNota = () => {
        setMostrarModalNotaFiscal(false);
        showToast.info('Preparando impressao...');
        setTimeout(() => {
            abrirNotaEmNovaTela(true);
            limparCarrinho();
            setUltimaVendaId(null);
            setUltimoComprovante(null);
        }, 1000);
    };

    const handleVisualizarNota = () => {
        abrirNotaEmNovaTela(false);
    };

    const handleFecharModalNota = () => {
        setMostrarModalNotaFiscal(false);
        setTimeout(() => {
            limparCarrinho();
            setUltimaVendaId(null);
            setUltimoComprovante(null);
        }, 500);
    };

    // const handleNovaVenda = () => {
    //     limparCarrinho();
    //     setUltimaVendaId(null);
    //     setDescontoAprovado(false);
    //     toast.success('Nova venda iniciada', {
    //         icon: '🛒',
    //     });
    // };

    const handleLimparCarrinho = () => {
        if (carrinho.length > 0) {
            if (confirm('Tem certeza que deseja cancelar esta venda?')) {
                limparCarrinho();
                setDescontoAprovado(false);
                showToast.info('Venda cancelada');
            }
        }
    };

    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            switch (e.key) {
                case 'F1':
                    e.preventDefault();
                    document.getElementById('produto-search-input')?.focus();
                    break;
                case 'F10':
                    e.preventDefault();
                    {
                        if (carrinho.length > 0) {
                            handleFinalizarVenda();
                        }
                    }
                    break;
                case 'F9':
                    e.preventDefault();
                    {
                        if (carrinho.length > 0) {
                            handleFinalizarVenda();
                        }
                    }
                    break;
                case 'Escape':
                    {
                        if (carrinho.length > 0) {
                            handleLimparCarrinho();
                        }
                    }
                    break;
                case 'F2':
                    e.preventDefault();
                    {
                        const btn = document.getElementById('cliente-select-open') as HTMLButtonElement | null;
                        btn?.click();
                        setTimeout(() => {
                            document.getElementById('cliente-search-input')?.focus();
                        }, 50);
                    }
                    break;
                case 'F4':
                    e.preventDefault();
                    {
                        setFormaPagamentoAberta((prev) => !prev);
                    }
                    break;
                default:
                    break;
            }
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [carrinho, handleFinalizarVenda, handleLimparCarrinho]);
    const renderIconPagamento = (tipo: string) => {
        switch (tipo) {
            case 'dinheiro':
                return <DollarSign className="w-5 h-5" />;
            case 'cartao_credito':
            case 'cartao_debito':
                return <CreditCard className="w-5 h-5" />;
            case 'pix':
                return <Smartphone className="w-5 h-5" />;
            default:
                return <TrendingUp className="w-5 h-5" />;
        }
    };

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
            <div className="max-w-7xl mx-auto">
                {/* Header com informações do caixa (refreshKey atualiza stats após venda) */}
                <CaixaHeader
                    funcionarioNome={configuracoes?.funcionario.nome}
                    funcionarioRole={configuracoes?.funcionario.role}
                    refreshKey={ultimaVendaId ?? undefined}
                />

                {/* Layout Principal */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Coluna 1: Busca e Carrinho */}
                    <div className="lg:col-span-2 space-y-6">
                        {/* Busca de Produtos */}
                        <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6">
                            <h2 className="text-lg font-semibold text-gray-800 dark:text-white mb-4">
                                Buscar Produtos
                            </h2>
                            <ProdutoSearch onProdutoSelecionado={handleProdutoSelecionado} />
                        </div>

                        {/* Carrinho */}
                        <div className="bg-white dark:bg-gray-800 rounded-xl shadow">
                            <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                                <div className="flex items-center justify-between">
                                    <h2 className="text-lg font-semibold text-gray-800 dark:text-white">
                                        Carrinho de Vendas
                                    </h2>
                                    <span className="px-3 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-300 rounded-full">
                                        {carrinho.length} {carrinho.length === 1 ? 'item' : 'itens'}
                                    </span>
                                </div>
                            </div>

                            <div className="p-6">
                                {carrinho.length === 0 ? (
                                    <div className="text-center py-12">
                                        <ShoppingCart className="w-16 h-16 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
                                        <p className="text-gray-500 dark:text-gray-400">
                                            Nenhum produto no carrinho
                                        </p>
                                        <p className="text-sm text-gray-400 dark:text-gray-500 mt-2">
                                            Busque e adicione produtos para começar uma venda
                                        </p>
                                    </div>
                                ) : (
                                    <div className="space-y-4">
                                        {carrinho.map((item) => (
                                            <CarrinhoItem
                                                key={item.produto.id}
                                                produto={item.produto}
                                                quantidade={item.quantidade}
                                                precoUnitario={item.precoUnitario}
                                                desconto={item.desconto}
                                                total={item.total}
                                                onAtualizarQuantidade={(qtd) => {
                                                    const estoque = item.produto.quantidade_estoque || 0;
                                                    if (qtd > estoque) {
                                                        showToast.error(`Estoque insuficiente! Máximo: ${estoque}`);
                                                        return;
                                                    }
                                                    atualizarQuantidade(item.produto.id, qtd);
                                                }}
                                                onRemover={() => removerProduto(item.produto.id)}
                                                onAplicarDesconto={(desc, perc) =>
                                                    aplicarDescontoItem(item.produto.id, desc, perc)
                                                }
                                            />
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Coluna 2: Resumo e Pagamento */}
                    <div className="space-y-6">
                        {/* Cliente */}
                        <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6">
                            <h2 className="text-lg font-semibold text-gray-800 dark:text-white mb-4">
                                Cliente
                            </h2>
                            <ClienteSelect
                                cliente={cliente}
                                onClienteSelecionado={setCliente}
                            />
                        </div>

                        {/* Resumo da Venda */}
                        <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6">
                            <h2 className="text-lg font-semibold text-gray-800 dark:text-white mb-4">
                                Resumo da Venda
                            </h2>

                            <div className="space-y-3">
                                <div className="flex justify-between text-gray-600 dark:text-gray-400">
                                    <span>Subtotal</span>
                                    <span className="font-medium text-gray-800 dark:text-white">
                                        {formatCurrency(subtotal)}
                                    </span>
                                </div>

                                {descontoItens > 0 && (
                                    <div className="flex justify-between text-sm">
                                        <span className="text-yellow-600 dark:text-yellow-400">Desconto em itens</span>
                                        <span className="text-yellow-600 dark:text-yellow-400">
                                            -{formatCurrency(descontoItens)}
                                        </span>
                                    </div>
                                )}

                                <div className="border-t border-gray-200 dark:border-gray-700 pt-3">
                                    <div className="flex items-center justify-between mb-2">
                                        <span className="text-gray-600 dark:text-gray-400">Desconto Geral</span>
                                        <div className="flex items-center space-x-2">
                                            <button
                                                onClick={() => setDescontoPercentual(!descontoPercentual)}
                                                className={`px-3 py-1 text-xs rounded transition ${descontoPercentual
                                                    ? 'bg-blue-500 text-white'
                                                    : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                                                    }`}
                                            >
                                                {descontoPercentual ? '%' : 'R$'}
                                            </button>
                                            <input
                                                type="number"
                                                value={descontoGeral}
                                                onChange={(e) => setDescontoGeral(parseFloat(e.target.value) || 0)}
                                                onBlur={handleAplicarDesconto}
                                                className="w-24 px-2 py-1 border border-gray-300 dark:border-gray-600 rounded text-right bg-white dark:bg-gray-700 text-gray-800 dark:text-white"
                                                step="0.01"
                                                min="0"
                                                max={descontoPercentual ? "100" : subtotal.toString()}
                                            />
                                        </div>
                                    </div>
                                    {descontoGeralCalculado > 0 && (
                                        <div className="text-right">
                                            <span className="text-sm text-red-500">
                                                -{formatCurrency(descontoGeralCalculado)}
                                            </span>
                                            {descontoAprovado && (
                                                <span className="ml-2 text-xs px-2 py-0.5 bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 rounded">
                                                    ✓ Aprovado
                                                </span>
                                            )}
                                        </div>
                                    )}
                                </div>

                                {descontoTotal > 0 && (
                                    <div className="flex justify-between text-sm font-medium text-red-600 dark:text-red-400">
                                        <span>Total em Descontos</span>
                                        <span>-{formatCurrency(descontoTotal)}</span>
                                    </div>
                                )}

                                <div className="border-t border-gray-200 dark:border-gray-700 pt-3">
                                    <div className="flex justify-between items-center">
                                        <span className="text-lg font-semibold text-gray-800 dark:text-white">
                                            Total a Pagar
                                        </span>
                                        <span className="text-3xl font-bold text-blue-600 dark:text-blue-400">
                                            {formatCurrency(total)}
                                        </span>
                                    </div>
                                </div>

                                {/* Indicador de permissões */}
                                {configuracoes && (
                                    <div className={`mt-4 p-3 rounded-lg ${configuracoes.funcionario.role === 'ADMIN'
                                        ? 'bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800'
                                        : 'bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800'
                                        }`}>
                                        <div className="flex items-center justify-between text-xs">
                                            <div className="flex items-center space-x-2">
                                                <Tag className="w-4 h-4" />
                                                <span className={
                                                    configuracoes.funcionario.role === 'ADMIN'
                                                        ? 'text-green-700 dark:text-green-300 font-semibold'
                                                        : 'text-blue-700 dark:text-blue-300'
                                                }>
                                                    {configuracoes.funcionario.role === 'ADMIN'
                                                        ? '👑 Admin - Desconto Ilimitado'
                                                        : `Limite de desconto: ${configuracoes.funcionario.limite_desconto}%`
                                                    }
                                                </span>
                                            </div>
                                            {configuracoes.funcionario.role === 'ADMIN' && (
                                                <span className="px-2 py-0.5 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded-full text-xs font-bold">
                                                    ✓ Sem Limite
                                                </span>
                                            )}
                                        </div>
                                        {configuracoes.funcionario.role !== 'ADMIN' && descontoGeralCalculado > 0 && (
                                            <div className="mt-2">
                                                <div className="flex justify-between text-xs mb-1">
                                                    <span className="text-gray-600 dark:text-gray-400">
                                                        Desconto usado: {((descontoGeralCalculado / subtotal) * 100).toFixed(1)}%
                                                    </span>
                                                    <span className={`font-semibold ${((descontoGeralCalculado / subtotal) * 100) > configuracoes.funcionario.limite_desconto
                                                        ? 'text-red-600 dark:text-red-400'
                                                        : 'text-green-600 dark:text-green-400'
                                                        }`}>
                                                        {((descontoGeralCalculado / subtotal) * 100) > configuracoes.funcionario.limite_desconto
                                                            ? '⚠️ Requer autorização'
                                                            : '✓ Dentro do limite'
                                                        }
                                                    </span>
                                                </div>
                                                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                                                    <div
                                                        className={`h-2 rounded-full transition-all ${((descontoGeralCalculado / subtotal) * 100) > configuracoes.funcionario.limite_desconto
                                                            ? 'bg-red-500'
                                                            : 'bg-green-500'
                                                            }`}
                                                        style={{
                                                            width: `${Math.min(100, ((descontoGeralCalculado / subtotal) * 100 / configuracoes.funcionario.limite_desconto) * 100)}%`
                                                        }}
                                                    ></div>
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Forma de Pagamento */}
                        <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6">
                            <div className="flex items-center justify-between mb-4">
                                <h2 className="text-lg font-semibold text-gray-800 dark:text-white">
                                    Forma de Pagamento
                                </h2>
                                <button
                                    onClick={() => setFormaPagamentoAberta(!formaPagamentoAberta)}
                                    className="text-sm text-blue-500 hover:text-blue-600 font-medium"
                                >
                                    {formaPagamentoAberta ? 'Fechar' : 'Alterar'} <span className="ml-1 text-[10px] px-1.5 py-0.5 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded">F4</span>
                                </button>
                            </div>

                            {formaPagamentoAberta ? (
                                <div className="space-y-2">
                                    {formasPagamento.map((forma) => (
                                        <button
                                            key={forma.tipo}
                                            onClick={() => {
                                                setFormaPagamentoSelecionada(forma.tipo);
                                                setFormaPagamentoAberta(false);
                                                if (!forma.permite_troco) {
                                                    setValorRecebido(0);
                                                }
                                            }}
                                            className={`w-full p-4 rounded-lg flex items-center justify-between transition ${formaPagamentoSelecionada === forma.tipo
                                                ? 'bg-blue-50 dark:bg-blue-900/20 border-2 border-blue-500'
                                                : 'border-2 border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700'
                                                }`}
                                        >
                                            <div className="flex items-center space-x-3">
                                                {renderIconPagamento(forma.tipo)}
                                                <span className="font-medium text-gray-800 dark:text-white">
                                                    {forma.label}
                                                </span>
                                            </div>
                                            {forma.taxa > 0 && (
                                                <span className="text-sm text-gray-500 dark:text-gray-400">
                                                    Taxa: {forma.taxa}%
                                                </span>
                                            )}
                                        </button>
                                    ))}
                                </div>
                            ) : (
                                <div className="p-4 bg-gradient-to-r from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 rounded-lg border border-blue-200 dark:border-blue-800">
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center space-x-3">
                                            <div className="p-2 bg-blue-500 rounded-lg">
                                                {renderIconPagamento(formaPagamentoSelecionada)}
                                                <span className="sr-only">Ícone</span>
                                            </div>
                                            <div>
                                                <span className="font-semibold text-gray-800 dark:text-white block">
                                                    {formasPagamento.find(f => f.tipo === formaPagamentoSelecionada)?.label || formaPagamentoSelecionada}
                                                </span>
                                                {formasPagamento.find(f => f.tipo === formaPagamentoSelecionada)?.permite_troco && (
                                                    <span className="text-xs text-blue-600 dark:text-blue-400">
                                                        Aceita troco
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                        {(() => {
                                            const forma = formasPagamento.find(f => f.tipo === formaPagamentoSelecionada);
                                            return forma && forma.taxa > 0 ? (
                                                <span className="text-sm px-3 py-1 bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400 rounded-full">
                                                    Taxa: {forma.taxa}%
                                                </span>
                                            ) : null;
                                        })()}
                                    </div>
                                </div>
                            )}

                            {/* Campo de Valor Recebido para Dinheiro */}
                            {formasPagamento.find(f => f.tipo === formaPagamentoSelecionada)?.permite_troco && (
                                <div className="mt-4 p-4 bg-gradient-to-r from-yellow-50 to-yellow-100 dark:from-yellow-900/20 dark:to-yellow-800/20 rounded-lg border border-yellow-200 dark:border-yellow-800">
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                        💵 Valor Recebido
                                    </label>
                                    <input
                                        type="number"
                                        value={valorRecebido}
                                        onChange={(e) => setValorRecebido(parseFloat(e.target.value) || 0)}
                                        className="w-full px-4 py-3 border-2 border-yellow-300 dark:border-yellow-700 rounded-lg focus:ring-2 focus:ring-yellow-500 focus:border-transparent font-bold text-lg bg-white dark:bg-gray-700 text-gray-800 dark:text-white"
                                        step="0.01"
                                        min="0"
                                        placeholder="0.00"
                                    />
                                    {troco > 0 && (
                                        <div className="mt-3 p-3 bg-green-100 dark:bg-green-900/30 rounded-lg border border-green-300 dark:border-green-700">
                                            <div className="flex items-center justify-between">
                                                <span className="text-sm font-medium text-green-700 dark:text-green-300">
                                                    Troco a devolver:
                                                </span>
                                                <span className="text-xl font-bold text-green-600 dark:text-green-400">
                                                    {formatCurrency(troco)}
                                                </span>
                                            </div>
                                        </div>
                                    )}
                                    {valorRecebido > 0 && valorRecebido < total && (
                                        <div className="mt-2 text-sm text-red-600 dark:text-red-400 flex items-center space-x-1">
                                            <AlertTriangle className="w-4 h-4" />
                                            <span>
                                                Faltam {formatCurrency(total - valorRecebido)}
                                            </span>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>

                        {/* Observações */}
                        <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6">
                            <h2 className="text-lg font-semibold text-gray-800 dark:text-white mb-4">
                                Observações
                            </h2>
                            <textarea
                                value={observacoes}
                                onChange={(e) => setObservacoes(e.target.value)}
                                placeholder="Observações sobre a venda..."
                                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent min-h-[100px]"
                                rows={3}
                            />
                        </div>

                        {/* Botões de Ação */}
                        <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6">
                            <div className="space-y-4">
                                <button
                                    onClick={handleFinalizarVenda}
                                    disabled={carrinho.length === 0 || loading || enviandoEmail}
                                    className={`w-full py-4 rounded-lg font-bold text-lg flex items-center justify-center space-x-3 transition shadow-lg ${carrinho.length === 0 || loading || enviandoEmail
                                        ? 'bg-gray-300 dark:bg-gray-700 text-gray-500 dark:text-gray-400 cursor-not-allowed'
                                        : 'bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white'
                                        }`}
                                >
                                    {loading || enviandoEmail ? (
                                        <>
                                            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-white"></div>
                                            <span>{enviandoEmail ? 'Enviando email...' : 'Processando...'}</span>
                                        </>
                                    ) : (
                                        <>
                                            <Check className="w-6 h-6" />
                                            <span>FINALIZAR VENDA</span>
                                            <span className="ml-2 text-xs px-2 py-0.5 bg-white/20 rounded">F10/F9</span>
                                        </>
                                    )}
                                </button>

                                <div className="grid grid-cols-2 gap-3">
                                    <button
                                        onClick={handleLimparCarrinho}
                                        disabled={carrinho.length === 0 || loading || enviandoEmail}
                                        className={`py-3 rounded-lg font-medium flex items-center justify-center space-x-2 transition ${carrinho.length === 0 || loading || enviandoEmail
                                            ? 'bg-gray-200 dark:bg-gray-700 text-gray-400 dark:text-gray-500 cursor-not-allowed'
                                            : 'bg-red-50 dark:bg-red-900/30 hover:bg-red-100 dark:hover:bg-red-900/50 text-red-600 dark:text-red-400'
                                            }`}
                                    >
                                        <X className="w-5 h-5" />
                                        <span>Cancelar</span>
                                        <span className="ml-2 text-xs px-2 py-0.5 bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-300 rounded">ESC</span>
                                    </button>

                                    <button
                                        disabled={carrinho.length === 0}
                                        className={`py-3 rounded-lg font-medium flex items-center justify-center space-x-2 transition ${carrinho.length === 0
                                            ? 'bg-gray-200 dark:bg-gray-700 text-gray-400 dark:text-gray-500 cursor-not-allowed'
                                            : 'bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300'
                                            }`}
                                    >
                                        <Printer className="w-5 h-5" />
                                        <span>Imprimir</span>
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Modal de Autorização de Gerente */}
                {mostrarAutorizacao && (
                    <GerenteAuthModal
                        acao="desconto"
                        valorDesconto={descontoGeralCalculado}
                        onAutorizado={handleAutorizacaoAprovada}
                        onCancelar={() => {
                            setMostrarAutorizacao(false);
                            setDescontoGeral(0);
                        }}
                    />
                )}

                {/* Modal Profissional de Nota Fiscal */}
                <NotaFiscalModal
                    mostrar={mostrarModalNotaFiscal}
                    emailCliente={cliente?.email}
                    onEnviarEmail={handleEnviarEmail}
                    onVisualizar={handleVisualizarNota}
                    onImprimir={handleImprimirNota}
                    onFechar={handleFecharModalNota}
                    enviando={enviandoEmail}
                />
            </div>
        </div>
    );
};

export default PDVPage;
