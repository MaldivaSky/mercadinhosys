import { useState, useEffect } from 'react';
import { Camera, Sparkles } from 'lucide-react';
import ResponsiveModal from '../../../components/ui/ResponsiveModal';
import { toast } from 'react-hot-toast';
import { Fornecedor, Produto } from '../../../types';
import { productsService } from '../productsService';
import { cosmosService } from '../../../services/cosmosService';
import BarcodeScanner from '../../pdv/components/BarcodeScanner';

interface ProductFormModalProps {
    show: boolean;
    editMode: boolean;
    produto: Produto | null;
    categorias: string[];
    fornecedores: Fornecedor[];
    onClose: () => void;
    onSuccess: () => void;
}

const ProductFormModal = ({
    show,
    editMode,
    produto,
    categorias,
    fornecedores,
    onClose,
    onSuccess
}: ProductFormModalProps) => {
    const [loading, setLoading] = useState(false);
    const [formData, setFormData] = useState({
        nome: '',
        codigo_barras: '',
        descricao: '',
        categoria: '',
        marca: 'Sem Marca',
        fabricante: '',
        tipo: 'Higiene',
        unidade_medida: 'un',
        preco_custo: 0,
        preco_venda: 0,
        margem_lucro: 30,
        quantidade: 0,
        quantidade_minima: 10,
        fornecedor_id: undefined as number | undefined,
        ativo: true,
        imagem_url: '',
    });
    const [showScanner, setShowScanner] = useState(false);
    const [isSearchingCosmos, setIsSearchingCosmos] = useState(false);

    useEffect(() => {
        if (show) {
            if (produto && editMode) {
                setFormData({
                    nome: produto.nome || '',
                    codigo_barras: produto.codigo_barras || '',
                    descricao: produto.descricao || '',
                    categoria: produto.categoria || '',
                    marca: produto.marca || 'Sem Marca',
                    fabricante: produto.fabricante || '',
                    tipo: produto.tipo || 'Higiene',
                    unidade_medida: produto.unidade_medida || 'un',
                    preco_custo: produto.preco_custo || 0,
                    preco_venda: produto.preco_venda || 0,
                    margem_lucro: produto.margem_lucro || 30,
                    quantidade: produto.quantidade || 0,
                    quantidade_minima: produto.quantidade_minima || 10,
                    fornecedor_id: produto.fornecedor_id,
                    ativo: produto.ativo ?? true,
                    imagem_url: produto.imagem_url || '',
                });
            } else {
                // Reset form for new product
                setFormData({
                    nome: '',
                    codigo_barras: '',
                    descricao: '',
                    categoria: '',
                    marca: 'Sem Marca',
                    fabricante: '',
                    tipo: 'Higiene',
                    unidade_medida: 'un',
                    preco_custo: 0,
                    preco_venda: 0,
                    margem_lucro: 30,
                    quantidade: 0,
                    quantidade_minima: 10,
                    fornecedor_id: undefined,
                    ativo: true,
                    imagem_url: '',
                });
            }
        }
    }, [show, editMode, produto]);

    const handleScanCodigo = async (codigo: string) => {
        setShowScanner(false);
        setFormData(prev => ({ ...prev, codigo_barras: codigo }));

        setIsSearchingCosmos(true);
        const loadingToast = toast.loading('Consultando Cosmos API...');

        try {
            const data = await cosmosService.buscarPorGtin(codigo);

            setFormData(prev => ({
                ...prev,
                nome: data.description || prev.nome,
                descricao: data.ncm?.full_description || data.description || prev.descricao,
                marca: data.brand?.name || prev.marca,
                imagem_url: data.thumbnail || prev.imagem_url,
                // Mapear categoria se possÃ­vel ou focar no nome/marca
            }));

            toast.success('Dados preenchidos automaticamente!', { id: loadingToast });
        } catch (error) {
            console.error('Erro na consulta Cosmos:', error);
            toast.error('Produto nÃ£o encontrado no banco de dados geral.', { id: loadingToast });
        } finally {
            setIsSearchingCosmos(false);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!formData.nome.trim()) { toast.error('Nome obrigatorio'); return; }
        if (!formData.categoria.trim()) { toast.error('Categoria obrigatoria'); return; }
        setLoading(true);
        try {
            if (editMode && produto) {
                await productsService.update(produto.id, formData);
                toast.success('Produto atualizado!');
            } else {
                await productsService.create(formData);
                toast.success('Produto criado!');
            }
            onSuccess();
        } catch (error: unknown) {
            const err = error as any;
            toast.error(err.response?.data?.error || 'Erro ao salvar');
        } finally {
            setLoading(false);
        }
    };

    const calcularPrecoVenda = () => {
        const preco = formData.preco_custo * (1 + formData.margem_lucro / 100);
        setFormData(prev => ({ ...prev, preco_venda: parseFloat(preco.toFixed(2)) }));
    };

    const calcularMargem = () => {
        if (formData.preco_custo > 0) {
            const margem = ((formData.preco_venda - formData.preco_custo) / formData.preco_custo) * 100;
            setFormData(prev => ({ ...prev, margem_lucro: parseFloat(margem.toFixed(2)) }));
        }
    };

    if (!show) return null;

    return (
        <ResponsiveModal
            isOpen={show}
            onClose={onClose}
            title={editMode ? 'Editar Produto' : 'Novo Produto'}
            subtitle={editMode ? `ID: ${produto?.id}` : 'Cadastre um novo item no estoque'}
            headerIcon={<Sparkles className="w-6 h-6" />}
            headerColor="blue"
            size="xl"
            footer={
                <div className="flex w-full sm:w-auto gap-3">
                    <button
                        type="button"
                        onClick={onClose}
                        className="flex-1 sm:flex-none px-6 py-3 text-gray-600 dark:text-gray-400 font-bold hover:bg-gray-100 dark:hover:bg-gray-700 rounded-xl transition-all"
                    >
                        Cancelar
                    </button>
                    <button
                        onClick={handleSubmit}
                        disabled={loading || isSearchingCosmos}
                        className="flex-1 sm:flex-none px-8 py-3 bg-blue-600 text-white rounded-xl font-bold hover:bg-blue-700 disabled:opacity-50 shadow-lg shadow-blue-500/20 active:scale-95 transition-all"
                    >
                        {loading ? 'Salvando...' : 'Salvar Produto'}
                    </button>
                </div>
            }
        >
            <form onSubmit={handleSubmit} className="space-y-8">
                {/* Banner de Cadastro Inteligente */}
                {!editMode && (
                    <button
                        type="button"
                        onClick={() => setShowScanner(true)}
                        className="w-full flex items-center justify-between p-4 bg-gradient-to-r from-blue-600 to-indigo-700 text-white rounded-2xl shadow-md hover:shadow-xl transition-all group overflow-hidden relative"
                    >
                        <div className="flex items-center gap-4 relative z-10">
                            <div className="p-3 bg-white/20 rounded-xl backdrop-blur-md">
                                <Camera className="w-6 h-6" />
                            </div>
                            <div className="text-left">
                                <h4 className="font-bold text-lg">Cadastro Inteligente</h4>
                                <p className="text-xs text-blue-100">Escanear cÃ³digo e buscar dados na nuvem</p>
                            </div>
                        </div>
                        <Sparkles className="w-8 h-8 opacity-20 group-hover:scale-125 transition-transform duration-500" />
                        <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full -mr-16 -mt-16 blur-3xl"></div>
                    </button>
                )}

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* IdentificaÃ§Ã£o Principal */}
                    <div className="space-y-4">
                        <h4 className="text-xs font-bold text-gray-400 uppercase tracking-widest ml-1">IdentificaÃ§Ã£o</h4>
                        <div className="space-y-4 p-5 bg-gray-50 dark:bg-gray-900/50 rounded-2xl border border-gray-100 dark:border-gray-800">
                            <div className="space-y-2">
                                <label className="text-sm font-semibold text-gray-700 dark:text-gray-300">Nome do Produto *</label>
                                <input
                                    type="text"
                                    value={formData.nome}
                                    onChange={(e) => setFormData(prev => ({ ...prev, nome: e.target.value }))}
                                    className="w-full px-4 py-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none transition-all"
                                    required
                                />
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm font-semibold text-gray-700 dark:text-gray-300">CÃ³digo de Barras</label>
                                <div className="flex gap-2">
                                    <input
                                        type="text"
                                        value={formData.codigo_barras}
                                        onChange={(e) => setFormData(prev => ({ ...prev, codigo_barras: e.target.value }))}
                                        className="flex-1 px-4 py-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none transition-all font-mono"
                                    />
                                    <button
                                        type="button"
                                        onClick={() => setShowScanner(true)}
                                        className="p-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors text-blue-600 shadow-sm"
                                    >
                                        <Camera className="w-6 h-6" />
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* OrganizaÃ§Ã£o */}
                    <div className="space-y-4">
                        <h4 className="text-xs font-bold text-gray-400 uppercase tracking-widest ml-1">OrganizaÃ§Ã£o</h4>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 p-5 bg-gray-50 dark:bg-gray-900/50 rounded-2xl border border-gray-100 dark:border-gray-800">
                            <div className="space-y-2">
                                <label className="text-sm font-semibold text-gray-700 dark:text-gray-300">Categoria *</label>
                                <input type="text" list="categorias-list" value={formData.categoria} onChange={(e) => setFormData(prev => ({ ...prev, categoria: e.target.value }))} className="w-full px-4 py-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl outline-none focus:ring-2 focus:ring-blue-500" required />
                                <datalist id="categorias-list">{categorias.map(c => <option key={c} value={c} />)}</datalist>
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm font-semibold text-gray-700 dark:text-gray-300">Unidade</label>
                                <select value={formData.unidade_medida} onChange={(e) => setFormData(prev => ({ ...prev, unidade_medida: e.target.value }))} className="w-full px-4 py-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl outline-none focus:ring-2 focus:ring-blue-500">
                                    <option value="un">Unidade (un)</option>
                                    <option value="kg">Quilograma (kg)</option>
                                    <option value="g">Grama (g)</option>
                                    <option value="l">Litro (l)</option>
                                    <option value="ml">Mililitro (ml)</option>
                                    <option value="cx">Caixa (cx)</option>
                                    <option value="pct">Pacote (pct)</option>
                                </select>
                            </div>
                            <div className="sm:col-span-2 space-y-2">
                                <label className="text-sm font-semibold text-gray-700 dark:text-gray-300">Marca/Fabricante</label>
                                <input type="text" value={formData.marca} onChange={(e) => setFormData(prev => ({ ...prev, marca: e.target.value }))} className="w-full px-4 py-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl outline-none focus:ring-2 focus:ring-blue-500" />
                            </div>
                            <div className="sm:col-span-2 space-y-2">
                                <label className="text-sm font-semibold text-gray-700 dark:text-gray-300">Fornecedor Principal</label>
                                <select
                                    value={formData.fornecedor_id || ''}
                                    onChange={(e) => setFormData(prev => ({ ...prev, fornecedor_id: e.target.value ? Number(e.target.value) : undefined }))}
                                    className="w-full px-4 py-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl outline-none focus:ring-2 focus:ring-blue-500"
                                >
                                    <option value="">Nenhum Fornecedor</option>
                                    {fornecedores.map(f => (
                                        <option key={f.id} value={f.id}>{f.nome_fantasia || f.nome}</option>
                                    ))}
                                </select>
                            </div>
                        </div>
                    </div>
                </div>

                {/* PrecificaÃ§Ã£o */}
                <div className="space-y-4">
                    <h4 className="text-xs font-bold text-gray-400 uppercase tracking-widest ml-1">PrecificaÃ§Ã£o e Lucro</h4>
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 p-6 bg-blue-50/50 dark:bg-blue-900/10 rounded-2xl border border-blue-100/50 dark:border-blue-900/30">
                        <div className="space-y-2">
                            <label className="text-sm font-semibold text-blue-800 dark:text-blue-300">PreÃ§o de Custo (R$)</label>
                            <input type="number" step="0.01" value={formData.preco_custo} onChange={(e) => setFormData(prev => ({ ...prev, preco_custo: parseFloat(e.target.value) || 0 }))} onBlur={calcularPrecoVenda} className="w-full px-4 py-3 bg-white dark:bg-gray-800 border border-blue-200 dark:border-blue-800 rounded-xl outline-none focus:ring-2 focus:ring-blue-500 text-lg font-semibold" />
                        </div>
                        <div className="space-y-2">
                            <label className="text-sm font-semibold text-blue-800 dark:text-blue-300">Margem (%)</label>
                            <input type="number" step="0.1" value={formData.margem_lucro} onChange={(e) => setFormData(prev => ({ ...prev, margem_lucro: parseFloat(e.target.value) || 0 }))} onBlur={calcularPrecoVenda} className="w-full px-4 py-3 bg-white dark:bg-gray-800 border border-blue-200 dark:border-blue-800 rounded-xl outline-none focus:ring-2 focus:ring-blue-500 text-lg font-semibold" />
                        </div>
                        <div className="space-y-2">
                            <label className="text-sm font-semibold text-blue-800 dark:text-blue-300">PreÃ§o de Venda (R$)</label>
                            <input type="number" step="0.01" value={formData.preco_venda} onChange={(e) => setFormData(prev => ({ ...prev, preco_venda: parseFloat(e.target.value) || 0 }))} onBlur={calcularMargem} className="w-full px-4 py-3 bg-blue-600 text-white border-transparent rounded-xl outline-none focus:ring-4 focus:ring-blue-500/30 text-lg font-bold shadow-lg shadow-blue-500/20" />
                        </div>
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Estoque */}
                    <div className="space-y-4">
                        <h4 className="text-xs font-bold text-gray-400 uppercase tracking-widest ml-1">Controle de Estoque</h4>
                        <div className="grid grid-cols-2 gap-4 p-5 bg-gray-50 dark:bg-gray-900/50 rounded-2xl border border-gray-100 dark:border-gray-800">
                            <div className="space-y-2">
                                <label className="text-sm font-semibold text-gray-700 dark:text-gray-300">Qtd. Atual</label>
                                <input type="number" value={formData.quantidade} onChange={(e) => setFormData(prev => ({ ...prev, quantidade: parseInt(e.target.value) || 0 }))} className="w-full px-4 py-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl outline-none focus:ring-2 focus:ring-blue-500" />
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm font-semibold text-gray-700 dark:text-gray-300">Qtd. MÃ­nima</label>
                                <input type="number" value={formData.quantidade_minima} onChange={(e) => setFormData(prev => ({ ...prev, quantidade_minima: parseInt(e.target.value) || 0 }))} className="w-full px-4 py-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl outline-none focus:ring-2 focus:ring-blue-500" />
                            </div>
                        </div>
                    </div>

                    {/* Detalhes Adicionais */}
                    <div className="space-y-4">
                        <h4 className="text-xs font-bold text-gray-400 uppercase tracking-widest ml-1">Metadados</h4>
                        <div className="space-y-4 p-5 bg-gray-50 dark:bg-gray-900/50 rounded-2xl border border-gray-100 dark:border-gray-800">
                            <div className="space-y-2">
                                <label className="text-sm font-semibold text-gray-700 dark:text-gray-300">DescriÃ§Ã£o/ObervaÃ§Ãµes</label>
                                <textarea value={formData.descricao} onChange={(e) => setFormData(prev => ({ ...prev, descricao: e.target.value }))} rows={2} className="w-full px-4 py-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl outline-none focus:ring-2 focus:ring-blue-500 resize-none" placeholder="Opcional..." />
                            </div>
                        </div>
                    </div>
                </div>
            </form>

            {showScanner && (
                <BarcodeScanner
                    onScan={handleScanCodigo}
                    onClose={() => setShowScanner(false)}
                />
            )}
        </ResponsiveModal>
    );
};

export default ProductFormModal;
