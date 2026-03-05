import React, { useEffect, useState } from 'react';
import { Cliente } from '../../types';
import CustomerTable from './components/CustomerTable';
import CustomerDetailsModal from './components/CustomerDetailsModal.tsx';
import CustomerForm from './components/CustomerForm';
import CustomerDashboard from './components/CustomerDashboard';
import { customerService } from './customerService';
import { apiClient } from '../../api/apiClient';
import { pdvService } from '../pdv/pdvService';
import { Button, Typography, CircularProgress, TextField, Box, FormControl, InputLabel, Select, MenuItem, InputAdornment, Chip, Tooltip, Menu, Dialog, DialogTitle, DialogContent, DialogActions } from '@mui/material';
import { showToast } from '../../utils/toast';
import SearchIcon from '@mui/icons-material/Search';
import FilterListIcon from '@mui/icons-material/FilterList';
import ClearIcon from '@mui/icons-material/Clear';
import GetAppIcon from '@mui/icons-material/GetApp';
import SyncIcon from '@mui/icons-material/Sync';
import PersonAddAlt1Icon from '@mui/icons-material/PersonAddAlt1';
import HandshakeIcon from '@mui/icons-material/Handshake';
import AttachMoneyIcon from '@mui/icons-material/AttachMoney';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import jsPDF from "jspdf";
import autoTable from "jspdf-autotable";
import * as XLSX from "xlsx";


const CustomersPage: React.FC = () => {
    const [clientes, setClientes] = useState<Cliente[]>([]);
    const [loading, setLoading] = useState(false);
    const [formOpen, setFormOpen] = useState(false);
    const [editData, setEditData] = useState<Partial<Cliente> | undefined>(undefined);
    const [saving, setSaving] = useState(false);
    const [selectedCliente, setSelectedCliente] = useState<Cliente | null>(null);
    const [clienteDetalhado, setClienteDetalhado] = useState<Cliente | null>(null);
    const [detalheLoading, setDetalheLoading] = useState(false);
    const [dashboard, setDashboard] = useState<{
        total: number;
        total_gasto: number;
        total_devido: number;
        melhor_cliente_nome: string;
        melhor_cliente_valor: number;
        maior_devedor_nome: string;
        maior_devedor_valor: number;
    }>({
        total: 0,
        total_gasto: 0,
        total_devido: 0,
        melhor_cliente_nome: "Nenhum",
        melhor_cliente_valor: 0,
        maior_devedor_nome: "Nenhum",
        maior_devedor_valor: 0
    });
    const [searchTerm, setSearchTerm] = useState('');
    const [statusFilter, setStatusFilter] = useState<string>('todos');
    const [fiadoFilter, setFiadoFilter] = useState(false);
    const [filteredClientes, setFilteredClientes] = useState<Cliente[]>([]);
    const [exportMenuAnchor, setExportMenuAnchor] = useState<null | HTMLElement>(null);

    // Estado do Modal de Fiado
    const [fiadoModal, setFiadoModal] = useState<{ open: boolean; cliente: Cliente | null }>({ open: false, cliente: null });
    const [fiadoValor, setFiadoValor] = useState('');
    const [fiadoForma, setFiadoForma] = useState('Dinheiro');
    const [fiadoLoading, setFiadoLoading] = useState(false);
    const [recalcLoading, setRecalcLoading] = useState(false);

    const handleRecalcularMetricas = async () => {
        setRecalcLoading(true);
        try {
            const res = await apiClient.post('/clientes/recalcular-metricas');
            showToast.success(res.data.message || 'Métricas recalculadas com sucesso!');
            fetchClientes();
            fetchDashboard();
        } catch {
            showToast.error('Erro ao recalcular métricas');
        } finally {
            setRecalcLoading(false);
        }
    };

    // Indicadores de Fiado
    const clientesComFiado = clientes.filter(c => (c.saldo_devedor ?? 0) > 0);
    const totalFiadoAberto = clientesComFiado.reduce((acc, c) => acc + (c.saldo_devedor ?? 0), 0);
    const maiorDevedor = clientesComFiado.length > 0
        ? clientesComFiado.reduce((prev, curr) => (curr.saldo_devedor ?? 0) > (prev.saldo_devedor ?? 0) ? curr : prev)
        : null;

    const fetchDashboard = async () => {
        try {
            const res = await apiClient.get('/clientes/');
            if (res.data && res.data.estatisticas) {
                setDashboard({
                    total: res.data.estatisticas.total || 0,
                    total_gasto: res.data.estatisticas.total_gasto || 0,
                    total_devido: res.data.estatisticas.total_devido || 0,
                    melhor_cliente_nome: res.data.estatisticas.melhor_cliente_nome || "Nenhum",
                    melhor_cliente_valor: res.data.estatisticas.melhor_cliente_valor || 0,
                    maior_devedor_nome: res.data.estatisticas.maior_devedor_nome || "Nenhum",
                    maior_devedor_valor: res.data.estatisticas.maior_devedor_valor || 0,
                });
            }
        } catch {
            showToast.error('Erro ao carregar métricas do dashboard');
        }
    };

    const fetchClientes = async () => {
        setLoading(true);
        try {
            const data = await customerService.list();
            setClientes(data);
        } catch {
            showToast.error('Erro ao carregar clientes');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchDashboard();
        fetchClientes();
    }, []);

    // Atalhos de teclado
    useEffect(() => {
        const handleKeyPress = (event: KeyboardEvent) => {
            // Só funciona se não estiver digitando em um input
            if (event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement) {
                return;
            }

            switch (event.key) {
                case 'n':
                case 'N':
                    if (!formOpen && !selectedCliente) {
                        event.preventDefault();
                        handleAdd();
                    }
                    break;
                case 'Escape':
                    if (formOpen) {
                        event.preventDefault();
                        setFormOpen(false);
                        setEditData(undefined);
                    } else if (selectedCliente) {
                        event.preventDefault();
                        setSelectedCliente(null);
                        setClienteDetalhado(null);
                    }
                    break;
            }
        };

        document.addEventListener('keydown', handleKeyPress);
        return () => document.removeEventListener('keydown', handleKeyPress);
    }, [formOpen, selectedCliente]);

    // Filtragem em tempo real
    useEffect(() => {
        let filtered = clientes;

        if (statusFilter !== 'todos') {
            filtered = filtered.filter(cliente => {
                if (statusFilter === 'ativos') return cliente.ativo === true;
                if (statusFilter === 'inativos') return cliente.ativo === false;
                return true;
            });
        }

        if (fiadoFilter) {
            filtered = filtered.filter(c => (c.saldo_devedor ?? 0) > 0);
        }

        if (searchTerm.trim()) {
            const term = searchTerm.toLowerCase();
            filtered = filtered.filter(cliente =>
                cliente.nome?.toLowerCase().includes(term) ||
                cliente.cpf?.includes(term) ||
                cliente.email?.toLowerCase().includes(term) ||
                cliente.celular?.includes(term)
            );
        }

        setFilteredClientes(filtered);
    }, [clientes, searchTerm, statusFilter, fiadoFilter]);

    const handleAbrirModalFiado = (cliente: Cliente) => {
        setFiadoModal({ open: true, cliente });
        setFiadoValor('');
        setFiadoForma('Dinheiro');
    };

    const handlePagarFiado = async () => {
        const { cliente } = fiadoModal;
        if (!cliente?.id) return;
        const valor = parseFloat(fiadoValor.replace(',', '.'));
        if (isNaN(valor) || valor <= 0) {
            showToast.error('Informe um valor válido');
            return;
        }
        setFiadoLoading(true);
        try {
            const res = await pdvService.pagarFiado(cliente.id, valor, fiadoForma);
            showToast.success(res.message || 'Pagamento registrado!');
            setFiadoModal({ open: false, cliente: null });
            fetchClientes();
        } catch (err: any) {
            const msg = err?.response?.data?.message || 'Erro ao registrar pagamento';
            showToast.error(msg);
        } finally {
            setFiadoLoading(false);
        }
    };

    const handleAdd = () => {
        setEditData(undefined);
        setFormOpen(true);
    };

    const handleEdit = async (cliente: Cliente) => {
        if (!cliente || !cliente.id) {
            showToast.error('Erro: Cliente inválido para edição');
            return;
        }

        setSaving(true);
        try {
            const res = await apiClient.get(`/clientes/${cliente.id}`);
            const clienteData = { ...res.data.cliente, id: cliente.id };
            setEditData(clienteData);
            setFormOpen(true);
            setSelectedCliente(null);
        } catch (err: any) {
            showToast.error('Erro ao buscar dados do cliente para edição');
        } finally {
            setSaving(false);
        }
    };

    const handleRowClick = async (cliente: Cliente) => {
        if (!cliente || !cliente.id) {
            return;
        }

        setDetalheLoading(true);
        setSelectedCliente(cliente);
        try {
            const res = await apiClient.get(`/clientes/${cliente.id}`);
            const detalhado = res.data.cliente ? { ...res.data.cliente, ...res.data } : res.data;
            setClienteDetalhado(detalhado);
        } catch (err: any) {
            setClienteDetalhado(null);
            setSelectedCliente(null);
            showToast.error('Erro ao buscar detalhes do cliente');
        } finally {
            setDetalheLoading(false);
        }
    };

    const handleDelete = async (cliente: Cliente) => {
        if (!cliente || !cliente.id) {
            showToast.error('Erro: Cliente inválido para exclusão');
            return;
        }

        const confirmed = window.confirm(
            `Tem certeza que deseja excluir o cliente "${cliente.nome}"?\n\nEsta ação não pode ser desfeita e removerá permanentemente todos os dados do cliente.`
        );
        if (!confirmed) return;

        try {
            await showToast.promise(customerService.remove(cliente.id), {
                loading: 'Excluindo cliente...',
                success: `Cliente "${cliente.nome}" excluído com sucesso`,
                error: 'Erro ao excluir cliente'
            }, { theme: 'error' });
            fetchClientes();
            fetchDashboard();
        } catch (error: unknown) {
            const err = error as { response?: { status?: number; data?: { message?: string; vinculos?: { vendas: number; contas_a_receber: number } } } };

            // Tratamento específico para erro de vínculos (400)
            if (err.response?.status === 400 && err.response?.data?.vinculos) {
                const { vendas, contas_a_receber } = err.response.data.vinculos;
                const msg = `Não é possível excluir este cliente pois ele possui registros vinculados:\n` +
                    `• ${vendas} Vendas\n` +
                    `• ${contas_a_receber} Débitos em Aberto\n\n` +
                    `Deseja DESATIVAR o cliente em vez de excluir?\n` +
                    `Isso impedirá novas vendas mas manterá o histórico.`;

                if (window.confirm(msg)) {
                    try {
                        await apiClient.patch(`/clientes/${cliente.id}/status`, { ativo: false });
                        showToast.error(`Cliente "${cliente.nome}" desativado com sucesso`);
                        fetchClientes();
                        fetchDashboard();
                    } catch (patchErr: unknown) {
                        const patchMsg = (patchErr as { response?: { data?: { message?: string } } })?.response?.data?.message || 'Erro ao desativar cliente';
                        showToast.error(patchMsg);
                    }
                    return; // Interrompe para não mostrar o erro original
                }
            }

            const errorMessage = err.response?.data?.message || 'Erro ao excluir cliente';
            showToast.error(errorMessage);
        } finally {
            setSaving(false);
        }
    };

    const handleSave = async (data: Partial<Cliente>) => {
        try {
            const promise = editData && editData.id
                ? customerService.update(editData.id, data)
                : customerService.create(data);

            const savedCustomer = await showToast.promise(promise, {
                loading: editData && editData.id ? 'Atualizando cliente...' : 'Cadastrando cliente...',
                success: editData && editData.id ? 'Cliente atualizado com sucesso' : 'Cliente cadastrado com sucesso',
                error: 'Erro ao salvar cliente'
            });

            if (editData && editData.id) {
                // Atualizar na lista local
                setClientes(prev => prev.map(c => c.id === editData.id ? { ...c, ...savedCustomer } : c));
            } else {
                // Adicionar no topo da lista local
                setClientes(prev => [savedCustomer, ...prev]);
                setSearchTerm(''); // Limpar busca para mostrar o novo cliente
            }

            setFormOpen(false);
            setEditData(undefined);

            // fetchClientes() e fetchDashboard() podem rodar em background para garantir sincronia total
            fetchClientes();
            fetchDashboard();
        } catch (error: unknown) {
            if (
                typeof error === 'object' &&
                error !== null &&
                'response' in error &&
                typeof (error as { response?: { data?: { message?: string; error?: string } } }).response === 'object'
            ) {
                const errResponse = (error as { response?: { data?: { message?: string; error?: string } } }).response;
                const errorMessage = errResponse?.data?.message || errResponse?.data?.error || 'Erro ao salvar cliente';
                showToast.error(errorMessage);
            } else {
                showToast.error('Erro ao salvar cliente');
            }
        } finally {
            setSaving(false);
        }
    };

    // Função de exportação
    const handleExportClick = (event: React.MouseEvent<HTMLButtonElement>) => {
        setExportMenuAnchor(event.currentTarget);
    };

    const handleExportClose = () => {
        setExportMenuAnchor(null);
    };

    const exportarCSV = () => {
        const csvContent = [
            ['Nome', 'CPF', 'Telefone', 'Email', 'Endereço', 'Status', 'Data Cadastro', 'Total Compras'],
            ...filteredClientes.map(cliente => [
                cliente.nome || '',
                cliente.cpf || '',
                cliente.celular || cliente.telefone || '',
                cliente.email || '',
                cliente.endereco_completo || '',
                cliente.ativo ? 'Ativo' : 'Inativo',
                cliente.data_cadastro ? new Date(cliente.data_cadastro).toLocaleDateString('pt-BR') : '',
                cliente.total_compras?.toString() || '0'
            ])
        ].map(row => row.map(cell => `"${cell}"`).join(',')).join('\n');

        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', `clientes_${new Date().toISOString().split('T')[0]}.csv`);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        handleExportClose();
        showToast.info('CSV exportado com sucesso');
    };

    const exportarExcel = () => {
        const wsData = [
            ['Nome', 'CPF', 'Telefone', 'Email', 'Endereço', 'Status', 'Data Cadastro', 'Total Compras'],
            ...filteredClientes.map(cliente => [
                cliente.nome || '',
                cliente.cpf || '',
                cliente.celular || cliente.telefone || '',
                cliente.email || '',
                cliente.endereco_completo || '',
                cliente.ativo ? 'Ativo' : 'Inativo',
                cliente.data_cadastro ? new Date(cliente.data_cadastro).toLocaleDateString('pt-BR') : '',
                cliente.total_compras || 0
            ])
        ];

        const ws = XLSX.utils.aoa_to_sheet(wsData);
        const wb = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(wb, ws, "Clientes");
        XLSX.writeFile(wb, `clientes_${new Date().toISOString().split('T')[0]}.xlsx`);

        handleExportClose();
        showToast.info('Excel exportado com sucesso');
    };

    const exportarPDF = () => {
        const doc = new jsPDF();

        // Cabeçalho
        doc.setFillColor(25, 118, 210); // Cor primária (Blue 700)
        doc.rect(0, 0, 210, 40, 'F');

        doc.setTextColor(255, 255, 255);
        doc.setFontSize(22);
        doc.text("Relatório de Clientes", 105, 20, { align: "center" });

        doc.setFontSize(10);
        doc.text(`Gerado em: ${new Date().toLocaleDateString("pt-BR")} às ${new Date().toLocaleTimeString("pt-BR")}`, 105, 30, { align: "center" });

        // Tabela
        const headers = [['Nome', 'CPF', 'Telefone', 'Status', 'Total Compras']];
        const data = filteredClientes.map(c => [
            c.nome,
            c.cpf,
            c.celular || c.telefone,
            c.ativo ? "Ativo" : "Inativo",
            c.total_compras?.toLocaleString("pt-BR", { style: "currency", currency: "BRL" }) || "R$ 0,00"
        ]);

        autoTable(doc, {
            head: headers,
            body: data.map(row => row.map(cell => cell ?? '')),
            startY: 50,
            theme: 'grid',
            styles: { fontSize: 8, cellPadding: 2 },
            headStyles: { fillColor: [25, 118, 210], textColor: [255, 255, 255] },
            alternateRowStyles: { fillColor: [245, 245, 245] }
        });

        // Rodapé
        const pageCount = doc.getNumberOfPages();
        doc.setFontSize(8);
        doc.setTextColor(100, 100, 100);
        for (let i = 1; i <= pageCount; i++) {
            doc.setPage(i);
            doc.text(`Página ${i} de ${pageCount} - MercadinhoSys`, 105, 290, { align: "center" });
        }

        doc.save(`clientes-${new Date().toISOString().split('T')[0]}.pdf`);

        handleExportClose();
        showToast.info('PDF exportado com sucesso');
    };

    return (
        <div className="max-w-6xl mx-auto p-4">

            {/* ===== PAINEL DE INDICADORES DE FIADO ===== */}
            {clientesComFiado.length > 0 && (
                <Box sx={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(190px, 1fr))',
                    gap: 2,
                    mb: 3,
                    p: 2.5,
                    borderRadius: 2,
                    border: '1.5px solid #f57c00',
                    background: 'linear-gradient(135deg, #fff8f0 0%, #fff3e0 100%)'
                }}>
                    <Box>
                        <Typography variant="caption" sx={{ color: '#e65100', fontWeight: 600, textTransform: 'uppercase', letterSpacing: 1 }}>Total Fiado em Aberto</Typography>
                        <Typography variant="h5" sx={{ fontWeight: 800, color: '#bf360c' }}>
                            {totalFiadoAberto.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                        </Typography>
                    </Box>
                    <Box>
                        <Typography variant="caption" sx={{ color: '#e65100', fontWeight: 600, textTransform: 'uppercase', letterSpacing: 1 }}>Clientes com Fiado</Typography>
                        <Typography variant="h5" sx={{ fontWeight: 800, color: '#bf360c' }}>
                            {clientesComFiado.length}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                            de {clientes.length} cadastrados
                        </Typography>
                    </Box>
                    {maiorDevedor && (
                        <Box>
                            <Typography variant="caption" sx={{ color: '#e65100', fontWeight: 600, textTransform: 'uppercase', letterSpacing: 1 }}>Maior Devedor</Typography>
                            <Typography variant="subtitle1" sx={{ fontWeight: 700, color: '#bf360c' }}>{maiorDevedor.nome}</Typography>
                            <Typography variant="caption" color="text.secondary">
                                {(maiorDevedor.saldo_devedor ?? 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                            </Typography>
                        </Box>
                    )}
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <Button
                            variant={fiadoFilter ? 'contained' : 'outlined'}
                            size="small"
                            startIcon={<HandshakeIcon />}
                            onClick={() => setFiadoFilter(!fiadoFilter)}
                            sx={{
                                borderColor: '#f57c00',
                                color: fiadoFilter ? '#fff' : '#f57c00',
                                bgcolor: fiadoFilter ? '#f57c00' : 'transparent',
                                '&:hover': { bgcolor: fiadoFilter ? '#e65100' : '#fff3e0' }
                            }}
                        >
                            {fiadoFilter ? 'Ver Todos' : 'Só com Fiado'}
                        </Button>
                    </Box>
                </Box>
            )}

            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                <Typography
                    variant="h4"
                    sx={{
                        fontWeight: 700,
                        color: '#1976d2',
                        textShadow: '0 1px 2px rgba(0,0,0,0.1)'
                    }}
                >
                    Gestão de Clientes
                </Typography>
                <Box sx={{ display: 'flex', gap: 1 }}>
                    <Button
                        variant="outlined"
                        startIcon={<GetAppIcon />}
                        onClick={handleExportClick}
                        sx={{
                            color: '#1976d2',
                            borderColor: '#1976d2',
                            '&:hover': {
                                borderColor: '#1565c0',
                                bgcolor: '#e3f2fd'
                            }
                        }}
                    >
                        Exportar
                    </Button>
                    <Menu
                        anchorEl={exportMenuAnchor}
                        open={Boolean(exportMenuAnchor)}
                        onClose={handleExportClose}
                    >
                        <MenuItem onClick={exportarCSV}>Exportar CSV</MenuItem>
                        <MenuItem onClick={exportarExcel}>Exportar Excel</MenuItem>
                        <MenuItem onClick={exportarPDF}>Exportar PDF</MenuItem>
                    </Menu>
                    <Tooltip title="Recalcula total de compras e valor gasto de todos os clientes com base nas vendas reais do banco">
                        <span>
                            <Button
                                variant="outlined"
                                startIcon={recalcLoading ? <CircularProgress size={16} /> : <SyncIcon />}
                                onClick={handleRecalcularMetricas}
                                disabled={recalcLoading}
                                sx={{ color: '#388e3c', borderColor: '#388e3c', '&:hover': { bgcolor: '#e8f5e9' } }}
                            >
                                {recalcLoading ? 'Sincronizando...' : 'Sincronizar Métricas'}
                            </Button>
                        </span>
                    </Tooltip>
                    <Button
                        variant="contained"
                        startIcon={<PersonAddAlt1Icon />}
                        onClick={handleAdd}
                        sx={{
                            bgcolor: '#1976d2',
                            '&:hover': {
                                bgcolor: '#1565c0'
                            }
                        }}
                    >
                        Novo Cliente
                    </Button>
                </Box>
            </Box>
            <CustomerDashboard {...dashboard} />

            {/* Controles de Busca e Filtros */}
            <Box sx={{ display: 'flex', gap: 2, mb: 3, flexWrap: 'wrap', alignItems: 'center' }}>
                <TextField
                    placeholder="Buscar por nome, CPF, email ou telefone..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    variant="outlined"
                    size="small"
                    sx={{ minWidth: 300, flex: 1 }}
                    InputProps={{
                        startAdornment: (
                            <InputAdornment position="start">
                                <SearchIcon />
                            </InputAdornment>
                        ),
                        endAdornment: searchTerm && (
                            <InputAdornment position="end">
                                <ClearIcon
                                    sx={{ cursor: 'pointer' }}
                                    onClick={() => setSearchTerm('')}
                                />
                            </InputAdornment>
                        ),
                    }}
                />

                <FormControl size="small" sx={{ minWidth: 150 }}>
                    <InputLabel>Status</InputLabel>
                    <Select
                        value={statusFilter}
                        label="Status"
                        onChange={(e) => setStatusFilter(e.target.value)}
                        startAdornment={<FilterListIcon sx={{ mr: 1 }} />}
                    >
                        <MenuItem value="todos">Todos</MenuItem>
                        <MenuItem value="ativos">Ativos</MenuItem>
                        <MenuItem value="inativos">Inativos</MenuItem>
                    </Select>
                </FormControl>

                {(searchTerm || statusFilter !== 'todos') && (
                    <Chip
                        label={`${filteredClientes.length} resultado${filteredClientes.length !== 1 ? 's' : ''}`}
                        sx={{
                            bgcolor: '#e3f2fd',
                            color: '#1976d2',
                            fontWeight: 500
                        }}
                        size="small"
                    />
                )}

                <Tooltip title="Exportar dados filtrados">
                    <span>
                        <Button
                            variant="outlined"
                            onClick={handleExportClick}
                            startIcon={<GetAppIcon />}
                            disabled={filteredClientes.length === 0}
                            sx={{
                                color: '#1976d2',
                                borderColor: '#1976d2',
                                '&:hover': {
                                    borderColor: '#1565c0',
                                    bgcolor: '#e3f2fd'
                                }
                            }}
                        >
                            Exportar
                        </Button>
                    </span>
                </Tooltip>
            </Box>

            <CustomerTable
                clientes={filteredClientes}
                loading={loading}
                onRowClick={handleRowClick}
                onEdit={handleEdit}
                onDelete={handleDelete}
                selectedClienteId={selectedCliente?.id}
                onReceberFiado={handleAbrirModalFiado}
            />
            <CustomerForm open={formOpen} onClose={() => setFormOpen(false)} onSave={handleSave} initialData={editData} loading={saving} />
            <CustomerDetailsModal
                open={!!selectedCliente}
                cliente={clienteDetalhado}
                loading={detalheLoading}
                onClose={() => { setSelectedCliente(null); setClienteDetalhado(null); }}
                onEdit={handleEdit}
                onDelete={handleDelete}
            />

            {/* ===== MODAL DE RECEBIMENTO DE FIADO ===== */}
            <Dialog open={fiadoModal.open} onClose={() => setFiadoModal({ open: false, cliente: null })} maxWidth="xs" fullWidth>
                <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1, color: '#e65100', fontWeight: 700 }}>
                    <AttachMoneyIcon /> Receber Fiado
                </DialogTitle>
                <DialogContent>
                    {fiadoModal.cliente && (
                        <Box>
                            <Box sx={{ mb: 2, p: 1.5, bgcolor: '#fff8f0', borderRadius: 1, border: '1px solid #ffe0b2' }}>
                                <Typography variant="subtitle2" sx={{ color: '#e65100', fontWeight: 700 }}>
                                    {fiadoModal.cliente.nome}
                                </Typography>
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                                    <WarningAmberIcon sx={{ color: '#f57c00', fontSize: 16 }} />
                                    <Typography variant="body2" sx={{ color: '#bf360c', fontWeight: 600 }}>
                                        Saldo Devedor: {(fiadoModal.cliente.saldo_devedor ?? 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                                    </Typography>
                                </Box>
                            </Box>

                            <TextField
                                label="Valor a Pagar (R$)"
                                value={fiadoValor}
                                onChange={e => setFiadoValor(e.target.value)}
                                fullWidth
                                type="number"
                                inputProps={{ min: 0, step: '0.01', max: fiadoModal.cliente.saldo_devedor ?? 0 }}
                                sx={{ mb: 2, mt: 1 }}
                                helperText={`Máximo: ${(fiadoModal.cliente.saldo_devedor ?? 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}`}
                            />

                            <FormControl fullWidth sx={{ mb: 1 }}>
                                <InputLabel>Forma de Pagamento</InputLabel>
                                <Select value={fiadoForma} label="Forma de Pagamento" onChange={e => setFiadoForma(e.target.value)}>
                                    <MenuItem value="Dinheiro">💵 Dinheiro</MenuItem>
                                    <MenuItem value="PIX">📱 PIX</MenuItem>
                                    <MenuItem value="Cartão de Débito">💳 Cartão de Débito</MenuItem>
                                    <MenuItem value="Cartão de Crédito">💳 Cartão de Crédito</MenuItem>
                                </Select>
                            </FormControl>

                            <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                                ⓘ O valor será registrado como entrada no Caixa aberto.
                            </Typography>
                        </Box>
                    )}
                </DialogContent>
                <DialogActions sx={{ px: 3, pb: 2 }}>
                    <Button onClick={() => setFiadoModal({ open: false, cliente: null })} color="inherit">Cancelar</Button>
                    <Button
                        variant="contained"
                        onClick={handlePagarFiado}
                        disabled={fiadoLoading || !fiadoValor}
                        sx={{ bgcolor: '#f57c00', '&:hover': { bgcolor: '#e65100' } }}
                    >
                        {fiadoLoading ? 'Registrando...' : 'Confirmar Recebimento'}
                    </Button>
                </DialogActions>
            </Dialog>

            <Box sx={{ mt: 4, p: 2, bgcolor: 'grey.50', borderRadius: 1, textAlign: 'center' }}>
                <Typography variant="body2" color="text.secondary">
                    💡 <strong>Dicas:</strong> Pressione <kbd>N</kbd> para novo cliente • <kbd>Esc</kbd> para fechar modais • Clique na linha para ver detalhes
                    {clientesComFiado.length > 0 && <> • <HandshakeIcon sx={{ fontSize: 14, verticalAlign: 'middle', color: '#f57c00' }} /> {clientesComFiado.length} clientes com fiado em aberto</>}
                </Typography>
            </Box>
            {loading && <div className="flex justify-center mt-4"><CircularProgress /></div>}
        </div>
    );
};

export default CustomersPage;