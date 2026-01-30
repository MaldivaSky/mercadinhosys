import React, { useEffect, useState } from 'react';
import { Cliente } from '../../types';
import CustomerTable from './components/CustomerTable';
import CustomerDetailsModal from './components/CustomerDetailsModal.tsx';
import CustomerForm from './components/CustomerForm';
import CustomerDashboard from './components/CustomerDashboard';
import { customerService } from './customerService';
import { apiClient } from '../../api/apiClient';
import { Button, Typography, CircularProgress, Snackbar, Alert, TextField, Box, FormControl, InputLabel, Select, MenuItem, InputAdornment, Chip, Tooltip, Menu } from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import FilterListIcon from '@mui/icons-material/FilterList';
import ClearIcon from '@mui/icons-material/Clear';
import GetAppIcon from '@mui/icons-material/GetApp';
import PersonAddAlt1Icon from '@mui/icons-material/PersonAddAlt1';
import jsPDF from "jspdf";
import autoTable from "jspdf-autotable";
import * as XLSX from "xlsx";

const CustomersPage: React.FC = () => {
    const [clientes, setClientes] = useState<Cliente[]>([]);
    //
    const [loading, setLoading] = useState(false);
    const [formOpen, setFormOpen] = useState(false);
    const [editData, setEditData] = useState<Partial<Cliente> | undefined>(undefined);
    const [saving, setSaving] = useState(false);
    const [selectedCliente, setSelectedCliente] = useState<Cliente | null>(null);
    const [clienteDetalhado, setClienteDetalhado] = useState<Cliente | null>(null);
    const [detalheLoading, setDetalheLoading] = useState(false);
    const [snackbar, setSnackbar] = useState<{open: boolean, message: string, severity: 'success'|'error'}>({open: false, message: '', severity: 'success'});
    const [dashboard, setDashboard] = useState<{total: number, ativos: number, inativos: number, novos: number, vip: number}>({total: 0, ativos: 0, inativos: 0, novos: 0, vip: 0});
    const [searchTerm, setSearchTerm] = useState('');
    const [statusFilter, setStatusFilter] = useState<string>('todos');
    const [filteredClientes, setFilteredClientes] = useState<Cliente[]>([]);
    const [exportMenuAnchor, setExportMenuAnchor] = useState<null | HTMLElement>(null);

    const fetchDashboard = async () => {
        try {
            const res = await apiClient.get('/clientes/');
            if (res.data && res.data.estatisticas) {
                setDashboard({
                    total: res.data.estatisticas.total || 0,
                    ativos: res.data.estatisticas.ativos || 0,
                    inativos: res.data.estatisticas.inativos || 0,
                    novos: 0, // Campo não disponível na API atual
                    vip: 0, // Campo não disponível na API atual
                });
            }
        } catch {
            setSnackbar({open: true, message: 'Erro ao carregar métricas do dashboard', severity: 'error'});
        }
    };

    const fetchClientes = async () => {
        setLoading(true);
        try {
            const data = await customerService.list();
            setClientes(data);
        } catch {
            setSnackbar({open: true, message: 'Erro ao carregar clientes', severity: 'error'});
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

        // Filtro por status
        if (statusFilter !== 'todos') {
            filtered = filtered.filter(cliente => {
                if (statusFilter === 'ativos') return cliente.ativo === true;
                if (statusFilter === 'inativos') return cliente.ativo === false;
                return true;
            });
        }

        // Busca por termo
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
    }, [clientes, searchTerm, statusFilter]);

    const handleAdd = () => {
        setEditData(undefined);
        setFormOpen(true);
    };

    const handleEdit = async (cliente: Cliente) => {
        if (!cliente || !cliente.id) {
            setSnackbar({open: true, message: 'Erro: Cliente inválido para edição', severity: 'error'});
            return;
        }

        setSaving(true);
        try {
            const res = await apiClient.get(`/clientes/${cliente.id}`);
            const clienteData = { ...res.data.cliente, id: cliente.id };
            setEditData(clienteData);
            setFormOpen(true);
            setSelectedCliente(null);
        } catch (err: unknown) {
            if (
                typeof err === 'object' &&
                err !== null &&
                'response' in err &&
                typeof (err as { response?: { status?: number } }).response === 'object' &&
                (err as { response?: { status?: number } }).response?.status === 404
            ) {
                setSnackbar({open: true, message: 'Cliente não encontrado ou já removido.', severity: 'error'});
            } else {
                setSnackbar({open: true, message: 'Erro ao buscar dados do cliente para edição', severity: 'error'});
            }
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
        } catch (err: unknown) {
            setClienteDetalhado(null);
            setSelectedCliente(null);
            if (
                typeof err === 'object' &&
                err !== null &&
                'response' in err &&
                typeof (err as { response?: { status?: number } }).response === 'object' &&
                (err as { response?: { status?: number } }).response?.status === 404
            ) {
                setSnackbar({open: true, message: 'Cliente não encontrado ou já removido.', severity: 'error'});
            } else {
                setSnackbar({open: true, message: 'Erro ao buscar detalhes do cliente', severity: 'error'});
            }
        } finally {
            setDetalheLoading(false);
        }
    };

    const handleDelete = async (cliente: Cliente) => {
        if (!cliente || !cliente.id) {
            setSnackbar({open: true, message: 'Erro: Cliente inválido para exclusão', severity: 'error'});
            return;
        }

        const confirmed = window.confirm(
            `Tem certeza que deseja excluir o cliente "${cliente.nome}"?\n\nEsta ação não pode ser desfeita e removerá permanentemente todos os dados do cliente.`
        );
        if (!confirmed) return;

        setSaving(true);
        try {
            await customerService.remove(cliente.id);
            setSnackbar({open: true, message: `Cliente "${cliente.nome}" excluído com sucesso`, severity: 'success'});
            fetchClientes();
            fetchDashboard();
        } catch (error: unknown) {
            const err = error as { response?: { status?: number; data?: { message?: string; vinculos?: { vendas: number; contas_a_receber: number } } } };
            
            // Tratamento específico para erro de vínculos (400)
            if (err.response?.status === 400 && err.response?.data?.vinculos) {
                const { vendas, contas_a_receber } = err.response.data.vinculos;
                const msg = `Não é possível excluir este cliente pois ele possui registros vinculados:\n` +
                           `• ${vendas} Vendas\n` +
                           `• ${contas_a_receber} Contas a receber\n\n` +
                           `Deseja DESATIVAR o cliente em vez de excluir?\n` +
                           `Isso impedirá novas vendas mas manterá o histórico.`;
                
                if (window.confirm(msg)) {
                    try {
                        await apiClient.patch(`/clientes/${cliente.id}/status`, { ativo: false });
                        setSnackbar({open: true, message: `Cliente "${cliente.nome}" desativado com sucesso`, severity: 'success'});
                        fetchClientes();
                        fetchDashboard();
                    } catch (patchErr: unknown) {
                        const patchMsg = (patchErr as { response?: { data?: { message?: string } } })?.response?.data?.message || 'Erro ao desativar cliente';
                        setSnackbar({open: true, message: patchMsg, severity: 'error'});
                    }
                    return; // Interrompe para não mostrar o erro original
                }
            }

            const errorMessage = err.response?.data?.message || 'Erro ao excluir cliente';
            setSnackbar({open: true, message: errorMessage, severity: 'error'});
        } finally {
            setSaving(false);
        }
    };

    const handleSave = async (data: Partial<Cliente>) => {
        setSaving(true);
        try {
            if (editData && editData.id) {
                await customerService.update(editData.id, data);
                setSnackbar({open: true, message: 'Cliente atualizado com sucesso', severity: 'success'});
            } else {
                await customerService.create(data);
                setSnackbar({open: true, message: 'Cliente cadastrado com sucesso', severity: 'success'});
            }
            setFormOpen(false);
            setEditData(undefined);
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
                setSnackbar({open: true, message: errorMessage, severity: 'error'});
            } else {
                setSnackbar({open: true, message: 'Erro ao salvar cliente', severity: 'error'});
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
        setSnackbar({open: true, message: 'CSV exportado com sucesso', severity: 'success'});
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
        setSnackbar({open: true, message: 'Excel exportado com sucesso', severity: 'success'});
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
        setSnackbar({open: true, message: 'PDF exportado com sucesso', severity: 'success'});
    };

    return (
        <div className="max-w-6xl mx-auto p-4">
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
            <Snackbar open={snackbar.open} autoHideDuration={4000} onClose={() => setSnackbar({...snackbar, open: false})}>
                <Alert onClose={() => setSnackbar({...snackbar, open: false})} severity={snackbar.severity} sx={{ width: '100%' }}>
                    {snackbar.message}
                </Alert>
            </Snackbar>

            {/* Dicas de atalhos */}
            <Box sx={{ mt: 4, p: 2, bgcolor: 'grey.50', dark: { bgcolor: 'grey.900' }, borderRadius: 1, textAlign: 'center' }}>
                <Typography variant="body2" color="text.secondary">
                    💡 <strong>Dicas:</strong> Pressione <kbd>N</kbd> para novo cliente • <kbd>Esc</kbd> para fechar modais • Clique na linha para ver detalhes
                </Typography>
            </Box>
            {loading && <div className="flex justify-center mt-4"><CircularProgress /></div>}
        </div>
    );
};

export default CustomersPage;