import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Truck, Plus, Search, Edit, Trash2, Phone, Mail, MapPin, Package, Users, TrendingUp, AlertCircle } from 'lucide-react';
import { Fornecedor } from '../../types';
import { apiClient } from '../../api/apiClient';
import { Toaster, toast } from 'react-hot-toast';

interface SupplierFormData {
    nome: string;
    cnpj: string;
    telefone: string;
    email: string;
    endereco: string;
    cidade: string;
    estado: string;
    cep: string;
    contato_principal: string;
    observacoes: string;
    ativo: boolean;
}

const SuppliersPage: React.FC = () => {
    const [suppliers, setSuppliers] = useState<Fornecedor[]>([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);
    const [editMode, setEditMode] = useState(false);
    const [selectedSupplier, setSelectedSupplier] = useState<Fornecedor | null>(null);
    const [searchTerm, setSearchTerm] = useState('');
    const [filterStatus, setFilterStatus] = useState<'all' | 'active' | 'inactive'>('all');

    const [formData, setFormData] = useState<SupplierFormData>({
        nome: '',
        cnpj: '',
        telefone: '',
        email: '',
        endereco: '',
        cidade: '',
        estado: '',
        cep: '',
        contato_principal: '',
        observacoes: '',
        ativo: true,
    });

    // Calcular estatísticas
    const stats = useMemo(() => {
        const total = suppliers.length;
        const ativos = suppliers.filter(s => s.ativo).length;
        const inativos = total - ativos;
        
        const por_estado: { [key: string]: number } = {};
        suppliers.forEach(s => {
            if (s.estado) {
                por_estado[s.estado] = (por_estado[s.estado] || 0) + 1;
            }
        });

        const com_produtos = suppliers.filter(s => (s.total_produtos || 0) > 0).length;
        const sem_produtos = total - com_produtos;

        return {
            total,
            ativos,
            inativos,
            por_estado,
            com_produtos,
            sem_produtos,
        };
    }, [suppliers]);

    const estadoMaisComum = useMemo(() => {
        const estados = Object.entries(stats.por_estado);
        if (estados.length === 0) return '-';
        return estados.reduce((a, b) => a[1] > b[1] ? a : b)[0];
    }, [stats]);

    const loadSuppliers = useCallback(async () => {
        try {
            setLoading(true);
            const response = await apiClient.get<{ fornecedores: Fornecedor[] }>('/fornecedores/', {
                params: {
                    per_page: 200,
                    ordenar_por: 'nome',
                },
            });
            setSuppliers(response.data.fornecedores || []);
        } catch (error) {
            console.error('Erro ao carregar fornecedores:', error);
            toast.error('Erro ao carregar fornecedores');
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        loadSuppliers();
    }, [loadSuppliers]);

    const resetForm = () => {
        setFormData({
            nome: '',
            cnpj: '',
            telefone: '',
            email: '',
            endereco: '',
            cidade: '',
            estado: '',
            cep: '',
            contato_principal: '',
            observacoes: '',
            ativo: true,
        });
        setEditMode(false);
        setSelectedSupplier(null);
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        try {
            if (editMode && selectedSupplier) {
                await apiClient.put(`/fornecedores/${selectedSupplier.id}`, formData);
                toast.success('Fornecedor atualizado com sucesso!');
            } else {
                await apiClient.post('/fornecedores/', formData);
                toast.success('Fornecedor cadastrado com sucesso!');
            }

            setShowModal(false);
            resetForm();
            loadSuppliers();
        } catch (error: unknown) {
            console.error('Erro ao salvar fornecedor:', error);
            const apiError = error as { response?: { data?: { error?: string } } };
            toast.error(apiError.response?.data?.error || 'Erro ao salvar fornecedor');
        }
    };

    const handleEdit = (supplier: Fornecedor) => {
        setSelectedSupplier(supplier);
        setFormData({
            nome: supplier.nome,
            cnpj: supplier.cnpj || '',
            telefone: supplier.telefone || '',
            email: supplier.email || '',
            endereco: supplier.endereco || '',
            cidade: supplier.cidade || '',
            estado: supplier.estado || '',
            cep: supplier.cep || '',
            contato_principal: supplier.contato_principal || '',
            observacoes: supplier.observacoes || '',
            ativo: supplier.ativo,
        });
        setEditMode(true);
        setShowModal(true);
    };

    const handleDelete = async (id: number) => {
        if (!window.confirm('Tem certeza que deseja desativar este fornecedor?')) return;

        try {
            await apiClient.delete(`/fornecedores/${id}`);
            toast.success('Fornecedor desativado com sucesso!');
            loadSuppliers();
        } catch (error) {
            console.error('Erro ao desativar fornecedor:', error);
            toast.error('Erro ao desativar fornecedor');
        }
    };

    const filteredSuppliers = suppliers.filter(supplier => {
        const matchesSearch = supplier.nome.toLowerCase().includes(searchTerm.toLowerCase()) ||
            supplier.cnpj?.toLowerCase().includes(searchTerm.toLowerCase()) ||
            supplier.cidade?.toLowerCase().includes(searchTerm.toLowerCase());
        
        const matchesStatus = filterStatus === 'all' ? true :
            filterStatus === 'active' ? supplier.ativo :
            !supplier.ativo;

        return matchesSearch && matchesStatus;
    });

    const handleCardClick = useCallback((type: string) => {
        switch(type) {
            case 'all':
                setFilterStatus('all');
                break;
            case 'active':
                setFilterStatus('active');
                break;
            case 'inactive':
                setFilterStatus('inactive');
                break;
            case 'with-products':
                // Filtrar fornecedores com produtos
                setFilterStatus('all');
                break;
            case 'without-products':
                // Filtrar fornecedores sem produtos
                setFilterStatus('all');
                break;
        }
    }, []);

    return (
        <div className="space-y-6 p-6">
            <Toaster position="top-right" />

            {/* Header */}
            <div className="flex justify-between items-start">
                <div>
                    <h1 className="text-3xl font-bold text-gray-800 dark:text-white mb-2">
                        Fornecedores
                    </h1>
                    <p className="text-gray-600 dark:text-gray-400">
                        Gerencie seus fornecedores e parcerias
                    </p>
                </div>
                <button
                    onClick={() => {
                        resetForm();
                        setShowModal(true);
                    }}
                    className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 flex items-center gap-2 transition-colors"
                >
                    <Plus className="w-5 h-5" />
                    <span>Novo Fornecedor</span>
                </button>
            </div>

            {/* Dashboard de Estatísticas */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {/* Total de Fornecedores */}
                <div 
                    onClick={() => handleCardClick('all')}
                    className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl shadow-lg p-6 text-white cursor-pointer hover:shadow-2xl hover:scale-105 transition-all duration-200"
                >
                    <div className="flex items-center justify-between mb-2">
                        <Truck className="w-8 h-8 opacity-80" />
                        <Users className="w-5 h-5" />
                    </div>
                    <p className="text-sm opacity-90 mb-1">Total Fornecedores</p>
                    <p className="text-3xl font-bold">{stats.total}</p>
                    <p className="text-xs opacity-75 mt-2">Clique para ver todos</p>
                </div>

                {/* Fornecedores Ativos */}
                <div 
                    onClick={() => handleCardClick('active')}
                    className="bg-gradient-to-br from-green-500 to-green-600 rounded-xl shadow-lg p-6 text-white cursor-pointer hover:shadow-2xl hover:scale-105 transition-all duration-200"
                >
                    <div className="flex items-center justify-between mb-2">
                        <TrendingUp className="w-8 h-8 opacity-80" />
                        <Package className="w-5 h-5" />
                    </div>
                    <p className="text-sm opacity-90 mb-1">Fornecedores Ativos</p>
                    <p className="text-3xl font-bold">{stats.ativos}</p>
                    <p className="text-xs opacity-75 mt-2">Clique para filtrar ativos</p>
                </div>

                {/* Fornecedores Inativos */}
                <div 
                    onClick={() => handleCardClick('inactive')}
                    className={`bg-gradient-to-br from-red-500 to-red-600 rounded-xl shadow-lg p-6 text-white cursor-pointer hover:shadow-2xl hover:scale-105 transition-all duration-200 ${stats.inativos > 0 ? 'animate-pulse' : ''}`}
                >
                    <div className="flex items-center justify-between mb-2">
                        <AlertCircle className="w-8 h-8 opacity-80" />
                        <Trash2 className="w-5 h-5" />
                    </div>
                    <p className="text-sm opacity-90 mb-1">Fornecedores Inativos</p>
                    <p className="text-3xl font-bold">{stats.inativos}</p>
                    <p className="text-xs opacity-75 mt-2">{stats.inativos > 0 ? '⚠️ Requer atenção' : 'Tudo OK'}</p>
                </div>

                {/* Estado com Mais Fornecedores */}
                <div 
                    className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl shadow-lg p-6 text-white"
                >
                    <div className="flex items-center justify-between mb-2">
                        <MapPin className="w-8 h-8 opacity-80" />
                        <TrendingUp className="w-5 h-5" />
                    </div>
                    <p className="text-sm opacity-90 mb-1">Região Principal</p>
                    <p className="text-3xl font-bold">{estadoMaisComum}</p>
                    <p className="text-xs opacity-75 mt-2">
                        {stats.por_estado[estadoMaisComum] || 0} fornecedores
                    </p>
                </div>
            </div>

            {/* Search */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
                <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                        type="text"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        placeholder="Buscar por nome, CNPJ ou cidade..."
                        className="w-full pl-10 pr-4 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                </div>
            </div>

            {/* Grid de Fornecedores */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {loading ? (
                    <div className="col-span-full flex justify-center py-12">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
                    </div>
                ) : filteredSuppliers.length === 0 ? (
                    <div className="col-span-full text-center py-12">
                        <Truck className="w-16 h-16 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
                        <p className="text-gray-500 dark:text-gray-400 text-lg">
                            Nenhum fornecedor encontrado
                        </p>
                    </div>
                ) : (
                    filteredSuppliers.map((supplier) => (
                        <div
                            key={supplier.id}
                            className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow"
                        >
                            <div className="flex items-start justify-between mb-4">
                                <div className="flex items-center gap-3">
                                    <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg flex items-center justify-center">
                                        <Truck className="w-6 h-6 text-white" />
                                    </div>
                                    <div>
                                        <h3 className="font-bold text-gray-900 dark:text-white">
                                            {supplier.nome}
                                        </h3>
                                        {supplier.cnpj && (
                                            <p className="text-sm text-gray-500 dark:text-gray-400">
                                                {supplier.cnpj}
                                            </p>
                                        )}
                                    </div>
                                </div>
                                <span
                                    className={`px-2 py-1 text-xs rounded-full ${
                                        supplier.ativo
                                            ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300'
                                            : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300'
                                    }`}
                                >
                                    {supplier.ativo ? 'Ativo' : 'Inativo'}
                                </span>
                            </div>

                            <div className="space-y-2 mb-4">
                                {supplier.telefone && (
                                    <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                                        <Phone className="w-4 h-4" />
                                        <span>{supplier.telefone}</span>
                                    </div>
                                )}
                                {supplier.email && (
                                    <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                                        <Mail className="w-4 h-4" />
                                        <span>{supplier.email}</span>
                                    </div>
                                )}
                                {supplier.cidade && (
                                    <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                                        <MapPin className="w-4 h-4" />
                                        <span>{supplier.cidade} - {supplier.estado}</span>
                                    </div>
                                )}
                            </div>

                            <div className="flex gap-2 pt-4 border-t border-gray-200 dark:border-gray-700">
                                <button
                                    onClick={() => handleEdit(supplier)}
                                    className="flex-1 px-3 py-2 bg-blue-50 text-blue-600 dark:bg-blue-900/20 dark:text-blue-400 rounded-lg hover:bg-blue-100 dark:hover:bg-blue-900/30 transition-colors flex items-center justify-center gap-2"
                                >
                                    <Edit className="w-4 h-4" />
                                    Editar
                                </button>
                                <button
                                    onClick={() => handleDelete(supplier.id)}
                                    className="flex-1 px-3 py-2 bg-red-50 text-red-600 dark:bg-red-900/20 dark:text-red-400 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/30 transition-colors flex items-center justify-center gap-2"
                                >
                                    <Trash2 className="w-4 h-4" />
                                    Desativar
                                </button>
                            </div>
                        </div>
                    ))
                )}
            </div>

            {/* Modal de Cadastro/Edição */}
            {showModal && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
                        <div className="sticky top-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4">
                            <h2 className="text-2xl font-bold text-gray-800 dark:text-white">
                                {editMode ? 'Editar Fornecedor' : 'Novo Fornecedor'}
                            </h2>
                        </div>

                        <form onSubmit={handleSubmit} className="p-6">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div className="md:col-span-2">
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                        Nome do Fornecedor *
                                    </label>
                                    <input
                                        type="text"
                                        required
                                        value={formData.nome}
                                        onChange={(e) => setFormData({ ...formData, nome: e.target.value })}
                                        className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500"
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                        CNPJ
                                    </label>
                                    <input
                                        type="text"
                                        value={formData.cnpj}
                                        onChange={(e) => setFormData({ ...formData, cnpj: e.target.value })}
                                        className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500"
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                        Telefone
                                    </label>
                                    <input
                                        type="text"
                                        value={formData.telefone}
                                        onChange={(e) => setFormData({ ...formData, telefone: e.target.value })}
                                        className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500"
                                    />
                                </div>

                                <div className="md:col-span-2">
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                        E-mail
                                    </label>
                                    <input
                                        type="email"
                                        value={formData.email}
                                        onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                                        className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500"
                                    />
                                </div>

                                <div className="md:col-span-2">
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                        Endereço
                                    </label>
                                    <input
                                        type="text"
                                        value={formData.endereco}
                                        onChange={(e) => setFormData({ ...formData, endereco: e.target.value })}
                                        className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500"
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                        Cidade
                                    </label>
                                    <input
                                        type="text"
                                        value={formData.cidade}
                                        onChange={(e) => setFormData({ ...formData, cidade: e.target.value })}
                                        className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500"
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                        Estado
                                    </label>
                                    <input
                                        type="text"
                                        maxLength={2}
                                        value={formData.estado}
                                        onChange={(e) => setFormData({ ...formData, estado: e.target.value.toUpperCase() })}
                                        className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500"
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                        CEP
                                    </label>
                                    <input
                                        type="text"
                                        value={formData.cep}
                                        onChange={(e) => setFormData({ ...formData, cep: e.target.value })}
                                        className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500"
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                        Contato Principal
                                    </label>
                                    <input
                                        type="text"
                                        value={formData.contato_principal}
                                        onChange={(e) => setFormData({ ...formData, contato_principal: e.target.value })}
                                        className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500"
                                    />
                                </div>

                                <div className="md:col-span-2">
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                        Observações
                                    </label>
                                    <textarea
                                        rows={3}
                                        value={formData.observacoes}
                                        onChange={(e) => setFormData({ ...formData, observacoes: e.target.value })}
                                        className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500"
                                    />
                                </div>

                                <div className="md:col-span-2">
                                    <label className="flex items-center space-x-2 cursor-pointer">
                                        <input
                                            type="checkbox"
                                            checked={formData.ativo}
                                            onChange={(e) => setFormData({ ...formData, ativo: e.target.checked })}
                                            className="w-5 h-5 text-blue-500 border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                                        />
                                        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                                            Fornecedor Ativo
                                        </span>
                                    </label>
                                </div>
                            </div>

                            <div className="mt-6 flex justify-end gap-3">
                                <button
                                    type="button"
                                    onClick={() => {
                                        setShowModal(false);
                                        resetForm();
                                    }}
                                    className="px-6 py-2.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white text-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors"
                                >
                                    Cancelar
                                </button>
                                <button
                                    type="submit"
                                    className="px-6 py-2.5 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
                                >
                                    {editMode ? 'Atualizar' : 'Cadastrar'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default SuppliersPage;
