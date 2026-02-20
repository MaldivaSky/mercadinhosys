import React, { useState, useEffect, useRef } from 'react';
import { showToast } from '../../utils/toast';
import {
    ShoppingCart,
    Check,
    CreditCard,
    DollarSign,
    Smartphone,
    TrendingUp,
    Tag,
    Search,
    Trash2,
    User
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
import ErrorBoundary from '../../components/ErrorBoundary';
import PDVSkeleton from './components/PDVSkeleton';

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

    // Ref para debounce do warning de desconto
    const descontoToastTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

    // Validar desconto ao alterar — debounce de 700ms para não disparar a cada keystroke
    useEffect(() => {
        if (descontoGeral > 0 && !descontoAprovado) {
            const permitido = validarDescontoPermitido(descontoGeralCalculado);
            if (!permitido) {
                if (descontoToastTimer.current) clearTimeout(descontoToastTimer.current);
                descontoToastTimer.current = setTimeout(() => {
                    showToast.warning(
                        `Desconto de ${formatCurrency(descontoGeralCalculado)} requer autorização de gerente`,
                        { id: TOAST_IDS.descontoAutorizacao }
                    );
                }, 700);
            }
        }
        return () => {
            if (descontoToastTimer.current) clearTimeout(descontoToastTimer.current);
        };
    }, [descontoGeral, descontoGeralCalculado, descontoAprovado, validarDescontoPermitido]);

    const handleProdutoSelecionado = (produto: Produto) => {
        // Campo de estoque pode vir como quantidade_estoque (validarProduto) ou quantidade (buscarProduto)
        const estoqueDisponivel = produto.quantidade_estoque ?? produto.quantidade ?? 0;

        // 1. Sem estoque — bloqueio total
        if (estoqueDisponivel <= 0) {
            showToast.error(`Sem estoque: ${produto.nome}`, {
                id: TOAST_IDS.estoqueIndisponivel,
                duration: 4000,
            });
            return;
        }

        // 2. Verificar quantidade já no carrinho
        const itemCarrinho = carrinho.find(item => item.produto.id === produto.id);
        const qtdAtual = itemCarrinho ? itemCarrinho.quantidade : 0;

        if (qtdAtual + 1 > estoqueDisponivel) {
            showToast.error(
                `Estoque insuficiente — ${produto.nome}. Disponível: ${estoqueDisponivel} un.`,
                { id: TOAST_IDS.estoqueInsuficiente, duration: 4000 }
            );
            return;
        }

        // 3. Validade
        if (produto.data_validade) {
            const hoje = new Date();
            hoje.setHours(0, 0, 0, 0);
            const partes = produto.data_validade.split('-');
            const validade = new Date(
                parseInt(partes[0]),
                parseInt(partes[1]) - 1,
                parseInt(partes[2])
            );
            const diffDays = Math.ceil((validade.getTime() - hoje.getTime()) / 86400000);

            if (diffDays < 0) {
                showToast.error(
                    `Produto VENCIDO — ${produto.nome}. Venceu em ${validade.toLocaleDateString('pt-BR')}`,
                    { duration: 6000, id: TOAST_IDS.produtoVencido }
                );
                return; // Bloquear venda de produto vencido
            } else if (diffDays <= 7) {
                showToast.warning(
                    `Validade crítica — ${produto.nome} vence em ${diffDays} dia(s)`,
                    { duration: 5000, id: TOAST_IDS.validadeProxima }
                );
            } else if (diffDays <= 30) {
                showToast.warning(
                    `Validade próxima — ${produto.nome} vence em ${diffDays} dias`,
                    { duration: 4000, id: TOAST_IDS.validadeProxima }
                );
            }
        }

        // 4. Estoque baixo — se mostrado, suprime o success para não empilhar dois toasts
        let warningExibido = false;
        const estoqueRestante = estoqueDisponivel - (qtdAtual + 1);
        if (produto.quantidade_minima && estoqueRestante <= produto.quantidade_minima && estoqueRestante >= 0) {
            showToast.warning(
                `Estoque baixo — ${produto.nome}: restará ${estoqueRestante} un.`,
                { duration: 4000, id: TOAST_IDS.estoqueBaixo }
            );
            warningExibido = true;
        }

        adicionarProduto(produto);
        // Feedback só no primeiro item E quando nenhum warning foi exibido (evita dois toasts simultâneos)
        if (!itemCarrinho && !warningExibido) {
            showToast.success(`${produto.nome} adicionado ao carrinho`, {
                id: `${TOAST_IDS.itemAdicionado}-${produto.id}`,
                duration: 2500,
            });
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
                `Venda ${venda.codigo} finalizada — ${formatCurrency(venda.total)}`,
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
                <tr class="item-row">
                    <td>
                        <div class="item-name">${item.nome}</div>
                        <div class="item-meta">
                            ${item.quantidade} x R$ ${Number(item.preco_unitario || 0).toFixed(2)}
                            <span style="float: right">R$ ${Number(item.total || 0).toFixed(2)}</span>
                        </div>
                    </td>
                </tr>
            `)
            .join('');

        const html = `
            <!doctype html>
            <html lang="pt-BR">
                <head>
                    <meta charset="utf-8" />
                    <title>Cupom - BR-${venda.codigo}</title>
                    <style>
                        /* ELITE THERMAL ENGINE V2 - 80MM OPTIMIZED */
                        @page {
                            margin: 0;
                            size: 80mm auto;
                        }
                        
                        * {
                            box-sizing: border-box;
                            -webkit-print-color-adjust: exact;
                        }

                        body {
                            margin: 0;
                            padding: 15px 10px;
                            width: 80mm;
                            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                            font-size: 11px;
                            line-height: 1.4;
                            color: #000;
                            background-color: #fff;
                        }

                        .ticket {
                            width: 100%;
                            max-width: 72mm;
                            margin: 0 auto;
                        }

                        .text-center { text-align: center; }
                        .text-right { text-align: right; }
                        .bold { font-weight: bold; }
                        .italic { font-style: italic; }
                        .text-xl { font-size: 16px; letter-spacing: 1px; }
                        .text-lg { font-size: 14px; }
                        .text-xs { font-size: 9px; }
                        
                        .divider { 
                            border-top: 1px dashed #000; 
                            margin: 10px 0; 
                            width: 100%;
                        }

                        .double-divider {
                            border-top: 2px solid #000;
                            margin: 10px 0;
                            width: 100%;
                        }

                        .header { margin-bottom: 15px; }
                        .brand-box {
                            border: 2px solid #000;
                            padding: 8px;
                            margin-bottom: 10px;
                            font-size: 16px;
                            font-weight: 900;
                            text-transform: uppercase;
                        }

                        table { 
                            width: 100%; 
                            border-collapse: collapse; 
                        }

                        .item-row td { padding: 6px 0; border-bottom: 1px dotted #ccc; }
                        .item-name { font-weight: bold; text-transform: uppercase; font-size: 11px; }
                        .item-meta { font-size: 10px; color: #111; margin-top: 2px; }

                        .total-section {
                            margin-top: 15px;
                            font-size: 12px;
                        }

                        .total-row {
                            display: flex;
                            justify-content: space-between;
                            padding: 3px 0;
                        }

                        .total-highlight {
                            font-size: 18px;
                            font-weight: 900;
                            border-top: 2px solid #000;
                            border-bottom: 2px solid #000;
                            padding: 8px 0;
                            margin: 8px 0;
                        }
                        
                        .footer { 
                            margin-top: 30px; 
                            font-size: 9px; 
                            text-align: center; 
                            padding-top: 10px;
                        }

                        .barcode-stub {
                            margin: 15px 0;
                            font-family: 'Libre Barcode 39', 'Courier', monospace;
                            font-size: 30px;
                        }

                        @media print {
                            .no-print { display: none; }
                        }
                    </style>
                </head>
                <body onload="${imprimirAutomaticamente ? 'window.print(); setTimeout(() => window.close(), 1000);' : ''}">
                    <div class="ticket">
                        <!-- BRANDING SEGMENT -->
                        <div class="text-center header">
                            ${comprovante.logo_url ?
                `<img src="${comprovante.logo_url}" style="max-width: 180px; margin-bottom: 10px; filter: grayscale(1);" />` :
                `<div class="brand-box">${estabelecimento?.nome_fantasia || 'MERCADINHOSYS'}</div>`
            }
                            <div class="bold text-lg">${estabelecimento?.nome_fantasia || 'MercadinhoSys'}</div>
                            ${estabelecimento?.razao_social ? `<div class="text-xs italic">${estabelecimento.razao_social}</div>` : ''}
                            <div class="text-xs">CNPJ: ${estabelecimento?.cnpj || '00.000.000/0001-00'}</div>
                            <div class="text-xs">${estabelecimento?.endereco || 'LOGRADOURO NÃO INFORMADO'}</div>
                            <div class="text-xs">TEL: ${estabelecimento?.telefone || '(00) 0000-0000'}</div>
                        </div>

                        <div class="double-divider"></div>

                        <!-- SALES INTEL -->
                        <div style="font-size: 10px; line-height: 1.5;">
                            <div class="total-row"><strong>PEDIDO #:</strong> <span>${venda.codigo}</span></div>
                            <div class="total-row"><strong>DATA/HORA:</strong> <span>${venda.data}</span></div>
                            <div class="total-row"><strong>CLIENTE:</strong> <span>${comprovante.cliente?.toUpperCase() || 'CONSUMIDOR FINAL'}</span></div>
                            <div class="total-row"><strong>TERMINAL:</strong> <span>${comprovante.funcionario?.toUpperCase() || 'CX-01'}</span></div>
                        </div>

                        <div class="divider"></div>

                        <!-- ITEMIZATION -->
                        <div class="bold text-xs" style="margin-bottom: 5px; border-bottom: 1px solid #000; padding-bottom: 3px;">
                            ITENS DA VENDA
                        </div>

                        <table>
                            ${itensHtml}
                        </table>

                        <!-- TOTALIZATION FLOW -->
                        <div class="total-section">
                            <div class="total-row">
                                <span>SUBTOTAL BRUTO:</span>
                                <span>R$ ${Number(comprovante.subtotal || 0).toFixed(2)}</span>
                            </div>
                            ${comprovante.desconto > 0 ? `
                                <div class="total-row" style="color: #000;">
                                    <span>DESCONTOS (-) :</span>
                                    <span>R$ ${Number(comprovante.desconto || 0).toFixed(2)}</span>
                                </div>
                            ` : ''}
                            
                            <div class="total-highlight">
                                <div class="total-row">
                                    <span>TOTAL:</span>
                                    <span>R$ ${Number(comprovante.total || 0).toFixed(2)}</span>
                                </div>
                            </div>
                        </div>

                        <!-- SETTLEMENT -->
                        <div style="padding: 5px; border: 1px solid #000; margin-top: 10px;">
                            <div class="total-row">
                                <span class="bold">FORMA:</span>
                                <span class="bold">${comprovante.forma_pagamento?.toUpperCase() || 'DINHEIRO'}</span>
                            </div>
                            <div class="total-row">
                                <span>VALOR PAGO:</span>
                                <span>R$ ${Number(comprovante.valor_recebido || 0).toFixed(2)}</span>
                            </div>
                            <div class="total-row" style="font-size: 14px; margin-top: 4px; border-top: 1px dotted #000; padding-top: 4px;">
                                <span class="bold">TROCO:</span>
                                <span class="bold">R$ ${Number(comprovante.troco || 0).toFixed(2)}</span>
                            </div>
                        </div>

                        <div class="divider"></div>

                        <!-- FOOTER & LEGAL -->
                        <div class="footer">
                            <div class="bold text-lg">${comprovante.rodape || 'OBRIGADO PELA PREFERÊNCIA!'}</div>
                            <div class="barcode-stub">${venda.codigo.replace(/[^0-9]/g, '').slice(-8)}</div>
                            <div style="margin-top: 10px; border-top: 1px solid #000; padding-top: 5px;">
                                *** ESTE NÃO É UM DOCUMENTO FISCAL ***
                            </div>
                            <div class="italic" style="margin-top: 5px;">POWERED BY ELITE-PDV ENGINE</div>
                        </div>
                    </div>
                </body>
            </html>
        `;

        const novaJanela = window.open('', '_blank');
        if (!novaJanela) {
            showToast.error('Não foi possível abrir a nota. Verifique se popups estão bloqueados.');
            return;
        }
        novaJanela.document.write(html);
        novaJanela.document.close();

        if (imprimirAutomaticamente) {
            novaJanela.focus();
            // Pequeno delay para garantir carregamento do DOM antes do print
            setTimeout(() => {
                novaJanela.print();
            }, 500);
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

            showToast.success(`Email enviado para ${email}`, {
                id: 'pdv-email-sucesso',
                duration: 5000,
            });

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
            showToast.error(
                `Falha ao enviar email${detalhe ? `: ${detalhe}` : '. Verifique as configurações SMTP.'}`,
                { duration: 6000, id: TOAST_IDS.erroEmail }
            );
        } finally {
            setEnviandoEmail(false);
        }
    };

    const handleImprimirNota = () => {
        setMostrarModalNotaFiscal(false);
        const loadingId = showToast.loading('Preparando impressão...');
        setTimeout(() => {
            showToast.dismiss(loadingId as string);
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

    if (loading && !configuracoes) {
        return <PDVSkeleton />;
    }

    return (
        <div className="flex flex-col lg:grid lg:grid-cols-12 min-h-screen lg:h-screen w-full bg-gray-50 dark:bg-gray-900 transition-colors duration-200 lg:overflow-hidden">

            {/* LEFT COLUMN: Header + Search + Cart / Scrollable on mobile, Fixed on Desktop */}
            <div className="flex-1 lg:col-span-8 flex flex-col min-h-0 lg:h-full bg-gray-50 dark:bg-gray-900">
                {/* Header Section - Fixed Top */}
                <div className="p-2 sm:p-4 lg:p-6 flex-shrink-0 z-30 bg-gray-50 dark:bg-gray-900">
                    <CaixaHeader
                        funcionarioNome={configuracoes?.funcionario.nome}
                        funcionarioRole={configuracoes?.funcionario.role}
                        refreshKey={ultimaVendaId ?? undefined}
                    />
                </div>

                {/* Main Content Area (Items) - Scrollable list */}
                <div className="flex-1 flex flex-col px-2 sm:px-4 lg:px-6 pb-4 lg:pb-6 min-h-0 lg:overflow-hidden">
                    <div className="flex flex-col h-full space-y-4 lg:overflow-y-auto custom-scrollbar lg:pr-2">

                        {/* Busca de Produtos */}
                        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 p-4 sm:p-6 flex-shrink-0">
                            <div className="flex items-center justify-between mb-4">
                                <h2 className="text-lg sm:text-xl font-bold text-gray-800 dark:text-white flex items-center">
                                    <Search className="w-5 h-5 sm:w-6 sm:h-6 mr-3 text-blue-600" />
                                    Vender Produto
                                </h2>
                                <div className="hidden sm:flex space-x-2">
                                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300">
                                        F1: Busca
                                    </span>
                                </div>
                            </div>
                            <ErrorBoundary name="Busca de Produtos">
                                <ProdutoSearch onProdutoSelecionado={handleProdutoSelecionado} />
                            </ErrorBoundary>
                        </div>

                        {/* Carrinho Section */}
                        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 flex flex-col flex-1 min-h-[350px] lg:min-h-0">
                            <div className="p-4 sm:p-6 border-b border-gray-100 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-800/50 flex items-center justify-between flex-shrink-0">
                                <div className="flex items-center space-x-3">
                                    <div className="p-2 bg-blue-600 rounded-lg text-white shadow-lg shadow-blue-600/20">
                                        <ShoppingCart className="w-5 h-5 sm:w-6 sm:h-6" />
                                    </div>
                                    <div>
                                        <h2 className="text-base sm:text-xl font-bold text-gray-800 dark:text-white">
                                            Carrinho
                                        </h2>
                                        <p className="text-[10px] sm:text-sm text-gray-500 dark:text-gray-400">
                                            {carrinho.length} {carrinho.length === 1 ? 'item' : 'itens'}
                                        </p>
                                    </div>
                                </div>
                                {carrinho.length > 0 && (
                                    <button
                                        onClick={handleLimparCarrinho}
                                        className="p-2 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                                    >
                                        <Trash2 className="w-5 h-5" />
                                    </button>
                                )}
                            </div>

                            <div className="flex-1 overflow-y-auto p-2 sm:p-4 custom-scrollbar bg-gray-50/30 dark:bg-gray-900/10">
                                {carrinho.length === 0 ? (
                                    <div className="h-full flex flex-col items-center justify-center text-center py-10 opacity-60">
                                        <div className="w-16 h-16 sm:w-20 sm:h-20 bg-gray-200 dark:bg-gray-800 rounded-full flex items-center justify-center mb-4">
                                            <ShoppingCart className="w-8 h-8 sm:w-10 sm:h-10 text-gray-400" />
                                        </div>
                                        <h3 className="text-base font-medium text-gray-900 dark:text-white">Carrinho Vazio</h3>
                                        <p className="text-xs text-gray-500 max-w-[200px] mx-auto mt-1">Pesquise produtos para começar a venda.</p>
                                    </div>
                                ) : (
                                    <div className="space-y-2 sm:space-y-3">
                                        {carrinho.map((item) => (
                                            <ErrorBoundary key={item.produto.id} name={`Item Carrinho: ${item.produto.nome}`}>
                                                <CarrinhoItem
                                                    produto={item.produto}
                                                    quantidade={item.quantidade}
                                                    precoUnitario={item.precoUnitario}
                                                    desconto={item.desconto}
                                                    total={item.total}
                                                    onAtualizarQuantidade={(qtd) => {
                                                        const estoque = item.produto.quantidade_estoque ?? item.produto.quantidade ?? 0;
                                                        if (qtd > estoque) {
                                                            showToast.error(`Estoque insuficiente`, { id: TOAST_IDS.estoqueInsuficiente });
                                                            return;
                                                        }
                                                        atualizarQuantidade(item.produto.id, qtd);
                                                    }}
                                                    onRemover={() => removerProduto(item.produto.id)}
                                                    onAplicarDesconto={(desc, perc) => aplicarDescontoItem(item.produto.id, desc, perc)}
                                                />
                                            </ErrorBoundary>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* RIGHT COLUMN: Summary & Payment / Fixed on Desktop, Flowing/Sticky on Mobile */}
            <div className="lg:col-span-4 flex flex-col bg-white dark:bg-gray-800 border-l border-gray-200 dark:border-gray-700 h-auto lg:h-full lg:overflow-hidden shadow-2xl z-20 pb-20 lg:pb-0">
                {/* Scrollable Summary Section */}
                <div className="flex-1 overflow-y-auto custom-scrollbar p-4 sm:p-6 space-y-6">
                    {/* Cliente Selection */}
                    <div>
                        <div className="flex items-center justify-between mb-3">
                            <label className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider flex items-center">
                                <User className="w-3.5 h-3.5 mr-2" />
                                Cliente
                            </label>
                            <span className="hidden sm:block text-[10px] font-bold px-1.5 py-0.5 bg-gray-100 text-gray-600 rounded dark:bg-gray-700 dark:text-gray-300">F2</span>
                        </div>
                        <ClienteSelect cliente={cliente} onClienteSelecionado={setCliente} />
                    </div>

                    <div className="border-t border-gray-100 dark:border-gray-700 my-4"></div>

                    {/* Resumo Financeiro */}
                    <div className="space-y-3">
                        <div className="flex justify-between text-gray-600 dark:text-gray-400 text-sm">
                            <span>Subtotal</span>
                            <span className="font-medium text-gray-900 dark:text-white">{formatCurrency(subtotal)}</span>
                        </div>
                        {descontoItens > 0 && (
                            <div className="flex justify-between text-xs text-green-600 dark:text-green-400">
                                <span>Descontos em Itens</span>
                                <span>-{formatCurrency(descontoItens)}</span>
                            </div>
                        )}
                        <div className="flex items-center justify-between">
                            <span className="text-sm text-gray-600 dark:text-gray-400">Desconto Extra</span>
                            <div className="flex items-center space-x-2">
                                <button
                                    onClick={() => setDescontoPercentual(!descontoPercentual)}
                                    className={`px-2 py-0.5 text-[10px] rounded font-bold transition-colors ${descontoPercentual ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300' : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'}`}
                                >
                                    {descontoPercentual ? '%' : 'R$'}
                                </button>
                                <input
                                    type="number"
                                    value={descontoGeral || ''}
                                    onChange={(e) => {
                                        const val = parseFloat(e.target.value);
                                        setDescontoGeral(isNaN(val) ? 0 : val);
                                        setDescontoAprovado(false);
                                    }}
                                    onBlur={handleAplicarDesconto}
                                    className={`w-20 sm:w-24 px-2 py-1 text-right text-sm border rounded-md focus:ring-2 focus:ring-blue-500 outline-none ${!descontoAprovado && descontoGeral > 0 && !validarDescontoPermitido(descontoGeralCalculado) ? 'border-yellow-500 bg-yellow-50 dark:bg-yellow-900/10' : 'border-gray-300 dark:border-gray-600 dark:bg-gray-700 text-gray-900 dark:text-white'}`}
                                    min="0"
                                    step="0.01"
                                />
                            </div>
                        </div>
                    </div>

                    <div className="border-t border-gray-100 dark:border-gray-700 my-4"></div>

                    {/* Desktop Total Display (Hidden on Mobile Sticky) */}
                    <div className="hidden lg:block bg-gray-50 dark:bg-gray-900/50 rounded-xl p-4 border border-gray-100 dark:border-gray-700">
                        <div className="flex justify-between items-end mb-1">
                            <span className="text-[10px] font-semibold text-gray-500 dark:text-gray-400 uppercase">Total a Pagar</span>
                        </div>
                        <div className="flex justify-between items-center text-3xl font-black text-gray-900 dark:text-white tracking-tight">
                            <span>R$</span>
                            <span>{Number(total).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                        </div>
                    </div>

                    {/* Payment Methods */}
                    <div className="space-y-3">
                        <div className="flex items-center justify-between">
                            <label className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider flex items-center">
                                <CreditCard className="w-3.5 h-3.5 mr-2" />
                                Pagamento
                            </label>
                            <span className="hidden sm:block text-[10px] font-bold px-1.5 py-0.5 bg-gray-100 text-gray-600 rounded dark:bg-gray-700 dark:text-gray-300">F4</span>
                        </div>
                        <div className="grid grid-cols-2 gap-2">
                            {formasPagamento.map((forma) => (
                                <button
                                    key={forma.tipo}
                                    onClick={() => setFormaPagamentoSelecionada(forma.tipo)}
                                    className={`
                                        relative p-2.5 sm:p-3 rounded-xl border text-left transition-all duration-200 group flex flex-col justify-between min-h-[70px] sm:min-h-[80px]
                                        ${formaPagamentoSelecionada === forma.tipo
                                            ? 'bg-blue-50 border-blue-500 ring-1 ring-blue-500 dark:bg-blue-900/20 dark:border-blue-500'
                                            : 'bg-white border-gray-200 hover:border-blue-300 hover:bg-gray-50 dark:bg-gray-800 dark:border-gray-700 dark:hover:border-gray-600'
                                        }
                                    `}
                                >
                                    <div className="flex items-center justify-between mb-1.5 w-full">
                                        <span className={`${formaPagamentoSelecionada === forma.tipo ? 'text-blue-700 dark:text-blue-300' : 'text-gray-600 dark:text-gray-400'}`}>
                                            {renderIconPagamento(forma.tipo)}
                                        </span>
                                        {forma.taxa > 0 && (
                                            <span className="text-[9px] font-bold px-1 py-0.5 bg-yellow-100 dark:bg-yellow-900/40 text-yellow-700 dark:text-yellow-400 rounded-full">
                                                +{forma.taxa}%
                                            </span>
                                        )}
                                    </div>
                                    <span className={`font-bold text-[11px] sm:text-xs leading-tight ${formaPagamentoSelecionada === forma.tipo ? 'text-blue-700 dark:text-blue-300' : 'text-gray-700 dark:text-gray-300'}`}>
                                        {forma.label}
                                    </span>
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Change / Received Display */}
                    {formasPagamento.find(f => f.tipo === formaPagamentoSelecionada)?.permite_troco && (
                        <div className="bg-gray-50 dark:bg-gray-900/50 rounded-xl p-3 sm:p-4 space-y-3 border border-gray-100 dark:border-gray-700">
                            <label className="block text-[10px] font-bold text-gray-500 dark:text-gray-400 uppercase">
                                Valor Recebido
                            </label>
                            <input
                                type="number"
                                value={valorRecebido || ''}
                                onChange={(e) => setValorRecebido(parseFloat(e.target.value) || 0)}
                                className="w-full bg-white dark:bg-gray-800 border-2 border-gray-200 dark:border-gray-700 rounded-lg px-3 py-2 text-xl font-bold text-right outline-none focus:border-blue-500 transition-colors text-gray-900 dark:text-white"
                                placeholder="0,00"
                                step="0.01"
                            />
                            {valorRecebido > 0 && (
                                <div className="flex justify-between items-center pt-2 border-t border-gray-100 dark:border-gray-700">
                                    <span className="text-xs font-medium text-gray-500 italic">Troco</span>
                                    <span className={`text-lg font-black ${troco >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                        {formatCurrency(troco)}
                                    </span>
                                </div>
                            )}
                        </div>
                    )}

                    {/* Observações */}
                    <div>
                        <label className="block text-[10px] font-bold text-gray-500 dark:text-gray-400 uppercase mb-2">
                            Notas da Venda
                        </label>
                        <textarea
                            value={observacoes}
                            onChange={(e) => setObservacoes(e.target.value)}
                            className="w-full bg-gray-50 dark:bg-gray-900/50 border border-gray-200 dark:border-gray-700 rounded-xl p-3 text-xs outline-none focus:border-blue-500 transition-colors text-gray-900 dark:text-white"
                            rows={2}
                            placeholder="Ex: Entrega rápida..."
                        />
                    </div>
                </div>

                {/* STICKY BOTTOM BAR (Mobile) / FIXED FOOTER (Desktop) */}
                <div className="fixed bottom-0 left-0 right-0 lg:static p-3 sm:p-4 lg:p-6 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 flex flex-col space-y-2 z-50 shadow-[0_-8px_30px_rgb(0,0,0,0.1)] lg:shadow-none">

                    {/* Mobile-only Summary Bar */}
                    <div className="flex lg:hidden justify-between items-center mb-1 px-1">
                        <div className="flex flex-col">
                            <span className="text-[10px] text-gray-500 font-bold uppercase">Total</span>
                            <span className="text-xl font-black text-gray-900 dark:text-white">{formatCurrency(total)}</span>
                        </div>
                        <div className="flex space-x-2">
                            <button
                                onClick={handleLimparCarrinho}
                                className="p-3 rounded-lg text-red-500 bg-red-50 dark:bg-red-900/20 border border-red-100 dark:border-red-900/30"
                            >
                                <Trash2 className="w-5 h-5" />
                            </button>
                        </div>
                    </div>

                    <button
                        onClick={handleFinalizarVenda}
                        disabled={carrinho.length === 0 || loading}
                        className={`
                            w-full h-12 sm:h-14 rounded-xl flex items-center justify-center space-x-2 text-white font-bold text-base sm:text-lg shadow-lg hover:shadow-xl hover:-translate-y-0.5 active:translate-y-0 transition-all
                            ${carrinho.length === 0 || loading
                                ? 'bg-gray-400 cursor-not-allowed shadow-none'
                                : 'bg-gradient-to-r from-green-600 to-green-500 hover:from-green-500 hover:to-green-400'
                            }
                        `}
                    >
                        {loading ? (
                            <div className="flex items-center">
                                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin mr-2" />
                                <span>Processando...</span>
                            </div>
                        ) : (
                            <>
                                <Check className="w-5 h-5 sm:w-6 sm:h-6" />
                                <span>FINALIZAR VENDA {carrinho.length > 0 && <span className="hidden sm:inline">(F9)</span>}</span>
                            </>
                        )}
                    </button>
                </div>
            </div>

            {/* Modals */}
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
    );
};

export default PDVPage;
