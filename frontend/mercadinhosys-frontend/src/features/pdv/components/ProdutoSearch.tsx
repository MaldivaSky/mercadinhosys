import React, { useState, useEffect, useRef } from 'react';
import { Search, Barcode, Package, Camera, AlertCircle } from 'lucide-react';
import { Produto } from '../../../types';
import { pdvService } from '../pdvService';
import BarcodeScanner from './BarcodeScanner';

interface ProdutoSearchProps {
    onProdutoSelecionado: (produto: Produto) => void;
}

const ProdutoSearch: React.FC<ProdutoSearchProps> = ({ onProdutoSelecionado }) => {
    const [query, setQuery] = useState('');
    const [resultados, setResultados] = useState<Produto[]>([]);
    const [loading, setLoading] = useState(false);
    const [erro, setErro] = useState<string | null>(null);
    const [scannerAberto, setScannerAberto] = useState(false);
    const inputRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        // Só buscar se tiver digitado algo
        if (!query.trim()) {
            setResultados([]);
            setErro(null);
            return;
        }

        const buscarProdutos = async () => {
            setLoading(true);
            setErro(null);
            
            try {
                // Se for código numérico LONGO (13 dígitos - EAN), buscar por código de barras
                if (/^\d{13}$/.test(query.trim())) {
                    const produto = await pdvService.buscarPorCodigoBarras(query.trim());
                    if (produto) {
                        const validacao = await pdvService.validarProduto({
                            produto_id: produto.id,
                            quantidade: 1
                        });

                        if (validacao.valido) {
                            onProdutoSelecionado(validacao.produto);
                            setQuery('');
                            setResultados([]);
                        } else {
                            setErro(validacao.mensagem || 'Produto indisponível');
                        }
                    } else {
                        setErro('Código de barras não encontrado');
                    }
                } else {
                    // Buscar por nome, marca, categoria
                    const produtos = await pdvService.buscarProduto(query);
                    console.log('📦 Produtos encontrados:', produtos.length, produtos);
                    
                    if (Array.isArray(produtos)) {
                        setResultados(produtos.slice(0, 20));
                    } else {
                        console.error('❌ Resposta inválida da API:', produtos);
                        setErro('Erro ao processar resposta da API');
                        setResultados([]);
                    }
                }
            } catch (error: any) {
                console.error('❌ Erro ao buscar produtos:', error);
                
                // Mensagens de erro mais específicas
                if (error.code === 'ERR_NETWORK') {
                    setErro('⚠️ Servidor offline. Verifique se o backend está rodando.');
                } else if (error.response?.status === 401) {
                    setErro('🔒 Sessão expirada. Faça login novamente.');
                } else if (error.response?.status === 404) {
                    setErro('❌ Endpoint não encontrado. Verifique a configuração da API.');
                } else {
                    setErro(error.response?.data?.error || error.message || 'Erro ao buscar produtos');
                }
                
                setResultados([]);
            } finally {
                setLoading(false);
            }
        };

        const debounce = setTimeout(buscarProdutos, 200);
        return () => clearTimeout(debounce);
    }, [query, onProdutoSelecionado]);

    // Handler para scan de código de barras
    const handleScanCodigo = async (codigo: string) => {
        setScannerAberto(false);
        setQuery(codigo);
    };

    // Handler para click em produto da lista
    const handleProdutoClick = async (produto: Produto) => {
        setErro(null);
        
        try {
            // Validar produto antes de adicionar
            const validacao = await pdvService.validarProduto({
                produto_id: produto.id,
                quantidade: 1
            });

            if (validacao.valido) {
                onProdutoSelecionado(validacao.produto);
                setQuery('');
                setResultados([]);
                inputRef.current?.focus();
            } else {
                setErro(validacao.mensagem || 'Produto indisponível');
            }
        } catch (error: any) {
            setErro(error.response?.data?.error || 'Erro ao validar produto');
        }
    };

    return (
        <div className="relative">
            {/* Barra de Busca com Botões */}
            <div className="flex items-center space-x-2 mb-4">
                {/* Botão Scanner de Câmera */}
                <button
                    onClick={() => setScannerAberto(true)}
                    className="p-3 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-lg hover:from-blue-600 hover:to-blue-700 shadow-lg transition"
                    title="Abrir scanner de código de barras"
                >
                    <Camera className="w-5 h-5" />
                </button>

                {/* Campo de Busca */}
                <div className="flex-1 relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                        ref={inputRef}
                        type="text"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder="Buscar por nome, marca, código de barras..."
                        className="w-full pl-10 pr-4 py-3 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-800 dark:text-white"
                        autoFocus
                    />

                    {loading && (
                        <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-500"></div>
                        </div>
                    )}
                </div>
            </div>

            {/* Mensagem de Erro */}
            {erro && (
                <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                    <div className="flex items-center space-x-2">
                        <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400" />
                        <p className="text-sm text-red-700 dark:text-red-400">{erro}</p>
                    </div>
                </div>
            )}

            {/* Lista de Resultados */}
            {resultados.length > 0 && (
                <div className="absolute z-50 w-full mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-2xl max-h-96 overflow-y-auto">
                    {resultados.map((produto) => (
                        <div
                            key={produto.id}
                            onClick={() => handleProdutoClick(produto)}
                            className="p-4 hover:bg-blue-50 dark:hover:bg-blue-900/20 cursor-pointer border-b border-gray-100 dark:border-gray-700 last:border-b-0 transition"
                        >
                            <div className="flex items-center justify-between">
                                <div className="flex-1">
                                    <div className="flex items-center space-x-3">
                                        <div className="w-12 h-12 bg-gradient-to-br from-blue-100 to-blue-200 dark:from-blue-900 dark:to-blue-800 rounded-lg flex items-center justify-center">
                                            <Package className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                                        </div>
                                        <div>
                                            <h4 className="font-semibold text-gray-800 dark:text-white">
                                                {produto.nome}
                                            </h4>
                                            <div className="flex items-center space-x-2 mt-1">
                                                <span className="text-xs px-2 py-0.5 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 rounded">
                                                    {produto.codigo_barras}
                                                </span>
                                                <span className="text-xs px-2 py-0.5 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded">
                                                    {produto.categoria}
                                                </span>
                                                {produto.marca && (
                                                    <span className="text-xs px-2 py-0.5 bg-purple-100 dark:bg-purple-900 text-purple-700 dark:text-purple-300 rounded">
                                                        {produto.marca}
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div className="text-right ml-4">
                                    <p className="font-bold text-xl text-gray-800 dark:text-white">
                                        R$ {(produto.preco_venda || 0).toFixed(2)}
                                    </p>
                                    <div className="flex items-center justify-end space-x-2 mt-1">
                                        <span className={`text-xs px-2 py-0.5 rounded ${
                                            (produto.quantidade_estoque || 0) > 10
                                                ? 'bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300'
                                                : (produto.quantidade_estoque || 0) > 0
                                                ? 'bg-yellow-100 dark:bg-yellow-900 text-yellow-700 dark:text-yellow-300'
                                                : 'bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-300'
                                        }`}>
                                            Estoque: {produto.quantidade_estoque || 0}
                                        </span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* Dica de Uso */}
            <div className="mt-3 flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
                <div className="flex items-center space-x-4">
                    <span className="flex items-center space-x-1">
                        <Search className="w-3 h-3" />
                        <span>Busca por nome, marca, categoria</span>
                    </span>
                    <span className="flex items-center space-x-1">
                        <Barcode className="w-3 h-3" />
                        <span>Código de barras automático</span>
                    </span>
                </div>
                <span className="flex items-center space-x-1">
                    <Camera className="w-3 h-3" />
                    <span>Scanner disponível</span>
                </span>
            </div>

            {/* Modal Scanner */}
            {scannerAberto && (
                <BarcodeScanner
                    onScan={handleScanCodigo}
                    onClose={() => setScannerAberto(false)}
                />
            )}
        </div>
    );
};

export default ProdutoSearch;