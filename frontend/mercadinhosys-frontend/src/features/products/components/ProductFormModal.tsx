import { useState, useEffect } from 'react';
import { Camera, Sparkles } from 'lucide-react';
import ResponsiveModal from '../../../components/ui/ResponsiveModal';
import { showToast } from '../../../utils/toast';
import { Produto } from '../../../types';
import { productsService } from '../productsService';
import { cosmosService } from '../../../services/cosmosService';
import BarcodeScanner from '../../pdv/components/BarcodeScanner';

interface ProductFormModalProps {
    show: boolean;
    editMode: boolean;
    produto: Produto | null;
    categorias: string[];
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
    ncm: '',
    cest: '',
    cfop_padrao: '5102',
    csosn: '102',
    tipo: '',
    unidade_medida: 'un',
    preco_custo: 0,
    preco_venda: 0,
    margem_lucro: 30,
    quantidade: 0,
    quantidade_minima: 10,
    ativo: true,
    imagem_url: '',
};

const ProductFormModal = ({
    show,
    editMode,
    produto,
    categorias,
    // Removendo fornecedores não utilizado
    onClose,
    onSuccess,
}: ProductFormModalProps) => {
    const [loading, setLoading] = useState(false);
    const [formData, setFormData] = useState({ ...emptyForm });
    const [showScanner, setShowScanner] = useState(false);
    const [isSearchingCosmos, setIsSearchingCosmos] = useState(false);
    const [showForceSync, setShowForceSync] = useState(false);

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
                ncm: (produto as any).ncm || '',
                cest: (produto as any).cest || '',
                cfop_padrao: (produto as any).cfop_padrao || '5102',
                csosn: (produto as any).csosn || '102',
                tipo: produto.tipo || '',
                unidade_medida: produto.unidade_medida || 'un',
                preco_custo: produto.preco_custo || 0,
                preco_venda: produto.preco_venda || 0,
                margem_lucro: produto.margem_lucro || 30,
                quantidade: produto.quantidade || 0,
                quantidade_minima: produto.quantidade_minima || 10,
                ativo: produto.ativo ?? true,
                imagem_url: produto.imagem_url || '',
            });
        } else {
            setFormData({ ...emptyForm });
        }
    }, [show, editMode, produto]);

    const handleScanCodigo = async (codigo: string, force: boolean = false) => {
        setShowScanner(false);
        setFormData(prev => ({ ...prev, codigo_barras: codigo }));
        setIsSearchingCosmos(true);
        setShowForceSync(false);
        const toastId = showToast.loading(force ? 'Forçando busca na Sefaz/Cosmos...' : 'Consultando banco de dados de produtos...');
        try {
            const res = await cosmosService.lookup(codigo, force);
            if (res.success && res.data) {
                const d = res.data;
                setFormData(prev => ({
                    ...prev,
                    nome: d.nome || prev.nome,
                    descricao: d.categoria || prev.descricao,
                    marca: d.marca || prev.marca,
                    ncm: d.ncm || prev.ncm,
                    cest: d.cest || prev.cest,
                    imagem_url: d.imagem_url || prev.imagem_url,
                }));
                const origem = res.source === 'catalogo' ? 'catálogo local' : 'Cosmos';
                const temNcm = d.ncm ? ` NCM ${d.ncm} preenchido.` : ' (sem NCM — preencha manualmente).';
                showToast.success(`Dados preenchidos (${origem}).${temNcm}`, { id: toastId });
            } else {
                // Mensagem verdadeira conforme a causa (não mais "não encontrado" genérico)
                const msg = res.message || 'Não foi possível consultar o produto.';
                if (res.code === 'nao_encontrado') {
                    showToast.error(msg, { id: toastId });
                    if (!force) setShowForceSync(true);
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
        if (!formData.preco_custo || formData.preco_custo <= 0) { showToast.error('Preço de custo inválido'); return; }
        if (!formData.preco_venda || formData.preco_venda <= 0) { showToast.error('Preço de venda inválido'); return; }

        setLoading(true);
        try {
            if (editMode && produto) {
                await showToast.promise(productsService.update(produto.id, formData), {
                    loading: 'Atualizando produto...',
                    success: 'Produto atualizado!',
                    error: 'Erro ao atualizar produto',
                }, { theme: 'warning' });
                onSuccess();
            } else {
                // Criar produto — tratando 409 (EAN duplicado) explicitamente
                const result = await productsService.create(formData);

                if (!result.success && (result.code === 'PRODUTO_DUPLICADO_EAN' || result.code === 'PRODUTO_DUPLICADO_CODIGO')) {
                    const existente = result.produto_existente;
                    const msg = existente
                        ? `Este produto já está cadastrado como "${existente.nome}" (id ${existente.id}). Edite o produto existente para atualizar estoque ou preço.`
                        : result.message || 'Produto já cadastrado com este EAN.';
                    showToast.error(msg, { duration: 8000 });
                    return; // Não chama onSuccess, não fecha o modal
                }

                if (!result.success) {
                    showToast.error(result.message || 'Erro ao criar produto');
                    return;
                }

                showToast.success('Produto cadastrado com sucesso!');
                onSuccess();
            }
        } catch (err: any) {
            showToast.error(err?.response?.data?.message || 'Erro ao salvar produto');
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
                                        onChange={e => {
                                            field('codigo_barras', e.target.value);
                                            setShowForceSync(false);
                                        }}
                                        className={`${inputClass} font-mono`} placeholder="EAN-13 / EAN-8" />
                                    <button type="button" onClick={() => setShowScanner(true)}
                                        className="p-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl hover:bg-gray-50 text-blue-600 shadow-sm">
                                        <Camera className="w-5 h-5" />
                                    </button>
                                </div>
                                {showForceSync && formData.codigo_barras && (
                                    <button type="button" onClick={() => handleScanCodigo(formData.codigo_barras, true)}
                                        className="mt-2 w-full py-2 px-3 text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg flex items-center justify-center gap-2 transition-colors">
                                        <Sparkles className="w-4 h-4" />
                                        Forçar Busca na API Cosmos
                                    </button>
                                )}
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

                {/* ── Seção Tributação ── */}
                <div>
                    <h4 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-3">Tributação (NFC-e / NF-e)</h4>
                    <div className={sectionClass}>
                        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
                            <div>
                                <label className={labelClass}>NCM</label>
                                <input type="text" inputMode="numeric" maxLength={8} value={formData.ncm}
                                    onChange={e => field('ncm', e.target.value.replace(/\D/g, '').slice(0, 8))}
                                    className={`${inputClass} ${formData.ncm && formData.ncm.length !== 8 ? 'border-amber-400' : ''}`}
                                    placeholder="8 dígitos" />
                                {formData.ncm && formData.ncm.length !== 8 && (
                                    <p className="text-xs text-amber-600 mt-1">Deve ter 8 dígitos.</p>
                                )}
                            </div>
                            <div>
                                <label className={labelClass}>CEST</label>
                                <input type="text" inputMode="numeric" maxLength={7} value={formData.cest}
                                    onChange={e => field('cest', e.target.value.replace(/\D/g, '').slice(0, 7))}
                                    className={inputClass} placeholder="7 dígitos" />
                            </div>
                            <div>
                                <label className={labelClass}>CFOP Padrão</label>
                                <input type="text" inputMode="numeric" maxLength={4} value={formData.cfop_padrao}
                                    onChange={e => field('cfop_padrao', e.target.value.replace(/\D/g, '').slice(0, 4))}
                                    className={inputClass} placeholder="Ex: 5102" />
                            </div>
                            <div>
                                <label className={labelClass}>CSOSN (Simples)</label>
                                <input type="text" inputMode="numeric" maxLength={3} value={formData.csosn}
                                    onChange={e => field('csosn', e.target.value.replace(/\D/g, '').slice(0, 3))}
                                    className={inputClass} placeholder="Ex: 102" />
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

                {/* ── Seção 4: Estoque Mínimo ── */}
                <div>
                    <h4 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-3">Controle de Estoque</h4>
                    <div className={sectionClass}>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                            <div>
                                <label className={labelClass}>Qtd. Mínima (Alerta)</label>
                                <input type="number" min="0" value={formData.quantidade_minima}
                                    onChange={e => field('quantidade_minima', parseFloat(e.target.value) || 0)}
                                    className={inputClass} />
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
