import React, { useState, useEffect, useRef } from 'react';
import { Search, Barcode, Package } from 'lucide-react';
import { Produto } from '../../../types';
import { pdvService } from '../pdvService';

interface ProdutoSearchProps {
    onProdutoSelecionado: (produto: Produto) => void;
}

const ProdutoSearch: React.FC<ProdutoSearchProps> = ({ onProdutoSelecionado }) => {
    const [query, setQuery] = useState('');
    const [resultados, setResultados] = useState<Produto[]>([]);
    const [loading, setLoading] = useState(false);
    const [modoBarras, setModoBarras] = useState(false);
    const inputRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        if (modoBarras) {
            inputRef.current?.focus();
        }
    }, [modoBarras]);

    useEffect(() => {
        if (!query.trim()) {
            setResultados([]);
            return;
        }

        const buscarProdutos = async () => {
            setLoading(true);
            try {
                if (modoBarras && /^\d+$/.test(query)) {
                    const produto = await pdvService.buscarProdutoPorCodigo(query);
                    if (produto) {
                        onProdutoSelecionado(produto);
                        setQuery('');
                    }
                } else {
                    const produtos = await pdvService.buscarProduto(query);
                    setResultados(produtos.slice(0, 10));
                }
            } catch (error) {
                console.error('Erro ao buscar produtos:', error);
            } finally {
                setLoading(false);
            }
        };

        const debounce = setTimeout(buscarProdutos, 300);
        return () => clearTimeout(debounce);
    }, [query, modoBarras, onProdutoSelecionado]);

    const handleProdutoClick = (produto: Produto) => {
        onProdutoSelecionado(produto);
        setQuery('');
        setResultados([]);
        inputRef.current?.focus();
    };

    return (
        <div className="relative">
            <div className="flex items-center space-x-2 mb-4">
                <button
                    onClick={() => setModoBarras(!modoBarras)}
                    className={`p-2 rounded-lg ${modoBarras
                            ? 'bg-blue-500 text-white'
                            : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                        }`}
                >
                    <Barcode className="w-5 h-5" />
                </button>

                <div className="flex-1 relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                        ref={inputRef}
                        type="text"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder={
                            modoBarras
                                ? 'Digite o código de barras...'
                                : 'Buscar produto por nome ou código...'
                        }
                        className="w-full pl-10 pr-4 py-3 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        autoFocus
                    />

                    {loading && (
                        <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-500"></div>
                        </div>
                    )}
                </div>
            </div>

            {resultados.length > 0 && (
                <div className="absolute z-50 w-full mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg max-h-96 overflow-y-auto">
                    {resultados.map((produto) => (
                        <div
                            key={produto.id}
                            onClick={() => handleProdutoClick(produto)}
                            className="p-3 hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer border-b border-gray-100 dark:border-gray-700 last:border-b-0"
                        >
                            <div className="flex items-center justify-between">
                                <div className="flex-1">
                                    <div className="flex items-center space-x-3">
                                        <div className="w-10 h-10 bg-gray-100 dark:bg-gray-700 rounded flex items-center justify-center">
                                            <Package className="w-6 h-6 text-gray-500" />
                                        </div>
                                        <div>
                                            <h4 className="font-medium text-gray-800 dark:text-white">
                                                {produto.nome}
                                            </h4>
                                            <p className="text-sm text-gray-500 dark:text-gray-400">
                                                {produto.codigo_barras} • {produto.categoria}
                                            </p>
                                        </div>
                                    </div>
                                </div>
                                <div className="text-right">
                                    <p className="font-bold text-lg text-gray-800 dark:text-white">
                                        R$ {produto.preco_venda.toFixed(2)}
                                    </p>
                                    <p className="text-sm text-gray-500 dark:text-gray-400">
                                        Estoque: {produto.quantidade_estoque}
                                    </p>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {modoBarras && (
                <div className="mt-2 text-sm text-blue-600 dark:text-blue-400 flex items-center">
                    <Barcode className="w-4 h-4 mr-1" />
                    Modo código de barras ativado. Aperte ENTER após digitar o código.
                </div>
            )}
        </div>
    );
};

export default ProdutoSearch;