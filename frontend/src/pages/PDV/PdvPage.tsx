// frontend/src/pages/PDV/PdvPage.tsx
import React, { useState, useEffect, useRef } from 'react';
import { vendaService } from '../../services/vendaService';
import { produtoService } from '../../services/produtoService';
import './PdvPage.css';
import iconPix from '../../assets/iconPix.png';
import api from '../../services/api';


// Ícones SVG profissionais
const IconeScanner = () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
        <path d="M3 4h4v2H3V4zm0 14h4v2H3v-2zm14 0h4v2h-4v-2zM7 4h10v2H7V4zm0 14h10v2H7v-2zm-4-4h2v6H3v-6zm14 0h2v6h-2v-6zM3 8h2v2H3V8zm14 0h2v2h-2V8zM7 8h10v2H7V8zm-4 4h2v2H3v-2zm14 0h2v2h-2v-2z" />
    </svg>
);

const IconeProduto = () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
        <path d="M21 9l-9-7-9 7v11a2 2 0 002 2h14a2 2 0 002-2V9z" />
    </svg>
);

const IconeCliente = () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" />
    </svg>
);

const IconeDinheiro = () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
        <path d="M11.8 10.9c-2.27-.59-3-1.2-3-2.15 0-1.09 1.01-1.85 2.7-1.85 1.78 0 2.44.85 2.5 2.1h2.21c-.07-1.72-1.12-3.3-3.21-3.81V3h-3v2.16c-1.94.42-3.5 1.68-3.5 3.61 0 2.31 1.91 3.46 4.7 4.13 2.5.6 3 1.48 3 2.41 0 .69-.49 1.79-2.7 1.79-2.06 0-2.87-.92-2.98-2.1h-2.2c.12 2.19 1.76 3.42 3.68 3.83V21h3v-2.15c1.95-.37 3.5-1.5 3.5-3.55 0-2.84-2.43-3.81-4.7-4.4z" />
    </svg>
);

const IconeCartao = () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
        <path d="M20 4H4c-1.11 0-1.99.89-1.99 2L2 18c0 1.11.89 2 2 2h16c1.11 0 2-.89 2-2V6c0-1.11-.89-2-2-2zm0 14H4v-6h16v6zm0-10H4V6h16v2z" />
    </svg>
);

const IconePix = () => (
    <img
        src={iconPix}
        alt="PIX"
        width="20"
        height="20"
        style={{
            display: 'block',
            objectFit: 'contain'
        }}
    />
);

const IconeAdd = () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
        <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z" />
    </svg>
);

const IconeRemove = () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
        <path d="M19 13H5v-2h14v2z" />
    </svg>
);

const IconeDelete = () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
        <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z" />
    </svg>
);

interface Produto {
    id: number;
    nome: string;
    preco: number;
    quantidadeEstoque: number;
    codigoBarras?: string;
}

interface ItemVenda {
    produtoId: number;
    quantidade: number;
    produto?: Produto;
}

const PdvPage: React.FC = () => {
    const [produtos, setProdutos] = useState<Produto[]>([]);
    const [itensVenda, setItensVenda] = useState<ItemVenda[]>([]);
    const [clienteId, setClienteId] = useState<string>('');
    const [pagamento, setPagamento] = useState<string>('dinheiro');
    const [carregando, setCarregando] = useState(false);
    const [codigoBarrasInput, setCodigoBarrasInput] = useState<string>('');
    const [modoScanner, setModoScanner] = useState<boolean>(false);
    const [buscaProduto, setBuscaProduto] = useState<string>('');
    const scannerInputRef = useRef<HTMLInputElement>(null);

    const produtosMock: Produto[] = [
        { id: 1, nome: 'Arroz 5kg', preco: 25.90, quantidadeEstoque: 100, codigoBarras: '7891000315507' },
        { id: 2, nome: 'Feijão Carioca 1kg', preco: 8.50, quantidadeEstoque: 150, codigoBarras: '7891000053502' },
        { id: 3, nome: 'Óleo de Soja 900ml', preco: 9.90, quantidadeEstoque: 80, codigoBarras: '7891000140309' },
        { id: 4, nome: 'Açúcar Cristal 5kg', preco: 22.50, quantidadeEstoque: 60, codigoBarras: '7891000053816' },
        { id: 5, nome: 'Café Tradicional 500g', preco: 18.90, quantidadeEstoque: 120, codigoBarras: '7891000055124' },
        { id: 6, nome: 'Leite Integral 1L', preco: 5.90, quantidadeEstoque: 200, codigoBarras: '7891000055506' },
        { id: 7, nome: 'Macarrão Espaguete 500g', preco: 4.50, quantidadeEstoque: 180, codigoBarras: '7891000312506' },
        { id: 8, nome: 'Molho de Tomate 340g', preco: 3.90, quantidadeEstoque: 90, codigoBarras: '7891000064505' },
    ];

    useEffect(() => {
        carregarProdutos();
        if (modoScanner && scannerInputRef.current) {
            scannerInputRef.current.focus();
        }
    }, [modoScanner]);

    const carregarProdutos = async () => {
        try {
            console.log('🔄 Carregando produtos via proxy...');

            // Usar a API via proxy
            const response = await produtoService.listar();
            console.log('✅ Produtos carregados:', response.data.length, 'itens');

            // Converter os dados da API para o formato do frontend
            const produtosDaAPI = (response.data as any[]).map((prod: any) => ({
                id: prod.id,
                nome: prod.nome,
                preco: prod.preco || 0,
                quantidadeEstoque: prod.quantidadeEstoque || 0,
                codigoBarras: prod.codigoBarras || ''
            }));

            setProdutos(produtosDaAPI);

        } catch (error) {
            console.error('❌ Erro ao carregar produtos:', error);
            console.log('🔄 Usando dados mock');
            setProdutos(produtosMock);
            alert('⚠️ Usando dados de demonstração. API offline.');
        }
    };

    const adicionarItem = (produto: Produto) => {
        const itemExistente = itensVenda.find(item => item.produtoId === produto.id);

        if (itemExistente) {
            setItensVenda(prev =>
                prev.map(item =>
                    item.produtoId === produto.id
                        ? { ...item, quantidade: item.quantidade + 1 }
                        : item
                )
            );
        } else {
            setItensVenda(prev => [
                ...prev,
                {
                    produtoId: produto.id,
                    quantidade: 1,
                    produto
                }
            ]);
        }

        if (modoScanner) {
            setCodigoBarrasInput('');
            scannerInputRef.current?.focus();
        }
    };

    const handleScannerInput = (e: React.ChangeEvent<HTMLInputElement>) => {
        const value = e.target.value;
        setCodigoBarrasInput(value);

        if (value.length >= 8) {
            processarCodigoBarras(value);
        }
    };

    const processarCodigoBarras = (codigo: string) => {
        const produtoEncontrado = produtos.find(
            p => p.codigoBarras === codigo || p.id.toString() === codigo
        );

        if (produtoEncontrado) {
            adicionarItem(produtoEncontrado);
        } else {
            alert('Produto não encontrado!');
            setCodigoBarrasInput('');
        }

        scannerInputRef.current?.focus();
    };

    const removerItem = (produtoId: number) => {
        setItensVenda(prev => prev.filter(item => item.produtoId !== produtoId));
    };

    const atualizarQuantidade = (produtoId: number, quantidade: number) => {
        if (quantidade <= 0) {
            removerItem(produtoId);
            return;
        }

        setItensVenda(prev =>
            prev.map(item =>
                item.produtoId === produtoId
                    ? { ...item, quantidade }
                    : item
            )
        );
    };

    const calcularTotal = () => {
        return itensVenda.reduce((total, item) => {
            const produto = produtos.find(p => p.id === item.produtoId);
            return total + (produto ? produto.preco * item.quantidade : 0);
        }, 0);
    };

    const handleFinalizarVenda = async () => {
        if (itensVenda.length === 0) {
            alert('Adicione itens à venda antes de finalizar');
            return;
        }

        setCarregando(true);

        try {
            // Converter para snake_case (como o backend espera)
            const vendaData = {
                cliente_id: clienteId ? parseInt(clienteId) : null,  // ← snake_case
                itens: itensVenda.map(item => ({
                    produto_id: item.produtoId,  // ← snake_case
                    quantidade: item.quantidade
                })),
                forma_pagamento: pagamento  // ← snake_case
            };

            console.log('📤 Dados da venda (snake_case):', vendaData);

            const response = await vendaService.criar(vendaData);

            alert(`✅ Venda finalizada com sucesso!\nNúmero: ${response.data.numero}\nTotal: R$ ${calcularTotal().toFixed(2)}`);

            // Limpar após venda
            setItensVenda([]);
            setClienteId('');
            setPagamento('dinheiro');
            setCodigoBarrasInput('');

        } catch (error: unknown) {
            console.error('❌ Erro ao finalizar venda:', error);

            if (error && typeof error === 'object' && 'response' in error) {
                const axiosError = error as { response?: { data?: { error?: string } } };
                if (axiosError.response?.data?.error) {
                    alert(`Erro: ${axiosError.response.data.error}`);
                } else {
                    alert('Erro ao finalizar venda. Verifique o console.');
                }
            } else {
                alert('Erro desconhecido ao finalizar venda.');
            }

        } finally {
            setCarregando(false);
        }
    };

    const limparVenda = () => {
        if (itensVenda.length > 0 && window.confirm('Cancelar esta venda?')) {
            setItensVenda([]);
            setClienteId('');
            setCodigoBarrasInput('');
        }
    };

    const produtosFiltrados = produtos.filter(produto =>
        produto.nome.toLowerCase().includes(buscaProduto.toLowerCase()) ||
        produto.codigoBarras?.includes(buscaProduto)
    );

    const testarConexaoAPI = async () => {
        try {
            setCarregando(true);
            console.log('🔌 Testando conexão com a API...');

            const response = await api.get('/health'); // ou endpoint apropriado
            alert(`✅ API conectada!\nStatus: ${response.status}\nMensagem: ${response.data?.message || 'OK'}`);

        } catch (error) {
            console.error('❌ Falha na conexão:', error);
            alert(`❌ Falha na conexão com a API:\n${error.message}\n\nVerifique:\n1. Backend está rodando?\n2. URL correta?\n3. CORS habilitado?`);

        } finally {
            setCarregando(false);
        }
    };

    return (
        <div className="pdv-container">
            {/* Header */}
            <header className="pdv-header">
                <div className="header-right">
                    <button
                        onClick={testarConexaoAPI}
                        className="btn-teste-conexao"
                        disabled={carregando}
                    >
                        {carregando ? 'Testando...' : 'Testar Conexão'}
                    </button>

                    <div className="status-indicator">
                        {/* ... código existente ... */}
                    </div>

                    <div className="venda-info">
                        {/* ... código existente ... */}
                    </div>
                </div>
                <div className="header-left">
                    <h1 className="pdv-title">Ponto de Venda</h1>
                    <span className="pdv-subtitle">Sistema Mercadinho v1.0</span>
                </div>
                <div className="header-right">
                    <div className="status-indicator">
                        <span className={`status-dot ${modoScanner ? 'active' : ''}`}></span>
                        <span className="status-text">
                            {modoScanner ? 'Scanner Ativo' : 'Modo Manual'}
                        </span>
                    </div>
                    <div className="venda-info">
                        <span className="venda-count">{itensVenda.length} itens</span>
                        <span className="venda-total">R$ {calcularTotal().toFixed(2)}</span>
                    </div>
                </div>
            </header>

            <div className="pdv-main">
                {/* Coluna da Esquerda - Produtos */}
                <div className="produtos-panel">
                    <div className="panel-header">
                        <div className="panel-title">
                            <IconeProduto />
                            <h2>Produtos</h2>
                        </div>
                        <div className="panel-actions">
                            <button
                                onClick={() => setModoScanner(!modoScanner)}
                                className={`scanner-toggle ${modoScanner ? 'active' : ''}`}
                            >
                                <IconeScanner />
                                {modoScanner ? 'Desativar Scanner' : 'Ativar Scanner'}
                            </button>
                        </div>
                    </div>

                    <div className="produtos-conteudo">
                        {modoScanner && (
                            <div className="scanner-panel">
                                <div className="scanner-input-wrapper">
                                    <input
                                        ref={scannerInputRef}
                                        type="text"
                                        value={codigoBarrasInput}
                                        onChange={handleScannerInput}
                                        placeholder="Posicione o código de barras..."
                                        className="scanner-input"
                                        autoFocus
                                    />
                                    <div className="scanner-hint">
                                        <span className="hint-text">Scanner ativo • Pressione ESC para cancelar</span>
                                    </div>
                                </div>
                            </div>
                        )}

                        <div className="busca-panel">
                            <input
                                type="text"
                                value={buscaProduto}
                                onChange={(e) => setBuscaProduto(e.target.value)}
                                placeholder="Buscar produto por nome ou código..."
                                className="busca-input"
                            />
                        </div>

                        <div className="produtos-grid">
                            {produtosFiltrados.map(produto => (
                                <div key={produto.id} className="produto-card">
                                    <div className="produto-header">
                                        <h3 className="produto-nome">{produto.nome}</h3>
                                        <span className="produto-codigo">{produto.codigoBarras || `ID: ${produto.id}`}</span>
                                    </div>
                                    <div className="produto-detalhes">
                                        <div className="produto-preco">
                                            <span className="preco-label">Preço</span>
                                            <span className="preco-valor">R$ {produto.preco.toFixed(2)}</span>
                                        </div>
                                        <div className="produto-estoque">
                                            <span className="estoque-label">Estoque</span>
                                            <span className={`estoque-valor ${produto.quantidadeEstoque < 10 ? 'low' : ''}`}>
                                                {produto.quantidadeEstoque} un
                                            </span>
                                        </div>
                                    </div>
                                    <button
                                        onClick={() => adicionarItem(produto)}
                                        className="btn-adicionar-produto"
                                    >
                                        <IconeAdd />
                                        Adicionar
                                    </button>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Coluna da Direita - Venda */}
                <div className="venda-panel">
                    <div className="panel-header">
                        <div className="panel-title">
                            <h2>Venda Atual</h2>
                            {itensVenda.length > 0 && (
                                <button onClick={limparVenda} className="btn-limpar-venda">
                                    <IconeDelete />
                                    Limpar
                                </button>
                            )}
                        </div>
                    </div>

                    {/* Conteúdo rolável da venda */}
                    <div className="venda-conteudo">
                        {/* Cliente Section */}
                        <div className="cliente-section">
                            <div className="section-header">
                                <IconeCliente />
                                <h3>Cliente</h3>
                            </div>
                            <div className="cliente-input-wrapper">
                                <input
                                    type="number"
                                    value={clienteId}
                                    onChange={(e) => setClienteId(e.target.value)}
                                    placeholder="ID do cliente (opcional)"
                                    className="cliente-input"
                                />
                                <span className="input-hint">Deixe em branco para venda avulsa</span>
                            </div>
                        </div>

                        {/* Itens da Venda - Esta seção terá scroll interno */}
                        <div className="itens-section">
                            <div className="section-header">
                                <h3>Itens da Venda</h3>
                                <span className="itens-count">({itensVenda.length})</span>
                            </div>

                            {itensVenda.length === 0 ? (
                                <div className="venda-vazia">
                                    <div className="vazia-icon">🛒</div>
                                    <p className="vazia-texto">Nenhum item adicionado</p>
                                    <p className="vazia-dica">Use o scanner ou adicione produtos manualmente</p>
                                </div>
                            ) : (
                                <div className="itens-lista">
                                    {itensVenda.map(item => {
                                        const produto = produtos.find(p => p.id === item.produtoId);
                                        return (
                                            <div key={item.produtoId} className="item-venda">
                                                <div className="item-info">
                                                    <div className="item-nome-wrapper">
                                                        <span className="item-nome">{produto?.nome || 'Produto'}</span>
                                                        <span className="item-codigo">{produto?.codigoBarras?.substring(0, 8)}</span>
                                                    </div>
                                                    <div className="item-quantidade">
                                                        <button
                                                            onClick={() => atualizarQuantidade(item.produtoId, item.quantidade - 1)}
                                                            className="btn-quantidade"
                                                            aria-label="Diminuir quantidade"
                                                        >
                                                            <IconeRemove />
                                                        </button>
                                                        <span className="quantidade-display">{item.quantidade}</span>
                                                        <button
                                                            onClick={() => atualizarQuantidade(item.produtoId, item.quantidade + 1)}
                                                            className="btn-quantidade"
                                                            aria-label="Aumentar quantidade"
                                                        >
                                                            <IconeAdd />
                                                        </button>
                                                    </div>
                                                    <div className="item-subtotal">
                                                        <span className="subtotal-label">Subtotal</span>
                                                        <span className="subtotal-valor">
                                                            R$ {produto ? (produto.preco * item.quantidade).toFixed(2) : '0.00'}
                                                        </span>
                                                    </div>
                                                </div>
                                                <button
                                                    onClick={() => removerItem(item.produtoId)}
                                                    className="btn-remover-item"
                                                    aria-label="Remover item"
                                                >
                                                    <IconeDelete />
                                                </button>
                                            </div>
                                        );
                                    })}
                                </div>
                            )}
                        </div>

                        {/* Pagamento Section */}
                        <div className="pagamento-section">
                            <div className="section-header">
                                <h3>Pagamento</h3>
                            </div>
                            <div className="pagamento-opcoes">
                                <button
                                    onClick={() => setPagamento('dinheiro')}
                                    className={`pagamento-btn ${pagamento === 'dinheiro' ? 'selected' : ''}`}
                                >
                                    <IconeDinheiro />
                                    <span>Dinheiro</span>
                                </button>
                                <button
                                    onClick={() => setPagamento('cartao_credito')}
                                    className={`pagamento-btn ${pagamento === 'cartao_credito' ? 'selected' : ''}`}
                                >
                                    <IconeCartao />
                                    <span>Cartão</span>
                                </button>
                                <button
                                    onClick={() => setPagamento('pix')}
                                    className={`pagamento-btn ${pagamento === 'pix' ? 'selected' : ''}`}
                                >
                                    <IconePix />
                                    <span>PIX</span>
                                </button>
                            </div>
                        </div>

                        {/* Resumo Venda */}
                        <div className="resumo-venda">
                            <div className="resumo-linha">
                                <span className="resumo-label">Subtotal</span>
                                <span className="resumo-valor">R$ {calcularTotal().toFixed(2)}</span>
                            </div>
                            <div className="resumo-linha">
                                <span className="resumo-label">Desconto</span>
                                <span className="resumo-valor">R$ 0,00</span>
                            </div>
                            <div className="resumo-linha total">
                                <span className="resumo-label">Total</span>
                                <span className="resumo-valor">R$ {calcularTotal().toFixed(2)}</span>
                            </div>
                        </div>
                    </div>

                    {/* Botões de Ação - Ficam fixos no final */}
                    <div className="acao-botoes">
                        <button
                            onClick={handleFinalizarVenda}
                            disabled={carregando || itensVenda.length === 0}
                            className={`btn-finalizar ${itensVenda.length === 0 ? 'disabled' : ''}`}
                        >
                            {carregando ? 'Processando...' : 'Finalizar Venda'}
                        </button>
                    </div>
                </div>
            </div>

            <footer className="pdv-footer">
                <div className="footer-content">
                    <span className="footer-text">© 2025 MercadoSys - Sistema de Gestão para Mercadinhos</span>
                    <div className="footer-atalhos">
                        <span className="atalho">F2: Scanner</span>
                        <span className="atalho">F3: Finalizar</span>
                        <span className="atalho">F4: Limpar</span>
                        <span className="atalho">F5: Atualizar</span>
                    </div>
                </div>
            </footer>
        </div>
    );
};

export default PdvPage;