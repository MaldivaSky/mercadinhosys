import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
    BarChart3, 
    FileSpreadsheet, 
    FileText, 
    Download, 
    Calendar as CalendarIcon,
    TrendingUp,
    Users,
    Package,
    Wallet,
    Archive,
    Loader2,
    X,
    Search,
    Clock,
    Target,
    AlertTriangle,
    Zap,
    Brain
} from 'lucide-react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import * as XLSX from 'xlsx';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
import { toast } from 'react-hot-toast';
import { salesService } from '../sales/salesService';
import { productsService } from '../products/productsService';
import { pontoService } from '../ponto/pontoService';
import { apiClient } from '../../api/apiClient';

// Interfaces
interface DateRange {
    startDate: string;
    endDate: string;
}

interface ReportCardProps {
    title: string;
    description: string;
    icon: React.ElementType;
    color: string;
    loading: boolean;
    onOpen: () => void;
}

const ReportCard: React.FC<ReportCardProps> = ({ 
    title, 
    description, 
    icon: Icon, 
    color, 
    loading, 
    onOpen
}) => (
    <button onClick={onOpen} className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 hover:shadow-md transition-all duration-200 group text-left">
        <div className="flex items-start justify-between mb-4">
            <div className={`p-3 rounded-lg ${color} group-hover:scale-110 transition-transform duration-200`}>
                <Icon className="w-6 h-6 text-white" />
            </div>
            {loading && <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />}
        </div>
        <h3 className="text-lg font-bold text-gray-900 mb-2">{title}</h3>
        <p className="text-sm text-gray-500 mb-2 min-h-[40px]">{description}</p>
        <span className="text-xs text-indigo-600 font-medium">Ver detalhes</span>
    </button>
);

const ReportsPage: React.FC = () => {
    const navigate = useNavigate();
    // Estado para datas (padrão: últimos 30 dias)
    const [dateRange, setDateRange] = useState<DateRange>({
        startDate: new Date(new Date().setDate(new Date().getDate() - 30)).toISOString().split('T')[0],
        endDate: new Date().toISOString().split('T')[0]
    });

    const [loadingReport, setLoadingReport] = useState<string | null>(null);
    const [loadingBackup, setLoadingBackup] = useState(false);
    const [modalType, setModalType] = useState<'vendas' | 'produtos' | 'financeiro' | 'equipe' | 'ponto' | 'rfm' | 'abc' | 'previsao' | null>(null);
    const [modalOpen, setModalOpen] = useState(false);
    const [vendasData, setVendasData] = useState<Array<{
        'Código': string;
        'Data/Hora': string;
        'Cliente': string;
        'Funcionário': string;
        'Subtotal (R$)': number;
        'Desconto (R$)': number;
        'Total (R$)': number;
        'Forma Pagamento': string;
        'Qtd Itens': number;
        'Status': string;
    }>>([]);
    const [produtosData, setProdutosData] = useState<Array<{ 'Código': string | number; 'Nome': string; 'Categoria': string; 'Preço Venda': number; 'Preço Custo': number; 'Estoque': any; 'Estoque Mínimo': number; 'Status': string }>>([]);
    const [financeiroData, setFinanceiroData] = useState<Array<{ 'Forma de Pagamento': string; 'Qtd. Transações': number; 'Total (R$)': number; 'Percentual (%)': string }>>([]);
    const [equipeData, setEquipeData] = useState<Array<{ 'Funcionário': string; 'Vendas Realizadas': number; 'Total Vendido (R$)': number; 'Ticket Médio (R$)': string }>>([]);
    const [pontoData, setPontoData] = useState<Array<{ 'Funcionário': string; 'Dias Trabalhados': number; 'Taxa Presença (%)': string; 'Total Atrasos': number; 'Minutos Atraso': number }>>([]);
    const [rfmData, setRfmData] = useState<Array<any>>([]);
    const [abcData, setAbcData] = useState<Array<any>>([]);
    const [previsaoData, setPrevisaoData] = useState<Array<any>>([]);
    const [searchQuery, setSearchQuery] = useState<string>('');
    const filterRow = (row: any) => {
        const q = searchQuery.trim().toLowerCase();
        if (!q) return true;
        return Object.values(row).some((v) => String(v ?? '').toLowerCase().includes(q));
    };
    
    const openModal = async (type: 'vendas' | 'produtos' | 'financeiro' | 'equipe' | 'ponto' | 'rfm' | 'abc' | 'previsao') => {
        // Se for ponto, navega para a página específica de relatórios de ponto
        if (type === 'ponto') {
            navigate('/ponto-relatorios');
            return;
        }
        
        setModalType(type);
        setModalOpen(true);
        try {
            if (type === 'vendas' && vendasData.length === 0) {
                await fetchVendasData();
            } else if (type === 'produtos' && produtosData.length === 0) {
                await fetchProdutosData();
            } else if (type === 'financeiro' && financeiroData.length === 0) {
                await fetchFinanceiroData();
            } else if (type === 'equipe' && equipeData.length === 0) {
                await fetchEquipeData();
            } else if (type === 'rfm' && rfmData.length === 0) {
                await fetchRFMData();
            } else if (type === 'abc' && abcData.length === 0) {
                await fetchABCData();
            } else if (type === 'previsao' && previsaoData.length === 0) {
                await fetchPrevisaoData();
            }
        } catch (e) {
            // erros já são tratados dentro dos fetchers
        }
    };
    
    const closeModal = () => {
        setModalOpen(false);
        setModalType(null);
    };

    const handleBackupExport = async () => {
        setLoadingBackup(true);
        try {
            const res = await apiClient.get('/relatorios/backup/exportar', { responseType: 'blob' });
            const blob = new Blob([res.data], { type: 'application/zip' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `backup_local_${new Date().toISOString().slice(0,19).replace(/[:T]/g,'-')}.zip`;
            a.click();
            window.URL.revokeObjectURL(url);
            toast.success('Backup baixado com sucesso!');
        } catch (error) {
            console.error(error);
            toast.error('Erro ao exportar backup');
        } finally {
            setLoadingBackup(false);
        }
    };

    // ==================== UTILITÁRIOS DE EXPORTAÇÃO ====================

    const exportToCSV = (data: any[], filename: string) => {
        const worksheet = XLSX.utils.json_to_sheet(data);
        const csvOutput = XLSX.utils.sheet_to_csv(worksheet);
        const blob = new Blob([csvOutput], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = `${filename}.csv`;
        link.click();
    };

    const exportToExcel = (data: any[], filename: string, sheetName: string) => {
        const worksheet = XLSX.utils.json_to_sheet(data);
        const workbook = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(workbook, worksheet, sheetName);
        XLSX.writeFile(workbook, `${filename}.xlsx`);
    };

    const generatePDFHeader = (doc: jsPDF, title: string, period?: string) => {
        const companyName = "MERCADINHO SYS";
        const reportDate = format(new Date(), "dd/MM/yyyy HH:mm", { locale: ptBR });
        
        doc.setFillColor(63, 81, 181); // Indigo
        doc.rect(0, 0, doc.internal.pageSize.width, 40, 'F');
        
        doc.setTextColor(255, 255, 255);
        doc.setFontSize(22);
        doc.setFont("helvetica", "bold");
        doc.text(companyName, 14, 20);
        
        doc.setFontSize(16);
        doc.setFont("helvetica", "normal");
        doc.text(title, 14, 32);
        
        doc.setFontSize(10);
        doc.text(`Gerado em: ${reportDate}`, doc.internal.pageSize.width - 14, 20, { align: 'right' });
        if (period) {
            doc.text(`Período: ${period}`, doc.internal.pageSize.width - 14, 32, { align: 'right' });
        }
    };

    // ==================== GERADORES DE RELATÓRIOS ====================

    const fetchVendasData = async () => {
        setLoadingReport('vendas');
        try {
            // Buscar TODAS as vendas do período
            const response = await apiClient.get('/vendas/', {
                params: {
                    data_inicio: dateRange.startDate,
                    data_fim: dateRange.endDate,
                    per_page: 10000, // Pegar TODAS as vendas
                    status: 'finalizada' // Apenas vendas finalizadas
                }
            });
            
            console.log('📊 Vendas carregadas:', response.data.vendas?.length || 0);
            
            // NÃO AGRUPAR! Mostrar TODAS as vendas individuais
            const data = response.data.vendas.map((venda: any) => {
                // Extrair data formatada
                let dataFormatada = '';
                try {
                    if (venda.data_formatada) {
                        dataFormatada = venda.data_formatada;
                    } else if (venda.data_venda) {
                        const dataObj = new Date(venda.data_venda);
                        dataFormatada = format(dataObj, 'dd/MM/yyyy HH:mm');
                    } else if (venda.data) {
                        const dataObj = new Date(venda.data);
                        dataFormatada = format(dataObj, 'dd/MM/yyyy HH:mm');
                    }
                } catch (err) {
                    console.error('Erro ao formatar data:', err);
                    dataFormatada = 'Data inválida';
                }

                return {
                    'Código': venda.codigo || '-',
                    'Data/Hora': dataFormatada,
                    'Cliente': venda.cliente?.nome || 'Consumidor Final',
                    'Funcionário': venda.funcionario?.nome || 'Não Informado',
                    'Subtotal (R$)': parseFloat(venda.subtotal || 0),
                    'Desconto (R$)': parseFloat(venda.desconto || 0),
                    'Total (R$)': parseFloat(venda.total || 0),
                    'Forma Pagamento': venda.forma_pagamento?.replace(/_/g, ' ').toUpperCase() || '-',
                    'Qtd Itens': venda.quantidade_itens || 0,
                    'Status': venda.status?.toUpperCase() || '-'
                };
            }).sort((a, b) => {
                // Ordenar por data/hora (mais recente primeiro)
                try {
                    const dateA = a['Data/Hora'].split(' ')[0].split('/').reverse().join('-');
                    const dateB = b['Data/Hora'].split(' ')[0].split('/').reverse().join('-');
                    return dateB.localeCompare(dateA);
                } catch {
                    return 0;
                }
            });
            
            console.log('✅ Vendas processadas:', data.length, 'vendas');
            
            if (data.length === 0) {
                toast.error('Nenhuma venda encontrada no período selecionado');
            }
            
            setVendasData(data);
        } catch (error) {
            console.error('❌ Erro ao carregar vendas:', error);
            toast.error('Erro ao carregar vendas');
        } finally {
            setLoadingReport(null);
        }
    };
    
    const handleVendasReport = async (type: 'pdf' | 'excel' | 'csv') => {
        setLoadingReport('vendas');
        try {
            if (vendasData.length === 0) {
                await fetchVendasData();
            }
            const dataToExport = vendasData;

            const filename = `Relatorio_Vendas_Detalhado_${dateRange.startDate}_${dateRange.endDate}`;

            if (type === 'csv') exportToCSV(dataToExport, filename);
            else if (type === 'excel') exportToExcel(dataToExport, filename, 'Vendas Detalhadas');
            else {
                const doc = new jsPDF('landscape'); // Paisagem para caber mais colunas
                generatePDFHeader(doc, "Relatório Detalhado de Vendas", `${format(new Date(dateRange.startDate), 'dd/MM/yyyy')} a ${format(new Date(dateRange.endDate), 'dd/MM/yyyy')}`);
                
                autoTable(doc, {
                    startY: 50,
                    head: [['Código', 'Data/Hora', 'Cliente', 'Funcionário', 'Total', 'Desconto', 'Forma Pgto']],
                    body: dataToExport.map(item => [
                        item['Código'],
                        item['Data/Hora'],
                        item['Cliente'],
                        item['Funcionário'],
                        item['Total (R$)'].toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' }),
                        item['Desconto (R$)'].toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' }),
                        item['Forma Pagamento']
                    ]),
                    theme: 'grid',
                    headStyles: { fillColor: [63, 81, 181], fontSize: 9 },
                    bodyStyles: { fontSize: 8 },
                    styles: { cellPadding: 2 }
                });

                // Adicionar sumário
                const totalPeriodo = dataToExport.reduce((acc, curr) => acc + curr['Total (R$)'], 0);
                const totalDescontos = dataToExport.reduce((acc, curr) => acc + curr['Desconto (R$)'], 0);
                const finalY = (doc as any).lastAutoTable.finalY || 50;
                doc.setFontSize(10);
                doc.setTextColor(0, 0, 0);
                doc.text(`Total de Vendas: ${dataToExport.length}`, 14, finalY + 10);
                doc.text(`Faturamento Total: ${totalPeriodo.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}`, 14, finalY + 17);
                doc.text(`Total Descontos: ${totalDescontos.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}`, 14, finalY + 24);

                doc.save(`${filename}.pdf`);
            }
            toast.success('Relatório gerado com sucesso!');
        } catch (error) {
            console.error(error);
            toast.error('Erro ao gerar relatório de vendas');
        } finally {
            setLoadingReport(null);
        }
    };

    const fetchProdutosData = async () => {
        setLoadingReport('produtos');
        try {
            const response = await productsService.getAllEstoque(1, 1000);
            const produtos = response.produtos;
            const data = produtos.map(p => ({
                'Código': p.codigo_barras || p.id,
                'Nome': p.nome,
                'Categoria': p.categoria || 'N/A',
                'Preço Venda': p.preco_venda,
                'Preço Custo': p.preco_custo,
                'Estoque': p.estoque_status ?? 'N/A',
                'Estoque Mínimo': (p.estoque_minimo ?? 0),
                'Status': (p.quantidade || 0) <= (p.estoque_minimo || 0) ? 'CRÍTICO' : 'OK'
            }));
            setProdutosData(data);
        } catch (error) {
            console.error(error);
            toast.error('Erro ao carregar produtos');
        } finally {
            setLoadingReport(null);
        }
    };
    
    const handleProdutosReport = async (type: 'pdf' | 'excel' | 'csv') => {
        setLoadingReport('produtos');
        try {
            if (produtosData.length === 0) {
                await fetchProdutosData();
            }
            const dataToExport = produtosData;

            const filename = `Relatorio_Estoque_${format(new Date(), 'yyyy-MM-dd')}`;

            if (type === 'csv') exportToCSV(dataToExport, filename);
            else if (type === 'excel') exportToExcel(dataToExport, filename, 'Estoque Atual');
            else {
                const doc = new jsPDF();
                generatePDFHeader(doc, "Relatório de Estoque e Inventário");
                
                autoTable(doc, {
                    startY: 50,
                    head: [['Nome', 'Categoria', 'Preço', 'Estoque', 'Status']],
                    body: dataToExport.map(item => [
                        item.Nome || '', 
                        item.Categoria || '', 
                        item['Preço Venda'].toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' }),
                        item.Estoque || '',
                        item.Status || ''
                    ]),
                    theme: 'striped',
                    headStyles: { fillColor: [16, 185, 129] }, // Green
                    didParseCell: function(data) {
                        if (data.section === 'body' && data.column.index === 4) {
                            if (data.cell.raw === 'CRÍTICO') {
                                data.cell.styles.textColor = [220, 38, 38]; // Red
                                data.cell.styles.fontStyle = 'bold';
                            }
                        }
                    }
                });

                doc.save(`${filename}.pdf`);
            }
            toast.success('Relatório de estoque gerado!');
        } catch (error) {
            console.error(error);
            toast.error('Erro ao gerar relatório de estoque');
        } finally {
            setLoadingReport(null);
        }
    };

    const fetchFinanceiroData = async () => {
        setLoadingReport('financeiro');
        try {
            const analytics = await salesService.getAnalytics({
                data_inicio: dateRange.startDate,
                data_fim: dateRange.endDate
            });
            const data = analytics.formasPagamento.map(f => ({
                'Forma de Pagamento': f.forma.toUpperCase(),
                'Qtd. Transações': f.quantidade,
                'Total (R$)': f.total,
                'Percentual (%)': f.percentual.toFixed(2)
            }));
            setFinanceiroData(data);
        } catch (error) {
            console.error(error);
            toast.error('Erro ao carregar financeiro');
        } finally {
            setLoadingReport(null);
        }
    };
    
    const handleFinanceiroReport = async (type: 'pdf' | 'excel' | 'csv') => {
        setLoadingReport('financeiro');
        try {
            if (financeiroData.length === 0) {
                await fetchFinanceiroData();
            }
            const dataToExport = financeiroData;

            const filename = `Relatorio_Financeiro_${dateRange.startDate}`;

            if (type === 'csv') exportToCSV(dataToExport, filename);
            else if (type === 'excel') exportToExcel(dataToExport, filename, 'Financeiro');
            else {
                const doc = new jsPDF();
                generatePDFHeader(doc, "Relatório Financeiro", `${format(new Date(dateRange.startDate), 'dd/MM/yyyy')} a ${format(new Date(dateRange.endDate), 'dd/MM/yyyy')}`);
                
                autoTable(doc, {
                    startY: 50,
                    head: [['Forma Pagamento', 'Transações', 'Total', '%']],
                    body: dataToExport.map(item => [
                        item['Forma de Pagamento'], 
                        item['Qtd. Transações'], 
                        item['Total (R$)'].toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' }),
                        item['Percentual (%)'] + '%'
                    ]),
                    theme: 'grid',
                    headStyles: { fillColor: [245, 158, 11] }, // Amber
                });

                doc.save(`${filename}.pdf`);
            }
            toast.success('Relatório financeiro gerado!');
        } catch (error) {
            console.error(error);
            toast.error('Erro ao gerar relatório financeiro');
        } finally {
            setLoadingReport(null);
        }
    };

    const fetchEquipeData = async () => {
        setLoadingReport('equipe');
        try {
            const analytics = await salesService.getAnalytics({
                data_inicio: dateRange.startDate,
                data_fim: dateRange.endDate
            });
            const data = analytics.topFuncionarios.map(f => ({
                'Funcionário': f.funcionario,
                'Vendas Realizadas': f.quantidade,
                'Total Vendido (R$)': f.total,
                'Ticket Médio (R$)': (f.total / f.quantidade).toFixed(2)
            }));
            setEquipeData(data);
        } catch (error) {
            console.error(error);
            toast.error('Erro ao carregar equipe');
        } finally {
            setLoadingReport(null);
        }
    };
    
    const handleEquipeReport = async (type: 'pdf' | 'excel' | 'csv') => {
        setLoadingReport('equipe');
        try {
            if (equipeData.length === 0) {
                await fetchEquipeData();
            }
            const dataToExport = equipeData;

            const filename = `Performance_Equipe_${dateRange.startDate}`;

            if (type === 'csv') exportToCSV(dataToExport, filename);
            else if (type === 'excel') exportToExcel(dataToExport, filename, 'Performance Equipe');
            else {
                const doc = new jsPDF();
                generatePDFHeader(doc, "Performance da Equipe", `${format(new Date(dateRange.startDate), 'dd/MM/yyyy')} a ${format(new Date(dateRange.endDate), 'dd/MM/yyyy')}`);
                
                autoTable(doc, {
                    startY: 50,
                    head: [['Nome', 'Vendas', 'Total', 'Ticket Médio']],
                    body: dataToExport.map(item => [
                        item.Funcionário, 
                        item['Vendas Realizadas'], 
                        item['Total Vendido (R$)'].toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' }),
                        parseFloat(item['Ticket Médio (R$)']).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
                    ]),
                    theme: 'striped',
                    headStyles: { fillColor: [236, 72, 153] }, // Pink
                });

                doc.save(`${filename}.pdf`);
            }
            toast.success('Relatório de equipe gerado!');
        } catch (error) {
            console.error(error);
            toast.error('Erro ao gerar relatório de equipe');
        } finally {
            setLoadingReport(null);
        }
    };

    const fetchPontoData = async () => {
        setLoadingReport('ponto');
        try {
            const response = await pontoService.obterRelatorioFuncionarios({
                data_inicio: dateRange.startDate,
                data_fim: dateRange.endDate
            });
            
            if (response.success && response.data) {
                const data = response.data.map((f: any) => ({
                    'Funcionário': f.funcionario_nome,
                    'Dias Trabalhados': f.dias_trabalhados,
                    'Taxa Presença (%)': f.taxa_presenca.toFixed(1),
                    'Total Atrasos': f.total_atrasos,
                    'Minutos Atraso': f.minutos_atraso_total
                }));
                setPontoData(data);
            }
        } catch (error) {
            console.error(error);
            toast.error('Erro ao carregar relatório de ponto');
        } finally {
            setLoadingReport(null);
        }
    };

    // ==================== NOVOS RELATÓRIOS DE INTELIGÊNCIA ====================

    const fetchRFMData = async () => {
        setLoadingReport('rfm');
        try {
            const response = await apiClient.get('/relatorios/rfm/clientes', {
                params: { days: 180 }
            });
            if (response.data.success) {
                const data = response.data.clientes.map((c: any) => ({
                    'Nome': c.nome,
                    'Email': c.email || 'N/A',
                    'Celular': c.celular || 'N/A',
                    'Segmento': c.segmento,
                    'Recência (dias)': c.recency_days,
                    'Frequência': c.frequency,
                    'Valor Total (R$)': c.monetary,
                    'Score RFM': c.rfm_score,
                    'Em Risco': c.em_risco ? 'SIM' : 'NÃO',
                    'Última Compra': c.ultima_compra ? new Date(c.ultima_compra).toLocaleDateString('pt-BR') : 'N/A'
                }));
                setRfmData(data);
            }
        } catch (error) {
            console.error(error);
            toast.error('Erro ao carregar análise RFM');
        } finally {
            setLoadingReport(null);
        }
    };

    const fetchABCData = async () => {
        setLoadingReport('abc');
        try {
            const response = await apiClient.get('/relatorios/rentabilidade/abc', {
                params: { days: 30 }
            });
            if (response.data.success) {
                const data = response.data.produtos.map((p: any) => ({
                    'Produto': p.produto_nome,
                    'Classe ABC': p.classe_abc,
                    'Quantidade Vendida': p.quantidade_vendida,
                    'Faturamento (R$)': p.faturamento,
                    'Lucro Real (R$)': p.lucro_real,
                    'Margem Real (%)': p.margem_real.toFixed(2),
                    'Estoque Atual': p.estoque_atual,
                    '% Faturamento': p.percentual_faturamento.toFixed(2)
                }));
                setAbcData(data);
            }
        } catch (error) {
            console.error(error);
            toast.error('Erro ao carregar análise ABC');
        } finally {
            setLoadingReport(null);
        }
    };

    const fetchPrevisaoData = async () => {
        setLoadingReport('previsao');
        try {
            const response = await apiClient.get('/relatorios/estoque/previsao-esgotamento');
            if (response.data.success) {
                const data = response.data.previsoes
                    .filter((p: any) => p.status !== 'SEM_MOVIMENTO')
                    .map((p: any) => ({
                        'Produto': p.produto_nome,
                        'Estoque Atual': p.estoque_atual,
                        'Média Vendas/Dia': p.media_vendas_diarias,
                        'Dias até Esgotamento': p.dias_ate_esgotamento || 'N/A',
                        'Data Prevista': p.data_esgotamento_prevista ? new Date(p.data_esgotamento_prevista).toLocaleDateString('pt-BR') : 'N/A',
                        'Status': p.status
                    }));
                setPrevisaoData(data);
            }
        } catch (error) {
            console.error(error);
            toast.error('Erro ao carregar previsão de esgotamento');
        } finally {
            setLoadingReport(null);
        }
    };
    
    const handlePontoReport = async (type: 'pdf' | 'excel' | 'csv') => {
        setLoadingReport('ponto');
        try {
            if (pontoData.length === 0) {
                await fetchPontoData();
            }
            const dataToExport = pontoData;

            const filename = `Relatorio_Ponto_${dateRange.startDate}_${dateRange.endDate}`;

            if (type === 'csv') exportToCSV(dataToExport, filename);
            else if (type === 'excel') exportToExcel(dataToExport, filename, 'Controle de Ponto');
            else {
                const doc = new jsPDF();
                generatePDFHeader(doc, "Relatório de Controle de Ponto", `${format(new Date(dateRange.startDate), 'dd/MM/yyyy')} a ${format(new Date(dateRange.endDate), 'dd/MM/yyyy')}`);
                
                autoTable(doc, {
                    startY: 50,
                    head: [['Funcionário', 'Dias Trab.', 'Presença %', 'Atrasos', 'Min. Atraso']],
                    body: dataToExport.map(item => [
                        item.Funcionário, 
                        item['Dias Trabalhados'], 
                        item['Taxa Presença (%)'] + '%',
                        item['Total Atrasos'],
                        item['Minutos Atraso']
                    ]),
                    theme: 'grid',
                    headStyles: { fillColor: [99, 102, 241] }, // Indigo
                    didParseCell: function(data) {
                        if (data.section === 'body' && data.column.index === 3) {
                            const atrasos = parseInt(data.cell.raw as string);
                            if (atrasos > 5) {
                                data.cell.styles.textColor = [220, 38, 38]; // Red
                                data.cell.styles.fontStyle = 'bold';
                            } else if (atrasos > 2) {
                                data.cell.styles.textColor = [245, 158, 11]; // Amber
                            }
                        }
                    }
                });

                // Adicionar sumário
                const totalAtrasos = dataToExport.reduce((acc, curr) => acc + curr['Total Atrasos'], 0);
                const mediaPresenca = dataToExport.reduce((acc, curr) => acc + parseFloat(curr['Taxa Presença (%)']), 0) / dataToExport.length;
                const finalY = (doc as any).lastAutoTable.finalY || 50;
                
                doc.setFontSize(11);
                doc.setTextColor(0, 0, 0);
                doc.setFont("helvetica", "bold");
                doc.text('Resumo do Período:', 14, finalY + 12);
                doc.setFont("helvetica", "normal");
                doc.setFontSize(10);
                doc.text(`• Total de Atrasos: ${totalAtrasos}`, 14, finalY + 20);
                doc.text(`• Taxa Média de Presença: ${mediaPresenca.toFixed(1)}%`, 14, finalY + 27);
                doc.text(`• Funcionários Monitorados: ${dataToExport.length}`, 14, finalY + 34);

                doc.save(`${filename}.pdf`);
            }
            toast.success('Relatório de ponto gerado com sucesso!');
        } catch (error) {
            console.error(error);
            toast.error('Erro ao gerar relatório de ponto');
        } finally {
            setLoadingReport(null);
        }
    };

    return (
        <div className="space-y-8 max-w-7xl mx-auto pb-10">
            {/* Header com Filtros */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 flex flex-col md:flex-row justify-between items-center gap-4">
                <div className="flex items-center space-x-4">
                    <div className="p-3 bg-indigo-600 rounded-lg shadow-lg shadow-indigo-200">
                        <BarChart3 className="w-8 h-8 text-white" />
                    </div>
                    <div>
                        <h1 className="text-2xl font-bold text-gray-900">
                            Central de Inteligência
                        </h1>
                        <p className="text-gray-500">
                            Extraia insights valiosos para tomada de decisão
                        </p>
                    </div>
                </div>

                <div className="flex items-center gap-3 bg-gray-50 p-2 rounded-lg border border-gray-200">
                    <CalendarIcon className="w-5 h-5 text-gray-500 ml-2" />
                    <div className="flex items-center gap-2">
                        <input 
                            type="date" 
                            value={dateRange.startDate}
                            onChange={(e) => setDateRange({...dateRange, startDate: e.target.value})}
                            className="bg-transparent border-none text-sm font-medium text-gray-700 focus:ring-0"
                        />
                        <span className="text-gray-400">até</span>
                        <input 
                            type="date" 
                            value={dateRange.endDate}
                            onChange={(e) => setDateRange({...dateRange, endDate: e.target.value})}
                            className="bg-transparent border-none text-sm font-medium text-gray-700 focus:ring-0"
                        />
                    </div>
                </div>
            </div>

            {/* Grid de Relatórios */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-6">
                <ReportCard 
                    title="Vendas Detalhadas" 
                    description="Análise cronológica de vendas, totais diários e volume de transações."
                    icon={TrendingUp}
                    color="bg-blue-500"
                    loading={loadingReport === 'vendas'}
                    onOpen={() => openModal('vendas')}
                />

                <ReportCard 
                    title="Estoque & Produtos" 
                    description="Inventário completo, níveis de estoque, custos e margens de produtos."
                    icon={Package}
                    color="bg-emerald-500"
                    loading={loadingReport === 'produtos'}
                    onOpen={() => openModal('produtos')}
                />

                <ReportCard 
                    title="Fluxo Financeiro" 
                    description="Detalhamento por formas de pagamento, entradas e projeções."
                    icon={Wallet}
                    color="bg-amber-500"
                    loading={loadingReport === 'financeiro'}
                    onOpen={() => openModal('financeiro')}
                />

                <ReportCard 
                    title="Performance Equipe" 
                    description="Ranking de vendedores, comissões, ticket médio e produtividade."
                    icon={Users}
                    color="bg-pink-500"
                    loading={loadingReport === 'equipe'}
                    onOpen={() => openModal('equipe')}
                />

                <ReportCard 
                    title="Controle de Ponto" 
                    description="Frequência, atrasos, taxa de presença e horas trabalhadas por funcionário."
                    icon={Clock}
                    color="bg-indigo-600"
                    loading={loadingReport === 'ponto'}
                    onOpen={() => openModal('ponto')}
                />

                <ReportCard 
                    title="🧠 Análise RFM de Clientes" 
                    description="Segmentação inteligente: Campeões, Fiéis, Em Risco e Perdidos. Identifique clientes para campanhas."
                    icon={Brain}
                    color="bg-purple-600"
                    loading={loadingReport === 'rfm'}
                    onOpen={() => openModal('rfm')}
                />

                <ReportCard 
                    title="📊 Rentabilidade ABC" 
                    description="Classificação Pareto 80/20, produtos com margem negativa e baixo giro. CMP em tempo real."
                    icon={Target}
                    color="bg-rose-600"
                    loading={loadingReport === 'abc'}
                    onOpen={() => openModal('abc')}
                />

                <ReportCard 
                    title="⚡ Previsão de Esgotamento" 
                    description="Previsão baseada em média móvel de 7 dias. Produtos críticos e em atenção."
                    icon={Zap}
                    color="bg-orange-600"
                    loading={loadingReport === 'previsao'}
                    onOpen={() => openModal('previsao')}
                />

                <ReportCard 
                    title="💾 Backup Completo (Power BI)" 
                    description="Exportação otimizada com dicionário de dados, Excel multi-abas e JSON. Pronto para Power BI."
                    icon={Archive}
                    color="bg-teal-600"
                    loading={loadingBackup}
                    onOpen={handleBackupExport}
                />
            </div>
            
            {modalOpen && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-xl shadow-2xl w-full max-w-4xl max-h-[85vh] overflow-y-auto">
                        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex justify-between items-center">
                            <h2 className="text-xl font-bold text-gray-800">
                                {modalType === 'vendas' && 'Vendas Detalhadas'}
                                {modalType === 'produtos' && 'Estoque & Produtos'}
                                {modalType === 'financeiro' && 'Fluxo Financeiro'}
                                {modalType === 'equipe' && 'Performance da Equipe'}
                                {modalType === 'ponto' && 'Controle de Ponto'}
                                {modalType === 'rfm' && '🧠 Análise RFM de Clientes'}
                                {modalType === 'abc' && '📊 Rentabilidade ABC'}
                                {modalType === 'previsao' && '⚡ Previsão de Esgotamento'}
                            </h2>
                            <button onClick={closeModal} className="text-gray-500 hover:text-gray-700">
                                <X className="w-6 h-6" />
                            </button>
                        </div>
                        <div className="px-6 py-4">
                            <div className="flex flex-wrap items-center gap-2 mb-4">
                                {(modalType === 'vendas' || modalType === 'produtos' || modalType === 'financeiro' || modalType === 'equipe' || modalType === 'ponto') && (
                                    <>
                                        <button
                                            onClick={() => (
                                                modalType === 'vendas' ? handleVendasReport('pdf') : 
                                                modalType === 'produtos' ? handleProdutosReport('pdf') : 
                                                modalType === 'financeiro' ? handleFinanceiroReport('pdf') : 
                                                modalType === 'ponto' ? handlePontoReport('pdf') :
                                                handleEquipeReport('pdf')
                                            )}
                                            disabled={loadingReport !== null}
                                            className="inline-flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-red-50 text-gray-700 hover:text-red-700 transition-colors border border-gray-100 hover:border-red-200"
                                        >
                                            <FileText className="w-4 h-4" />
                                            <span className="text-xs font-medium">Exportar PDF</span>
                                        </button>
                                        <button
                                            onClick={() => (
                                                modalType === 'vendas' ? handleVendasReport('excel') : 
                                                modalType === 'produtos' ? handleProdutosReport('excel') : 
                                                modalType === 'financeiro' ? handleFinanceiroReport('excel') : 
                                                modalType === 'ponto' ? handlePontoReport('excel') :
                                                handleEquipeReport('excel')
                                            )}
                                            disabled={loadingReport !== null}
                                            className="inline-flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-green-50 text-gray-700 hover:text-green-700 transition-colors border border-gray-100 hover:border-green-200"
                                        >
                                            <FileSpreadsheet className="w-4 h-4" />
                                            <span className="text-xs font-medium">Exportar Excel</span>
                                        </button>
                                        <button
                                            onClick={() => (
                                                modalType === 'vendas' ? handleVendasReport('csv') : 
                                                modalType === 'produtos' ? handleProdutosReport('csv') : 
                                                modalType === 'financeiro' ? handleFinanceiroReport('csv') : 
                                                modalType === 'ponto' ? handlePontoReport('csv') :
                                                handleEquipeReport('csv')
                                            )}
                                            disabled={loadingReport !== null}
                                            className="inline-flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-blue-50 text-gray-700 hover:text-blue-700 transition-colors border border-gray-100 hover:border-blue-200"
                                        >
                                            <Download className="w-4 h-4" />
                                            <span className="text-xs font-medium">Exportar CSV</span>
                                        </button>
                                    </>
                                )}
                                {(modalType === 'rfm' || modalType === 'abc' || modalType === 'previsao') && (
                                    <>
                                        <button
                                            onClick={() => {
                                                const data = modalType === 'rfm' ? rfmData : modalType === 'abc' ? abcData : previsaoData;
                                                const filename = modalType === 'rfm' ? 'Analise_RFM' : modalType === 'abc' ? 'Rentabilidade_ABC' : 'Previsao_Esgotamento';
                                                exportToExcel(data, filename, 'Dados');
                                            }}
                                            className="inline-flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-green-50 text-gray-700 hover:text-green-700 transition-colors border border-gray-100 hover:border-green-200"
                                        >
                                            <FileSpreadsheet className="w-4 h-4" />
                                            <span className="text-xs font-medium">Exportar Excel</span>
                                        </button>
                                        <button
                                            onClick={() => {
                                                const data = modalType === 'rfm' ? rfmData : modalType === 'abc' ? abcData : previsaoData;
                                                const filename = modalType === 'rfm' ? 'Analise_RFM' : modalType === 'abc' ? 'Rentabilidade_ABC' : 'Previsao_Esgotamento';
                                                exportToCSV(data, filename);
                                            }}
                                            className="inline-flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-blue-50 text-gray-700 hover:text-blue-700 transition-colors border border-gray-100 hover:border-blue-200"
                                        >
                                            <Download className="w-4 h-4" />
                                            <span className="text-xs font-medium">Exportar CSV</span>
                                        </button>
                                    </>
                                )}
                                <div className="ml-auto flex items-center gap-2 px-3 py-2 border border-gray-200 rounded-lg">
                                    <Search className="w-4 h-4 text-gray-500" />
                                    <input
                                        type="text"
                                        value={searchQuery}
                                        onChange={(e) => setSearchQuery(e.target.value)}
                                        placeholder="Buscar..."
                                        className="bg-transparent text-sm focus:outline-none"
                                    />
                                </div>
                            </div>
                            <div className="rounded-lg border border-gray-100 max-h-[65vh] overflow-auto">
                                {modalType === 'vendas' && (
                                    <>
                                        <div className="mb-4 grid grid-cols-4 gap-4">
                                            <div className="bg-blue-50 rounded-lg p-4">
                                                <p className="text-xs text-blue-600 font-medium mb-1">Total de Vendas</p>
                                                <p className="text-2xl font-bold text-blue-900">{vendasData.length}</p>
                                            </div>
                                            <div className="bg-green-50 rounded-lg p-4">
                                                <p className="text-xs text-green-600 font-medium mb-1">Faturamento Total</p>
                                                <p className="text-2xl font-bold text-green-900">
                                                    {vendasData.reduce((sum, v) => sum + v['Total (R$)'], 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                                                </p>
                                            </div>
                                            <div className="bg-red-50 rounded-lg p-4">
                                                <p className="text-xs text-red-600 font-medium mb-1">Total Descontos</p>
                                                <p className="text-2xl font-bold text-red-900">
                                                    {vendasData.reduce((sum, v) => sum + v['Desconto (R$)'], 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                                                </p>
                                            </div>
                                            <div className="bg-purple-50 rounded-lg p-4">
                                                <p className="text-xs text-purple-600 font-medium mb-1">Ticket Médio</p>
                                                <p className="text-2xl font-bold text-purple-900">
                                                    {vendasData.length > 0 ? (vendasData.reduce((sum, v) => sum + v['Total (R$)'], 0) / vendasData.length).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' }) : 'R$ 0,00'}
                                                </p>
                                            </div>
                                        </div>
                                        <table className="min-w-full text-sm">
                                            <thead className="bg-gray-50 sticky top-0">
                                                <tr>
                                                    <th className="px-3 py-2 text-left font-medium text-gray-700">Código</th>
                                                    <th className="px-3 py-2 text-left font-medium text-gray-700">Data/Hora</th>
                                                    <th className="px-3 py-2 text-left font-medium text-gray-700">Cliente</th>
                                                    <th className="px-3 py-2 text-left font-medium text-gray-700">Funcionário</th>
                                                    <th className="px-3 py-2 text-right font-medium text-gray-700">Subtotal</th>
                                                    <th className="px-3 py-2 text-right font-medium text-gray-700">Desconto</th>
                                                    <th className="px-3 py-2 text-right font-medium text-gray-700">Total</th>
                                                    <th className="px-3 py-2 text-left font-medium text-gray-700">Forma Pgto</th>
                                                    <th className="px-3 py-2 text-center font-medium text-gray-700">Itens</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {vendasData.filter(filterRow).map((item, idx) => (
                                                    <tr key={idx} className="border-t hover:bg-gray-50 transition-colors">
                                                        <td className="px-3 py-2 font-mono text-xs text-blue-600">{item['Código']}</td>
                                                        <td className="px-3 py-2 text-xs whitespace-nowrap">{item['Data/Hora']}</td>
                                                        <td className="px-3 py-2 text-xs">{item['Cliente']}</td>
                                                        <td className="px-3 py-2 text-xs">{item['Funcionário']}</td>
                                                        <td className="px-3 py-2 text-right text-xs text-gray-600">
                                                            {item['Subtotal (R$)'].toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                                                        </td>
                                                        <td className="px-3 py-2 text-right text-xs font-semibold text-red-600">
                                                            {item['Desconto (R$)'].toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                                                        </td>
                                                        <td className="px-3 py-2 text-right text-xs font-bold text-green-600">
                                                            {item['Total (R$)'].toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                                                        </td>
                                                        <td className="px-3 py-2 text-xs">
                                                            <span className="inline-block px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs">
                                                                {item['Forma Pagamento']}
                                                            </span>
                                                        </td>
                                                        <td className="px-3 py-2 text-center text-xs">
                                                            <span className="inline-block px-2 py-1 bg-gray-100 text-gray-700 rounded-full font-medium">
                                                                {item['Qtd Itens']}
                                                            </span>
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                        {vendasData.filter(filterRow).length === 0 && (
                                            <div className="text-center py-12 text-gray-500">
                                                <p className="text-lg">Nenhuma venda encontrada</p>
                                                <p className="text-sm mt-2">Ajuste os filtros de data ou busca</p>
                                            </div>
                                        )}
                                    </>
                                )}
                                {modalType === 'produtos' && (
                                    <table className="min-w-full text-sm">
                                        <thead className="bg-gray-50 sticky top-0">
                                            <tr>
                                                <th className="px-4 py-2 text-left font-medium text-gray-700">Nome</th>
                                                <th className="px-4 py-2 text-left font-medium text-gray-700">Categoria</th>
                                                <th className="px-4 py-2 text-left font-medium text-gray-700">Preço</th>
                                                <th className="px-4 py-2 text-left font-medium text-gray-700">Estoque</th>
                                                <th className="px-4 py-2 text-left font-medium text-gray-700">Status</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {produtosData.filter(filterRow).map((item, idx) => (
                                                <tr key={idx} className="border-t">
                                                    <td className="px-4 py-2">{item['Nome']}</td>
                                                    <td className="px-4 py-2">{item['Categoria']}</td>
                                                    <td className="px-4 py-2">{item['Preço Venda'].toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}</td>
                                                    <td className="px-4 py-2">{String(item['Estoque'] ?? '')}</td>
                                                    <td className={`px-4 py-2 ${item['Status'] === 'CRÍTICO' ? 'text-red-600 font-semibold' : 'text-emerald-600'}`}>{item['Status']}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                )}
                                {modalType === 'financeiro' && (
                                    <table className="min-w-full text-sm">
                                        <thead className="bg-gray-50 sticky top-0">
                                            <tr>
                                                <th className="px-4 py-2 text-left font-medium text-gray-700">Forma Pagamento</th>
                                                <th className="px-4 py-2 text-left font-medium text-gray-700">Transações</th>
                                                <th className="px-4 py-2 text-left font-medium text-gray-700">Total</th>
                                                <th className="px-4 py-2 text-left font-medium text-gray-700">%</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {financeiroData.filter(filterRow).map((item, idx) => (
                                                <tr key={idx} className="border-t">
                                                    <td className="px-4 py-2">{item['Forma de Pagamento']}</td>
                                                    <td className="px-4 py-2">{item['Qtd. Transações']}</td>
                                                    <td className="px-4 py-2">{item['Total (R$)'].toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}</td>
                                                    <td className="px-4 py-2">{item['Percentual (%)']}%</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                )}
                                {modalType === 'equipe' && (
                                    <table className="min-w-full text-sm">
                                        <thead className="bg-gray-50 sticky top-0">
                                            <tr>
                                                <th className="px-4 py-2 text-left font-medium text-gray-700">Nome</th>
                                                <th className="px-4 py-2 text-left font-medium text-gray-700">Vendas</th>
                                                <th className="px-4 py-2 text-left font-medium text-gray-700">Total</th>
                                                <th className="px-4 py-2 text-left font-medium text-gray-700">Ticket Médio</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {equipeData.filter(filterRow).map((item, idx) => (
                                                <tr key={idx} className="border-t">
                                                    <td className="px-4 py-2">{item['Funcionário']}</td>
                                                    <td className="px-4 py-2">{item['Vendas Realizadas']}</td>
                                                    <td className="px-4 py-2">{item['Total Vendido (R$)'].toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}</td>
                                                    <td className="px-4 py-2">{parseFloat(item['Ticket Médio (R$)']).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                )}
                                {modalType === 'ponto' && (
                                    <table className="min-w-full text-sm">
                                        <thead className="bg-gray-50 sticky top-0">
                                            <tr>
                                                <th className="px-4 py-2 text-left font-medium text-gray-700">Funcionário</th>
                                                <th className="px-4 py-2 text-left font-medium text-gray-700">Dias Trabalhados</th>
                                                <th className="px-4 py-2 text-left font-medium text-gray-700">Presença %</th>
                                                <th className="px-4 py-2 text-left font-medium text-gray-700">Atrasos</th>
                                                <th className="px-4 py-2 text-left font-medium text-gray-700">Min. Atraso</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {pontoData.filter(filterRow).map((item, idx) => (
                                                <tr key={idx} className="border-t">
                                                    <td className="px-4 py-2 font-medium">{item['Funcionário']}</td>
                                                    <td className="px-4 py-2">{item['Dias Trabalhados']}</td>
                                                    <td className="px-4 py-2">
                                                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                                                            parseFloat(item['Taxa Presença (%)']) >= 95 ? 'bg-green-100 text-green-800' :
                                                            parseFloat(item['Taxa Presença (%)']) >= 85 ? 'bg-yellow-100 text-yellow-800' :
                                                            'bg-red-100 text-red-800'
                                                        }`}>
                                                            {item['Taxa Presença (%)']}%
                                                        </span>
                                                    </td>
                                                    <td className="px-4 py-2">
                                                        <span className={`font-semibold ${
                                                            item['Total Atrasos'] > 5 ? 'text-red-600' :
                                                            item['Total Atrasos'] > 2 ? 'text-amber-600' :
                                                            'text-green-600'
                                                        }`}>
                                                            {item['Total Atrasos']}
                                                        </span>
                                                    </td>
                                                    <td className="px-4 py-2 text-gray-600">{item['Minutos Atraso']} min</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                )}
                                {modalType === 'rfm' && (
                                    <table className="min-w-full text-sm">
                                        <thead className="bg-gray-50 sticky top-0">
                                            <tr>
                                                <th className="px-4 py-2 text-left font-medium text-gray-700">Cliente</th>
                                                <th className="px-4 py-2 text-left font-medium text-gray-700">Segmento</th>
                                                <th className="px-4 py-2 text-left font-medium text-gray-700">Recência</th>
                                                <th className="px-4 py-2 text-left font-medium text-gray-700">Frequência</th>
                                                <th className="px-4 py-2 text-left font-medium text-gray-700">Valor Total</th>
                                                <th className="px-4 py-2 text-left font-medium text-gray-700">Score</th>
                                                <th className="px-4 py-2 text-left font-medium text-gray-700">Status</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {rfmData.filter(filterRow).map((item, idx) => (
                                                <tr key={idx} className="border-t">
                                                    <td className="px-4 py-2 font-medium">{item['Nome']}</td>
                                                    <td className="px-4 py-2">
                                                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                                                            item['Segmento'] === 'Campeão' ? 'bg-purple-100 text-purple-800' :
                                                            item['Segmento'] === 'Fiel' ? 'bg-blue-100 text-blue-800' :
                                                            item['Segmento'] === 'Em Risco' ? 'bg-orange-100 text-orange-800' :
                                                            item['Segmento'] === 'Perdido' ? 'bg-red-100 text-red-800' :
                                                            'bg-gray-100 text-gray-800'
                                                        }`}>
                                                            {item['Segmento']}
                                                        </span>
                                                    </td>
                                                    <td className="px-4 py-2">{item['Recência (dias)']} dias</td>
                                                    <td className="px-4 py-2">{item['Frequência']} compras</td>
                                                    <td className="px-4 py-2 font-semibold text-green-600">{item['Valor Total (R$)'].toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}</td>
                                                    <td className="px-4 py-2 font-mono text-xs">{item['Score RFM']}</td>
                                                    <td className="px-4 py-2">
                                                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                                                            item['Em Risco'] === 'SIM' ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'
                                                        }`}>
                                                            {item['Em Risco'] === 'SIM' ? '⚠️ Em Risco' : '✅ OK'}
                                                        </span>
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                )}
                                {modalType === 'abc' && (
                                    <table className="min-w-full text-sm">
                                        <thead className="bg-gray-50 sticky top-0">
                                            <tr>
                                                <th className="px-4 py-2 text-left font-medium text-gray-700">Produto</th>
                                                <th className="px-4 py-2 text-left font-medium text-gray-700">Classe</th>
                                                <th className="px-4 py-2 text-left font-medium text-gray-700">Qtd Vendida</th>
                                                <th className="px-4 py-2 text-left font-medium text-gray-700">Faturamento</th>
                                                <th className="px-4 py-2 text-left font-medium text-gray-700">Lucro Real</th>
                                                <th className="px-4 py-2 text-left font-medium text-gray-700">Margem %</th>
                                                <th className="px-4 py-2 text-left font-medium text-gray-700">% Fat.</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {abcData.filter(filterRow).map((item, idx) => (
                                                <tr key={idx} className="border-t">
                                                    <td className="px-4 py-2 font-medium">{item['Produto']}</td>
                                                    <td className="px-4 py-2">
                                                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-bold ${
                                                            item['Classe ABC'] === 'A' ? 'bg-green-100 text-green-800' :
                                                            item['Classe ABC'] === 'B' ? 'bg-yellow-100 text-yellow-800' :
                                                            'bg-red-100 text-red-800'
                                                        }`}>
                                                            {item['Classe ABC']}
                                                        </span>
                                                    </td>
                                                    <td className="px-4 py-2">{item['Quantidade Vendida']}</td>
                                                    <td className="px-4 py-2 font-semibold">{item['Faturamento (R$)'].toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}</td>
                                                    <td className="px-4 py-2 text-green-600 font-semibold">{item['Lucro Real (R$)'].toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}</td>
                                                    <td className="px-4 py-2">
                                                        <span className={`font-semibold ${
                                                            parseFloat(item['Margem Real (%)']) < 0 ? 'text-red-600' :
                                                            parseFloat(item['Margem Real (%)']) < 20 ? 'text-orange-600' :
                                                            'text-green-600'
                                                        }`}>
                                                            {item['Margem Real (%)']}%
                                                        </span>
                                                    </td>
                                                    <td className="px-4 py-2 text-gray-600">{item['% Faturamento']}%</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                )}
                                {modalType === 'previsao' && (
                                    <table className="min-w-full text-sm">
                                        <thead className="bg-gray-50 sticky top-0">
                                            <tr>
                                                <th className="px-4 py-2 text-left font-medium text-gray-700">Produto</th>
                                                <th className="px-4 py-2 text-left font-medium text-gray-700">Estoque</th>
                                                <th className="px-4 py-2 text-left font-medium text-gray-700">Média/Dia</th>
                                                <th className="px-4 py-2 text-left font-medium text-gray-700">Dias Restantes</th>
                                                <th className="px-4 py-2 text-left font-medium text-gray-700">Data Prevista</th>
                                                <th className="px-4 py-2 text-left font-medium text-gray-700">Status</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {previsaoData.filter(filterRow).map((item, idx) => (
                                                <tr key={idx} className="border-t">
                                                    <td className="px-4 py-2 font-medium">{item['Produto']}</td>
                                                    <td className="px-4 py-2">{item['Estoque Atual']} un</td>
                                                    <td className="px-4 py-2">{item['Média Vendas/Dia']}</td>
                                                    <td className="px-4 py-2 font-semibold">{item['Dias até Esgotamento']}</td>
                                                    <td className="px-4 py-2 text-gray-600">{item['Data Prevista']}</td>
                                                    <td className="px-4 py-2">
                                                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                                                            item['Status'] === 'CRÍTICO' ? 'bg-red-100 text-red-800 animate-pulse' :
                                                            item['Status'] === 'ATENÇÃO' ? 'bg-orange-100 text-orange-800' :
                                                            item['Status'] === 'ESGOTADO' ? 'bg-gray-100 text-gray-800' :
                                                            'bg-green-100 text-green-800'
                                                        }`}>
                                                            {item['Status']}
                                                        </span>
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            )}

            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
                <div className="flex items-start justify-between mb-4">
                    <div className="p-3 rounded-lg bg-slate-500">
                        <Archive className="w-6 h-6 text-white" />
                    </div>
                    {loadingBackup && <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />}
                </div>
                <h3 className="text-lg font-bold text-gray-900 mb-2">Backup Local</h3>
                <p className="text-sm text-gray-500 mb-6">Exporta dados essenciais (Produtos, Clientes, Vendas) em um arquivo ZIP para segurança e uso offline.</p>
                <button onClick={handleBackupExport} disabled={loadingBackup} className="inline-flex items-center gap-2 px-4 py-2 bg-gray-800 text-white rounded-lg hover:bg-gray-900 transition-colors">
                    <Download className="w-4 h-4" />
                    <span>Baixar Backup</span>
                </button>
            </div>

            {/* Dica Pro */}
            <div className="bg-gradient-to-r from-indigo-50 to-blue-50 border border-indigo-100 rounded-xl p-6 flex items-start gap-4">
                <div className="p-2 bg-white rounded-full shadow-sm">
                    <span className="text-xl">💡</span>
                </div>
                <div>
                    <h4 className="font-bold text-indigo-900">Dica do Especialista</h4>
                    <p className="text-indigo-700 text-sm mt-1">
                        Utilize o relatório de <strong>Estoque & Produtos</strong> semanalmente para identificar itens com baixo giro e planejar promoções. 
                        O relatório de <strong>Performance Equipe</strong> é ideal para reuniões mensais de feedback.
                    </p>
                </div>
            </div>
        </div>
    );
};

export default ReportsPage;
