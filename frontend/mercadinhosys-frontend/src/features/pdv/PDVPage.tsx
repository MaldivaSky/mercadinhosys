import React, { useState, useEffect, useRef } from 'react';
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
    AlertTriangle,
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

    return (
        <div className="min-h-screen lg:h-screen lg:overflow-hidden flex flex-col bg-gray-50 dark:bg-gray-900">
            <div className="flex-1 p-2 sm:p-4 lg:p-6 overflow-y-auto lg:overflow-hidden">
                <div className="max-w-[1600px] mx-auto">
                    {/* Header com informações do caixa (refreshKey atualiza stats após venda) */}
                    <CaixaHeader
                        funcionarioNome={configuracoes?.funcionario.nome}
                        funcionarioRole={configuracoes?.funcionario.role}
                        refreshKey={ultimaVendaId ?? undefined}
                    />

                    {/* Layout Principal */}
                    <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 lg:gap-8">
                        {/* Coluna 1: Busca e Carrinho */}
                        <div className="lg:col-span-8 flex flex-col space-y-4 min-h-[500px] lg:min-h-0">
                            {/* Busca de Produtos */}
                            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl border border-gray-100 dark:border-gray-700 p-4 sm:p-6 flex flex-col flex-shrink-0">
                                <div className="flex items-center justify-between mb-4">
                                    <h2 className="text-lg sm:text-xl font-bold text-gray-800 dark:text-white flex items-center">
                                        <Search className="w-5 h-5 sm:w-6 sm:h-6 mr-2 text-blue-500" />
                                        Vender Produto
                                    </h2>
                                    <span className="hidden sm:inline-block text-xs font-semibold px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-500 rounded border border-gray-200 dark:border-gray-600">
                                        F1 ou ESC para foco
                                    </span>
                                </div>
                                <ErrorBoundary name="Busca de Produtos">
                                    <ProdutoSearch onProdutoSelecionado={handleProdutoSelecionado} />
                                </ErrorBoundary>
                            </div>

                            {/* Carrinho */}
                            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl border border-gray-100 dark:border-gray-700 overflow-hidden flex flex-col flex-1 min-h-[400px]">
                                <div className="p-4 sm:p-6 border-b border-gray-100 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-800/50 flex items-center justify-between">
                                    <div className="flex items-center space-x-3">
                                        <div className="p-2 bg-blue-500 rounded-lg text-white">
                                            <ShoppingCart className="w-5 h-5 sm:w-6 sm:h-6" />
                                        </div>
                                        <div>
                                            <h2 className="text-lg sm:text-xl font-bold text-gray-800 dark:text-white">
                                                Carrinho
                                            </h2>
                                            <p className="hidden sm:block text-xs text-gray-500 dark:text-gray-400">
                                                Itens para checkout
                                            </p>
                                        </div>
                                    </div>
                                    <div className="flex items-center space-x-3 sm:space-x-4">
                                        <span className="px-3 py-1.5 sm:px-4 sm:py-2 bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 rounded-xl font-bold text-base sm:text-lg">
                                            {carrinho.length}
                                        </span>
                                        {carrinho.length > 0 && (
                                            <button
                                                onClick={handleLimparCarrinho}
                                                className="p-2 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-xl transition-colors"
                                                title="Limpar carrinho"
                                            >
                                                <Trash2 className="w-5 h-5 sm:w-6 sm:h-6" />
                                            </button>
                                        )}
                                    </div>
                                </div>

                                <div className="flex-1 overflow-y-auto p-3 sm:p-6 custom-scrollbar bg-gray-50/30 dark:bg-gray-900/10">
                                    {carrinho.length === 0 ? (
                                        <div className="h-full flex flex-col items-center justify-center text-center py-12">
                                            <div className="w-20 h-20 sm:w-24 sm:h-24 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mb-6">
                                                <ShoppingCart className="w-10 h-10 sm:w-12 sm:h-12 text-gray-400 dark:text-gray-600" />
                                            </div>
                                            <h3 className="text-base sm:text-lg font-bold text-gray-700 dark:text-gray-300 mb-2">
                                                Seu carrinho está vazio
                                            </h3>
                                        </div>
                                    ) : (
                                        <div className="space-y-3">
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
                                                                showToast.error(`Estoque insuficiente`, {
                                                                    id: TOAST_IDS.estoqueInsuficiente,
                                                                });
                                                                return;
                                                            }
                                                            atualizarQuantidade(item.produto.id, qtd);
                                                        }}
                                                        onRemover={() => removerProduto(item.produto.id)}
                                                        onAplicarDesconto={(desc, perc) =>
                                                            aplicarDescontoItem(item.produto.id, desc, perc)
                                                        }
                                                    />
                                                </ErrorBoundary>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>

                        {/* Coluna 2: Resumo e Pagamento (Ocupa 4/12 no desktop) */}
                        <div className="lg:col-span-4 flex flex-col space-y-4 lg:space-y-6 lg:overflow-y-auto lg:custom-scrollbar pb-20 lg:pb-6">
                            {/* Cliente */}
                            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl border border-gray-100 dark:border-gray-700 p-6">
                                <div className="flex items-center justify-between mb-4">
                                    <h2 className="text-lg font-bold text-gray-800 dark:text-white flex items-center">
                                        <User className="w-5 h-5 mr-2 text-blue-500" />
                                        Identificar Cliente
                                    </h2>
                                    <span className="text-[10px] font-bold px-1.5 py-0.5 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded">
                                        F2
                                    </span>
                                </div>
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
                                    <div className="space-y-2 max-h-[300px] overflow-y-auto custom-scrollbar p-1">
                                        {(formasPagamento.length > 0 ? formasPagamento : [
                                            { tipo: 'dinheiro', label: 'Dinheiro', taxa: 0, permite_troco: true },
                                            { tipo: 'credito', label: 'Cartão de Crédito', taxa: 0, permite_troco: false },
                                            { tipo: 'debito', label: 'Cartão de Débito', taxa: 0, permite_troco: false },
                                            { tipo: 'pix', label: 'PIX', taxa: 0, permite_troco: false }
                                        ]).map((forma) => (
                                            <button
                                                key={forma.tipo}
                                                onClick={() => {
                                                    setFormaPagamentoSelecionada(forma.tipo);
                                                    setFormaPagamentoAberta(false);
                                                    if (!forma.permite_troco) {
                                                        setValorRecebido(0);
                                                    }
                                                }}
                                                className={`w-full p-4 rounded-xl flex items-center justify-between transition-all duration-200 ${formaPagamentoSelecionada === forma.tipo
                                                    ? 'bg-blue-50 dark:bg-blue-900/30 border-2 border-blue-500 shadow-md transform scale-[1.01]'
                                                    : 'bg-white dark:bg-gray-800 border-2 border-gray-100 dark:border-gray-700 hover:border-blue-200 dark:hover:border-blue-800 hover:bg-gray-50 dark:hover:bg-gray-700/50'
                                                    }`}
                                            >
                                                <div className="flex items-center space-x-3">
                                                    <div className={`p-2 rounded-lg ${formaPagamentoSelecionada === forma.tipo ? 'bg-blue-500 text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-500'}`}>
                                                        {renderIconPagamento(forma.tipo)}
                                                    </div>
                                                    <span className={`font-bold ${formaPagamentoSelecionada === forma.tipo ? 'text-blue-700 dark:text-blue-300' : 'text-gray-700 dark:text-gray-300'}`}>
                                                        {forma.label}
                                                    </span>
                                                </div>
                                                {forma.taxa > 0 ? (
                                                    <span className="text-xs font-semibold px-2 py-1 bg-yellow-100 dark:bg-yellow-900/40 text-yellow-700 dark:text-yellow-400 rounded-full">
                                                        +{forma.taxa}%
                                                    </span>
                                                ) : (
                                                    <span className="text-xs text-gray-400">Sem taxa</span>
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
        </div>
    );
};

export default PDVPage;
