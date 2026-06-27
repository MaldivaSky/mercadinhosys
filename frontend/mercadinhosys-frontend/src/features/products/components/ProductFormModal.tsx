import { useState, useEffect } from 'react';
import { Camera, Sparkles, AlertTriangle } from 'lucide-react';
import ResponsiveModal from '../../../components/ui/ResponsiveModal';
import { showToast } from '../../../utils/toast';
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

const UNIDADES = [
    { value: 'un', label: 'Unidade (un)' },
    { value: 'kg', label: 'Quilograma (kg)' },
    { value: 'g',  label: 'Grama (g)' },
    { value: 'l',  label: 'Litro (l)' },
    { value: 'ml', label: 'Mililitro (ml)' },
    { value: 'cx', label: 'Caixa (cx)' },
    { value: 'pct', label: 'Pacote (pct)' },
    { value: 'fardo', label: 'Fardo' },
    { value: 'duzia', label: 'Dúzia' },
];

const emptyForm = {
    nome: '',
    codigo_barras: '',
    descricao: '',
    categoria: '',
    marca: '',
    fabricante: '',
    tipo: '',
    unidade_medida: 'un',
    preco_custo: 0,
    preco_venda: 0,
    margem_lucro: 30,
    quantidade: 0,
    quantidade_minima: 10,
    fornecedor_id: undefined as number | undefined,
    lote: '',
    data_validade: '',
    data_fabricacao: '',
    data_compra: '',
    data_recebimento: '',
    ativo: true,
    imagem_url: '',
};

const ProductFormModal = ({
    show,
    editMode,
    produto,
    categorias,
    fornecedores,
    onClose,
    onSuccess,
}: ProductFormModalProps) => {
    const [loading, setLoading] = useState(false);
    const [formData, setFormData] = useState({ ...emptyForm });
    const [showScanner, setShowScanner] = useState(false);
    const [isSearchingCosmos, setIsSearchingCosmos] = useState(false);

    useEffect(() => {
        if (!show) return;
        if (produto && editMode) {
            setFormData({
                nome: produto.nome || '',
                codigo_barras: produto.codigo_barras || '',
                descricao: produto.descricao || '',
                categoria: produto.categoria || '',
                marca: produto.marca || '',
                fabricante: produto.fabricante || '',
                tipo: produto.tipo || '',
                unidade_medida: produto.unidade_medida || 'un',
                preco_custo: produto.preco_custo || 0,
                preco_venda: produto.preco_venda || 0,
                margem_lucro: produto.margem_lucro || 30,
                quantidade: produto.quantidade || 0,
                quantidade_minima: produto.quantidade_minima || 10,
                fornecedor_id: produto.fornecedor_id,
                lote: produto.lote || '',
                data_validade: produto.data_validade || '',
                data_fabricacao: produto.data_fabricacao || '',
                data_compra: (produto as any).data_compra || '',
                data_recebimento: (produto as any).data_recebimento || '',
                ativo: produto.ativo ?? true,
                imagem_url: produto.imagem_url || '',
            });
        } else {
            setFormData({ ...emptyForm });
        }
    }, [show, editMode, produto]);

    const handleScanCodigo = async (codigo: string) => {
        setShowScanner(false);
        setFormData(prev => ({ ...prev, codigo_barras: codigo }));
        setIsSearchingCosmos(true);
        const toastId = showToast.loading('Consultando banco de dados de produtos...');
        try {
            const res = await cosmosService.lookup(codigo);
            if (res.success && res.data) {
                const d = res.data;
                setFormData(prev => ({
                    ...prev,
                    nome: d.nome || prev.nome,
                    descricao: d.categoria || prev.descricao,
                    marca: d.marca || prev.marca,
                    imagem_url: d.imagem_url || prev.imagem_url,
                }));
                const origem = res.source === 'catalogo' ? 'catálogo local' : 'Cosmos';
                showToast.success(`Dados preenchidos automaticamente (${origem}).`, { id: toastId });
            } else {
                // Mensagem verdadeira conforme a causa (não mais "não encontrado" genérico)
                const msg = res.message || 'Não foi possível consultar o produto.';
                if (res.code === 'nao_encontrado') {
                    showToast.error(msg, { id: toastId });
                } else {
                    // quota/token/conexão/api: alerta diferenciado — o problema NÃO é o produto
                    showToast.error(msg, { id: toastId, duration: 6000 });
                }
            }
        } catch {
            showToast.error('Falha inesperada ao consultar o produto.', { id: toastId });
        } finally {
            setIsSearchingCosmos(false);
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

    const field = (key: keyof typeof emptyForm, value: any) =>
        setFormData(prev => ({ ...prev, [key]: value }));

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        // Validações obrigatórias
        if (!formData.nome.trim()) { showToast.error('Nome do produto é obrigatório'); return; }
        if (!formData.categoria.trim()) { showToast.error('Categoria é obrigatória'); return; }
        if (!formData.fornecedor_id) { showToast.error('Fornecedor é obrigatório'); return; }
        if (!formData.preco_custo || formData.preco_custo <= 0) { showToast.error('Preço de custo inválido'); return; }
        if (!formData.preco_venda || formData.preco_venda <= 0) { showToast.error('Preço de venda inválido'); return; }

        setLoading(true);
        try {
            const promise = editMode && produto
                ? productsService.update(produto.id, formData)
                : productsService.create(formData);

            await showToast.promise(promise, {
                loading: editMode ? 'Atualizando produto...' : 'Criando produto...',
                success: editMode ? 'Produto atualizado!' : 'Produto cadastrado!',
                error: 'Erro ao salvar produto',
            }, { theme: editMode ? 'warning' : 'success' });

            onSuccess();
        } catch {
            // tratado pelo showToast.promise
        } finally {
            setLoading(false);
        }
    };

    if (!show) return null;

    const inputClass = 'w-full px-4 py-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none transition-all text-gray-900 dark:text-white';
    const labelClass = 'block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1';
    const sectionClass = 'p-5 bg-gray-50 dark:bg-gray-900/50 rounded-2xl border border-gray-100 dark:border-gray-800 space-y-4';

    return (
        <ResponsiveModal
            isOpen={show}
            onClose={onClose}
            title={editMode ? 'Editar Produto' : 'Novo Produto'}
            subtitle={editMode ? `ID: ${produto?.id}` : 'Preencha todos os campos obrigatórios (*)'}
            headerIcon={<Sparkles className="w-6 h-6" />}
            headerColor="blue"
            size="xl"
            footer={
                <div className="flex w-full sm:w-auto gap-3">
                    <button type="button" onClick={onClose}
                        className="flex-1 sm:flex-none px-6 py-3 text-gray-600 dark:text-gray-400 font-bold hover:bg-gray-100 dark:hover:bg-gray-700 rounded-xl transition-all">
                        Cancelar
                    </button>
                    <button onClick={handleSubmit} disabled={loading || isSearchingCosmos}
                        className="flex-1 sm:flex-none px-8 py-3 bg-blue-600 text-white rounded-xl font-bold hover:bg-blue-700 disabled:opacity-50 shadow-lg shadow-blue-500/20 active:scale-95 transition-all">
                        {loading ? 'Salvando...' : 'Salvar Produto'}
                    </button>
                </div>
            }
        >
            <form onSubmit={handleSubmit} className="space-y-8">

                {/* Banner cadastro inteligente */}
                {!editMode && (
                    <button type="button" onClick={() => setShowScanner(true)}
                        className="w-full flex items-center justify-between p-4 bg-gradient-to-r from-blue-600 to-indigo-700 text-white rounded-2xl shadow-md hover:shadow-xl transition-all group relative overflow-hidden">
                        <div className="flex items-center gap-4 z-10">
                            <div className="p-3 bg-white/20 rounded-xl backdrop-blur-md">
                                <Camera className="w-6 h-6" />
                            </div>
                            <div className="text-left">
                                <h4 className="font-bold text-lg">Cadastro Inteligente</h4>
                                <p className="text-xs text-blue-100">Escanear código de barras e buscar dados automaticamente</p>
                            </div>
                        </div>
                        <Sparkles className="w-8 h-8 opacity-20 group-hover:scale-125 transition-transform duration-500" />
                    </button>
                )}

                {/* Aviso de fornecedor obrigatório */}
                {!formData.fornecedor_id && (
                    <div className="flex items-start gap-3 p-3 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700 rounded-xl">
                        <AlertTriangle className="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
                        <p className="text-sm text-amber-700 dark:text-amber-300">
                            <strong>Fornecedor obrigatório.</strong> Todo produto deve ter um fornecedor vinculado para rastreabilidade e geração automática de despesa de compra.
                        </p>
                    </div>
                )}

                {/* ── Seção 1: Identificação ── */}
                <div>
                    <h4 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-3">Identificação</h4>
                    <div className={sectionClass}>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                            <div className="sm:col-span-2">
                                <label className={labelClass}>Nome do Produto *</label>
                                <input type="text" value={formData.nome} required
                                    onChange={e => field('nome', e.target.value)}
                                    className={inputClass} placeholder="Ex: Arroz Tio João 5kg" />
                            </div>
                            <div>
                                <label className={labelClass}>Código de Barras</label>
                                <div className="flex gap-2">
                                    <input type="text" value={formData.codigo_barras}
                                        onChange={e => field('codigo_barras', e.target.value)}
                                        className={`${inputClass} font-mono`} placeholder="EAN-13 / EAN-8" />
                                    <button type="button" onClick={() => setShowScanner(true)}
                                        className="p-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl hover:bg-gray-50 text-blue-600 shadow-sm">
                                        <Camera className="w-5 h-5" />
                                    </button>
                                </div>
                            </div>
                            <div>
                                <label className={labelClass}>Categoria *</label>
                                <input type="text" list="cat-list" value={formData.categoria} required
                                    onChange={e => field('categoria', e.target.value)}
                                    className={inputClass} placeholder="Ex: Alimentos, Bebidas..." />
                                <datalist id="cat-list">{categorias.map(c => <option key={c} value={c} />)}</datalist>
                            </div>
                            <div>
                                <label className={labelClass}>Marca / Fabricante</label>
                                <input type="text" value={formData.marca}
                                    onChange={e => field('marca', e.target.value)}
                                    className={inputClass} placeholder="Ex: Nestlé" />
                            </div>
                            <div>
                                <label className={labelClass}>Unidade de Medida</label>
                                <select value={formData.unidade_medida}
                                    onChange={e => field('unidade_medida', e.target.value)}
                                    className={inputClass}>
                                    {UNIDADES.map(u => <option key={u.value} value={u.value}>{u.label}</option>)}
                                </select>
                            </div>
                        </div>
                    </div>
                </div>

                {/* ── Seção 2: Fornecedor (obrigatório) ── */}
                <div>
                    <h4 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-3">Fornecedor *</h4>
                    <div className={sectionClass}>
                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                            <div className="sm:col-span-3">
                                <label className={labelClass}>Fornecedor Principal *</label>
                                <select value={formData.fornecedor_id || ''} required
                                    onChange={e => field('fornecedor_id', e.target.value ? Number(e.target.value) : undefined)}
                                    className={`${inputClass} ${!formData.fornecedor_id ? 'border-amber-400 focus:ring-amber-400' : 'border-green-300'}`}>
                                    <option value="">-- Selecione o Fornecedor --</option>
                                    {fornecedores.map(f => (
                                        <option key={f.id} value={f.id}>{f.nome_fantasia || f.nome}</option>
                                    ))}
                                </select>
                                {fornecedores.length === 0 && (
                                    <p className="text-xs text-red-500 mt-1">Nenhum fornecedor cadastrado. Cadastre um fornecedor antes de criar produtos.</p>
                                )}
                            </div>
                            <div>
                                <label className={labelClass}>Data da Compra</label>
                                <input type="date" value={formData.data_compra}
                                    onChange={e => field('data_compra', e.target.value)}
                                    className={inputClass} />
                            </div>
                            <div>
                                <label className={labelClass}>Data de Recebimento</label>
                                <input type="date" value={formData.data_recebimento}
                                    onChange={e => field('data_recebimento', e.target.value)}
                                    className={inputClass} />
                            </div>
                            <div>
                                <label className={labelClass}>Lote</label>
                                <input type="text" value={formData.lote}
                                    onChange={e => field('lote', e.target.value)}
                                    className={inputClass} placeholder="Ex: L2024-01" />
                            </div>
                        </div>
                    </div>
                </div>

                {/* ── Seção 3: Precificação ── */}
                <div>
                    <h4 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-3">Precificação e Lucro</h4>
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 p-6 bg-blue-50/50 dark:bg-blue-900/10 rounded-2xl border border-blue-100/50 dark:border-blue-900/30">
                        <div>
                            <label className="block text-sm font-semibold text-blue-800 dark:text-blue-300 mb-1">Preço de Custo (R$) *</label>
                            <input type="number" step="0.01" min="0.01" required
                                value={formData.preco_custo}
                                onChange={e => field('preco_custo', parseFloat(e.target.value) || 0)}
                                onBlur={calcularPrecoVenda}
                                className={`${inputClass} text-lg font-semibold border-blue-200 dark:border-blue-800`} />
                        </div>
                        <div>
                            <label className="block text-sm font-semibold text-blue-800 dark:text-blue-300 mb-1">Margem de Lucro (%)</label>
                            <input type="number" step="0.1" min="0"
                                value={formData.margem_lucro}
                                onChange={e => field('margem_lucro', parseFloat(e.target.value) || 0)}
                                onBlur={calcularPrecoVenda}
                                className={`${inputClass} text-lg font-semibold border-blue-200 dark:border-blue-800`} />
                        </div>
                        <div>
                            <label className="block text-sm font-semibold text-blue-800 dark:text-blue-300 mb-1">Preço de Venda (R$) *</label>
                            <input type="number" step="0.01" min="0.01" required
                                value={formData.preco_venda}
                                onChange={e => field('preco_venda', parseFloat(e.target.value) || 0)}
                                onBlur={calcularMargem}
                                className="w-full px-4 py-3 bg-blue-600 text-white border-transparent rounded-xl outline-none focus:ring-4 focus:ring-blue-500/30 text-lg font-bold shadow-lg shadow-blue-500/20" />
                        </div>
                    </div>
                </div>

                {/* ── Seção 4: Estoque e Validade ── */}
                <div>
                    <h4 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-3">Estoque e Validade</h4>
                    <div className={sectionClass}>
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                            <div>
                                <label className={labelClass}>Qtd. Atual</label>
                                <input type="number" min="0" value={formData.quantidade}
                                    onChange={e => field('quantidade', parseFloat(e.target.value) || 0)}
                                    className={inputClass} />
                            </div>
                            <div>
                                <label className={labelClass}>Qtd. Mínima</label>
                                <input type="number" min="0" value={formData.quantidade_minima}
                                    onChange={e => field('quantidade_minima', parseFloat(e.target.value) || 0)}
                                    className={inputClass} />
                            </div>
                            <div>
                                <label className={labelClass}>Data de Fabricação</label>
                                <input type="date" value={formData.data_fabricacao}
                                    onChange={e => field('data_fabricacao', e.target.value)}
                                    className={inputClass} />
                            </div>
                            <div>
                                <label className={labelClass}>Data de Validade</label>
                                <input type="date" value={formData.data_validade}
                                    onChange={e => field('data_validade', e.target.value)}
                                    className={`${inputClass} ${formData.data_validade && new Date(formData.data_validade) < new Date() ? 'border-red-400 bg-red-50 dark:bg-red-900/20' : ''}`} />
                            </div>
                        </div>
                    </div>
                </div>

                {/* ── Seção 5: Imagem e descrição ── */}
                <div>
                    <h4 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-3">Imagem e Detalhes</h4>
                    <div className={sectionClass}>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                            <div>
                                <label className={labelClass}>URL da Imagem</label>
                                <input type="url" value={formData.imagem_url}
                                    onChange={e => field('imagem_url', e.target.value)}
                                    className={inputClass} placeholder="https://..." />
                                {formData.imagem_url && (
                                    <img src={formData.imagem_url} alt="preview"
                                        className="mt-2 h-20 w-20 object-cover rounded-xl border border-gray-200 dark:border-gray-700"
                                        onError={e => (e.currentTarget.style.display = 'none')} />
                                )}
                            </div>
                            <div>
                                <label className={labelClass}>Descrição / Observações</label>
                                <textarea value={formData.descricao} rows={3}
                                    onChange={e => field('descricao', e.target.value)}
                                    className={`${inputClass} resize-none`} placeholder="Informações adicionais..." />
                            </div>
                        </div>
                        <div className="flex items-center gap-3 pt-2">
                            <input type="checkbox" id="ativo-check" checked={formData.ativo}
                                onChange={e => field('ativo', e.target.checked)}
                                className="w-4 h-4 text-blue-600 rounded" />
                            <label htmlFor="ativo-check" className="text-sm font-medium text-gray-700 dark:text-gray-300">
                                Produto ativo (visível no PDV)
                            </label>
                        </div>
                    </div>
                </div>

            </form>

            {showScanner && (
                <BarcodeScanner onScan={handleScanCodigo} onClose={() => setShowScanner(false)} />
            )}
        </ResponsiveModal>
    );
};

export default ProductFormModal;
