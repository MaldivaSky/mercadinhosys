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
    Clock
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
    const [modalType, setModalType] = useState<'vendas' | 'produtos' | 'financeiro' | 'equipe' | 'ponto' | null>(null);
    const [modalOpen, setModalOpen] = useState(false);
    const [vendasData, setVendasData] = useState<Array<{Data: string; 'Quantidade Vendas': number; 'Total (R$)': number}>>([]);
    const [produtosData, setProdutosData] = useState<Array<{ 'Código': string | number; 'Nome': string; 'Categoria': string; 'Preço Venda': number; 'Preço Custo': number; 'Estoque': any; 'Estoque Mínimo': number; 'Status': string }>>([]);
    const [financeiroData, setFinanceiroData] = useState<Array<{ 'Forma de Pagamento': string; 'Qtd. Transações': number; 'Total (R$)': number; 'Percentual (%)': string }>>([]);
    const [equipeData, setEquipeData] = useState<Array<{ 'Funcionário': string; 'Vendas Realizadas': number; 'Total Vendido (R$)': number; 'Ticket Médio (R$)': string }>>([]);
    const [pontoData, setPontoData] = useState<Array<{ 'Funcionário': string; 'Dias Trabalhados': number; 'Taxa Presença (%)': string; 'Total Atrasos': number; 'Minutos Atraso': number }>>([]);
    const [searchQuery, setSearchQuery] = useState<string>('');
    const filterRow = (row: any) => {
        const q = searchQuery.trim().toLowerCase();
        if (!q) return true;
        return Object.values(row).some((v) => String(v ?? '').toLowerCase().includes(q));
    };
    
    const openModal = async (type: 'vendas' | 'produtos' | 'financeiro' | 'equipe' | 'ponto') => {
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
            } else if (type === 'ponto' && pontoData.length === 0) {
                await fetchPontoData();
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
            const analytics = await salesService.getAnalytics({
                data_inicio: dateRange.startDate,
                data_fim: dateRange.endDate
            });
            const data = analytics.vendasPorDia.map(d => ({
                Data: format(new Date(d.data), 'dd/MM/yyyy'),
                'Quantidade Vendas': d.quantidade,
                'Total (R$)': d.total
            }));
            setVendasData(data);
        } catch (error) {
            console.error(error);
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

            const filename = `Relatorio_Vendas_${dateRange.startDate}_${dateRange.endDate}`;

            if (type === 'csv') exportToCSV(dataToExport, filename);
            else if (type === 'excel') exportToExcel(dataToExport, filename, 'Vendas Diárias');
            else {
                const doc = new jsPDF();
                generatePDFHeader(doc, "Relatório de Vendas Diárias", `${format(new Date(dateRange.startDate), 'dd/MM/yyyy')} a ${format(new Date(dateRange.endDate), 'dd/MM/yyyy')}`);
                
                autoTable(doc, {
                    startY: 50,
                    head: [['Data', 'Qtd. Vendas', 'Total (R$)']],
                    body: dataToExport.map(item => [item.Data, item['Quantidade Vendas'], item['Total (R$)'].toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })]),
                    theme: 'grid',
                    headStyles: { fillColor: [63, 81, 181] },
                });

                // Adicionar sumário
                const totalPeriodo = dataToExport.reduce((acc, curr) => acc + curr['Total (R$)'], 0);
                const finalY = (doc as any).lastAutoTable.finalY || 50;
                doc.setFontSize(12);
                doc.setTextColor(0, 0, 0);
                doc.text(`Total do Período: ${totalPeriodo.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}`, 14, finalY + 10);

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
                            </h2>
                            <button onClick={closeModal} className="text-gray-500 hover:text-gray-700">
                                <X className="w-6 h-6" />
                            </button>
                        </div>
                        <div className="px-6 py-4">
                            <div className="flex flex-wrap items-center gap-2 mb-4">
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
                                    <table className="min-w-full text-sm">
                                        <thead className="bg-gray-50 sticky top-0">
                                            <tr>
                                                <th className="px-4 py-2 text-left font-medium text-gray-700">Data</th>
                                                <th className="px-4 py-2 text-left font-medium text-gray-700">Qtd. Vendas</th>
                                                <th className="px-4 py-2 text-left font-medium text-gray-700">Total (R$)</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {vendasData.filter(filterRow).map((item, idx) => (
                                                <tr key={idx} className="border-t">
                                                    <td className="px-4 py-2">{item.Data}</td>
                                                    <td className="px-4 py-2">{item['Quantidade Vendas']}</td>
                                                    <td className="px-4 py-2">{item['Total (R$)'].toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
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
