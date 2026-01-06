import React, { useEffect, useState } from 'react';
import { Cliente } from '../../types';
import CustomerTable from './components/CustomerTable';
import CustomerDetailsModal from './components/CustomerDetailsModal.tsx';
import CustomerForm from './components/CustomerForm';
import CustomerDashboard from './components/CustomerDashboard';
import { customerService } from './customerService';
import { apiClient } from '../../api/apiClient';
import { Button, Typography, CircularProgress, Snackbar, Alert } from '@mui/material';

const CustomersPage: React.FC = () => {
    const [clientes, setClientes] = useState<Cliente[]>([]);
    //
    const [loading, setLoading] = useState(false);
    const [formOpen, setFormOpen] = useState(false);
    const [editData, setEditData] = useState<Partial<Cliente> | undefined>(undefined);
    const [saving, setSaving] = useState(false);
    const [selectedCliente, setSelectedCliente] = useState<Cliente | null>(null);
    const [snackbar, setSnackbar] = useState<{open: boolean, message: string, severity: 'success'|'error'}>({open: false, message: '', severity: 'success'});
    const [dashboard, setDashboard] = useState<{total: number, ativos: number, inativos: number, novos: number, vip: number}>({total: 0, ativos: 0, inativos: 0, novos: 0, vip: 0});
    // const [dashboardFilter, setDashboardFilter] = useState<string | null>(null);

    const fetchDashboard = async () => {
        try {
            const res = await apiClient.get('/clientes/');
            if (res.data && res.data.estatisticas) {
                setDashboard({
                    total: res.data.estatisticas.total_clientes || 0,
                    ativos: res.data.estatisticas.clientes_ativos || 0,
                    inativos: res.data.estatisticas.clientes_inativos || 0,
                    novos: res.data.estatisticas.clientes_novos || 0,
                    vip: res.data.estatisticas.clientes_vip || 0,
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

    const handleAdd = () => {
        setEditData(undefined);
        setFormOpen(true);
    };

    const handleEdit = (cliente: Cliente) => {
        setEditData(cliente);
        setFormOpen(true);
        setSelectedCliente(null);
    };

    const handleRowClick = (cliente: Cliente) => {
        setSelectedCliente(cliente);
    };

    const handleDelete = async (cliente: Cliente) => {
        if (!window.confirm(`Excluir cliente ${cliente.nome}?`)) return;
        setSaving(true);
        try {
            await customerService.remove(cliente.id);
            setSnackbar({open: true, message: 'Cliente excluído com sucesso', severity: 'success'});
            fetchClientes();
        } catch {
            setSnackbar({open: true, message: 'Erro ao excluir cliente', severity: 'error'});
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
            fetchClientes();
        } catch {
            setSnackbar({open: true, message: 'Erro ao salvar cliente', severity: 'error'});
        } finally {
            setSaving(false);
        }
    };

    return (
        <div className="max-w-6xl mx-auto p-4">
            <Typography variant="h4" gutterBottom>Gestão de Clientes</Typography>
            <CustomerDashboard {...dashboard} />
            <Button variant="contained" color="primary" onClick={handleAdd} sx={{ mb: 2 }}>Novo Cliente</Button>
            <CustomerTable clientes={clientes} loading={loading} onRowClick={handleRowClick} />
            <CustomerForm open={formOpen} onClose={() => setFormOpen(false)} onSave={handleSave} initialData={editData} loading={saving} />
            <CustomerDetailsModal
                open={!!selectedCliente}
                cliente={selectedCliente}
                onClose={() => setSelectedCliente(null)}
                onEdit={handleEdit}
                onDelete={handleDelete}
            />
            <Snackbar open={snackbar.open} autoHideDuration={4000} onClose={() => setSnackbar({...snackbar, open: false})}>
                <Alert onClose={() => setSnackbar({...snackbar, open: false})} severity={snackbar.severity} sx={{ width: '100%' }}>
                    {snackbar.message}
                </Alert>
            </Snackbar>
            {loading && <div className="flex justify-center mt-4"><CircularProgress /></div>}
        </div>
    );
};

export default CustomersPage;