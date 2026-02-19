import React, { useState, useEffect } from 'react';
import { X, Camera, Sparkles } from 'lucide-react';
import { toast } from 'react-hot-toast';
import { Produto, Fornecedor } from '../../../types';
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

const ProductFormModal: React.FC<ProductFormModalProps> = ({
    show,
    editMode,
    produto,
    categorias,
    fornecedores,
    onClose,
    onSuccess
}) => {
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
                // Mapear categoria se possível ou focar no nome/marca
            }));

            toast.success('Dados preenchidos automaticamente!', { id: loadingToast });
        } catch (error) {
            console.error('Erro na consulta Cosmos:', error);
            toast.error('Produto não encontrado no banco de dados geral.', { id: loadingToast });
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
        } catch (error: any) {
            toast.error(error.response?.data?.error || 'Erro ao salvar');
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
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-hidden">
                <div className="flex items-center justify-between p-4 border-b dark:border-gray-700 bg-blue-50 dark:bg-blue-900">
                    <div className="flex items-center gap-3">
                        <h3 className="text-lg font-bold">{editMode ? 'Editar Produto' : 'Novo Produto'}</h3>
                        {!editMode && (
                            <button
                                type="button"
                                onClick={() => setShowScanner(true)}
                                className="flex items-center gap-2 px-3 py-1 bg-white dark:bg-gray-800 text-blue-600 dark:text-blue-400 text-xs font-bold rounded-full shadow-sm hover:shadow-md transition-all border border-blue-200 dark:border-blue-700 animate-pulse"
                            >
                                <Sparkles className="w-3.5 h-3.5" />
                                CADASTRO INTELIGENTE
                            </button>
                        )}
                    </div>
                    <button onClick={onClose} className="p-1 hover:bg-blue-100 dark:hover:bg-blue-800 rounded"><X className="w-5 h-5" /></button>
                </div>
                <form onSubmit={handleSubmit} className="p-4 space-y-4 overflow-y-auto max-h-[70vh]">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium mb-1">Nome *</label>
                            <input type="text" value={formData.nome} onChange={(e) => setFormData(prev => ({ ...prev, nome: e.target.value }))} className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600" required />
                        </div>
                        <div>
                            <label className="block text-sm font-medium mb-1">Codigo de Barras</label>
                            <div className="flex gap-2">
                                <input type="text" value={formData.codigo_barras} onChange={(e) => setFormData(prev => ({ ...prev, codigo_barras: e.target.value }))} className="flex-1 px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600" />
                                <button
                                    type="button"
                                    onClick={() => setShowScanner(true)}
                                    className="p-2 bg-gray-100 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                                    title="Escanear com a camera"
                                >
                                    <Camera className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                                </button>
                            </div>
                        </div>
                        <div>
                            <label className="block text-sm font-medium mb-1">Categoria *</label>
                            <input type="text" list="categorias-list" value={formData.categoria} onChange={(e) => setFormData(prev => ({ ...prev, categoria: e.target.value }))} className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600" required />
                            <datalist id="categorias-list">{categorias.map(c => <option key={c} value={c} />)}</datalist>
                        </div>
                        <div>
                            <label className="block text-sm font-medium mb-1">Marca</label>
                            <input type="text" value={formData.marca} onChange={(e) => setFormData(prev => ({ ...prev, marca: e.target.value }))} className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600" />
                        </div>
                        <div>
                            <label className="block text-sm font-medium mb-1">Fornecedor</label>
                            <select value={formData.fornecedor_id || ''} onChange={(e) => setFormData(prev => ({ ...prev, fornecedor_id: e.target.value ? parseInt(e.target.value) : undefined }))} className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600">
                                <option value="">Selecione</option>
                                {fornecedores.map(f => <option key={f.id} value={f.id}>{f.nome_fantasia}</option>)}
                            </select>
                        </div>
                        <div>
                            <label className="block text-sm font-medium mb-1">Unidade</label>
                            <select value={formData.unidade_medida} onChange={(e) => setFormData(prev => ({ ...prev, unidade_medida: e.target.value }))} className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600">
                                <option value="un">Unidade</option>
                                <option value="kg">Quilograma</option>
                                <option value="g">Grama</option>
                                <option value="l">Litro</option>
                                <option value="ml">Mililitro</option>
                                <option value="cx">Caixa</option>
                                <option value="pct">Pacote</option>
                            </select>
                        </div>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div>
                            <label className="block text-sm font-medium mb-1">Preco Custo</label>
                            <input type="number" step="0.01" value={formData.preco_custo} onChange={(e) => setFormData(prev => ({ ...prev, preco_custo: parseFloat(e.target.value) || 0 }))} onBlur={calcularPrecoVenda} className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600" />
                        </div>
                        <div>
                            <label className="block text-sm font-medium mb-1">Margem (%)</label>
                            <input type="number" step="0.1" value={formData.margem_lucro} onChange={(e) => setFormData(prev => ({ ...prev, margem_lucro: parseFloat(e.target.value) || 0 }))} onBlur={calcularPrecoVenda} className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600" />
                        </div>
                        <div>
                            <label className="block text-sm font-medium mb-1">Preco Venda</label>
                            <input type="number" step="0.01" value={formData.preco_venda} onChange={(e) => setFormData(prev => ({ ...prev, preco_venda: parseFloat(e.target.value) || 0 }))} onBlur={calcularMargem} className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600" />
                        </div>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium mb-1">Quantidade</label>
                            <input type="number" value={formData.quantidade} onChange={(e) => setFormData(prev => ({ ...prev, quantidade: parseInt(e.target.value) || 0 }))} className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600" />
                        </div>
                        <div>
                            <label className="block text-sm font-medium mb-1">Quantidade Minima</label>
                            <input type="number" value={formData.quantidade_minima} onChange={(e) => setFormData(prev => ({ ...prev, quantidade_minima: parseInt(e.target.value) || 0 }))} className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600" />
                        </div>
                    </div>
                    <div>
                        <label className="block text-sm font-medium mb-1">Descricao</label>
                        <textarea value={formData.descricao} onChange={(e) => setFormData(prev => ({ ...prev, descricao: e.target.value }))} rows={2} className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600" />
                    </div>
                </form>
                <div className="flex justify-end gap-2 p-4 border-t dark:border-gray-700">
                    <button type="button" onClick={onClose} className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg">Cancelar</button>
                    <button onClick={handleSubmit} disabled={loading || isSearchingCosmos} className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50">
                        {loading ? 'Salvando...' : 'Salvar'}
                    </button>
                </div>
            </div>

            {showScanner && (
                <BarcodeScanner
                    onScan={handleScanCodigo}
                    onClose={() => setShowScanner(false)}
                />
            )}
        </div>
    );
};

export default ProductFormModal;
