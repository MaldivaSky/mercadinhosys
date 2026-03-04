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

        // Ganhos
        const valorHoraExtra = (salarioBase / 220) * 1.5;
        const totalHorasExtras = Number(func.horas_extras_horas || 0) * valorHoraExtra;

        // Benefícios Detalhados
        const listaBeneficios = func.beneficios_detalhes || [];

        // Descontos
        const inss = salarioBase * 0.09;
        const irrf = salarioBase > 5000 ? (salarioBase * 0.15) : 0;

        const vencimentos = [
            { descricao: 'Salário Base', referencia: '30 dias', valor: salarioBase },
            { descricao: 'Horas Extras', referencia: `${func.horas_extras_horas || 0}h`, valor: totalHorasExtras },
            ...listaBeneficios.map(b => ({
                descricao: b.descricao,
                referencia: 'Variável',
                valor: b.valor
            }))
        ];

        const totalVencimentos = vencimentos.reduce((acc, item) => acc + item.valor, 0);
        const totalDescontos = inss + irrf;
        const salarioLiquido = totalVencimentos - totalDescontos;

        return {
            vencimentos,
            descontos: [
                { descricao: 'INSS', referencia: '9.00%', valor: inss },
                { descricao: 'IRRF', referencia: irrf > 0 ? '15.00%' : 'Isento', valor: irrf }
            ],
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
            <div className="space-y-6 p-2 max-w-4xl mx-auto dark:text-white">
                {/* Branding Premium Topo */}
                <div className="flex items-center justify-between border-b-4 border-gray-900 dark:border-gray-100 pb-4">
                    <div className="flex items-center gap-3">
                        <div className="w-14 h-14 bg-gray-900 dark:bg-white text-white dark:text-gray-900 rounded-xl flex items-center justify-center font-black text-2xl shadow-lg">
                            MS
                        </div>
                        <div>
                            <h2 className="text-2xl font-black text-gray-900 dark:text-white leading-none uppercase tracking-tighter">MercadinhoSys</h2>
                            <p className="text-xs text-gray-800 dark:text-gray-300 font-black tracking-[0.2em] uppercase mt-1">Intelligent ERP</p>
                        </div>
                    </div>
                    <div className="text-right">
                        <p className="text-[10px] text-gray-700 dark:text-gray-400 font-black uppercase mb-1 tracking-widest">Contracheque Mensal</p>
                        <p className="text-xl font-black text-gray-900 dark:text-indigo-400 leading-none">{periodo}</p>
                    </div>
                </div>

                {/* Grid de Dados Principais */}
                <div className="grid grid-cols-1 md:grid-cols-12 gap-px bg-gray-300 dark:bg-gray-700 rounded-3xl overflow-hidden border-2 border-gray-300 dark:border-gray-700 shadow-xl">
                    {/* Empresa */}
                    <div className="md:col-span-7 bg-white dark:bg-gray-800 p-6 space-y-4">
                        <div>
                            <p className="text-[10px] text-gray-700 dark:text-gray-300 font-black uppercase mb-2 tracking-widest">Empregador</p>
                            <h4 className="font-black text-lg text-gray-900 dark:text-white uppercase leading-tight">
                                {estabelecimento?.razao_social || 'MERCADINHO SYS - SOLUTIONS ERP LTDA'}
                            </h4>
                            <p className="text-sm text-gray-700 dark:text-gray-300 font-bold bg-gray-100 dark:bg-gray-900/50 inline-block px-3 py-1 rounded-full mt-2">
                                CNPJ: {estabelecimento?.cnpj || '00.000.000/0001-00'} {estabelecimento?.inscricao_estadual && `| IE: ${estabelecimento.inscricao_estadual}`}
                            </p>
                        </div>
                        <div>
                            <p className="text-[10px] text-gray-700 dark:text-gray-300 font-black uppercase mb-1 tracking-widest">Localização</p>
                            <p className="text-sm text-gray-800 dark:text-gray-300 font-semibold">
                                {estabelecimento?.logradouro || 'Endereço não informado'}, {estabelecimento?.numero || 'S/N'}
                                {estabelecimento?.complemento && ` - ${estabelecimento.complemento}`}
                            </p>
                            <p className="text-sm text-gray-800 dark:text-gray-300 font-semibold">
                                {estabelecimento?.bairro || ''} • {estabelecimento?.cidade || ''} - {estabelecimento?.estado || ''}
                            </p>
                        </div>
                    </div>

                    {/* Colaborador */}
                    <div className="md:col-span-5 bg-gray-50 dark:bg-gray-900/40 p-6 space-y-5 border-l border-gray-100 dark:border-gray-700">
                        <div>
                            <p className="text-[10px] text-gray-700 dark:text-gray-300 font-black uppercase mb-2 tracking-widest">Colaborador</p>
                            <h4 className="font-black text-lg text-gray-900 dark:text-white uppercase leading-tight">{funcionario.nome}</h4>
                            <div className="mt-2">
                                <span className="text-[10px] bg-indigo-600 dark:bg-indigo-500 text-white px-3 py-1 rounded-lg font-black uppercase shadow-md shadow-indigo-500/20">
                                    {funcionario.cargo}
                                </span>
                            </div>
                        </div>
                        <div className="grid grid-cols-2 gap-6 pt-2 border-t border-gray-200 dark:border-gray-700">
                            <div>
                                <p className="text-[10px] text-gray-700 dark:text-gray-300 font-black uppercase mb-1 tracking-widest">CPF</p>
                                <p className="text-sm font-black text-gray-900 dark:text-gray-100">{funcionario.cpf || '---'}</p>
                            </div>
                            <div>
                                <p className="text-[10px] text-gray-700 dark:text-gray-300 font-black uppercase mb-1 tracking-widest">Admissão</p>
                                <p className="text-sm font-black text-gray-900 dark:text-gray-100">{formatDate(funcionario.data_admissao)}</p>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Tabela de Lançamentos */}
                <div className="bg-white dark:bg-gray-800 rounded-3xl border-4 border-gray-900 dark:border-gray-700 overflow-hidden shadow-2xl">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="bg-gray-900 dark:bg-gray-700 text-white">
                                <th className="px-6 py-4 text-[11px] font-black uppercase tracking-widest border-r border-gray-800 last:border-0">Descrição</th>
                                <th className="px-4 py-4 text-[11px] font-black uppercase tracking-widest text-center border-r border-gray-800 last:border-0">Ref</th>
                                <th className="px-6 py-4 text-[11px] font-black uppercase tracking-widest text-right border-r border-gray-800 last:border-0">Vencimentos</th>
                                <th className="px-6 py-4 text-[11px] font-black uppercase tracking-widest text-right">Descontos</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y-2 divide-gray-100 dark:divide-gray-900">
                            {dados.vencimentos.map((item, idx) => (
                                <tr key={`v-${idx}`} className="text-sm hover:bg-gray-50 dark:hover:bg-gray-900/50 transition-colors">
                                    <td className="px-6 py-5 font-black text-gray-900 dark:text-gray-100 border-r border-gray-50 dark:border-gray-700 last:border-0">{item.descricao}</td>
                                    <td className="px-4 py-5 text-center text-gray-700 dark:text-gray-400 font-bold border-r border-gray-50 dark:border-gray-700 last:border-0">{item.referencia}</td>
                                    <td className="px-6 py-5 text-right font-black text-green-700 dark:text-green-400 border-r border-gray-50 dark:border-gray-700 last:border-0">{formatCurrency(item.valor)}</td>
                                    <td className="px-6 py-5 text-right text-gray-400 dark:text-gray-600 font-black select-none">---</td>
                                </tr>
                            ))}
                            {dados.descontos.map((item, idx) => (
                                <tr key={`d-${idx}`} className="text-sm hover:bg-gray-50 dark:hover:bg-gray-900/50 transition-colors">
                                    <td className="px-6 py-5 font-black text-gray-900 dark:text-gray-100 border-r border-gray-50 dark:border-gray-700 last:border-0">{item.descricao}</td>
                                    <td className="px-4 py-5 text-center text-gray-700 dark:text-gray-400 font-bold border-r border-gray-50 dark:border-gray-700 last:border-0">{item.referencia}</td>
                                    <td className="px-6 py-5 text-right text-gray-400 dark:text-gray-600 font-black border-r border-gray-50 dark:border-gray-700 last:border-0 select-none">---</td>
                                    <td className="px-6 py-5 text-right font-black text-red-600 dark:text-red-500">{formatCurrency(item.valor)}</td>
                                </tr>
                            ))}
                        </tbody>
                        <tfoot className="bg-gray-50 dark:bg-gray-900 border-t-4 border-gray-900 dark:border-gray-700">
                            <tr className="font-black text-gray-900 dark:text-white uppercase text-[11px] leading-none">
                                <td colSpan={2} className="px-6 py-6 tracking-widest border-r border-gray-200 dark:border-gray-700">Totais da Folha</td>
                                <td className="px-6 py-6 text-right text-green-700 dark:text-green-400 text-base border-r border-gray-200 dark:border-gray-700">{formatCurrency(dados.totais.bruto)}</td>
                                <td className="px-6 py-6 text-right text-red-600 dark:text-red-500 text-base">{formatCurrency(dados.totais.descontos)}</td>
                            </tr>
                        </tfoot>
                    </table>
                </div>

                {/* Resumo e Valor Líquido */}
                <div className="flex flex-col md:flex-row items-stretch gap-6">
                    <div className="flex-1 bg-white dark:bg-gray-800 p-8 rounded-[2rem] border-2 border-gray-200 dark:border-gray-700 shadow-xl">
                        <p className="text-[10px] text-gray-700 dark:text-gray-300 font-black uppercase tracking-[0.3em] mb-4">Informações de Base</p>
                        <div className="space-y-4">
                            <div className="flex justify-between items-center text-sm font-black">
                                <span className="text-black dark:text-gray-300 font-black">Base p/ FGTS:</span>
                                <span>{formatCurrency(dados.totais.bruto)}</span>
                            </div>
                            <div className="flex justify-between items-center text-sm font-black">
                                <span className="text-black dark:text-gray-300 font-black">FGTS recolhido:</span>
                                <span className="text-indigo-600 dark:text-indigo-400">{formatCurrency(dados.totais.bruto * 0.08)}</span>
                            </div>
                        </div>
                    </div>

                    <div className="flex-[1.4] bg-gray-900 dark:bg-indigo-950 p-8 rounded-[2rem] text-white flex flex-col justify-center relative overflow-hidden shadow-2xl group transition-all hover:scale-[1.01]">
                        <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/20 to-transparent pointer-events-none"></div>
                        <div className="absolute top-0 right-0 w-40 h-40 bg-white/5 rounded-full -mr-20 -mt-20 blur-3xl"></div>

                        <p className="text-[10px] font-black uppercase tracking-[0.4em] opacity-60 mb-2">Total Líquido a Receber</p>
                        <div className="flex items-baseline gap-3">
                            <span className="text-2xl font-black opacity-40">R$</span>
                            <span className="text-6xl font-black tracking-tighter tabular-nums drop-shadow-2xl">
                                {formatCurrency(dados.totais.liquido).replace('R$', '').trim()}
                            </span>
                        </div>

                        <div className="mt-8 pt-4 border-t border-white/10 flex items-center justify-between">
                            <div className="flex items-center gap-2">
                                <div className="w-2.5 h-2.5 bg-green-400 rounded-full animate-pulse shadow-[0_0_10px_rgba(74,222,128,0.5)]"></div>
                                <span className="text-[10px] font-black uppercase tracking-widest opacity-80">Processamento Concluído</span>
                            </div>
                            <span className="text-[9px] font-black opacity-40 uppercase tabular-nums">ID: {Math.random().toString(36).substr(2, 9).toUpperCase()}</span>
                        </div>
                    </div>
                </div>

                {/* Rodapé Legal */}
                <div className="pt-6 border-t-2 border-gray-100 dark:border-gray-800 text-center">
                    <p className="text-[10px] font-black uppercase tracking-[0.8em] text-gray-400 dark:text-gray-600 select-none pb-2">
                        MercadinhoSys Enterprise Solutions • 2024
                    </p>
                </div>
            </div>
        </ResponsiveModal>
    );
};

export default HoleriteModal;
