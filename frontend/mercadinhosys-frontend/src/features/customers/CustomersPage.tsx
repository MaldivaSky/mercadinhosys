import React, { useEffect, useMemo, useState } from 'react';
import {
    Box,
    Button,
    Card,
    CardContent,
    Chip,
    CircularProgress,
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
    FormControl,
    InputAdornment,
    InputLabel,
    Menu,
    MenuItem,
    Select,
    TextField,
    Tooltip,
    Typography,
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import FilterListIcon from '@mui/icons-material/FilterList';
import ClearIcon from '@mui/icons-material/Clear';
import GetAppIcon from '@mui/icons-material/GetApp';
import SyncIcon from '@mui/icons-material/Sync';
import PersonAddAlt1Icon from '@mui/icons-material/PersonAddAlt1';
import HandshakeIcon from '@mui/icons-material/Handshake';
import AttachMoneyIcon from '@mui/icons-material/AttachMoney';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import WhatsAppIcon from '@mui/icons-material/WhatsApp';
import AutoGraphIcon from '@mui/icons-material/AutoGraph';
import CampaignIcon from '@mui/icons-material/Campaign';
import AutorenewIcon from '@mui/icons-material/Autorenew';
import StarIcon from '@mui/icons-material/Star';
import InsightsIcon from '@mui/icons-material/Insights';
import CakeIcon from '@mui/icons-material/Cake';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
import * as XLSX from 'xlsx';

import { Cliente } from '../../types';
import { apiClient } from '../../api/apiClient';
import { showToast } from '../../utils/toast';
import { pdvService } from '../pdv/pdvService';
import { customerService } from './customerService';
import CustomerDashboard from './components/CustomerDashboard';
import CustomerDetailsModal from './components/CustomerDetailsModal';
import CustomerForm from './components/CustomerForm';
import CustomerTable from './components/CustomerTable';

type CRMTab = 'overview' | 'recovery' | 'campaigns' | 'portfolio';
type CampaignKey = 'reactivation' | 'vip' | 'debt' | 'promotion';
type StatusFilter = 'todos' | 'ativos' | 'inativos';
type SegmentFilter = 'todos' | 'Campeão' | 'Fiel' | 'Regular' | 'Risco' | 'Perdido' | 'Novo';

type DashboardState = {
    total: number;
    total_gasto: number;
    total_devido: number;
    melhor_cliente_nome: string;
    melhor_cliente_valor: number;
    maior_devedor_nome: string;
    maior_devedor_valor: number;
};

type RfmCustomer = {
    cliente_id: number;
    segment: string;
    recency_days?: number;
    frequency?: number;
    monetary?: number;
};

type CRMCustomer = Cliente & {
    crmSegment: string;
    lifecycle: string;
    lastPurchaseDays: number | null;
    whatsappNumber: string;
    hasDebt: boolean;
    actionPriority: number;
};

type CampaignConfig = {
    key: CampaignKey;
    title: string;
    subtitle: string;
    badge: string;
    color: string;
    description: string;
};

const initialDashboard: DashboardState = {
    total: 0,
    total_gasto: 0,
    total_devido: 0,
    melhor_cliente_nome: 'Nenhum',
    melhor_cliente_valor: 0,
    maior_devedor_nome: 'Nenhum',
    maior_devedor_valor: 0,
};

const tabs: Array<{ id: CRMTab; label: string; description: string }> = [
    { id: 'overview', label: 'CRM Executivo', description: 'Visao comercial, segmentos e prioridades' },
    { id: 'recovery', label: 'Recuperacao', description: 'Clientes em risco, inativos e cobranca consultiva' },
    { id: 'campaigns', label: 'Campanhas', description: 'Mensagens inteligentes para WhatsApp e reativacao' },
    { id: 'portfolio', label: 'Base de Clientes', description: 'Cadastro, carteira, filtros e historico' },
];

const campaignConfigs: CampaignConfig[] = [
    {
        key: 'reactivation',
        title: 'Reativacao',
        subtitle: 'Clientes em risco ou inativos',
        badge: 'Retencao',
        color: '#2563eb',
        description: 'Traz de volta clientes com baixa recencia usando abordagem de retorno.',
    },
    {
        key: 'vip',
        title: 'VIP & Fidelidade',
        subtitle: 'Campeoes e clientes fieis',
        badge: 'LTV',
        color: '#7c3aed',
        description: 'Fortalece relacionamento com clientes de alto valor e frequencia.',
    },
    {
        key: 'debt',
        title: 'Carteira em Aberto',
        subtitle: 'Clientes com saldo devedor',
        badge: 'Cash',
        color: '#ea580c',
        description: 'Acelera recebimento com mensagem profissional e conciliadora.',
    },
    {
        key: 'promotion',
        title: 'Promocao Direcionada',
        subtitle: 'Clientes ativos com potencial de recompra',
        badge: 'Growth',
        color: '#16a34a',
        description: 'Aciona base elegivel para oferta, novidade ou campanha sazonal.',
    },
];

const segmentColors: Record<string, string> = {
    'Campeão': '#16a34a',
    'Fiel': '#2563eb',
    'Regular': '#7c3aed',
    'Risco': '#ea580c',
    'Perdido': '#dc2626',
    'Novo': '#0f766e',
};

const formatCurrency = (value: number) =>
    value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

const normalizePhone = (value?: string) => (value || '').replace(/\D/g, '');

const firstName = (name?: string) => (name || '').trim().split(' ')[0] || 'cliente';

const buildWhatsAppUrl = (cliente: Cliente, message: string) => {
    const phone = normalizePhone(cliente.celular || cliente.telefone);
    if (!phone) {
        return null;
    }
    const withCountry = phone.startsWith('55') ? phone : `55${phone}`;
    return `https://wa.me/${withCountry}?text=${encodeURIComponent(message)}`;
};

const classifyLifecycle = (cliente: Cliente, segment: string, lastPurchaseDays: number | null) => {
    const debt = Number(cliente.saldo_devedor || 0);
    const totalPurchases = Number(cliente.total_compras || 0);
    const totalSpent = Number(cliente.valor_total_gasto || 0);

    if (debt > 0) return 'carteira_aberta';
    if (segment === 'Campeão' || totalSpent >= 5000) return 'vip';
    if (segment === 'Risco' || (lastPurchaseDays !== null && lastPurchaseDays >= 45)) return 'em_risco';
    if (!cliente.ativo || segment === 'Perdido' || (lastPurchaseDays !== null && lastPurchaseDays >= 90)) return 'inativo';
    if (totalPurchases <= 1) return 'novo';
    return 'ativo';
};

const lifecyclePriority = (lifecycle: string, debt: number) => {
    if (lifecycle === 'carteira_aberta' && debt >= 300) return 100;
    if (lifecycle === 'inativo') return 90;
    if (lifecycle === 'em_risco') return 80;
    if (lifecycle === 'vip') return 70;
    if (lifecycle === 'novo') return 60;
    return 40;
};

const buildCampaignMessage = (campaign: CampaignKey, cliente: CRMCustomer) => {
    const name = firstName(cliente.nome);
    const debt = Number(cliente.saldo_devedor || 0);
    const spent = Number(cliente.valor_total_gasto || 0);
    const days = cliente.lastPurchaseDays;

    switch (campaign) {
        case 'reactivation':
            const timeMsg = days && days > 15 ? `Já faz ${days} dias desde sua última visita.` : 'Sentimos sua falta aqui.';
            return `Olá, ${name}! ${timeMsg} Preparamos um cupom de R$ 15 de desconto exclusivo para você voltar a comprar conosco. Me responde aqui para ativar o seu cupom!`;
        case 'vip':
            const discount = Math.max(10, Math.floor(spent * 0.05)); // 5% of total spent as bonus, min 10
            return `Olá, ${name}! Como um de nossos melhores clientes (já economizou comprando mais de ${formatCurrency(spent)} conosco), liberamos um cashback especial de ${formatCurrency(discount)} para sua próxima compra! Aproveite as novidades exclusivas.`;
        case 'debt':
            return `Olá, ${name}! Passando para te ajudar a regularizar o seu saldo em aberto de ${formatCurrency(debt)} conosco. Podemos gerar um PIX ou parcelar no cartão para você continuar aproveitando nossas ofertas. Como fica melhor para você?`;
        case 'promotion':
        default:
            const promoValue = Math.max(5, Math.floor((spent > 0 ? spent : 100) * 0.03));
            return `Olá, ${name}! Separamos ofertas imbatíveis para você hoje! E para melhorar, te dou ${formatCurrency(promoValue)} de desconto imediato em qualquer pedido acima de R$ 50. Quer ver o catálogo?`;
    }
};

const lifecycleLabel = (value: string) => {
    const map: Record<string, string> = {
        carteira_aberta: 'Carteira em aberto',
        inativo: 'Inativo',
        em_risco: 'Em risco',
        vip: 'VIP',
        novo: 'Novo',
        ativo: 'Ativo',
    };
    return map[value] || value;
};

const KpiCard = ({
    title,
    value,
    subtitle,
    color,
    icon,
    onClick,
}: {
    title: string;
    value: string | number;
    subtitle: string;
    color: string;
    icon: React.ReactNode;
    onClick?: () => void;
}) => (
    <Card 
        onClick={onClick}
        sx={{ 
            height: '100%', 
            border: '1px solid', 
            borderColor: 'divider', 
            bgcolor: 'background.paper',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
            cursor: onClick ? 'pointer' : 'default',
            transition: 'all 0.2s',
            '&:hover': onClick ? { transform: 'translateY(-2px)', boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)' } : {}
        }}
    >
        <CardContent sx={{ p: 2.5 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 2 }}>
                <Box>
                    <Typography variant="overline" sx={{ color: 'text.secondary', fontWeight: 700, letterSpacing: 1 }}>
                        {title}
                    </Typography>
                    <Typography variant="h4" sx={{ color, fontWeight: 800, mt: 1 }}>
                        {value}
                    </Typography>
                    <Typography variant="body2" sx={{ color: 'text.secondary', mt: 0.5 }}>
                        {subtitle}
                    </Typography>
                </Box>
                <Box
                    sx={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        width: 52,
                        height: 52,
                        borderRadius: 3,
                        bgcolor: `${color}15`,
                        color,
                    }}
                >
                    {icon}
                </Box>
            </Box>
        </CardContent>
    </Card>
);

const CustomersPage: React.FC = () => {
    const [clientes, setClientes] = useState<Cliente[]>([]);
    const [loading, setLoading] = useState(false);
    const [formOpen, setFormOpen] = useState(false);
    const [editData, setEditData] = useState<Partial<Cliente> | undefined>(undefined);
    const [saving, setSaving] = useState(false);
    const [selectedCliente, setSelectedCliente] = useState<Cliente | null>(null);
    const [clienteDetalhado, setClienteDetalhado] = useState<Cliente | null>(null);
    const [detalheLoading, setDetalheLoading] = useState(false);
    const [dashboard, setDashboard] = useState<DashboardState>(initialDashboard);
    const [searchTerm, setSearchTerm] = useState('');
    const [statusFilter, setStatusFilter] = useState<StatusFilter>('todos');
    const [segmentFilter, setSegmentFilter] = useState<SegmentFilter>('todos');
    const [fiadoFilter, setFiadoFilter] = useState(false);
    const [exportMenuAnchor, setExportMenuAnchor] = useState<null | HTMLElement>(null);
    const [fiadoModal, setFiadoModal] = useState<{ open: boolean; cliente: Cliente | null }>({ open: false, cliente: null });
    const [fiadoValor, setFiadoValor] = useState('');
    const [fiadoForma, setFiadoForma] = useState('Dinheiro');
    const [fiadoLoading, setFiadoLoading] = useState(false);
    const [recalcLoading, setRecalcLoading] = useState(false);
    const [rfmData, setRfmData] = useState<{ customers?: RfmCustomer[]; segments?: Record<string, number>; window_days?: number } | null>(null);
    const [activeTab, setActiveTab] = useState<CRMTab>('overview');
    const [selectedCampaign, setSelectedCampaign] = useState<CampaignKey>('reactivation');
    const [campaignCustomerId, setCampaignCustomerId] = useState<number | null>(null);

    const fetchDashboard = async () => {
        try {
            const [clientesRes, rfmRes] = await Promise.all([
                apiClient.get('/clientes/'),
                apiClient.get('/clientes/rfm'),
            ]);

            if (clientesRes.data?.estatisticas) {
                setDashboard({
                    total: clientesRes.data.estatisticas.total || 0,
                    total_gasto: clientesRes.data.estatisticas.total_gasto || 0,
                    total_devido: clientesRes.data.estatisticas.total_devido || 0,
                    melhor_cliente_nome: clientesRes.data.estatisticas.melhor_cliente_nome || 'Nenhum',
                    melhor_cliente_valor: clientesRes.data.estatisticas.melhor_cliente_valor || 0,
                    maior_devedor_nome: clientesRes.data.estatisticas.maior_devedor_nome || 'Nenhum',
                    maior_devedor_valor: clientesRes.data.estatisticas.maior_devedor_valor || 0,
                });
            }

            if (rfmRes.data?.rfm) {
                setRfmData(rfmRes.data.rfm);
            } else {
                setRfmData({ customers: [], segments: {}, window_days: 180 });
            }
        } catch {
            showToast.error('Erro ao carregar métricas do CRM');
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

    const refreshAll = async () => {
        await Promise.all([fetchClientes(), fetchDashboard()]);
    };

    useEffect(() => {
        refreshAll();
    }, []);

    useEffect(() => {
        const handleKeyPress = (event: KeyboardEvent) => {
            if (event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement) {
                return;
            }

            if ((event.key === 'n' || event.key === 'N') && !formOpen && !selectedCliente) {
                event.preventDefault();
                setEditData(undefined);
                setFormOpen(true);
            }

            if (event.key === 'Escape') {
                if (formOpen) {
                    event.preventDefault();
                    setFormOpen(false);
                    setEditData(undefined);
                } else if (selectedCliente) {
                    event.preventDefault();
                    setSelectedCliente(null);
                    setClienteDetalhado(null);
                }
            }
        };

        document.addEventListener('keydown', handleKeyPress);
        return () => document.removeEventListener('keydown', handleKeyPress);
    }, [formOpen, selectedCliente]);

    const rfmMap = useMemo(() => {
        const map = new Map<number, RfmCustomer>();
        (rfmData?.customers || []).forEach((customer) => {
            map.set(Number(customer.cliente_id), customer);
        });
        return map;
    }, [rfmData]);

    const crmClientes = useMemo<CRMCustomer[]>(() => {
        return clientes
            .map((cliente) => {
                const rfmCustomer = rfmMap.get(Number(cliente.id));
                const lastPurchaseDays = cliente.ultima_compra
                    ? Math.floor((Date.now() - new Date(cliente.ultima_compra).getTime()) / (1000 * 60 * 60 * 24))
                    : null;
                const crmSegment =
                    rfmCustomer?.segment ||
                    (Number(cliente.total_compras || 0) <= 1 ? 'Novo' : 'Regular');
                const lifecycle = classifyLifecycle(cliente, crmSegment, lastPurchaseDays);
                const debt = Number(cliente.saldo_devedor || 0);

                return {
                    ...cliente,
                    crmSegment,
                    lifecycle,
                    lastPurchaseDays,
                    whatsappNumber: normalizePhone(cliente.celular || cliente.telefone),
                    hasDebt: debt > 0,
                    actionPriority: lifecyclePriority(lifecycle, debt),
                };
            })
            .sort((a, b) => b.actionPriority - a.actionPriority);
    }, [clientes, rfmMap]);

    const filteredClientes = useMemo(() => {
        return crmClientes.filter((cliente) => {
            if (statusFilter === 'ativos' && !cliente.ativo) return false;
            if (statusFilter === 'inativos' && cliente.ativo !== false) return false;
            if (fiadoFilter && !cliente.hasDebt) return false;
            if (segmentFilter !== 'todos' && cliente.crmSegment !== segmentFilter) return false;

            if (!searchTerm.trim()) return true;
            const term = searchTerm.toLowerCase();
            return (
                cliente.nome?.toLowerCase().includes(term) ||
                cliente.cpf?.includes(term) ||
                cliente.email?.toLowerCase().includes(term) ||
                cliente.celular?.includes(term) ||
                cliente.telefone?.includes(term)
            );
        });
    }, [crmClientes, statusFilter, fiadoFilter, segmentFilter, searchTerm]);

    const clientesComFiado = useMemo(() => crmClientes.filter((cliente) => cliente.hasDebt), [crmClientes]);
    const totalFiadoAberto = useMemo(
        () => clientesComFiado.reduce((acc, cliente) => acc + Number(cliente.saldo_devedor || 0), 0),
        [clientesComFiado],
    );
    const clientesRecuperacao = useMemo(
        () => crmClientes.filter((cliente) => ['inativo', 'em_risco'].includes(cliente.lifecycle)),
        [crmClientes],
    );
    const clientesVip = useMemo(
        () => crmClientes.filter((cliente) => ['vip', 'Campeão', 'Fiel'].includes(cliente.lifecycle) || ['Campeão', 'Fiel'].includes(cliente.crmSegment)),
        [crmClientes],
    );
    const clientesPromotion = useMemo(
        () => crmClientes.filter((cliente) => cliente.lifecycle === 'ativo' || cliente.lifecycle === 'vip').slice(0, 12),
        [crmClientes],
    );

    const campaignTargets = useMemo(() => {
        switch (selectedCampaign) {
            case 'reactivation':
                return clientesRecuperacao;
            case 'vip':
                return clientesVip;
            case 'debt':
                return clientesComFiado;
            case 'promotion':
            default:
                return clientesPromotion;
        }
    }, [selectedCampaign, clientesRecuperacao, clientesVip, clientesComFiado, clientesPromotion]);

    const selectedCampaignCustomer =
        campaignTargets.find((cliente) => cliente.id === campaignCustomerId) || campaignTargets[0] || null;

    useEffect(() => {
        setCampaignCustomerId(campaignTargets[0]?.id || null);
    }, [selectedCampaign, campaignTargets]);

    const crmStats = useMemo(() => {
        const vip = clientesVip.length;
        const inRisk = crmClientes.filter((cliente) => cliente.lifecycle === 'em_risco').length;
        const inactive = crmClientes.filter((cliente) => cliente.lifecycle === 'inativo').length;
        const debt = clientesComFiado.length;
        const mesAtual = new Date().getMonth();
        const aniversariantes = crmClientes.filter((cliente) => {
            const dn = (cliente as any).data_nascimento;
            if (!dn) return false;
            const d = new Date(String(dn).includes('T') ? dn : `${dn}T00:00:00`);
            return !isNaN(d.getTime()) && d.getMonth() === mesAtual;
        }).length;
        return { vip, inRisk, inactive, debt, aniversariantes };
    }, [crmClientes, clientesVip, clientesComFiado]);

    const handleRecalcularMetricas = async () => {
        setRecalcLoading(true);
        try {
            const res = await apiClient.post('/clientes/recalcular-metricas');
            showToast.success(res.data.message || 'Métricas recalculadas com sucesso!');
            await refreshAll();
        } catch {
            showToast.error('Erro ao recalcular métricas');
        } finally {
            setRecalcLoading(false);
        }
    };

    const handleAbrirModalFiado = (cliente: Cliente) => {
        setFiadoModal({ open: true, cliente });
        setFiadoValor('');
        setFiadoForma('Dinheiro');
    };

    const handlePagarFiado = async () => {
        const { cliente } = fiadoModal;
        if (!cliente?.id) return;

        const valor = parseFloat(fiadoValor.replace(',', '.'));
        if (Number.isNaN(valor) || valor <= 0) {
            showToast.error('Informe um valor válido');
            return;
        }

        setFiadoLoading(true);
        try {
            const res = await pdvService.pagarFiado(cliente.id, valor, fiadoForma);
            showToast.success(res.message || 'Pagamento registrado!');
            setFiadoModal({ open: false, cliente: null });
            await refreshAll();
        } catch (err: any) {
            const msg = err?.response?.data?.message || 'Erro ao registrar pagamento';
            showToast.error(msg);
        } finally {
            setFiadoLoading(false);
        }
    };

    const handleEdit = async (cliente: Cliente) => {
        if (!cliente?.id) {
            showToast.error('Erro: cliente inválido para edição');
            return;
        }

        setSaving(true);
        try {
            const res = await apiClient.get(`/clientes/${cliente.id}`);
            setEditData({ ...res.data.cliente, id: cliente.id });
            setFormOpen(true);
            setSelectedCliente(null);
        } catch {
            showToast.error('Erro ao buscar dados do cliente para edição');
        } finally {
            setSaving(false);
        }
    };

    const handleRowClick = async (cliente: Cliente) => {
        if (!cliente?.id) return;

        setDetalheLoading(true);
        setSelectedCliente(cliente);
        try {
            const res = await apiClient.get(`/clientes/${cliente.id}`);
            const detalhado = res.data.cliente ? { ...res.data.cliente, ...res.data } : res.data;
            setClienteDetalhado(detalhado);
        } catch {
            setClienteDetalhado(null);
            setSelectedCliente(null);
            showToast.error('Erro ao buscar detalhes do cliente');
        } finally {
            setDetalheLoading(false);
        }
    };

    const handleDelete = async (cliente: Cliente) => {
        if (!cliente?.id) {
            showToast.error('Erro: cliente inválido para exclusão');
            return;
        }

        const confirmed = window.confirm(
            `Tem certeza que deseja excluir o cliente "${cliente.nome}"?\n\nEsta ação não pode ser desfeita e removerá permanentemente os dados do cliente.`,
        );
        if (!confirmed) return;

        try {
            await showToast.promise(
                customerService.remove(cliente.id),
                {
                    loading: 'Excluindo cliente...',
                    success: `Cliente "${cliente.nome}" excluído com sucesso`,
                    error: 'Erro ao excluir cliente',
                },
                { theme: 'error' },
            );
            await refreshAll();
        } catch (error: unknown) {
            const err = error as {
                response?: {
                    status?: number;
                    data?: {
                        message?: string;
                        vinculos?: { vendas: number; contas_a_receber: number };
                    };
                };
            };

            if (err.response?.status === 400 && err.response?.data?.vinculos) {
                const { vendas, contas_a_receber } = err.response.data.vinculos;
                const msg =
                    `Não é possível excluir este cliente pois ele possui registros vinculados:\n` +
                    `• ${vendas} vendas\n` +
                    `• ${contas_a_receber} débitos em aberto\n\n` +
                    `Deseja desativar o cliente em vez de excluir?`;

                if (window.confirm(msg)) {
                    try {
                        await apiClient.patch(`/clientes/${cliente.id}/status`, { ativo: false });
                        showToast.success(`Cliente "${cliente.nome}" desativado com sucesso`);
                        await refreshAll();
                    } catch (patchErr: unknown) {
                        const patchMsg =
                            (patchErr as { response?: { data?: { message?: string } } })?.response?.data?.message ||
                            'Erro ao desativar cliente';
                        showToast.error(patchMsg);
                    }
                    return;
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
            const promise =
                editData && editData.id
                    ? customerService.update(editData.id, data)
                    : customerService.create(data);

            const savedCustomer = await showToast.promise(promise, {
                loading: editData?.id ? 'Atualizando cliente...' : 'Cadastrando cliente...',
                success: editData?.id ? 'Cliente atualizado com sucesso' : 'Cliente cadastrado com sucesso',
                error: 'Erro ao salvar cliente',
            });

            if (editData?.id) {
                setClientes((prev) => prev.map((cliente) => (cliente.id === editData.id ? { ...cliente, ...savedCustomer } : cliente)));
            } else {
                setClientes((prev) => [savedCustomer, ...prev]);
            }

            setFormOpen(false);
            setEditData(undefined);
            await refreshAll();
        } catch (error: unknown) {
            const errResponse =
                typeof error === 'object' && error !== null && 'response' in error
                    ? (error as { response?: { data?: { message?: string; error?: string } } }).response
                    : undefined;
            const errorMessage = errResponse?.data?.message || errResponse?.data?.error || 'Erro ao salvar cliente';
            showToast.error(errorMessage);
        } finally {
            setSaving(false);
        }
    };

    const handleExportClick = (event: React.MouseEvent<HTMLButtonElement>) => {
        setExportMenuAnchor(event.currentTarget);
    };

    const handleExportClose = () => {
        setExportMenuAnchor(null);
    };

    const exportRows = filteredClientes.map((cliente) => ({
        Nome: cliente.nome || '',
        CPF: cliente.cpf || '',
        Telefone: cliente.celular || cliente.telefone || '',
        Email: cliente.email || '',
        Segmento: cliente.crmSegment,
        Carteira: lifecycleLabel(cliente.lifecycle),
        Status: cliente.ativo ? 'Ativo' : 'Inativo',
        'Ultima Compra': cliente.ultima_compra ? new Date(cliente.ultima_compra).toLocaleDateString('pt-BR') : '',
        'Valor Gasto': Number(cliente.valor_total_gasto || 0),
        'Saldo Devedor': Number(cliente.saldo_devedor || 0),
    }));

    const exportarCSV = () => {
        const csvContent = [
            Object.keys(exportRows[0] || {
                Nome: '',
                CPF: '',
                Telefone: '',
                Email: '',
                Segmento: '',
                Carteira: '',
                Status: '',
                'Ultima Compra': '',
                'Valor Gasto': '',
                'Saldo Devedor': '',
            }),
            ...exportRows.map(Object.values),
        ]
            .map((row) => row.map((cell) => `"${String(cell ?? '')}"`).join(','))
            .join('\n');

        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', `crm-clientes_${new Date().toISOString().split('T')[0]}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        handleExportClose();
        showToast.success('CSV CRM exportado com sucesso');
    };

    const exportarExcel = () => {
        const ws = XLSX.utils.json_to_sheet(exportRows);
        const wb = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(wb, ws, 'CRM Clientes');
        XLSX.writeFile(wb, `crm-clientes_${new Date().toISOString().split('T')[0]}.xlsx`);
        handleExportClose();
        showToast.success('Excel CRM exportado com sucesso');
    };

    const exportarPDF = () => {
        const doc = new jsPDF();
        doc.setFillColor(15, 23, 42);
        doc.rect(0, 0, 210, 34, 'F');
        doc.setTextColor(255, 255, 255);
        doc.setFontSize(20);
        doc.text('Relatório CRM de Clientes', 105, 18, { align: 'center' });
        doc.setFontSize(9);
        doc.text(`Gerado em ${new Date().toLocaleDateString('pt-BR')} ${new Date().toLocaleTimeString('pt-BR')}`, 105, 26, {
            align: 'center',
        });

        autoTable(doc, {
            startY: 42,
            head: [['Nome', 'Segmento', 'Carteira', 'Telefone', 'Valor Gasto', 'Saldo Devedor']],
            body: filteredClientes.map((cliente) => [
                cliente.nome || '',
                cliente.crmSegment,
                lifecycleLabel(cliente.lifecycle),
                cliente.celular || cliente.telefone || '',
                formatCurrency(Number(cliente.valor_total_gasto || 0)),
                formatCurrency(Number(cliente.saldo_devedor || 0)),
            ]),
            headStyles: { fillColor: [37, 99, 235] },
            styles: { fontSize: 8 },
        });

        doc.save(`crm-clientes_${new Date().toISOString().split('T')[0]}.pdf`);
        handleExportClose();
        showToast.success('PDF CRM exportado com sucesso');
    };

    const handleCampaignAction = async (cliente: CRMCustomer, action: 'open' | 'copy') => {
        const message = buildCampaignMessage(selectedCampaign, cliente);
        const whatsappUrl = buildWhatsAppUrl(cliente, message);

        if (action === 'copy') {
            await navigator.clipboard.writeText(message);
            showToast.success(`Mensagem copiada para ${cliente.nome}`);
            return;
        }

        if (!whatsappUrl) {
            showToast.error('Cliente sem numero de WhatsApp valido');
            return;
        }

        window.open(whatsappUrl, '_blank', 'noopener,noreferrer');
    };

    const handleCopyCampaignBatch = async () => {
        const payload = campaignTargets
            .slice(0, 20)
            .map((cliente) => {
                const message = buildCampaignMessage(selectedCampaign, cliente);
                return `${cliente.nome} - ${cliente.celular || cliente.telefone || 'sem telefone'}\n${message}`;
            })
            .join('\n\n-----------------\n\n');

        await navigator.clipboard.writeText(payload);
        showToast.success('Roteiro da campanha copiado para a equipe comercial');
    };

    return (
        <div className="mx-auto max-w-7xl space-y-6 p-4">
            <section className="rounded-3xl border border-slate-200 bg-gradient-to-r from-slate-950 via-blue-950 to-slate-900 p-6 text-white shadow-xl">
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3, justifyContent: 'space-between', alignItems: 'center' }}>
                    <Box>
                        <Typography variant="h4" sx={{ fontWeight: 800 }}>Clientes</Typography>
                        <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.7)', mt: 0.5 }}>
                            Carteira, relacionamento e cobrança
                        </Typography>
                    </Box>

                    <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', justifyContent: 'flex-end' }}>
                        <Button variant="outlined" startIcon={<GetAppIcon />} onClick={handleExportClick} sx={{ color: '#fff', borderColor: 'rgba(255,255,255,0.35)' }}>
                            Exportar
                        </Button>
                        <Tooltip title="Recalcula total de compras, valor gasto e segmentacao">
                            <span>
                                <Button
                                    variant="outlined"
                                    startIcon={recalcLoading ? <CircularProgress size={16} sx={{ color: '#fff' }} /> : <SyncIcon />}
                                    onClick={handleRecalcularMetricas}
                                    disabled={recalcLoading}
                                    sx={{ color: '#fff', borderColor: 'rgba(255,255,255,0.35)' }}
                                >
                                    {recalcLoading ? 'Sincronizando...' : 'Sincronizar CRM'}
                                </Button>
                            </span>
                        </Tooltip>
                        <Button variant="contained" startIcon={<PersonAddAlt1Icon />} onClick={() => { setEditData(undefined); setFormOpen(true); }} sx={{ bgcolor: '#22c55e', '&:hover': { bgcolor: '#16a34a' } }}>
                            Novo Cliente
                        </Button>
                    </Box>
                </Box>
            </section>

            <Box sx={{ display: 'grid', gap: 2, gridTemplateColumns: { xs: '1fr', md: 'repeat(2, minmax(0, 1fr))', xl: 'repeat(6, minmax(0, 1fr))' } }}>
                <KpiCard title="Base Ativa" value={dashboard.total} subtitle="Clientes gerenciados no CRM" color="#2563eb" icon={<AutoGraphIcon />} />
                <KpiCard 
                    title="Aniversariantes" 
                    value={crmStats.aniversariantes} 
                    subtitle="Neste mês — envie um WhatsApp" 
                    color="#db2777" 
                    icon={<CakeIcon />} 
                    onClick={() => {
                        // TODO: Implement actual birthday filtering logic in filteredClientes
                        // For now we just go to portfolio
                        setActiveTab('portfolio');
                    }}
                />
                <KpiCard 
                    title="Clientes Em Risco" 
                    value={crmStats.inRisk} 
                    subtitle="Exigem contato de retencao" 
                    color="#ea580c" 
                    icon={<AutorenewIcon />} 
                    onClick={() => {
                        setSegmentFilter('Risco');
                        setActiveTab('portfolio');
                    }}
                />
                <KpiCard title="Clientes Inativos" value={crmStats.inactive} subtitle="Fila de reativacao comercial" color="#dc2626" icon={<WarningAmberIcon />} />
                <KpiCard title="VIP & Fidelidade" value={crmStats.vip} subtitle="Carteira de alto valor" color="#7c3aed" icon={<StarIcon />} />
                <KpiCard title="Fiado Em Aberto" value={formatCurrency(totalFiadoAberto)} subtitle={`${crmStats.debt} clientes com saldo`} color="#d97706" icon={<AttachMoneyIcon />} onClick={() => { setFiadoFilter(true); setActiveTab('portfolio'); }} />
            </Box>

            <section className="rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-3 shadow-sm">
                <div className="grid gap-3 lg:grid-cols-4">
                    {tabs.map((tab) => {
                        const active = activeTab === tab.id;
                        return (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id)}
                                className={`rounded-2xl border px-4 py-4 text-left transition ${
                                    active
                                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 shadow-sm'
                                        : 'border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-slate-300 dark:hover:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800'
                                }`}
                            >
                                <div className="space-y-1">
                                    <p className={`text-sm font-semibold ${active ? 'text-blue-700 dark:text-blue-400' : 'text-slate-900 dark:text-white'}`}>{tab.label}</p>
                                    <p className="text-xs text-slate-500 dark:text-slate-400">{tab.description}</p>
                                </div>
                            </button>
                        );
                    })}
                </div>
            </section>

            {activeTab === 'overview' && (
                <div className="space-y-6">
                    <CustomerDashboard 
                        {...dashboard} 
                        rfmData={rfmData} 
                        onSegmentClick={(segment) => {
                            setSegmentFilter(segment as SegmentFilter);
                            setActiveTab('portfolio');
                        }}
                    />

                    <Box sx={{ display: 'grid', gap: 2, gridTemplateColumns: { xs: '1fr', xl: '1.4fr 1fr' } }}>
                        <Card className="rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-xl dark:shadow-none">
                            <CardContent className="p-6">
                                <Box className="flex justify-between items-center mb-4">
                                    <div>
                                        <Typography variant="h6" className="font-extrabold text-slate-900 dark:text-white">
                                            Fila de prioridade comercial
                                        </Typography>
                                        <Typography variant="body2" className="text-slate-500 dark:text-slate-400">
                                            Clientes que devem entrar na cadencia de contato agora.
                                        </Typography>
                                    </div>
                                    <Chip label="Top 6" className="bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400 font-bold" />
                                </Box>

                                <Box sx={{ display: 'grid', gap: 1.5 }}>
                                    {crmClientes.slice(0, 6).map((cliente) => (
                                        <Box
                                            key={cliente.id}
                                            className="flex justify-between items-center gap-4 p-4 rounded-2xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50"
                                        >
                                            <Box>
                                                <Typography className="font-bold text-slate-900 dark:text-white">{cliente.nome}</Typography>
                                                <Typography variant="body2" className="text-slate-500 dark:text-slate-400">
                                                    {lifecycleLabel(cliente.lifecycle)} • Segmento {cliente.crmSegment}
                                                </Typography>
                                            </Box>
                                            <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', flexWrap: 'wrap', justifyContent: 'flex-end' }}>
                                                <Chip
                                                    size="small"
                                                    label={cliente.hasDebt ? formatCurrency(Number(cliente.saldo_devedor || 0)) : cliente.lastPurchaseDays !== null ? `${cliente.lastPurchaseDays} dias` : 'Sem historico'}
                                                    sx={{
                                                        bgcolor: cliente.hasDebt ? '#fff7ed' : '#eff6ff',
                                                        color: cliente.hasDebt ? '#c2410c' : '#1d4ed8',
                                                        fontWeight: 700,
                                                    }}
                                                />
                                                <Button size="small" variant="outlined" onClick={() => handleRowClick(cliente)}>
                                                    Ver cliente
                                                </Button>
                                            </Box>
                                        </Box>
                                    ))}
                                </Box>
                            </CardContent>
                        </Card>

                        <Card className="rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-xl dark:shadow-none">
                            <CardContent className="p-6">
                                <Box className="flex items-center gap-2 mb-4">
                                    <CampaignIcon className="text-blue-600 dark:text-blue-400" />
                                    <Typography variant="h6" className="font-extrabold text-slate-900 dark:text-white">
                                        Centro de acao CRM
                                    </Typography>
                                </Box>

                                <Box sx={{ display: 'grid', gap: 1.5 }}>
                                    {campaignConfigs.map((campaign) => {
                                        const isSelected = selectedCampaign === campaign.key;
                                        const targetCount =
                                            campaign.key === 'reactivation'
                                                ? clientesRecuperacao.length
                                                : campaign.key === 'vip'
                                                    ? clientesVip.length
                                                    : campaign.key === 'debt'
                                                        ? clientesComFiado.length
                                                        : clientesPromotion.length;

                                        return (
                                            <button
                                                key={campaign.key}
                                                onClick={() => {
                                                    setSelectedCampaign(campaign.key);
                                                    setActiveTab('campaigns');
                                                }}
                                                className={`rounded-2xl border p-4 text-left transition ${
                                                    isSelected ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 dark:border-blue-500' : 'border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 hover:border-slate-300 dark:hover:border-slate-600'
                                                }`}
                                            >
                                                <div className="flex items-start justify-between gap-3">
                                                    <div>
                                                        <p className="text-sm font-semibold text-slate-900 dark:text-white">{campaign.title}</p>
                                                        <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">{campaign.subtitle}</p>
                                                    </div>
                                                    <span className="rounded-full bg-white px-2 py-1 text-xs font-semibold text-slate-700 shadow-sm">
                                                        {targetCount}
                                                    </span>
                                                </div>
                                            </button>
                                        );
                                    })}
                                </Box>
                            </CardContent>
                        </Card>
                    </Box>
                </div>
            )}

            {activeTab === 'recovery' && (
                <Box sx={{ display: 'grid', gap: 2, gridTemplateColumns: { xs: '1fr', xl: 'repeat(3, minmax(0, 1fr))' } }}>
                    {[
                        {
                            title: 'Recuperacao de Inativos',
                            description: 'Clientes que ficaram sem comprar e precisam de reativacao.',
                            customers: crmClientes.filter((cliente) => cliente.lifecycle === 'inativo').slice(0, 8),
                            empty: 'Nenhum cliente inativo critico no momento.',
                            action: 'reactivation' as CampaignKey,
                            color: '#dc2626',
                        },
                        {
                            title: 'Clientes Em Risco',
                            description: 'Carteira com sinais de queda de recorrencia.',
                            customers: crmClientes.filter((cliente) => cliente.lifecycle === 'em_risco').slice(0, 8),
                            empty: 'Nenhum cliente em risco identificado.',
                            action: 'reactivation' as CampaignKey,
                            color: '#ea580c',
                        },
                        {
                            title: 'Carteira Para Cobranca',
                            description: 'Clientes com fiado em aberto para abordagem consultiva.',
                            customers: clientesComFiado.slice(0, 8),
                            empty: 'Nenhum saldo em aberto para contato.',
                            action: 'debt' as CampaignKey,
                            color: '#b45309',
                        },
                    ].map((panel) => (
                        <Card key={panel.title} className="rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-xl dark:shadow-none">
                            <CardContent className="p-6">
                                <Typography variant="h6" className="font-extrabold text-slate-900 dark:text-white">
                                    {panel.title}
                                </Typography>
                                <Typography variant="body2" className="text-slate-500 dark:text-slate-400 mb-4">
                                    {panel.description}
                                </Typography>

                                <Box className="grid gap-4">
                                    {panel.customers.length === 0 && (
                                        <Box className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/50 text-slate-500 dark:text-slate-400">{panel.empty}</Box>
                                    )}

                                    {panel.customers.map((cliente) => (
                                        <Box
                                            key={cliente.id}
                                            className="p-4 rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800"
                                        >
                                            <Box className="flex justify-between gap-4">
                                                <Box>
                                                    <Typography className="font-bold text-slate-900 dark:text-white">{cliente.nome}</Typography>
                                                    <Typography variant="body2" className="text-slate-500 dark:text-slate-400">
                                                        {cliente.lastPurchaseDays !== null
                                                            ? `${cliente.lastPurchaseDays} dias sem compra`
                                                            : 'Sem historico recente'}
                                                    </Typography>
                                                </Box>
                                                <Chip
                                                    size="small"
                                                    label={cliente.crmSegment}
                                                    sx={{ bgcolor: `${panel.color}15`, color: panel.color, fontWeight: 700 }}
                                                />
                                            </Box>

                                            <Box sx={{ display: 'flex', gap: 1, mt: 2, flexWrap: 'wrap' }}>
                                                <Button size="small" variant="contained" color="success" startIcon={<WhatsAppIcon />} onClick={() => {
                                                    setSelectedCampaign(panel.action);
                                                    handleCampaignAction(cliente, 'open');
                                                }}>
                                                    WhatsApp
                                                </Button>
                                                <Button size="small" variant="outlined" onClick={() => handleRowClick(cliente)}>
                                                    Ver detalhes
                                                </Button>
                                                {cliente.hasDebt && (
                                                    <Button size="small" variant="outlined" color="warning" onClick={() => handleAbrirModalFiado(cliente)}>
                                                        Receber fiado
                                                    </Button>
                                                )}
                                            </Box>
                                        </Box>
                                    ))}
                                </Box>
                            </CardContent>
                        </Card>
                    ))}
                </Box>
            )}

            {activeTab === 'campaigns' && (
                <Box className="grid gap-4 xl:grid-cols-[1.15fr_0.85fr]">
                    <Card className="rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-xl dark:shadow-none">
                        <CardContent className="p-6">
                            <Box className="flex justify-between items-center gap-4 mb-4 flex-wrap">
                                <Box>
                                    <Typography variant="h6" className="font-extrabold text-slate-900 dark:text-white">
                                        Campanhas inteligentes por WhatsApp
                                    </Typography>
                                    <Typography variant="body2" className="text-slate-500 dark:text-slate-400">
                                        Selecione um playbook e acione a carteira certa com discurso comercial adequado.
                                    </Typography>
                                </Box>
                                <Button variant="outlined" startIcon={<CampaignIcon />} onClick={handleCopyCampaignBatch} className="dark:border-slate-600 dark:text-slate-300">
                                    Copiar roteiro
                                </Button>
                            </Box>

                            <Box className="grid gap-4 mb-6 md:grid-cols-2">
                                {campaignConfigs.map((campaign) => {
                                    const active = selectedCampaign === campaign.key;
                                    return (
                                        <button
                                            key={campaign.key}
                                            onClick={() => setSelectedCampaign(campaign.key)}
                                            className={`group relative rounded-3xl border-2 p-5 text-left transition-all duration-300 ease-out overflow-hidden ${
                                                active 
                                                    ? 'border-blue-500 bg-gradient-to-br from-blue-50 to-blue-100/50 dark:from-blue-900/30 dark:to-blue-900/10 dark:border-blue-500 shadow-lg shadow-blue-500/20 scale-[1.02]' 
                                                    : 'border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-blue-300 dark:hover:border-blue-700 hover:shadow-md hover:-translate-y-0.5'
                                            }`}
                                        >
                                            {active && <div className="absolute inset-0 bg-blue-500/5 dark:bg-blue-400/10 animate-pulse" />}
                                            <div className="relative flex items-center justify-between gap-3">
                                                <div>
                                                    <p className={`text-sm font-bold transition-colors ${active ? 'text-blue-700 dark:text-blue-400' : 'text-slate-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-300'}`}>
                                                        {campaign.title}
                                                    </p>
                                                    <p className="mt-1.5 text-xs text-slate-500 dark:text-slate-400 leading-relaxed">{campaign.description}</p>
                                                </div>
                                                <span
                                                    className={`shrink-0 rounded-full px-3 py-1.5 text-[10px] uppercase tracking-wider font-extrabold text-white shadow-sm transition-transform ${active ? 'scale-110' : 'group-hover:scale-105'}`}
                                                    style={{ backgroundColor: campaign.color }}
                                                >
                                                    {campaign.badge}
                                                </span>
                                            </div>
                                        </button>
                                    );
                                })}
                            </Box>

                            <Box className="grid gap-3">
                                {campaignTargets.slice(0, 12).map((cliente) => (
                                    <Box
                                        key={cliente.id}
                                        className={`group relative p-4 rounded-2xl border cursor-pointer transition-all duration-300 ${
                                            cliente.id === selectedCampaignCustomer?.id
                                                ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 dark:border-blue-500 shadow-md ring-4 ring-blue-500/10 dark:ring-blue-500/20'
                                                : 'border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-blue-300 dark:hover:border-slate-600 hover:shadow-lg hover:bg-slate-50 dark:hover:bg-slate-800/80 hover:-translate-y-0.5'
                                        }`}
                                        onClick={() => setCampaignCustomerId(cliente.id)}
                                    >
                                        {cliente.id === selectedCampaignCustomer?.id && (
                                            <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1.5 h-8 bg-blue-500 rounded-r-full" />
                                        )}
                                        <Box className="flex justify-between items-center gap-4 pl-2">
                                            <Box>
                                                <Typography className={`font-bold transition-colors ${cliente.id === selectedCampaignCustomer?.id ? 'text-blue-700 dark:text-blue-400' : 'text-slate-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-300'}`}>
                                                    {cliente.nome}
                                                </Typography>
                                                <Typography variant="body2" className="text-slate-500 dark:text-slate-400 mt-1 flex items-center gap-1.5">
                                                    <span className="w-1.5 h-1.5 rounded-full bg-slate-300 dark:bg-slate-600" />
                                                    {lifecycleLabel(cliente.lifecycle)} • Segmento {cliente.crmSegment}
                                                </Typography>
                                            </Box>
                                            <Box className="flex items-center gap-2 flex-wrap justify-end">
                                                {cliente.whatsappNumber && (
                                                    <Chip size="small" icon={<WhatsAppIcon sx={{ fontSize: '1rem' }} />} label="WhatsApp" color="success" variant="outlined" className="bg-green-50 dark:bg-green-900/10 border-green-200 dark:border-green-800" />
                                                )}
                                                <Chip
                                                    size="small"
                                                    label={cliente.hasDebt ? formatCurrency(Number(cliente.saldo_devedor || 0)) : formatCurrency(Number(cliente.valor_total_gasto || 0))}
                                                    className={`font-extrabold border shadow-sm ${
                                                        cliente.hasDebt 
                                                            ? 'bg-rose-50 text-rose-700 border-rose-200 dark:bg-rose-900/20 dark:text-rose-400 dark:border-rose-800/50' 
                                                            : 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-900/20 dark:text-emerald-400 dark:border-emerald-800/50'
                                                    }`}
                                                />
                                            </Box>
                                        </Box>
                                    </Box>
                                ))}
                            </Box>
                        </CardContent>
                    </Card>

                    <Card className="rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-2xl shadow-slate-200/50 dark:shadow-none overflow-hidden relative">
                        {/* Decorative background gradient */}
                        <div className="absolute top-0 right-0 w-64 h-64 bg-blue-500/5 dark:bg-blue-500/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2 pointer-events-none" />
                        
                        <CardContent className="p-8 relative">
                            <Box className="flex items-center gap-3 mb-6">
                                <div className="p-2.5 bg-blue-50 dark:bg-blue-900/30 rounded-xl">
                                    <InsightsIcon className="text-blue-600 dark:text-blue-400" />
                                </div>
                                <Typography variant="h6" className="font-extrabold text-slate-900 dark:text-white tracking-tight">
                                    Preview da abordagem
                                </Typography>
                            </Box>

                            {!selectedCampaignCustomer ? (
                                <Box className="p-8 rounded-3xl bg-slate-50 dark:bg-slate-800/40 text-slate-500 dark:text-slate-400 border border-slate-200/60 dark:border-slate-700/50 text-center flex flex-col items-center justify-center min-h-[300px] border-dashed">
                                    <div className="w-16 h-16 mb-4 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center">
                                        <WhatsAppIcon className="text-slate-300 dark:text-slate-600" fontSize="large" />
                                    </div>
                                    <Typography className="font-medium text-lg">Nenhum cliente selecionado</Typography>
                                    <Typography variant="body2" className="mt-1 opacity-70">Escolha um playbook e clique em um cliente da fila ao lado.</Typography>
                                </Box>
                            ) : (
                                <Box className="grid gap-5">
                                    {/* Info Header */}
                                    <Box className="p-5 rounded-2xl bg-white dark:bg-slate-800/80 border border-slate-100 dark:border-slate-700 shadow-sm flex flex-col gap-3">
                                        <div className="flex items-start justify-between">
                                            <div>
                                                <Typography className="font-extrabold text-lg text-slate-900 dark:text-white">{selectedCampaignCustomer.nome}</Typography>
                                                <Typography variant="body2" className="text-slate-500 dark:text-slate-400 mt-0.5">
                                                    {selectedCampaignCustomer.email || 'Sem e-mail'} •{' '}
                                                    {selectedCampaignCustomer.celular || selectedCampaignCustomer.telefone || 'Sem telefone'}
                                                </Typography>
                                            </div>
                                            <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-blue-500 to-indigo-500 flex items-center justify-center text-white font-bold text-lg shadow-md shadow-blue-500/20">
                                                {selectedCampaignCustomer.nome.charAt(0).toUpperCase()}
                                            </div>
                                        </div>
                                        <Box className="flex gap-2 flex-wrap mt-1">
                                            <Chip
                                                size="small"
                                                label={`Segmento ${selectedCampaignCustomer.crmSegment}`}
                                                sx={{
                                                    bgcolor: `${segmentColors[selectedCampaignCustomer.crmSegment] || '#64748b'}20`,
                                                    color: segmentColors[selectedCampaignCustomer.crmSegment] || '#64748b',
                                                    fontWeight: 800,
                                                }}
                                            />
                                            <Chip size="small" label={lifecycleLabel(selectedCampaignCustomer.lifecycle)} className="bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-300 font-bold border-0" />
                                        </Box>
                                    </Box>

                                    {/* Message Bubble */}
                                    <Box className="relative p-6 rounded-3xl rounded-tl-sm bg-slate-900 dark:bg-slate-950 text-white border border-slate-800 shadow-xl">
                                        <Typography variant="overline" className="opacity-80 tracking-widest font-bold flex items-center gap-2">
                                            <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                                            Mensagem sugerida
                                        </Typography>
                                        <Typography className="mt-4 whitespace-pre-wrap leading-relaxed text-slate-100 text-[15px]">
                                            {buildCampaignMessage(selectedCampaign, selectedCampaignCustomer)}
                                        </Typography>
                                    </Box>

                                    {/* Action Buttons */}
                                    <Box className="flex gap-3 flex-wrap mt-2">
                                        <Button
                                            variant="contained"
                                            className="bg-green-500 hover:bg-green-600 shadow-lg shadow-green-500/30 text-white rounded-xl px-6 py-2.5 font-bold transition-all hover:-translate-y-0.5 active:scale-95"
                                            startIcon={<WhatsAppIcon />}
                                            onClick={() => handleCampaignAction(selectedCampaignCustomer, 'open')}
                                        >
                                            Abrir WhatsApp
                                        </Button>
                                        <Button variant="outlined" onClick={() => handleCampaignAction(selectedCampaignCustomer, 'copy')} className="rounded-xl px-6 py-2.5 font-bold border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 transition-all active:scale-95">
                                            Copiar mensagem
                                        </Button>
                                        <Button variant="text" onClick={() => handleRowClick(selectedCampaignCustomer)} className="rounded-xl px-6 py-2.5 font-bold text-slate-500 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 transition-all active:scale-95">
                                            Ver Perfil Completo
                                        </Button>
                                    </Box>

                                    {/* Helper Tip */}
                                    <Box className="p-4 rounded-2xl bg-gradient-to-r from-blue-50/80 to-indigo-50/50 dark:from-blue-900/10 dark:to-indigo-900/10 border border-blue-100 dark:border-blue-800/30 mt-2 flex items-start gap-3">
                                        <div className="mt-0.5"><InsightsIcon className="text-blue-500" fontSize="small" /></div>
                                        <div>
                                            <Typography variant="subtitle2" className="text-blue-800 dark:text-blue-300 font-bold">
                                                Operacao recomendada
                                            </Typography>
                                            <Typography variant="body2" className="text-slate-600 dark:text-slate-400 mt-1 leading-relaxed">
                                                Use esta area como cadencia comercial. A automacao assistida por WhatsApp ja prepara a
                                                mensagem com base no momento do cliente.
                                            </Typography>
                                        </div>
                                    </Box>
                                </Box>
                            )}
                        </CardContent>
                    </Card>
                </Box>
            )}

            {activeTab === 'portfolio' && (
                <div className="space-y-4">
                    <Box sx={{ display: 'grid', gap: 2, gridTemplateColumns: { xs: '1fr', lg: '2fr 1fr 1fr' }, alignItems: 'center' }}>
                        <TextField
                            placeholder="Buscar por nome, CPF, telefone ou email"
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            variant="outlined"
                            size="small"
                            InputProps={{
                                startAdornment: (
                                    <InputAdornment position="start">
                                        <SearchIcon />
                                    </InputAdornment>
                                ),
                                endAdornment: searchTerm && (
                                    <InputAdornment position="end">
                                        <ClearIcon sx={{ cursor: 'pointer' }} onClick={() => setSearchTerm('')} />
                                    </InputAdornment>
                                ),
                            }}
                        />

                        <FormControl size="small">
                            <InputLabel>Status</InputLabel>
                            <Select value={statusFilter} label="Status" onChange={(e) => setStatusFilter(e.target.value as StatusFilter)} startAdornment={<FilterListIcon sx={{ mr: 1 }} />}>
                                <MenuItem value="todos">Todos</MenuItem>
                                <MenuItem value="ativos">Ativos</MenuItem>
                                <MenuItem value="inativos">Inativos</MenuItem>
                            </Select>
                        </FormControl>

                        <FormControl size="small">
                            <InputLabel>Segmento</InputLabel>
                            <Select value={segmentFilter} label="Segmento" onChange={(e) => setSegmentFilter(e.target.value as SegmentFilter)}>
                                <MenuItem value="todos">Todos</MenuItem>
                                <MenuItem value="Campeão">Campeão</MenuItem>
                                <MenuItem value="Fiel">Fiel</MenuItem>
                                <MenuItem value="Regular">Regular</MenuItem>
                                <MenuItem value="Risco">Risco</MenuItem>
                                <MenuItem value="Perdido">Perdido</MenuItem>
                                <MenuItem value="Novo">Novo</MenuItem>
                            </Select>
                        </FormControl>
                    </Box>

                    <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                        <Chip label={`${filteredClientes.length} clientes na carteira`} className="bg-slate-200 text-slate-900 dark:bg-slate-800 dark:text-slate-200 font-bold" />
                        <Chip
                            label={fiadoFilter ? 'Somente com fiado' : 'Todos os perfis'}
                            onClick={() => setFiadoFilter((current) => !current)}
                            color={fiadoFilter ? 'warning' : 'default'}
                            icon={<HandshakeIcon />}
                        />
                        {segmentFilter !== 'todos' && (
                            <Chip label={`Segmento ${segmentFilter}`} onDelete={() => setSegmentFilter('todos')} color="primary" variant="outlined" />
                        )}
                    </Box>

                    <CustomerTable
                        clientes={filteredClientes}
                        loading={loading}
                        onRowClick={handleRowClick}
                        onEdit={handleEdit}
                        onDelete={handleDelete}
                        selectedClienteId={selectedCliente?.id}
                        onReceberFiado={handleAbrirModalFiado}
                        rfmData={rfmData}
                    />
                </div>
            )}

            <Menu anchorEl={exportMenuAnchor} open={Boolean(exportMenuAnchor)} onClose={handleExportClose}>
                <MenuItem onClick={exportarCSV}>Exportar CSV</MenuItem>
                <MenuItem onClick={exportarExcel}>Exportar Excel</MenuItem>
                <MenuItem onClick={exportarPDF}>Exportar PDF</MenuItem>
            </Menu>

            <CustomerForm
                open={formOpen}
                onClose={() => {
                    setFormOpen(false);
                    setEditData(undefined);
                }}
                onSave={handleSave}
                initialData={editData}
                loading={saving}
            />

            <CustomerDetailsModal
                open={!!selectedCliente}
                cliente={clienteDetalhado}
                loading={detalheLoading}
                onClose={() => {
                    setSelectedCliente(null);
                    setClienteDetalhado(null);
                }}
                onEdit={handleEdit}
                onDelete={handleDelete}
                rfmData={rfmData}
            />

            <Dialog open={fiadoModal.open} onClose={() => setFiadoModal({ open: false, cliente: null })} maxWidth="xs" fullWidth>
                <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1, color: '#b45309', fontWeight: 800 }}>
                    <AttachMoneyIcon /> Receber fiado
                </DialogTitle>
                <DialogContent>
                    {fiadoModal.cliente && (
                        <Box>
                            <Box sx={{ mb: 2, p: 1.5, bgcolor: '#fff7ed', borderRadius: 2, border: '1px solid #fed7aa' }}>
                                <Typography variant="subtitle2" sx={{ color: '#b45309', fontWeight: 700 }}>
                                    {fiadoModal.cliente.nome}
                                </Typography>
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                                    <WarningAmberIcon sx={{ color: '#f59e0b', fontSize: 16 }} />
                                    <Typography variant="body2" sx={{ color: '#9a3412', fontWeight: 600 }}>
                                        Saldo devedor: {formatCurrency(Number(fiadoModal.cliente.saldo_devedor || 0))}
                                    </Typography>
                                </Box>
                            </Box>

                            <TextField
                                label="Valor a pagar (R$)"
                                value={fiadoValor}
                                onChange={(e) => setFiadoValor(e.target.value)}
                                fullWidth
                                type="number"
                                inputProps={{ min: 0, step: '0.01', max: fiadoModal.cliente.saldo_devedor ?? 0 }}
                                sx={{ mb: 2, mt: 1 }}
                                helperText={`Máximo: ${formatCurrency(Number(fiadoModal.cliente.saldo_devedor || 0))}`}
                            />

                            <FormControl fullWidth sx={{ mb: 1 }}>
                                <InputLabel>Forma de pagamento</InputLabel>
                                <Select value={fiadoForma} label="Forma de pagamento" onChange={(e) => setFiadoForma(e.target.value)}>
                                    <MenuItem value="Dinheiro">Dinheiro</MenuItem>
                                    <MenuItem value="PIX">PIX</MenuItem>
                                    <MenuItem value="Cartão de Débito">Cartão de Débito</MenuItem>
                                    <MenuItem value="Cartão de Crédito">Cartão de Crédito</MenuItem>
                                </Select>
                            </FormControl>

                            <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                                O valor será registrado como recebimento da carteira e refletido no caixa.
                            </Typography>
                        </Box>
                    )}
                </DialogContent>
                <DialogActions sx={{ px: 3, pb: 2 }}>
                    <Button onClick={() => setFiadoModal({ open: false, cliente: null })} color="inherit">
                        Cancelar
                    </Button>
                    <Button variant="contained" onClick={handlePagarFiado} disabled={fiadoLoading || !fiadoValor} sx={{ bgcolor: '#f59e0b', '&:hover': { bgcolor: '#d97706' } }}>
                        {fiadoLoading ? 'Registrando...' : 'Confirmar recebimento'}
                    </Button>
                </DialogActions>
            </Dialog>

            {loading && (
                <div className="flex justify-center py-6">
                    <CircularProgress />
                </div>
            )}
        </div>
    );
};

export default CustomersPage;
