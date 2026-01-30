import React, { useState } from 'react';
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
    Loader2
} from 'lucide-react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import * as XLSX from 'xlsx';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
import { toast } from 'react-hot-toast';
import { salesService } from '../sales/salesService';
import { productsService } from '../products/productsService';

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
    onExport: (type: 'pdf' | 'excel' | 'csv') => void;
}

const ReportCard: React.FC<ReportCardProps> = ({ 
    title, 
    description, 
    icon: Icon, 
    color, 
    loading, 
    onExport 
}) => (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 hover:shadow-md transition-all duration-200 group">
        <div className="flex items-start justify-between mb-4">
            <div className={`p-3 rounded-lg ${color} group-hover:scale-110 transition-transform duration-200`}>
                <Icon className="w-6 h-6 text-white" />
            </div>
            {loading && <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />}
        </div>
        
        <h3 className="text-lg font-bold text-gray-900 mb-2">{title}</h3>
        <p className="text-sm text-gray-500 mb-6 min-h-[40px]">{description}</p>
        
        <div className="grid grid-cols-3 gap-2">
            <button
                onClick={() => onExport('pdf')}
                disabled={loading}
                className="flex flex-col items-center justify-center p-2 rounded-lg hover:bg-red-50 text-gray-600 hover:text-red-600 transition-colors border border-gray-100 hover:border-red-200"
                title="Exportar PDF"
            >
                <FileText className="w-5 h-5 mb-1" />
                <span className="text-xs font-medium">PDF</span>
            </button>
            <button
                onClick={() => onExport('excel')}
                disabled={loading}
                className="flex flex-col items-center justify-center p-2 rounded-lg hover:bg-green-50 text-gray-600 hover:text-green-600 transition-colors border border-gray-100 hover:border-green-200"
                title="Exportar Excel"
            >
                <FileSpreadsheet className="w-5 h-5 mb-1" />
                <span className="text-xs font-medium">Excel</span>
            </button>
            <button
                onClick={() => onExport('csv')}
                disabled={loading}
                className="flex flex-col items-center justify-center p-2 rounded-lg hover:bg-blue-50 text-gray-600 hover:text-blue-600 transition-colors border border-gray-100 hover:border-blue-200"
                title="Exportar CSV"
            >
                <Download className="w-5 h-5 mb-1" />
                <span className="text-xs font-medium">CSV</span>
            </button>
        </div>
    </div>
);

const ReportsPage: React.FC = () => {
    // Estado para datas (padrão: últimos 30 dias)
    const [dateRange, setDateRange] = useState<DateRange>({
        startDate: new Date(new Date().setDate(new Date().getDate() - 30)).toISOString().split('T')[0],
        endDate: new Date().toISOString().split('T')[0]
    });

    const [loadingReport, setLoadingReport] = useState<string | null>(null);

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

    const handleVendasReport = async (type: 'pdf' | 'excel' | 'csv') => {
        setLoadingReport('vendas');
        try {
            // Buscar dados brutos (simulando fetch de todos, na prática deveria ter endpoint específico)
            // Aqui vamos usar a rota de analytics que já traz agregados interessantes, 
            // mas idealmente buscaríamos uma lista de vendas filtrada
            
            // Para este exemplo, vamos buscar estatísticas que já temos acesso fácil
            const analytics = await salesService.getAnalytics({
                data_inicio: dateRange.startDate,
                data_fim: dateRange.endDate
            });

            const dataToExport = analytics.vendasPorDia.map(d => ({
                Data: format(new Date(d.data), 'dd/MM/yyyy'),
                'Quantidade Vendas': d.quantidade,
                'Total (R$)': d.total
            }));

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

    const handleProdutosReport = async (type: 'pdf' | 'excel' | 'csv') => {
        setLoadingReport('produtos');
        try {
            // Buscar produtos (estoque)
            const response = await productsService.getAllEstoque(1, 1000); // Tentar pegar o máximo
            const produtos = response.produtos;

            const dataToExport = produtos.map(p => ({
                'Código': p.codigo_barras || p.id,
                'Nome': p.nome,
                'Categoria': p.categoria || 'N/A',
                'Preço Venda': p.preco_venda,
                'Preço Custo': p.preco_custo,
                'Estoque': p.estoque_status,
                'Estoque Mínimo': p.estoque_minimo,
                'Status': (p.quantidade || 0) <= (p.estoque_minimo || 0) ? 'CRÍTICO' : 'OK'
            }));

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

    const handleFinanceiroReport = async (type: 'pdf' | 'excel' | 'csv') => {
        setLoadingReport('financeiro');
        try {
            const analytics = await salesService.getAnalytics({
                data_inicio: dateRange.startDate,
                data_fim: dateRange.endDate
            });

            const dataToExport = analytics.formasPagamento.map(f => ({
                'Forma de Pagamento': f.forma.toUpperCase(),
                'Qtd. Transações': f.quantidade,
                'Total (R$)': f.total,
                'Percentual (%)': f.percentual.toFixed(2)
            }));

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

    const handleEquipeReport = async (type: 'pdf' | 'excel' | 'csv') => {
        setLoadingReport('equipe');
        try {
            // Usando analytics de vendas por funcionário
            const analytics = await salesService.getAnalytics({
                data_inicio: dateRange.startDate,
                data_fim: dateRange.endDate
            });

            const dataToExport = analytics.topFuncionarios.map(f => ({
                'Funcionário': f.funcionario,
                'Vendas Realizadas': f.quantidade,
                'Total Vendido (R$)': f.total,
                'Ticket Médio (R$)': (f.total / f.quantidade).toFixed(2)
            }));

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
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <ReportCard 
                    title="Vendas Detalhadas" 
                    description="Análise cronológica de vendas, totais diários e volume de transações."
                    icon={TrendingUp}
                    color="bg-blue-500"
                    loading={loadingReport === 'vendas'}
                    onExport={handleVendasReport}
                />

                <ReportCard 
                    title="Estoque & Produtos" 
                    description="Inventário completo, níveis de estoque, custos e margens de produtos."
                    icon={Package}
                    color="bg-emerald-500"
                    loading={loadingReport === 'produtos'}
                    onExport={handleProdutosReport}
                />

                <ReportCard 
                    title="Fluxo Financeiro" 
                    description="Detalhamento por formas de pagamento, entradas e projeções."
                    icon={Wallet}
                    color="bg-amber-500"
                    loading={loadingReport === 'financeiro'}
                    onExport={handleFinanceiroReport}
                />

                <ReportCard 
                    title="Performance Equipe" 
                    description="Ranking de vendedores, comissões, ticket médio e produtividade."
                    icon={Users}
                    color="bg-pink-500"
                    loading={loadingReport === 'equipe'}
                    onExport={handleEquipeReport}
                />
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