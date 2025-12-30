import React, { useState, useEffect, useRef } from 'react';
import { api } from '../../services/api';
import iconPix from '../../assets/iconPix.png';

interface Product {
    id: string;
    name: string;
    barcode?: string;
    price: number;
    stock: number;
    isBulk?: boolean;
    unit?: string;
}

interface CartItem {
    id: string;
    productId: string;
    name: string;
    quantity: number;
    price: number;
    total: number;
    isBulk?: boolean;
    unit?: string;
}

const PdvPage: React.FC = () => {
    // Estados principais
    const [barcodeInput, setBarcodeInput] = useState('');
    const [cart, setCart] = useState<CartItem[]>([]);
    const [searchTerm, setSearchTerm] = useState('');
    const [filterTerm, setFilterTerm] = useState('');

    // Estados para modais
    const [showProductModal, setShowProductModal] = useState(false);
    const [showQuickAddModal, setShowQuickAddModal] = useState(false);
    const [showBulkModal, setShowBulkModal] = useState(false);
    const [filteredProducts, setFilteredProducts] = useState<Product[]>([]);
    const [selectedBulkProduct, setSelectedBulkProduct] = useState<Product | null>(null);
    const [bulkQuantity, setBulkQuantity] = useState('');

    // Estado para novo produto
    const [newProduct, setNewProduct] = useState({
        name: '',
        barcode: '',
        price: '',
        stock: '0',
        isBulk: false,
        unit: 'un'
    });

    // Estados para checkout
    const [showCheckoutModal, setShowCheckoutModal] = useState(false);
    const [paymentMethod, setPaymentMethod] = useState('money');
    const [cashReceived, setCashReceived] = useState('');
    const [saleChange, setSaleChange] = useState(0);
    const [isProcessingSale, setIsProcessingSale] = useState(false);
    const [discount, setDiscount] = useState(0); // Percentual de desconto
    const [discountValue, setDiscountValue] = useState(0); // Valor em R$

    // Referência para foco automático
    const barcodeInputRef = useRef<HTMLInputElement>(null);

    // Focar no input do código de barras ao carregar
    useEffect(() => {
        if (barcodeInputRef.current) {
            barcodeInputRef.current.focus();
        }
    }, []);

    // Buscar produto pelo código de barras
    const handleBarcodeSubmit = async () => {
        if (!barcodeInput.trim()) return;

        try {
            console.log('Buscando produto com código:', barcodeInput);
            const response = await api.get(`/api/produtos/barcode/${barcodeInput}`);

            // Verificar se recebemos dados válidos
            if (!response.data || !response.data.id) {
                throw new Error('Produto não encontrado no sistema');
            }

            addToCart(response.data);
            setBarcodeInput('');

            if (barcodeInputRef.current) {
                barcodeInputRef.current.focus();
            }

        } catch (error: unknown) {
            const apiError = error as { message?: string; code?: string };
            console.error('Erro ao buscar produto:', error);

            // Mensagem amigável para o usuário
            if ((apiError.message ?? '').includes('Network Error') || apiError.code === 'ERR_NETWORK') {
                alert('⚠️ Backend offline. Usando dados de exemplo para teste.\n\nTente usar a busca manual ou cadastrar produto.');
            } else {
                alert(`Produto não encontrado: ${barcodeInput}\n\nUse a busca manual para cadastrar este produto.`);
            }

            setBarcodeInput('');

            // Focar na busca manual
            const searchInput = document.querySelector('input[placeholder*="Buscar por nome"]') as HTMLInputElement;
            if (searchInput) {
                searchInput.focus();
                searchInput.value = barcodeInput;
                setSearchTerm(barcodeInput);
            }
        }
    };

    // Busca manual de produtos
    const handleManualSearch = async () => {
        if (!searchTerm.trim()) {
            alert('Digite algo para buscar');
            return;
        }

        console.log(`🔍 Buscando: "${searchTerm}"`);

        try {
            // URL CORRETA: /api/produtos/search
            const response = await api.get(`/api/produtos/search?q=${searchTerm}`);

            console.log('📊 Resultados da API:', response.data);

            if (response.data.length === 0) {
                // Nenhum produto encontrado
                const shouldAdd = window.confirm(
                    `Nenhum produto encontrado para "${searchTerm}".\nDeseja cadastrar um novo produto?`
                );

                if (shouldAdd) {
                    setNewProduct(prev => ({
                        ...prev,
                        name: searchTerm,
                        barcode: searchTerm.match(/^\d+$/) ? searchTerm : ''
                    }));
                    setShowQuickAddModal(true);
                }

            } else if (response.data.length === 1) {
                // Apenas um produto
                addToCart(response.data[0]);
                setSearchTerm('');

            } else {
                // Múltiplos produtos
                setFilteredProducts(response.data);
                setShowProductModal(true);
                setSearchTerm('');
            }

        } catch (error: unknown) {
            const apiError = error as { code?: string; message?: string; config?: { url?: string }; response?: { status?: number; data?: { error?: string } } };
            console.error('❌ Erro na busca:', error);

            // Mostrar URL que tentou acessar
            console.error('URL tentada:', apiError.config?.url);

            if (apiError.code === 'ERR_NETWORK' || (apiError.message ?? '').includes('Network Error')) {
                alert(`Erro de conexão com o backend.\n\nVerifique se o Flask está rodando na porta 5000.\nURL: ${apiError.config?.url}`);
            } else if (apiError.response?.status === 404) {
                alert(`Rota não encontrada (404).\n\nBackend não tem a rota: ${apiError.config?.url}`);
            } else {
                alert(`Erro: ${apiError.response?.data?.error || apiError.message}`);
            }
        }
    };

    // Adicionar produto ao carrinho
    const addToCart = (product: Product) => {
        // Verificar se é produto a granel
        if (product.isBulk) {
            setSelectedBulkProduct(product);
            setShowBulkModal(true);
            return;
        }

        // Verificar se produto já está no carrinho
        const existingItem = cart.find(item => item.productId === product.id);

        if (existingItem) {
            // Atualizar quantidade se já estiver no carrinho
            const updatedCart = cart.map(item =>
                item.productId === product.id
                    ? {
                        ...item,
                        quantity: item.quantity + 1,
                        total: (item.quantity + 1) * item.price
                    }
                    : item
            );
            setCart(updatedCart);
        } else {
            // Adicionar novo item ao carrinho
            const newItem: CartItem = {
                id: Date.now().toString(),
                productId: product.id,
                name: product.name,
                quantity: 1,
                price: product.price,
                total: product.price,
                isBulk: product.isBulk,
                unit: product.unit
            };
            setCart([...cart, newItem]);
        }
    };

    // Adicionar produto a granel com quantidade específica
    const addBulkProduct = () => {
        if (!selectedBulkProduct || !bulkQuantity) return;

        const quantity = parseFloat(bulkQuantity);
        if (isNaN(quantity) || quantity <= 0) {
            alert('Quantidade inválida');
            return;
        }

        const newItem: CartItem = {
            id: Date.now().toString(),
            productId: selectedBulkProduct.id,
            name: `${selectedBulkProduct.name} (${bulkQuantity}${selectedBulkProduct.unit})`,
            quantity: 1,
            price: selectedBulkProduct.price * quantity,
            total: selectedBulkProduct.price * quantity,
            isBulk: true,
            unit: selectedBulkProduct.unit
        };

        setCart([...cart, newItem]);
        setShowBulkModal(false);
        setSelectedBulkProduct(null);
        setBulkQuantity('');
    };

    // Finalizar venda
    const handleCheckout = async () => {
        if (cart.length === 0) {
            alert('Carrinho vazio! Adicione produtos antes de finalizar.');
            return;
        }

        // Calcular totais com desconto
        const discountAmount = (subtotal * discount) / 100;
        const finalTotal = subtotal - discountAmount;

        // VALIDAÇÃO: Se for dinheiro, verificar se valor recebido é suficiente
        if (paymentMethod === 'money') {
            const received = parseFloat(cashReceived) || 0;
            if (received < finalTotal) {
                alert(`Valor recebido insuficiente!\nTotal: R$ ${finalTotal.toFixed(2)}\nRecebido: R$ ${received.toFixed(2)}\nFaltam: R$ ${(finalTotal - received).toFixed(2)}`);
                return;
            }
        }

        setIsProcessingSale(true);

        try {
            // Preparar dados para enviar ao backend
            const saleData = {
                items: cart.map(item => ({
                    productId: item.productId,
                    quantity: item.quantity,
                    price: item.price,
                    total: item.total
                })),
                subtotal: subtotal,
                desconto: discountAmount, // Em português para o backend
                total: finalTotal,
                paymentMethod: paymentMethod,
                cashReceived: paymentMethod === 'money' ? parseFloat(cashReceived) || 0 : 0,
                change: saleChange
            };

            console.log('📤 Enviando dados da venda:', saleData);

            // Chamar API do backend
            const response = await api.post('/api/vendas', saleData);

            console.log('✅ Resposta do backend:', response.data);

            // Sucesso - mostrar mensagem
            alert(`✅ Venda finalizada com sucesso!\n\nCódigo: ${response.data.venda?.codigo || 'N/A'}\nTotal: R$ ${finalTotal.toFixed(2)}${discount > 0 ? `\nDesconto: ${discount}% (-R$ ${discountAmount.toFixed(2)})` : ''}`);

            // Limpar tudo
            setCart([]);
            setShowCheckoutModal(false);
            setCashReceived('');
            setSaleChange(0);
            setDiscount(0);
            setDiscountValue(0);

            // Focar no scanner novamente
            if (barcodeInputRef.current) {
                barcodeInputRef.current.focus();
            }

        } catch (error: any) {
            console.error('❌ Erro ao finalizar venda:', error);

            let errorMessage = 'Erro ao finalizar venda. Tente novamente.';

            if (error.response?.data?.error) {
                errorMessage = error.response.data.error;
            } else if (error.message.includes('Network Error')) {
                errorMessage = 'Erro de conexão com o servidor. Verifique se o backend está rodando.';
            }

            alert(`❌ ${errorMessage}`);

        } finally {
            setIsProcessingSale(false);
        }
    };

    // Calcular troco quando digitar valor recebido
    const calculateChange = (received: string) => {
        const receivedNum = parseFloat(received) || 0;
        const discountAmount = (subtotal * discount) / 100;
        const finalTotal = subtotal - discountAmount;
        const change = receivedNum - finalTotal;
        setCashReceived(received);
        setSaleChange(change > 0 ? change : 0);
    };

    // Função para aplicar desconto por percentual
    const applyDiscount = (percent: number) => {
        setDiscount(percent);
        setDiscountValue((subtotal * percent) / 100);

        // Recalcular troco se já tiver valor recebido
        if (cashReceived) {
            calculateChange(cashReceived);
        }
    };


    // Cadastrar produto rapidamente
    const handleQuickAddProduct = async () => {
        // Validações básicas
        if (!newProduct.name.trim()) {
            alert('Nome do produto é obrigatório');
            return;
        }

        if (!newProduct.price || parseFloat(newProduct.price) <= 0) {
            alert('Preço inválido');
            return;
        }

        try {
            const productData = {
                name: newProduct.name,
                barcode: newProduct.barcode || null,
                price: parseFloat(newProduct.price),
                stock: parseInt(newProduct.stock) || 0,
                isBulk: newProduct.isBulk,
                unit: newProduct.isBulk ? newProduct.unit : 'un'
            };

            const response = await api.post('/api/produtos/quick-add', productData);

            // Adicionar ao carrinho
            addToCart(response.data);

            // Resetar form e fechar modais
            setNewProduct({
                name: '',
                barcode: '',
                price: '',
                stock: '0',
                isBulk: false,
                unit: 'un'
            });

            setShowQuickAddModal(false);
            setShowProductModal(false);

            // Focar no input do código de barras
            if (barcodeInputRef.current) {
                barcodeInputRef.current.focus();
            }

        } catch (error) {
            console.error('Erro ao cadastrar produto:', error);
            alert('Erro ao cadastrar produto. Tente novamente.');
        }
    };

    // Filtrar produtos no modal
    const getFilteredModalProducts = () => {
        if (!filterTerm.trim()) return filteredProducts;

        return filteredProducts.filter(product =>
            product.name.toLowerCase().includes(filterTerm.toLowerCase()) ||
            (product.barcode && product.barcode.includes(filterTerm))
        );
    };

    // Calcular totais
    const subtotal = cart.reduce((sum, item) => sum + item.total, 0);
    const totalItems = cart.reduce((sum, item) => sum + item.quantity, 0);

    // Remover item do carrinho
    const removeFromCart = (itemId: string) => {
        setCart(cart.filter(item => item.id !== itemId));
    };

    // Atualizar quantidade no carrinho
    const updateQuantity = (itemId: string, newQuantity: number) => {
        if (newQuantity < 1) {
            removeFromCart(itemId);
            return;
        }

        const updatedCart = cart.map(item =>
            item.id === itemId
                ? {
                    ...item,
                    quantity: newQuantity,
                    total: newQuantity * item.price
                }
                : item
        );

        setCart(updatedCart);
    };

    

    return (
        <div className="min-h-screen bg-gray-100 p-4">
            <div className="max-w-7xl mx-auto">
                {/* Cabeçalho */}
                <header className="mb-6">
                    <h1 className="text-2xl font-bold text-gray-800">Ponto de Venda (PDV)</h1>
                    <p className="text-gray-600">Sistema de checkout para vendas rápidas</p>
                </header>

                <div className="flex gap-6">
                    {/* Coluna esquerda - Entrada de produtos */}
                    <div className="flex-1 bg-white rounded-lg shadow p-6">
                        {/* Scanner de código de barras */}
                        <div className="mb-8">
                            <h2 className="text-lg font-semibold mb-4">Scanner de Código de Barras</h2>
                            <div className="flex gap-2">
                                <input
                                    ref={barcodeInputRef}
                                    type="text"
                                    value={barcodeInput}
                                    onChange={(e) => setBarcodeInput(e.target.value)}
                                    onKeyPress={(e) => e.key === 'Enter' && handleBarcodeSubmit()}
                                    placeholder="Digite ou escaneie o código de barras"
                                    className="flex-1 p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                />
                                <button
                                    onClick={handleBarcodeSubmit}
                                    className="bg-blue-500 hover:bg-blue-600 text-white px-6 py-3 rounded-lg font-medium transition"
                                >
                                    Adicionar
                                </button>
                            </div>
                        </div>

                        {/* Busca manual de produtos */}
                        <div className="mb-8">
                            <h2 className="text-lg font-semibold mb-4">Busca Manual de Produtos</h2>
                            <div className="flex gap-2">
                                <input
                                    type="text"
                                    value={searchTerm}
                                    onChange={(e) => setSearchTerm(e.target.value)}
                                    onKeyPress={(e) => e.key === 'Enter' && handleManualSearch()}
                                    placeholder="Buscar por nome ou código do produto..."
                                    className="flex-1 p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                />
                                <button
                                    onClick={handleManualSearch}
                                    className="bg-green-500 hover:bg-green-600 text-white px-6 py-3 rounded-lg font-medium transition"
                                >
                                    Buscar
                                </button>
                            </div>
                            <p className="text-sm text-gray-500 mt-2">
                                Use este campo para buscar produtos sem código de barras ou cadastrar novos produtos
                            </p>
                        </div>

                        {/* Carrinho de compras */}
                        <div>
                            <h2 className="text-lg font-semibold mb-4">Carrinho de Compras</h2>

                            {cart.length === 0 ? (
                                <div className="text-center py-12 border-2 border-dashed border-gray-300 rounded-lg">
                                    <p className="text-gray-500">Carrinho vazio</p>
                                    <p className="text-sm text-gray-400 mt-2">
                                        Use o scanner ou a busca manual para adicionar produtos
                                    </p>
                                </div>
                            ) : (
                                <div className="space-y-3">
                                    {cart.map(item => (
                                        <div key={item.id} className="border border-gray-200 rounded-lg p-4 flex items-center justify-between hover:bg-gray-50">
                                            <div className="flex-1">
                                                <h3 className="font-medium">{item.name}</h3>
                                                <p className="text-sm text-gray-600">
                                                    R$ {item.price.toFixed(2)} {item.isBulk ? '' : 'un'}
                                                </p>
                                            </div>

                                            <div className="flex items-center gap-4">
                                                <div className="flex items-center gap-2">
                                                    <button
                                                        onClick={() => updateQuantity(item.id, item.quantity - 1)}
                                                        className="w-8 h-8 flex items-center justify-center border border-gray-300 rounded hover:bg-gray-100"
                                                    >
                                                        -
                                                    </button>
                                                    <span className="w-12 text-center">{item.quantity}</span>
                                                    <button
                                                        onClick={() => updateQuantity(item.id, item.quantity + 1)}
                                                        className="w-8 h-8 flex items-center justify-center border border-gray-300 rounded hover:bg-gray-100"
                                                    >
                                                        +
                                                    </button>
                                                </div>

                                                <span className="font-semibold w-24 text-right">
                                                    R$ {item.total.toFixed(2)}
                                                </span>

                                                <button
                                                    onClick={() => removeFromCart(item.id)}
                                                    className="text-red-500 hover:text-red-700"
                                                >
                                                    ×
                                                </button>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Coluna direita - Resumo e pagamento */}
                    <div className="w-80 bg-white rounded-lg shadow p-6">
                        {/* Informações do usuário */}
                        <div className="mb-6 pb-6 border-b">
                            <div className="flex items-center justify-between">
                                <div>
                                    <h3 className="font-semibold">Rafael Silva</h3>
                                    <p className="text-sm text-gray-600">Gerente</p>
                                </div>
                                <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm">
                                    Online
                                </span>
                            </div>
                        </div>

                        {/* Resumo pendente */}
                        <div className="mb-6 pb-6 border-b">
                            <h3 className="font-semibold mb-2">Pendente</h3>
                            <p className="text-2xl font-bold">{totalItems} itens</p>
                        </div>

                        {/* Resumo da venda */}
                        <div className="mb-6 pb-6 border-b">
                            <h3 className="font-semibold mb-4">Resumo da Venda</h3>

                            <div className="space-y-3">
                                <div className="flex justify-between">
                                    <span>Subtotal</span>
                                    <span className="font-semibold">R$ {subtotal.toFixed(2)}</span>
                                </div>

                                <div className="flex justify-between">
                                    <span>Desconto</span>
                                    <span>0%</span>
                                </div>

                                <div className="pt-3 border-t">
                                    <div className="flex justify-between text-lg font-bold">
                                        <span>TOTAL</span>
                                        <span>R$ {subtotal.toFixed(2)}</span>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Método de pagamento */}
                        <div>
                            
                            <button
                                onClick={() => cart.length === 0 ? null : setShowCheckoutModal(true)}
                                disabled={cart.length === 0}
                                className={`w-full mt-6 py-3 rounded-lg font-semibold ${cart.length === 0 ? 'bg-gray-300 cursor-not-allowed' : 'bg-green-500 hover:bg-green-600 text-white'}`}
                            >
                                {cart.length === 0 ? 'Carrinho Vazio' : 'Finalizar Venda'}
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            {/* Modal de Seleção de Produtos */}
            {showProductModal && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-lg w-full max-w-2xl max-h-[80vh] flex flex-col">
                        <div className="p-6 border-b">
                            <h3 className="text-xl font-bold">Selecionar Produto</h3>
                            <input
                                type="text"
                                placeholder="Digite para filtrar produtos..."
                                className="w-full p-3 border border-gray-300 rounded-lg mt-4"
                                value={filterTerm}
                                onChange={(e) => setFilterTerm(e.target.value)}
                            />
                        </div>

                        <div className="flex-1 overflow-y-auto p-2">
                            {getFilteredModalProducts().length === 0 ? (
                                <div className="text-center py-8 text-gray-500">
                                    Nenhum produto encontrado
                                </div>
                            ) : (
                                getFilteredModalProducts().map(product => (
                                    <div
                                        key={product.id}
                                        className="p-4 border-b hover:bg-blue-50 cursor-pointer"
                                        onClick={() => {
                                            addToCart(product);
                                            setShowProductModal(false);
                                            setFilterTerm('');
                                        }}
                                    >
                                        <div className="flex justify-between items-center">
                                            <div>
                                                <h4 className="font-medium">{product.name}</h4>
                                                <div className="text-sm text-gray-600">
                                                    <span>Código: {product.barcode || 'Sem código'} | </span>
                                                    <span>Preço: R$ {product.price.toFixed(2)} | </span>
                                                    <span>Estoque: {product.stock} {product.isBulk ? product.unit : 'un'}</span>
                                                    {product.isBulk && <span className="ml-2 px-2 py-1 bg-yellow-100 text-yellow-800 text-xs rounded">A Granel</span>}
                                                </div>
                                            </div>
                                            <button className="text-blue-500 hover:text-blue-700 font-medium">
                                                Adicionar
                                            </button>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>

                        <div className="p-6 border-t flex justify-between">
                            <button
                                onClick={() => {
                                    setShowProductModal(false);
                                    setFilterTerm('');
                                }}
                                className="px-6 py-3 border border-gray-300 rounded-lg hover:bg-gray-50"
                            >
                                Cancelar
                            </button>
                            <button
                                onClick={() => {
                                    setShowProductModal(false);
                                    setShowQuickAddModal(true);
                                    setFilterTerm('');
                                }}
                                className="px-6 py-3 bg-green-500 hover:bg-green-600 text-white rounded-lg font-medium"
                            >
                                + Cadastrar Novo Produto
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Modal de Cadastro Rápido */}
            {showQuickAddModal && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-lg w-full max-w-md">
                        <div className="p-6 border-b">
                            <h3 className="text-xl font-bold">Cadastrar Produto Rápido</h3>
                            <p className="text-sm text-gray-600 mt-1">Produto será salvo e adicionado ao carrinho</p>
                        </div>

                        <div className="p-6 space-y-4">
                            <div>
                                <label className="block text-sm font-medium mb-1">Nome do Produto *</label>
                                <input
                                    type="text"
                                    className="w-full p-3 border border-gray-300 rounded-lg"
                                    value={newProduct.name}
                                    onChange={(e) => setNewProduct({ ...newProduct, name: e.target.value })}
                                    placeholder="Ex: Arroz 5kg"
                                />
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium mb-1">Preço (R$) *</label>
                                    <input
                                        type="number"
                                        step="0.01"
                                        min="0.01"
                                        className="w-full p-3 border border-gray-300 rounded-lg"
                                        value={newProduct.price}
                                        onChange={(e) => setNewProduct({ ...newProduct, price: e.target.value })}
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-medium mb-1">Estoque Inicial</label>
                                    <input
                                        type="number"
                                        min="0"
                                        className="w-full p-3 border border-gray-300 rounded-lg"
                                        value={newProduct.stock}
                                        onChange={(e) => setNewProduct({ ...newProduct, stock: e.target.value })}
                                    />
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm font-medium mb-1">Código de Barras</label>
                                <input
                                    type="text"
                                    className="w-full p-3 border border-gray-300 rounded-lg"
                                    value={newProduct.barcode}
                                    onChange={(e) => setNewProduct({ ...newProduct, barcode: e.target.value })}
                                    placeholder="Opcional - preenchido automaticamente"
                                />
                            </div>

                            <div className="flex items-center">
                                <input
                                    type="checkbox"
                                    id="isBulk"
                                    checked={newProduct.isBulk}
                                    onChange={(e) => setNewProduct({ ...newProduct, isBulk: e.target.checked })}
                                    className="h-5 w-5 text-blue-500 rounded"
                                />
                                <label htmlFor="isBulk" className="ml-2 text-sm font-medium">
                                    Produto a granel (vende por peso)
                                </label>
                            </div>

                            {newProduct.isBulk && (
                                <div>
                                    <label className="block text-sm font-medium mb-1">Unidade de Medida</label>
                                    <select
                                        className="w-full p-3 border border-gray-300 rounded-lg"
                                        value={newProduct.unit}
                                        onChange={(e) => setNewProduct({ ...newProduct, unit: e.target.value })}
                                    >
                                        <option value="kg">Quilo (kg)</option>
                                        <option value="g">Grama (g)</option>
                                        <option value="un">Unidade</option>
                                    </select>
                                </div>
                            )}
                        </div>

                        <div className="p-6 border-t flex justify-end gap-3">
                            <button
                                onClick={() => {
                                    setShowQuickAddModal(false);
                                    setNewProduct({
                                        name: '',
                                        barcode: '',
                                        price: '',
                                        stock: '0',
                                        isBulk: false,
                                        unit: 'un'
                                    });
                                }}
                                className="px-6 py-3 border border-gray-300 rounded-lg hover:bg-gray-50"
                            >
                                Cancelar
                            </button>
                            <button
                                onClick={handleQuickAddProduct}
                                className="px-6 py-3 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-medium"
                            >
                                Salvar e Adicionar
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Modal para Produto a Granel */}
            {showBulkModal && selectedBulkProduct && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-lg w-full max-w-sm p-6">
                        <h3 className="text-xl font-bold mb-2">Produto a Granel</h3>
                        <p className="text-gray-600 mb-6">
                            {selectedBulkProduct.name} - R$ {selectedBulkProduct.price.toFixed(2)}/{selectedBulkProduct.unit}
                        </p>

                        <div className="mb-6">
                            <label className="block text-sm font-medium mb-2">
                                Quantidade ({selectedBulkProduct.unit})
                            </label>
                            <input
                                type="number"
                                step="0.001"
                                min="0.001"
                                className="w-full p-3 border border-gray-300 rounded-lg text-center text-xl"
                                value={bulkQuantity}
                                onChange={(e) => setBulkQuantity(e.target.value)}
                                placeholder="Ex: 0.500"
                                autoFocus
                            />
                        </div>

                        <div className="flex gap-3">
                            <button
                                onClick={() => {
                                    setShowBulkModal(false);
                                    setSelectedBulkProduct(null);
                                    setBulkQuantity('');
                                }}
                                className="flex-1 px-4 py-3 border border-gray-300 rounded-lg hover:bg-gray-50"
                            >
                                Cancelar
                            </button>
                            <button
                                onClick={addBulkProduct}
                                className="flex-1 px-4 py-3 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-medium"
                            >
                                Adicionar
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Modal de Finalização de Venda */}
            {showCheckoutModal && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-lg w-full max-w-md">
                        <div className="p-6 border-b">
                            <h3 className="text-xl font-bold">Finalizar Venda</h3>
                            <p className="text-sm text-gray-600">Resumo do pedido</p>
                        </div>

                        <div className="p-6">
                            {/* Resumo dos itens */}
                            <div className="mb-4">
                                <h4 className="font-semibold mb-2">Itens ({cart.length})</h4>
                                <div className="max-h-40 overflow-y-auto border rounded p-2">
                                    {cart.map(item => (
                                        <div key={item.id} className="flex justify-between py-1 border-b last:border-0">
                                            <span className="text-sm truncate max-w-[200px]">
                                                {item.quantity}x {item.name}
                                            </span>
                                            <span className="text-sm font-medium">
                                                R$ {item.total.toFixed(2)}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {/* Totais com desconto */}
                            <div className="space-y-3 mb-6">
                                <div className="flex justify-between">
                                    <span>Subtotal:</span>
                                    <span>R$ {subtotal.toFixed(2)}</span>
                                </div>

                                {/* Seção de desconto */}
                                <div className="border-t pt-3">
                                    <div className="flex items-center justify-between mb-2">
                                        <span className="font-medium">Desconto:</span>
                                        <div className="flex items-center gap-2">
                                            <button
                                                onClick={() => applyDiscount(0)}
                                                className={`px-3 py-1 text-sm border rounded ${discount === 0 ? 'bg-gray-200 font-semibold' : 'hover:bg-gray-100'}`}
                                            >
                                                0%
                                            </button>
                                            <button
                                                onClick={() => applyDiscount(5)}
                                                className={`px-3 py-1 text-sm border rounded ${discount === 5 ? 'bg-blue-100 border-blue-300 font-semibold' : 'hover:bg-gray-100'}`}
                                            >
                                                5%
                                            </button>
                                            <button
                                                onClick={() => applyDiscount(10)}
                                                className={`px-3 py-1 text-sm border rounded ${discount === 10 ? 'bg-blue-100 border-blue-300 font-semibold' : 'hover:bg-gray-100'}`}
                                            >
                                                10%
                                            </button>
                                            <div className="relative">
                                                <input
                                                    type="number"
                                                    min="0"
                                                    max="100"
                                                    value={discount}
                                                    onChange={(e) => {
                                                        const value = parseInt(e.target.value) || 0;
                                                        const finalValue = value > 100 ? 100 : value;
                                                        applyDiscount(finalValue);
                                                    }}
                                                    className="w-16 px-2 py-1 border rounded text-center"
                                                    placeholder="%"
                                                />
                                                <span className="absolute right-2 top-1/2 transform -translate-y-1/2 text-gray-500 text-sm">
                                                    %
                                                </span>
                                            </div>
                                        </div>
                                    </div>

                                    {discount > 0 && (
                                        <div className="flex justify-between text-red-600 bg-red-50 p-2 rounded">
                                            <span className="font-medium">Desconto aplicado:</span>
                                            <span className="font-semibold">
                                                - R$ {discountValue.toFixed(2)} ({discount}%)
                                            </span>
                                        </div>
                                    )}
                                </div>

                                {/* Total final */}
                                <div className="flex justify-between text-lg font-bold border-t pt-3">
                                    <span>TOTAL:</span>
                                    <span className="text-green-600">
                                        R$ {(subtotal - discountValue).toFixed(2)}
                                    </span>
                                </div>
                            </div>

                            {/* Método de pagamento com ícones */}
                            <div className="mb-6">
                                <label className="block text-sm font-medium mb-3">
                                    Método de Pagamento
                                </label>
                                <div className="grid grid-cols-4 gap-2">
                                    {/* Dinheiro */}
                                    <button
                                        type="button"
                                        onClick={() => setPaymentMethod('money')}
                                        className={`p-3 border rounded-lg flex flex-col items-center justify-center transition-all ${paymentMethod === 'money'
                                                ? 'bg-blue-500 text-white border-blue-500'
                                                : 'border-gray-300 hover:bg-gray-50'
                                            }`}
                                    >
                                        <svg className="w-6 h-6 mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                        </svg>
                                        <span className="text-xs font-medium">Dinheiro</span>
                                    </button>

                                    {/* Crédito */}
                                    <button
                                        type="button"
                                        onClick={() => setPaymentMethod('credit')}
                                        className={`p-3 border rounded-lg flex flex-col items-center justify-center transition-all ${paymentMethod === 'credit'
                                                ? 'bg-blue-500 text-white border-blue-500'
                                                : 'border-gray-300 hover:bg-gray-50'
                                            }`}
                                    >
                                        <svg className="w-6 h-6 mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
                                        </svg>
                                        <span className="text-xs font-medium">Crédito</span>
                                    </button>

                                    {/* Débito */}
                                    <button
                                        type="button"
                                        onClick={() => setPaymentMethod('debit')}
                                        className={`p-3 border rounded-lg flex flex-col items-center justify-center transition-all ${paymentMethod === 'debit'
                                                ? 'bg-blue-500 text-white border-blue-500'
                                                : 'border-gray-300 hover:bg-gray-50'
                                            }`}
                                    >
                                        <svg className="w-6 h-6 mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
                                        </svg>
                                        <span className="text-xs font-medium">Débito</span>
                                    </button>

                                    {/* PIX */}
                                    <button
                                        type="button"
                                        onClick={() => setPaymentMethod('pix')}
                                        className={`p-3 border rounded-lg flex flex-col items-center justify-center transition-all ${paymentMethod === 'pix'
                                                ? 'bg-blue-500 text-white border-blue-500'
                                                : 'border-gray-300 hover:bg-gray-50'
                                            }`}
                                    >
                                        <img src={iconPix} alt="PIX" className="w-6 h-6 mb-1" />
                                        <span className="text-xs font-medium">PIX</span>
                                    </button>
                                </div>
                            </div>

                            {/* Campo para valor recebido (se for dinheiro) */}
                            {paymentMethod === 'money' && (
                                <div className="mb-6">
                                    <label className="block text-sm font-medium mb-2">
                                        Valor Recebido (R$)
                                    </label>
                                    <div className="relative">
                                        <span className="absolute left-3 top-3 text-gray-500">R$</span>
                                        <input
                                            type="number"
                                            step="0.01"
                                            min={subtotal - discountValue}
                                            value={cashReceived}
                                            onChange={(e) => calculateChange(e.target.value)}
                                            className="w-full pl-10 p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                            placeholder="0,00"
                                            autoFocus
                                        />
                                    </div>

                                    {/* Mostrar troco ou valor faltante */}
                                    {saleChange > 0 ? (
                                        <div className="mt-2 p-3 bg-green-50 border border-green-200 rounded">
                                            <div className="flex justify-between items-center">
                                                <span className="font-medium text-green-800">Troco:</span>
                                                <span className="text-lg font-bold text-green-800">
                                                    R$ {saleChange.toFixed(2)}
                                                </span>
                                            </div>
                                        </div>
                                    ) : parseFloat(cashReceived) > 0 && parseFloat(cashReceived) < (subtotal - discountValue) ? (
                                        <div className="mt-2 p-3 bg-red-50 border border-red-200 rounded">
                                            <div className="flex justify-between items-center">
                                                <span className="font-medium text-red-800">Faltam:</span>
                                                <span className="text-lg font-bold text-red-800">
                                                    R$ {((subtotal - discountValue) - parseFloat(cashReceived)).toFixed(2)}
                                                </span>
                                            </div>
                                        </div>
                                    ) : null}
                                </div>
                            )}

                            {/* Botões de ação */}
                            <div className="flex gap-3">
                                <button
                                    onClick={() => {
                                        setShowCheckoutModal(false);
                                        setCashReceived('');
                                        setSaleChange(0);
                                        setDiscount(0);
                                        setDiscountValue(0);
                                    }}
                                    className="flex-1 px-4 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 transition"
                                >
                                    Cancelar
                                </button>
                                <button
                                    onClick={handleCheckout}
                                    disabled={
                                        isProcessingSale ||
                                        (paymentMethod === 'money' && (!cashReceived || parseFloat(cashReceived) < (subtotal - discountValue)))
                                    }
                                    className="flex-1 px-4 py-3 bg-green-500 hover:bg-green-600 text-white rounded-lg font-semibold transition disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    {isProcessingSale ? 'Processando...' : 'Confirmar Venda'}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default PdvPage;