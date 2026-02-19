import React from 'react';
import { X, Tag, Barcode, Clipboard, Calendar, Image as ImageIcon, MapPin } from 'lucide-react';
import { Produto } from '../../../types';
import { formatCurrency, formatDate } from '../../../utils/formatters';

interface ProdutoDetalhesModalProps {
    produto: Produto;
    onClose: () => void;
}

const ProdutoDetalhesModal: React.FC<ProdutoDetalhesModalProps> = ({ produto, onClose }) => {
    return (
        <div className="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-50 p-4 backdrop-blur-sm">
            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col md:flex-row border border-gray-100 dark:border-gray-700">

                {/* Lateral Esquerda - Imagem e Status */}
                <div className="w-full md:w-80 bg-gray-50 dark:bg-gray-900/50 p-6 flex flex-col items-center border-b md:border-b-0 md:border-r border-gray-100 dark:border-gray-700">
                    <div className="w-full aspect-square bg-white dark:bg-gray-800 rounded-xl shadow-inner border border-gray-200 dark:border-gray-700 flex items-center justify-center overflow-hidden mb-6">
                        {produto.imagem_url ? (
                            <img src={produto.imagem_url} alt={produto.nome} className="w-full h-full object-contain p-2" />
                        ) : (
                            <ImageIcon className="w-16 h-16 text-gray-300 dark:text-gray-600" />
                        )}
                    </div>

                    <div className="w-full space-y-4">
                        <div className="bg-white dark:bg-gray-800 p-4 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700">
                            <p className="text-xs text-gray-500 uppercase font-bold mb-1">Status de Estoque</p>
                            <div className="flex items-center gap-2">
                                <span className={`w-3 h-3 rounded-full ${produto.quantidade <= 0 ? 'bg-red-500' :
                                    produto.quantidade <= (produto.quantidade_minima || 10) ? 'bg-yellow-500' : 'bg-green-500'
                                    } shadow-sm`}></span>
                                <span className="font-bold text-gray-800 dark:text-white">
                                    {produto.quantidade} {produto.unidade_medida?.toUpperCase() || 'UN'}
                                </span>
                            </div>
                        </div>

                        <div className="bg-white dark:bg-gray-800 p-4 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700">
                            <p className="text-xs text-gray-500 uppercase font-bold mb-1">Classificacao ABC</p>
                            <div className="flex items-center gap-2">
                                <span className={`px-2 py-0.5 rounded text-xs font-bold ${produto.classificacao_abc === 'A' ? 'bg-green-100 text-green-700' :
                                    produto.classificacao_abc === 'B' ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-650'
                                    }`}>
                                    Classe {produto.classificacao_abc || 'C'}
                                </span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Conteúdo Principal */}
                <div className="flex-1 flex flex-col overflow-hidden">
                    <div className="p-6 border-b border-gray-100 dark:border-gray-700 flex justify-between items-start">
                        <div>
                            <h2 className="text-2xl font-bold text-gray-900 dark:text-white leading-tight">{produto.nome}</h2>
                            <p className="text-gray-500 flex items-center gap-1 mt-1 font-medium">
                                <Tag className="w-4 h-4" /> {produto.categoria} | <MapPin className="w-4 h-4 ml-1" /> {produto.marca || 'Sem Marca'}
                            </p>
                        </div>
                        <button onClick={onClose} className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-full transition-colors">
                            <X className="w-6 h-6 text-gray-400" />
                        </button>
                    </div>

                    <div className="p-6 overflow-y-auto space-y-8">
                        {/* Grade de Preços */}
                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                            <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-2xl border border-blue-100 dark:border-blue-800">
                                <p className="text-xs text-blue-600 dark:text-blue-400 font-bold uppercase mb-1">Preco de Custo</p>
                                <p className="text-xl font-black text-blue-700 dark:text-blue-300">{formatCurrency(produto.preco_custo)}</p>
                            </div>
                            <div className="bg-green-50 dark:bg-green-900/20 p-4 rounded-2xl border border-green-100 dark:border-green-800">
                                <p className="text-xs text-green-600 dark:text-green-400 font-bold uppercase mb-1">Preco de Venda</p>
                                <p className="text-xl font-black text-green-700 dark:text-green-300">{formatCurrency(produto.preco_venda)}</p>
                            </div>
                            <div className="bg-purple-50 dark:bg-purple-900/20 p-4 rounded-2xl border border-purple-100 dark:border-purple-800">
                                <p className="text-xs text-purple-600 dark:text-purple-400 font-bold uppercase mb-1">Margem de Lucro</p>
                                <p className="text-xl font-black text-purple-700 dark:text-purple-300">
                                    {produto.margem_lucro ? `${produto.margem_lucro}%` : '0%'}
                                </p>
                            </div>
                        </div>

                        {/* Informações Técnicas */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div className="space-y-4">
                                <h3 className="text-sm font-bold text-gray-400 uppercase tracking-wider flex items-center gap-2">
                                    <Clipboard className="w-4 h-4" /> Especificacoes
                                </h3>
                                <div className="space-y-3">
                                    <div className="flex justify-between items-center py-2 border-b border-gray-50 dark:border-gray-700">
                                        <span className="text-gray-500 dark:text-gray-400">Codigo de Barras</span>
                                        <span className="font-mono font-bold text-gray-700 dark:text-gray-300">{produto.codigo_barras || '---'}</span>
                                    </div>
                                    <div className="flex justify-between items-center py-2 border-b border-gray-50 dark:border-gray-700">
                                        <span className="text-gray-500 dark:text-gray-400">Fabricante</span>
                                        <span className="font-bold text-gray-700 dark:text-gray-300">{produto.fabricante || '---'}</span>
                                    </div>
                                    <div className="flex justify-between items-center py-2 border-b border-gray-50 dark:border-gray-700">
                                        <span className="text-gray-500 dark:text-gray-400">NCM</span>
                                        <span className="font-bold text-gray-700 dark:text-gray-300">{produto.ncm || '---'}</span>
                                    </div>
                                </div>
                            </div>

                            <div className="space-y-4">
                                <h3 className="text-sm font-bold text-gray-400 uppercase tracking-wider flex items-center gap-2">
                                    <Calendar className="w-4 h-4" /> Controle de Estoque
                                </h3>
                                <div className="space-y-3">
                                    <div className="flex justify-between items-center py-2 border-b border-gray-50 dark:border-gray-700">
                                        <span className="text-gray-500 dark:text-gray-400">Estoque Minimo</span>
                                        <span className="font-bold text-gray-700 dark:text-gray-300">{produto.quantidade_minima} {produto.unidade_medida}</span>
                                    </div>
                                    <div className="flex justify-between items-center py-2 border-b border-gray-50 dark:border-gray-700">
                                        <span className="text-gray-500 dark:text-gray-400">Ultima Venda</span>
                                        <span className="font-bold text-gray-700 dark:text-gray-300">{produto.ultima_venda ? formatDate(produto.ultima_venda) : 'Nunca vendido'}</span>
                                    </div>
                                    <div className="flex justify-between items-center py-2 border-b border-gray-50 dark:border-gray-700">
                                        <span className="text-gray-500 dark:text-gray-400">Data de Validade</span>
                                        <span className={`font-bold ${produto.alerta_validade ? 'text-red-500' : 'text-gray-700 dark:text-gray-300'}`}>
                                            {produto.data_validade ? formatDate(produto.data_validade) : 'Nao controlada'}
                                        </span>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Descrição */}
                        {produto.descricao && (
                            <div className="bg-gray-50 dark:bg-gray-900/30 p-5 rounded-2xl">
                                <h3 className="text-sm font-bold text-gray-400 uppercase tracking-wider mb-2 flex items-center gap-2">
                                    <Barcode className="w-4 h-4" /> Descricao Detalhada
                                </h3>
                                <p className="text-gray-600 dark:text-gray-400 leading-relaxed italic">
                                    "{produto.descricao}"
                                </p>
                            </div>
                        )}
                    </div>

                    <div className="p-4 bg-gray-50 dark:bg-gray-900/50 border-t border-gray-100 dark:border-gray-700 text-center">
                        <p className="text-[10px] text-gray-400 uppercase font-bold tracking-[0.2em]">
                            MercadinhoSys Professional Product Information System
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ProdutoDetalhesModal;
