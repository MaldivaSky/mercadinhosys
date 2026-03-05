import { useState, useEffect } from 'react';
import { Download, Printer, Clock } from 'lucide-react';
import ResponsiveModal from '../../../components/ui/ResponsiveModal';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
import { formatCurrency, formatDate } from '../../../utils/formatters';
import { apiClient } from '../../../api/apiClient';
import { Funcionario } from '../../../types';

interface HoleriteModalProps {
    isOpen: boolean;
    onClose: () => void;
    funcionario: Funcionario;
    periodo: string;
}

interface Estabelecimento {
    razao_social: string;
    cnpj: string;
    logradouro: string;
    numero: string;
    bairro: string;
    cidade: string;
    estado: string;
    complemento?: string;
    inscricao_estadual?: string;
}

const HoleriteModal = ({ isOpen, onClose, funcionario, periodo }: HoleriteModalProps) => {
    const [estabelecimento, setEstabelecimento] = useState<Estabelecimento | null>(null);

    useEffect(() => {
        if (isOpen) {
            const loadEstabelecimento = async () => {
                try {
                    const res = await apiClient.get('/configuracao/estabelecimento');
                    setEstabelecimento(res.data.estabelecimento);
                } catch (error) {
                    console.error('Erro ao carregar dados da empresa:', error);
                }
            };
            loadEstabelecimento();
        }
    }, [isOpen]);

    const calcularHolerite = (func: Funcionario) => {
        const salarioBase = Number(func.salario_base || 0);
        const valorHora = salarioBase / 220;

        // Ganhos
        const totalHorasExtras = Number(func.horas_extras_horas || 0) * (valorHora * 1.5);

        // Atrasos (Desconto)
        const totalAtrasos = Number(func.atrasos_horas || 0) * valorHora;

        // Benefícios Detalhados
        const listaBeneficios = func.beneficios_detalhes || [];

        // Impostos (Simulação Básica)
        const inss = salarioBase * 0.09;
        const irrf = salarioBase > 5000 ? (salarioBase * 0.15) : 0;

        const vencimentos = [
            { descricao: 'Salário Base', referencia: '30 dias', valor: salarioBase }
        ];

        if (totalHorasExtras > 0) {
            vencimentos.push({ descricao: 'Horas Extras (50%)', referencia: `${func.horas_extras_horas}h`, valor: totalHorasExtras });
        }

        listaBeneficios.forEach(b => {
            // Assuming all are positive benefits; if a benefit must be a discount, adjust accordingly
            vencimentos.push({ descricao: b.descricao, referencia: 'Benefício', valor: b.valor });
        });

        const descontos = [
            { descricao: 'INSS', referencia: '9.00%', valor: inss }
        ];

        if (irrf > 0) {
            descontos.push({ descricao: 'IRRF', referencia: '15.00%', valor: irrf });
        }

        if (totalAtrasos > 0) {
            descontos.push({ descricao: 'Atrasos / Faltas', referencia: `${func.atrasos_horas}h`, valor: totalAtrasos });
        }

        const totalVencimentos = vencimentos.reduce((acc, item) => acc + item.valor, 0);
        const totalDescontos = descontos.reduce((acc, item) => acc + item.valor, 0);
        const salarioLiquido = totalVencimentos - totalDescontos;

        return {
            vencimentos,
            descontos,
            totais: {
                bruto: totalVencimentos,
                descontos: totalDescontos,
                liquido: salarioLiquido
            }
        };
    };

    const dados = calcularHolerite(funcionario);

    const handlePrint = () => {
        window.print();
    };

    const handleDownloadPDF = () => {
        const doc = new jsPDF();

        // --- CÁLCULO DE POSIÇÕES E ESTILOS ---
        const MARGIN_X = 20;
        let currentY = 20;

        // --- CABEÇALHO DO DOCUMENTO ---
        doc.setFillColor(31, 41, 55); // Gray-800
        doc.rect(0, 0, 210, 45, 'F');

        doc.setTextColor(255, 255, 255);
        doc.setFontSize(24);
        doc.setFont('helvetica', 'bold');
        doc.text('RECIBO DE PAGAMENTO', 105, 25, { align: 'center' });

        doc.setFontSize(11);
        doc.setFont('helvetica', 'normal');
        doc.text(`DEMONSTRATIVO MENSAL DE SALÁRIO • REFERÊNCIA: ${periodo}`, 105, 35, { align: 'center' });

        currentY = 60;

        // --- DADOS DA EMPRESA ---
        doc.setTextColor(17, 24, 39); // Gray-900
        doc.setFontSize(14);
        doc.setFont('helvetica', 'bold');
        doc.text(estabelecimento?.razao_social || 'MERCADINHO SYS - SOLUTIONS ERP', MARGIN_X, currentY);

        doc.setFontSize(10);
        doc.setFont('helvetica', 'normal');
        doc.setTextColor(75, 85, 99); // Gray-600
        doc.text(`CNPJ: ${estabelecimento?.cnpj || '00.000.000/0001-00'}`, MARGIN_X, currentY + 7);
        const enderecoCompleto = `${estabelecimento?.logradouro || 'Endereço não informado'}, ${estabelecimento?.numero || 'S/N'} - ${estabelecimento?.cidade || ''}/${estabelecimento?.estado || ''}`;
        doc.text(enderecoCompleto, MARGIN_X, currentY + 12);

        // --- LINHA DIVISORA ---
        doc.setDrawColor(209, 213, 219); // Gray-300
        doc.setLineWidth(0.5);
        doc.line(MARGIN_X, currentY + 20, 190, currentY + 20);

        currentY += 30;

        // --- DADOS DO FUNCIONÁRIO ---
        doc.setTextColor(17, 24, 39);
        doc.setFontSize(11);
        doc.setFont('helvetica', 'bold');
        doc.text('IDENTIFICAÇÃO DO COLABORADOR', MARGIN_X, currentY);

        doc.setFontSize(10);
        doc.setFont('helvetica', 'normal');
        doc.setTextColor(55, 65, 81); // Gray-700
        doc.text(`NOME: ${funcionario.nome.toUpperCase()}`, MARGIN_X, currentY + 8);
        doc.text(`CPF: ${funcionario.cpf || '---'}`, MARGIN_X, currentY + 14);

        doc.text(`CARGO: ${funcionario.cargo.toUpperCase()}`, 110, currentY + 8);
        doc.text(`DATA ADMISSÃO: ${formatDate(funcionario.data_admissao)}`, 110, currentY + 14);

        currentY += 25;

        // --- TABELA DE LANÇAMENTOS ---
        const tableBody = [
            ...dados.vencimentos.map(item => [item.descricao, item.referencia, formatCurrency(item.valor), '']),
            ...dados.descontos.map(item => [item.descricao, item.referencia, '', formatCurrency(item.valor)])
        ];

        autoTable(doc, {
            startY: currentY,
            head: [['DESCRIÇÃO DO EVENTO', 'REF', 'VENCIMENTOS', 'DESCONTOS']],
            body: tableBody,
            theme: 'grid',
            headStyles: {
                fillColor: [31, 41, 55],
                textColor: [255, 255, 255],
                fontStyle: 'bold',
                halign: 'center',
                fontSize: 9
            },
            styles: {
                fontSize: 9,
                cellPadding: 5,
                textColor: [31, 41, 55],
                lineColor: [209, 213, 219]
            },
            columnStyles: {
                0: { cellWidth: 80 },
                1: { halign: 'center', cellWidth: 30 },
                2: { halign: 'right', cellWidth: 30 },
                3: { halign: 'right', cellWidth: 30 }
            }
        });

        const finalTableY = (doc as any).lastAutoTable.finalY + 10;

        // --- QUADRO DE TOTAIS ---
        doc.setFillColor(249, 250, 251); // Gray-50
        doc.rect(110, finalTableY, 80, 40, 'F');
        doc.setDrawColor(31, 41, 55);
        doc.setLineWidth(0.8);
        doc.rect(110, finalTableY, 80, 40, 'D');

        doc.setFontSize(10);
        doc.setFont('helvetica', 'bold');
        doc.setTextColor(31, 41, 55);
        doc.text('TOTAL VENCIMENTOS:', 115, finalTableY + 10);
        doc.text(formatCurrency(dados.totais.bruto), 185, finalTableY + 10, { align: 'right' });

        doc.text('TOTAL DESCONTOS:', 115, finalTableY + 18);
        doc.setTextColor(220, 38, 38); // Red-600
        doc.text(formatCurrency(dados.totais.descontos), 185, finalTableY + 18, { align: 'right' });

        doc.line(115, finalTableY + 23, 185, finalTableY + 23);

        doc.setFontSize(13);
        doc.setTextColor(17, 24, 39);
        doc.text('VALOR LÍQUIDO:', 115, finalTableY + 32);
        doc.text(formatCurrency(dados.totais.liquido), 185, finalTableY + 32, { align: 'right' });

        // --- RODAPÉ ---
        doc.setFontSize(8);
        doc.setFont('helvetica', 'italic');
        doc.setTextColor(156, 163, 175);
        doc.text('ESTE DOCUMENTO É UMA REPRESENTAÇÃO DIGITAL DO CONTRACHEQUE DO COLABORADOR.', 105, 275, { align: 'center' });
        doc.text(`GERADO POR MERCADINHOSYS ERP EM ${new Date().toLocaleDateString('pt-BR')} AS ${new Date().toLocaleTimeString('pt-BR')}`, 105, 280, { align: 'center' });

        doc.save(`Holerite_${funcionario.nome.split(' ')[0]}_${periodo.replace('/', '-')}.pdf`);
    };

    return (
        <ResponsiveModal
            isOpen={isOpen}
            onClose={onClose}
            title="Demonstrativo de Pagamento"
            subtitle={`Referência: ${periodo}`}
            headerIcon={<Clock className="w-6 h-6" />}
            headerColor="indigo"
            size="xl"
            footer={
                <div className="flex w-full gap-3 sm:justify-end">
                    <button
                        onClick={handlePrint}
                        className="flex-1 sm:flex-none flex items-center justify-center gap-2 px-6 py-3 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-100 border-2 border-gray-200 dark:border-gray-700 rounded-xl font-bold hover:bg-gray-50 dark:hover:bg-gray-700 transition-all shadow-sm"
                    >
                        <Printer className="w-5 h-5" />
                        Imprimir
                    </button>
                    <button
                        onClick={handleDownloadPDF}
                        className="flex-1 sm:flex-none flex items-center justify-center gap-2 px-6 py-3 bg-gray-900 dark:bg-indigo-600 text-white rounded-xl font-bold hover:bg-black dark:hover:bg-indigo-700 shadow-xl transition-all"
                    >
                        <Download className="w-5 h-5" />
                        Download PDF
                    </button>
                </div>
            }
        >
            <div className="space-y-6 p-2 max-w-4xl mx-auto dark:text-gray-100">
                {/* Branding Premium Topo */}
                <div className="flex flex-col sm:flex-row sm:items-end justify-between border-b-2 border-gray-200 dark:border-gray-800 pb-5 gap-4">
                    <div className="flex items-center gap-4">
                        <div className="w-16 h-16 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl flex items-center justify-center font-black text-3xl text-white shadow-lg shadow-indigo-500/30">
                            MS
                        </div>
                        <div>
                            <h2 className="text-3xl font-black text-gray-900 dark:text-white leading-none tracking-tight">MercadinhoSys</h2>
                            <p className="text-xs text-indigo-600 dark:text-indigo-400 font-bold uppercase tracking-widest mt-1">Intelligent ERP • Payroll</p>
                        </div>
                    </div>
                    <div className="sm:text-right">
                        <p className="text-xs text-gray-500 dark:text-gray-400 font-bold uppercase mb-1 tracking-widest">Contracheque Mensal</p>
                        <p className="text-2xl font-black text-gray-900 dark:text-white leading-none">{periodo}</p>
                    </div>
                </div>

                {/* Grid de Dados Principais */}
                <div className="grid grid-cols-1 md:grid-cols-12 gap-px bg-gray-200 dark:bg-gray-800 rounded-2xl overflow-hidden border border-gray-200 dark:border-gray-800 shadow-sm">
                    {/* Empresa */}
                    <div className="md:col-span-7 bg-white dark:bg-gray-900 p-6 space-y-4">
                        <div>
                            <p className="text-[10px] text-gray-500 dark:text-gray-400 font-bold uppercase mb-2 tracking-widest">Empregador</p>
                            <h4 className="font-black text-xl text-gray-900 dark:text-white uppercase leading-tight">
                                {estabelecimento?.razao_social || 'MERCADINHO SYS - SOLUTIONS ERP LTDA'}
                            </h4>
                            <p className="text-sm text-gray-600 dark:text-gray-400 font-medium bg-gray-50 dark:bg-gray-800/50 inline-block px-3 py-1 rounded-lg mt-3 border border-gray-100 dark:border-gray-800">
                                CNPJ: {estabelecimento?.cnpj || '00.000.000/0001-00'} {estabelecimento?.inscricao_estadual && `| IE: ${estabelecimento.inscricao_estadual}`}
                            </p>
                        </div>
                        <div>
                            <p className="text-[10px] text-gray-500 dark:text-gray-400 font-bold uppercase mb-1 tracking-widest">Localização</p>
                            <p className="text-sm text-gray-700 dark:text-gray-300 font-medium">
                                {estabelecimento?.logradouro || 'Endereço não informado'}, {estabelecimento?.numero || 'S/N'}
                                {estabelecimento?.complemento && ` - ${estabelecimento.complemento}`}
                            </p>
                            <p className="text-sm text-gray-700 dark:text-gray-300 font-medium">
                                {estabelecimento?.bairro || ''} • {estabelecimento?.cidade || ''} - {estabelecimento?.estado || ''}
                            </p>
                        </div>
                    </div>

                    {/* Colaborador */}
                    <div className="md:col-span-5 bg-gray-50/80 dark:bg-gray-900/60 p-6 space-y-5">
                        <div>
                            <p className="text-[10px] text-gray-500 dark:text-gray-400 font-bold uppercase mb-2 tracking-widest">Colaborador</p>
                            <h4 className="font-black text-xl text-gray-900 dark:text-white uppercase leading-tight">{funcionario.nome}</h4>
                            <div className="mt-3">
                                <span className="text-xs bg-indigo-100 dark:bg-indigo-500/20 text-indigo-700 dark:text-indigo-300 px-3 py-1 rounded-md font-bold uppercase tracking-wider">
                                    {funcionario.cargo}
                                </span>
                            </div>
                        </div>
                        <div className="grid grid-cols-2 gap-6 pt-4 border-t border-gray-200 dark:border-gray-800">
                            <div>
                                <p className="text-[10px] text-gray-500 dark:text-gray-400 font-bold uppercase mb-1 tracking-widest">CPF</p>
                                <p className="text-sm font-black text-gray-900 dark:text-gray-200">{funcionario.cpf || '---'}</p>
                            </div>
                            <div>
                                <p className="text-[10px] text-gray-500 dark:text-gray-400 font-bold uppercase mb-1 tracking-widest">Admissão</p>
                                <p className="text-sm font-black text-gray-900 dark:text-gray-200">{formatDate(funcionario.data_admissao)}</p>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Tabela de Lançamentos */}
                <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 overflow-hidden shadow-sm">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="bg-gray-50 dark:bg-gray-800 text-gray-600 dark:text-gray-300 border-b border-gray-200 dark:border-gray-700">
                                <th className="px-6 py-4 text-xs font-bold uppercase tracking-widest">Descrição do Evento</th>
                                <th className="px-4 py-4 text-xs font-bold uppercase tracking-widest text-center">Referência</th>
                                <th className="px-6 py-4 text-xs font-bold uppercase tracking-widest text-right">Vencimentos</th>
                                <th className="px-6 py-4 text-xs font-bold uppercase tracking-widest text-right">Descontos</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100 dark:divide-gray-800/60">
                            {dados.vencimentos.map((item, idx) => (
                                <tr key={`v-${idx}`} className="text-sm hover:bg-gray-50/50 dark:hover:bg-gray-800/40 transition-colors">
                                    <td className="px-6 py-4 font-bold text-gray-900 dark:text-gray-200">{item.descricao}</td>
                                    <td className="px-4 py-4 text-center text-gray-500 dark:text-gray-400 font-medium">{item.referencia}</td>
                                    <td className="px-6 py-4 text-right font-black text-emerald-600 dark:text-emerald-400">{formatCurrency(item.valor)}</td>
                                    <td className="px-6 py-4 text-right text-gray-300 dark:text-gray-700 font-bold select-none">---</td>
                                </tr>
                            ))}
                            {dados.descontos.map((item, idx) => (
                                <tr key={`d-${idx}`} className="text-sm hover:bg-gray-50/50 dark:hover:bg-gray-800/40 transition-colors">
                                    <td className="px-6 py-4 font-bold text-gray-900 dark:text-gray-200">{item.descricao}</td>
                                    <td className="px-4 py-4 text-center text-gray-500 dark:text-gray-400 font-medium">{item.referencia}</td>
                                    <td className="px-6 py-4 text-right text-gray-300 dark:text-gray-700 font-bold select-none">---</td>
                                    <td className="px-6 py-4 text-right font-black text-rose-600 dark:text-rose-400">{formatCurrency(item.valor)}</td>
                                </tr>
                            ))}
                        </tbody>
                        <tfoot className="bg-gray-50 dark:bg-gray-800 border-t-2 border-gray-200 dark:border-gray-700">
                            <tr className="font-bold text-gray-700 dark:text-gray-300 uppercase text-xs">
                                <td colSpan={2} className="px-6 py-5 tracking-widest text-right border-r border-gray-200 dark:border-gray-700/50">Totalizadores</td>
                                <td className="px-6 py-5 text-right text-emerald-700 dark:text-emerald-400 text-base font-black border-r border-gray-200 dark:border-gray-700/50">{formatCurrency(dados.totais.bruto)}</td>
                                <td className="px-6 py-5 text-right text-rose-600 dark:text-rose-400 text-base font-black">{formatCurrency(dados.totais.descontos)}</td>
                            </tr>
                        </tfoot>
                    </table>
                </div>

                {/* Resumo e Valor Líquido */}
                <div className="flex flex-col md:flex-row items-stretch gap-6">
                    <div className="flex-1 bg-white dark:bg-gray-900 p-8 rounded-3xl border border-gray-200 dark:border-gray-800 shadow-sm relative overflow-hidden">
                        <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-50 dark:bg-indigo-500/5 rounded-bl-full -mr-8 -mt-8"></div>
                        <p className="text-[10px] text-gray-500 dark:text-gray-400 font-bold uppercase tracking-widest mb-6 relative z-10">Bases de Cálculo</p>
                        <div className="space-y-4 relative z-10">
                            <div className="flex justify-between items-end border-b border-gray-100 dark:border-gray-800 pb-3">
                                <span className="text-sm text-gray-700 dark:text-gray-400 font-medium">Salário Base (CLT)</span>
                                <span className="text-base text-gray-900 dark:text-white font-bold">{formatCurrency((Number(funcionario.salario_base || 0)))}</span>
                            </div>
                            <div className="flex justify-between items-end border-b border-gray-100 dark:border-gray-800 pb-3">
                                <span className="text-sm text-gray-700 dark:text-gray-400 font-medium">Base p/ FGTS Mensal</span>
                                <span className="text-base text-gray-900 dark:text-white font-bold">{formatCurrency(dados.totais.bruto)}</span>
                            </div>
                            <div className="flex justify-between items-end">
                                <span className="text-sm text-gray-700 dark:text-gray-400 font-medium">FGTS Depositado (8%)</span>
                                <span className="text-lg text-indigo-600 dark:text-indigo-400 font-black">{formatCurrency(dados.totais.bruto * 0.08)}</span>
                            </div>
                        </div>
                    </div>

                    <div className="flex-[1.4] bg-indigo-600 dark:bg-indigo-950 p-8 rounded-3xl text-white flex flex-col justify-center relative overflow-hidden shadow-xl shadow-indigo-600/20 group">
                        <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-transparent pointer-events-none"></div>
                        <div className="absolute -top-24 -right-24 w-64 h-64 bg-white/10 rounded-full blur-3xl transition-transform duration-700 group-hover:scale-110"></div>

                        <p className="text-xs font-bold uppercase tracking-widest text-indigo-100 dark:text-indigo-300 mb-3 relative z-10">Líquido a Receber</p>
                        <div className="flex items-baseline gap-2 relative z-10">
                            <span className="text-2xl font-black text-indigo-200 dark:text-indigo-400">R$</span>
                            <span className="text-5xl sm:text-6xl font-black tracking-tight drop-shadow-md">
                                {formatCurrency(dados.totais.liquido).replace('R$', '').trim()}
                            </span>
                        </div>

                        <div className="mt-8 pt-5 border-t border-indigo-500/50 dark:border-indigo-800 flex items-center justify-between relative z-10">
                            <div className="flex items-center gap-2">
                                <div className="w-2.5 h-2.5 bg-emerald-400 rounded-full animate-pulse shadow-[0_0_10px_rgba(52,211,153,0.5)]"></div>
                                <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-100 dark:text-indigo-300">Processado Online</span>
                            </div>
                            <span className="text-[10px] font-medium uppercase tracking-widest text-indigo-200 dark:text-indigo-400 opacity-80">REF: {Math.random().toString(36).substr(2, 6).toUpperCase()}</span>
                        </div>
                    </div>
                </div>

                {/* Rodapé Legal */}
                <div className="pt-8 pb-4 text-center">
                    <p className="text-[10px] font-bold uppercase tracking-widest text-gray-400 dark:text-gray-600 select-none">
                        Reconheço a exatidão deste recibo • MercadinhoSys Solutions
                    </p>
                </div>
            </div>
        </ResponsiveModal>
    );
};

export default HoleriteModal;
