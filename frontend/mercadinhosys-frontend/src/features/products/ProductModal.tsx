import React, { memo } from 'react';
import { X, Save } from 'lucide-react';
import { Fornecedor } from '../../types';

interface ProductFormData {
    nome: string;
    codigo_barras: string;
    descricao: string;
    categoria: string;
    marca: string;
    fabricante: string;
    tipo: string;
    unidade_medida: string;
    preco_custo: number;
    preco_venda: number;
    margem_lucro: number;
    quantidade: number;
    quantidade_minima: number;
    fornecedor_id?: number;
    lote?: string;
    data_fabricacao?: string;
    data_validade?: string;
    ativo: boolean;
}

interface ProductModalProps {
    show: boolean;
    editMode: boolean;
    formData: ProductFormData;
    categorias: string[];
    fornecedores: Fornecedor[];
    onClose: () => void;
    onSubmit: (e: React.FormEvent) => void;
    onNomeChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
    onCodigoBarrasChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
    onCategoriaChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
    onMarcaChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
    onFabricanteChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
    onDescricaoChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => void;
    onFornecedorChange: (e: React.ChangeEvent<HTMLSelectElement>) => void;
    onTipoChange: (e: React.ChangeEvent<HTMLSelectElement>) => void;
    onUnidadeChange: (e: React.ChangeEvent<HTMLSelectElement>) => void;
    onPrecoCustoChange: (value: string) => void;
    onPrecoCustoBlur: () => void;
    onPrecoVendaChange: (value: string) => void;
    onPrecoVendaBlur: () => void;
    onMargemChange: (value: string) => void;
    onMargemBlur: () => void;
    onQuantidadeChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
    onQuantidadeMinimaChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
    onAtivoChange: (checked: boolean) => void;
    onLoteChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
    onDataFabricacaoChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
    onDataValidadeChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
}

const ProductModal: React.FC<ProductModalProps> = ({
    show,
    editMode,
    formData,
    categorias,
    fornecedores,
    onClose,
    onSubmit,
    onNomeChange,
    onCodigoBarrasChange,
    onCategoriaChange,
    onMarcaChange,
    onFabricanteChange,
    onDescricaoChange,
    onFornecedorChange,
    onTipoChange,
    onUnidadeChange,
    onPrecoCustoChange,
    onPrecoCustoBlur,
    onPrecoVendaChange,
    onPrecoVendaBlur,
    onMargemChange,
    onMargemBlur,
    onQuantidadeChange,
    onQuantidadeMinimaChange,
    onAtivoChange,
    onLoteChange,
    onDataFabricacaoChange,
    onDataValidadeChange,
}) => {
    if (!show) return null;

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
                <div className="sticky top-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4 flex justify-between items-center">
                    <h2 className="text-2xl font-bold text-gray-800 dark:text-white">
                        {editMode ? 'Editar Produto' : 'Novo Produto'}
                    </h2>
                    <button
                        onClick={onClose}
                        className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
                    >
                        <X className="w-6 h-6" />
                    </button>
                </div>

                <form onSubmit={onSubmit} className="p-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {/* Nome */}
                        <div className="md:col-span-2">
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                Nome do Produto *
                            </label>
                            <input
                                type="text"
                                required
                                value={formData.nome}
                                onChange={onNomeChange}
                                className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500"
                                placeholder="Ex: Coca-Cola 2L"
                            />
                        </div>

                        {/* Código de Barras */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                Código de Barras
                            </label>
                            <input
                                type="text"
                                value={formData.codigo_barras}
                                onChange={onCodigoBarrasChange}
                                className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500"
                                placeholder="7891234567890"
                            />
                        </div>

                        {/* Categoria */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                Categoria
                            </label>
                            <input
                                type="text"
                                required
                                value={formData.categoria}
                                onChange={onCategoriaChange}
                                className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500"
                                placeholder="Ex: Refrigerantes, Massas, Sabonetes"
                                list="categorias-list"
                            />
                            <datalist id="categorias-list">
                                {categorias.map((cat) => (
                                    <option key={cat} value={cat} />
                                ))}
                            </datalist>
                        </div>

                        {/* Marca */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                Marca
                            </label>
                            <input
                                type="text"
                                value={formData.marca}
                                onChange={onMarcaChange}
                                className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500"
                                placeholder="Ex: Coca-Cola"
                            />
                        </div>

                        {/* Fabricante */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                Fabricante
                            </label>
                            <input
                                type="text"
                                value={formData.fabricante}
                                onChange={onFabricanteChange}
                                className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500"
                                placeholder="Ex: Ambev"
                            />
                        </div>

                        {/* Fornecedor */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                Fornecedor
                            </label>
                            <select
                                value={formData.fornecedor_id || ''}
                                onChange={onFornecedorChange}
                                className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500"
                            >
                                <option value="">Selecione</option>
                                {fornecedores.map((fornecedor) => (
                                    <option key={fornecedor.id} value={fornecedor.id}>
                                        {fornecedor.nome}
                                    </option>
                                ))}
                            </select>
                        </div>

                        {/* Tipo */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                Tipo de Produto
                            </label>
                            <select
                                value={formData.tipo}
                                onChange={onTipoChange}
                                className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500"
                            >
                                <option value="Higiene">Higiene</option>
                                <option value="Limpeza">Limpeza</option>
                                <option value="Utilidades Domésticas">Utilidades Domésticas</option>
                                <option value="Perfumaria">Perfumaria</option>
                                <option value="Descartáveis">Descartáveis</option>
                                <option value="Hortifruti">Hortifruti</option>
                                <option value="Padaria">Padaria</option>
                                <option value="Carnes">Carnes (Açougue)</option>
                                <option value="Frios e Laticínios">Frios e Laticínios</option>
                                <option value="Mercearia">Mercearia</option>
                                <option value="Mercearia Seca">Mercearia Seca</option>
                                <option value="Massas e Grãos">Massas e Grãos</option>
                                <option value="Doces e Sobremesas">Doces e Sobremesas</option>
                                <option value="Snacks e Salgados">Snacks e Salgados</option>
                                <option value="Padaria e Confeitaria">Padaria e Confeitaria</option>
                                <option value="Matinais">Matinais</option>
                                <option value="Bebidas Não Alcoólicas">Bebidas Não Alcoólicas</option>
                                <option value="Bebidas Alcoólicas">Bebidas Alcoólicas</option>
                                <option value="Congelados">Congelados</option>
                                <option value="Rotisseria e Prontos">Rotisseria e Prontos</option>
                                <option value="Bazar e Utilidades">Bazar e Utilidades</option>
                                <option value="Bebê e Infantil">Bebê e Infantil</option>
                                <option value="Pet Shop">Pet Shop</option>
                            </select>
                        </div>

                        {/* Unidade de Medida */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                Unidade de Medida
                            </label>
                            <select
                                value={formData.unidade_medida}
                                onChange={onUnidadeChange}
                                className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500"
                            >
                                <option value="un">Unidade</option>
                                <option value="kg">Quilograma</option>
                                <option value="g">Grama</option>
                                <option value="l">Litro</option>
                                <option value="ml">Mililitro</option>
                                <option value="m">Metro</option>
                                <option value="cm">Centímetro</option>
                                <option value="cx">Caixa</option>
                                <option value="pct">Pacote</option>
                            </select>
                        </div>

                        {/* Preço de Custo */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                Preço de Custo *
                            </label>
                            <div className="relative">
                                <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500">
                                    R$
                                </span>
                                <input
                                    type="number"
                                    step="0.01"
                                    min="0"
                                    required
                                    value={formData.preco_custo}
                                    onChange={(e) => onPrecoCustoChange(e.target.value)}
                                    onBlur={onPrecoCustoBlur}
                                    className="w-full pl-10 pr-4 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500"
                                    placeholder="0.00"
                                />
                            </div>
                        </div>

                        {/* Preço de Venda */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                Preço de Venda *
                            </label>
                            <div className="relative">
                                <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500">
                                    R$
                                </span>
                                <input
                                    type="number"
                                    step="0.01"
                                    min="0"
                                    required
                                    value={formData.preco_venda}
                                    onChange={(e) => onPrecoVendaChange(e.target.value)}
                                    onBlur={onPrecoVendaBlur}
                                    className="w-full pl-10 pr-4 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500"
                                    placeholder="0.00"
                                />
                            </div>
                        </div>

                        {/* Margem de Lucro */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                Margem de Lucro (%)
                            </label>
                            <input
                                type="number"
                                step="0.1"
                                min="0"
                                value={formData.margem_lucro}
                                onChange={(e) => onMargemChange(e.target.value)}
                                onBlur={onMargemBlur}
                                className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500"
                                placeholder="30.0"
                            />
                        </div>

                        {/* Quantidade */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                Quantidade em Estoque *
                            </label>
                            <input
                                type="number"
                                step="0.01"
                                min="0"
                                required
                                value={formData.quantidade}
                                onChange={onQuantidadeChange}
                                className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500"
                                placeholder="0"
                            />
                        </div>

                        {/* Quantidade Mínima */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                Estoque Mínimo *
                            </label>
                            <input
                                type="number"
                                step="0.01"
                                min="0"
                                required
                                value={formData.quantidade_minima}
                                onChange={onQuantidadeMinimaChange}
                                className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500"
                                placeholder="10"
                            />
                        </div>
                        {/* Lote */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                Lote
                            </label>
                            <input
                                type="text"
                                value={formData.lote || ''}
                                onChange={onLoteChange}
                                className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500"
                                placeholder="Ex: L123456"
                            />
                        </div>

                        {/* Data de Fabricação */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                Data de Fabricação
                            </label>
                            <input
                                type="date"
                                value={formData.data_fabricacao || ''}
                                onChange={onDataFabricacaoChange}
                                className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500"
                            />
                        </div>

                        {/* Data de Validade */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                Data de Validade
                            </label>
                            <input
                                type="date"
                                value={formData.data_validade || ''}
                                onChange={onDataValidadeChange}
                                className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500"
                            />
                        </div>
                        {/* Descrição */}
                        <div className="md:col-span-2">
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                Descrição
                            </label>
                            <textarea
                                value={formData.descricao}
                                onChange={onDescricaoChange}
                                rows={3}
                                className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500"
                                placeholder="Descrição detalhada do produto..."
                            />
                        </div>

                        {/* Checkboxes */}
                        <div className="md:col-span-2 flex gap-6">
                            <label className="flex items-center space-x-2 cursor-pointer">
                                <input
                                    type="checkbox"
                                    checked={formData.ativo}
                                    onChange={(e) => onAtivoChange(e.target.checked)}
                                    className="w-5 h-5 text-blue-500 border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                                />
                                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                                    Produto Ativo
                                </span>
                            </label>
                        </div>
                    </div>

                    {/* Botões */}
                    <div className="mt-6 flex justify-end gap-3">
                        <button
                            type="button"
                            onClick={onClose}
                            className="px-6 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white text-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors"
                        >
                            Cancelar
                        </button>
                        <button
                            type="submit"
                            className="px-6 py-2.5 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors flex items-center gap-2"
                        >
                            <Save className="w-5 h-5" />
                            {editMode ? 'Atualizar' : 'Cadastrar'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

ProductModal.displayName = 'ProductModal';

export default memo(ProductModal);
