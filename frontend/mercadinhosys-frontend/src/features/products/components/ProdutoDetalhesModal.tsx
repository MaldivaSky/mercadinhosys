import { Tag, Image as ImageIcon, Clipboard, Calendar, Barcode, Building2 } from 'lucide-react';
import { Produto } from '../../../types';
import { formatCurrency, formatDate } from '../../../utils/formatters';
import ResponsiveModal from '../../../components/ui/ResponsiveModal';

interface ProdutoDetalhesModalProps {
    produto: Produto;
    onClose: () => void;
}

const ProdutoDetalhesModal = ({ produto, onClose }: ProdutoDetalhesModalProps) => {
    return (
        <ResponsiveModal
            isOpen={true}
            onClose={onClose}
            title={produto.nome}
            subtitle={`${produto.categoria} | ${produto.marca || 'Sem Marca'}`}
            headerIcon={<Tag className="w-6 h-6" />}
            headerColor="blue"
            size="xl"
            footer={
                <button
                    onClick={onClose}
                    className="w-full sm:w-auto px-8 py-3 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-white rounded-xl font-bold hover:bg-gray-200 dark:hover:bg-gray-600 transition-all border border-gray-200 dark:border-gray-600"
                >
                    Fechar
                </button>
            }
        >
            <div className="flex flex-col lg:flex-row gap-8">
                <div className="w-full lg:w-72 space-y-6">
                    <div className="aspect-square bg-gray-50 dark:bg-gray-900/50 rounded-2xl border border-gray-100 dark:border-gray-700 flex items-center justify-center overflow-hidden shadow-inner">
                        {produto.imagem_url ? (
                            <img src={produto.imagem_url} alt={produto.nome} className="w-full h-full object-contain p-4 transition-transform hover:scale-105 duration-500" />
                        ) : (
                            <ImageIcon className="w-20 h-20 text-gray-200 dark:text-gray-700" />
                        )}
                    </div>

                    <div className="grid grid-cols-2 lg:grid-cols-1 gap-3">
                        <div className="bg-white dark:bg-gray-800 p-4 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700">
                            <p className="text-[10px] text-gray-500 uppercase font-black mb-1">Status de Estoque</p>
                            <div className="flex items-center gap-2">
                                <span className={`w-3 h-3 rounded-full ${produto.quantidade <= 0 ? 'bg-red-500' :
                                    produto.quantidade <= (produto.quantidade_minima || 10) ? 'bg-yellow-500' : 'bg-green-500'
                                    } shadow-sm`}></span>
                                <span className="font-bold text-gray-800 dark:text-white text-sm">
                                    {produto.quantidade} {produto.unidade_medida?.toUpperCase() || 'UN'}
                                </span>
                            </div>
                        </div>

                        <div className="bg-white dark:bg-gray-800 p-4 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700">
                            <p className="text-[10px] text-gray-500 uppercase font-black mb-1">Curva ABC</p>
                            <span className={`inline-block px-2.5 py-1 rounded-lg text-[10px] font-black tracking-wider uppercase ${produto.classificacao_abc === 'A' ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 border border-green-200 dark:border-green-800' :
                                    produto.classificacao_abc === 'B' ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 border border-blue-200 dark:border-blue-800' :
                                        'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 border border-gray-200 dark:border-gray-600'
                                }`}>
                                Classe {produto.classificacao_abc || 'C'}
                            </span>
                        </div>
                    </div>
                </div>

                <div className="flex-1 space-y-8">
                    <div className="hidden lg:block">
                        <h2 className="text-3xl font-black text-gray-900 dark:text-white leading-tight">{produto.nome}</h2>
                        <div className="flex items-center gap-4 mt-3">
                            <span className="flex items-center gap-1.5 px-3 py-1 bg-gray-100 dark:bg-gray-700 rounded-full text-xs font-bold text-gray-500">
                                <Tag className="w-3.5 h-3.5 text-blue-500" /> {produto.categoria}
                            </span>
                            <span className="flex items-center gap-1.5 px-3 py-1 bg-gray-100 dark:bg-gray-700 rounded-full text-xs font-bold text-gray-500">
                                <Building2 className="w-3.5 h-3.5 text-red-500" /> {produto.marca || 'Sem Marca'}
                            </span>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                        <div className="bg-indigo-50 dark:bg-indigo-900/20 p-5 rounded-2xl border border-indigo-100 dark:border-indigo-800/50">
                            <p className="text-[10px] text-indigo-600 dark:text-indigo-400 font-black uppercase tracking-widest mb-2">Preço de Custo</p>
                            <p className="text-2xl font-black text-indigo-700 dark:text-indigo-300">{formatCurrency(produto.preco_custo)}</p>
                            <div className="h-1 w-8 bg-indigo-200 dark:bg-indigo-700 mt-2 rounded-full"></div>
                        </div>

                        <div className="bg-green-50 dark:bg-green-900/20 p-5 rounded-2xl border border-green-100 dark:border-green-800/50">
                            <p className="text-[10px] text-green-600 dark:text-green-400 font-black uppercase tracking-widest mb-2">Preço de Venda</p>
                            <p className="text-2xl font-black text-green-700 dark:text-green-300">{formatCurrency(produto.preco_venda)}</p>
                            <div className="h-1 w-8 bg-green-200 dark:bg-green-700 mt-2 rounded-full"></div>
                        </div>

                        <div className="bg-purple-50 dark:bg-purple-900/20 p-5 rounded-2xl border border-purple-100 dark:border-purple-800/50">
                            <p className="text-[10px] text-purple-600 dark:text-purple-400 font-black uppercase tracking-widest mb-2">Margem Bruta</p>
                            <p className="text-2xl font-black text-purple-700 dark:text-purple-300">
                                {produto.margem_lucro ? `${produto.margem_lucro}%` : '0%'}
                            </p>
                            <div className="h-1 w-8 bg-purple-200 dark:bg-purple-700 mt-2 rounded-full"></div>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                        <div className="space-y-4">
                            <h3 className="text-xs font-black text-gray-400 uppercase tracking-[0.2em] flex items-center gap-2">
                                <Clipboard className="w-4 h-4 text-gray-300" /> Especificações Técnicas
                            </h3>
                            <div className="space-y-3">
                                {[
                                    { label: 'Cód. de Barras', value: produto.codigo_barras || '---', mono: true },
                                    { label: 'Fabricante', value: produto.fabricante || '---' },
                                    { label: 'NCM', value: produto.ncm || '---' },
                                    { label: 'Tipo Unidade', value: produto.unidade_medida?.toUpperCase() || 'UN' }
                                ].map((item, idx) => (
                                    <div key={idx} className="flex justify-between items-center py-2 border-b border-gray-100 dark:border-gray-700/50">
                                        <span className="text-sm font-medium text-gray-500 dark:text-gray-400">{item.label}</span>
                                        <span className={`text-sm font-bold text-gray-800 dark:text-gray-200 ${item.mono ? 'font-mono' : ''}`}>
                                            {item.value}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </div>

                        <div className="space-y-4">
                            <h3 className="text-xs font-black text-gray-400 uppercase tracking-[0.2em] flex items-center gap-2">
                                <Calendar className="w-4 h-4 text-gray-300" /> Controle Comercial
                            </h3>
                            <div className="space-y-3">
                                <div className="flex justify-between items-center py-2 border-b border-gray-100 dark:border-gray-700/50">
                                    <span className="text-sm font-medium text-gray-500 dark:text-gray-400">Estoque Mínimo</span>
                                    <span className="text-sm font-bold text-gray-800 dark:text-gray-200">{produto.quantidade_minima} {produto.unidade_medida}</span>
                                </div>
                                <div className="flex justify-between items-center py-2 border-b border-gray-100 dark:border-gray-700/50">
                                    <span className="text-sm font-medium text-gray-500 dark:text-gray-400">Última Venda</span>
                                    <span className="text-sm font-bold text-gray-800 dark:text-gray-200">
                                        {produto.ultima_venda ? formatDate(produto.ultima_venda) : 'Nunca Vendido'}
                                    </span>
                                </div>
                                <div className="flex justify-between items-center py-2 border-b border-gray-100 dark:border-gray-700/50">
                                    <span className="text-sm font-medium text-gray-500 dark:text-gray-400">Validade</span>
                                    <span className={`text-sm font-bold ${produto.alerta_validade ? 'text-red-500 animate-pulse' : 'text-gray-800 dark:text-gray-200'}`}>
                                        {produto.data_validade ? formatDate(produto.data_validade) : 'N/D'}
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>

                    {produto.descricao && (
                        <div className="bg-gray-50 dark:bg-gray-900/40 p-6 rounded-2xl border border-gray-100 dark:border-gray-700/50 group">
                            <h3 className="text-[10px] font-black text-gray-400 uppercase tracking-[0.3em] mb-3 flex items-center gap-2">
                                <Barcode className="w-4 h-4 opacity-50 transition-transform group-hover:rotate-12" /> Descrição Completa
                            </h3>
                            <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed italic">
                                "{produto.descricao}"
                            </p>
                        </div>
                    )}

                    <div className="pt-4 text-center">
                        <p className="text-[9px] text-gray-300 dark:text-gray-600 font-bold uppercase tracking-[0.4em]">
                            Smart Retail Intelligence • MercadinhoSys Enterprise
                        </p>
                    </div>
                </div>
            </div>
        </ResponsiveModal>
    );
};

export default ProdutoDetalhesModal;
