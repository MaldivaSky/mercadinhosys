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
    endereco: string;
    cidade: string;
    estado: string;
}

const HoleriteModal = ({ isOpen, onClose, funcionario, periodo }: HoleriteModalProps) => {
    const [estabelecimento, setEstabelecimento] = useState<Estabelecimento | null>(null);

    useEffect(() => {
        if (isOpen) {
            const loadEstabelecimento = async () => {
                try {
                    const res = await apiClient.get('/configuracao');
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
        const totalHorasExtras = Number(func.horas_extras || 0) * valorHoraExtra;

        // Descontos
        const inss = salarioBase * 0.09; // Simplificado
        const irrf = salarioBase > 5000 ? (salarioBase * 0.15) : 0; // Regra conforme solicitado

        const totalVencimentos = salarioBase + totalHorasExtras;
        const totalDescontos = inss + irrf;
        const salarioLiquido = totalVencimentos - totalDescontos;

        return {
            vencimentos: [
                { descricao: 'Salário Base', referencia: '30 dias', valor: salarioBase },
                { descricao: 'Horas Extras', referencia: `${func.horas_extras || 0}h`, valor: totalHorasExtras }
            ],
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

        // Cabeçalho da Empresa
        doc.setFontSize(10);
        doc.text(estabelecimento?.razao_social || 'MERCADINHO SYS', 20, 20);
        doc.text(`CNPJ: ${estabelecimento?.cnpj || '00.000.000/0001-00'}`, 20, 25);

        doc.setFontSize(16);
        doc.text('RECIBO DE PAGAMENTO DE SALÁRIO', 105, 40, { align: 'center' });

        doc.setFontSize(10);
        doc.text(`Funcionário: ${funcionario.nome}`, 20, 55);
        doc.text(`CPF: ${funcionario.cpf || '---'}`, 20, 60);
        doc.text(`Mês/Ano: ${periodo}`, 160, 55);

        // Tabela de Itens
        const tableData = [
            ...dados.vencimentos.map(item => [item.descricao, item.referencia, formatCurrency(item.valor), '']),
            ...dados.descontos.map(item => [item.descricao, item.referencia, '', formatCurrency(item.valor)])
        ];

        autoTable(doc, {
            startY: 70,
            head: [['Descrição', 'Referência', 'Vencimentos', 'Descontos']],
            body: tableData,
            theme: 'grid',
            headStyles: { fillColor: [200, 200, 200], textColor: 0, fontStyle: 'bold' }
        });

        // Totais
        const finalY = (doc as any).lastAutoTable.finalY + 10;
        doc.text(`Total Vencimentos: ${formatCurrency(dados.totais.bruto)}`, 140, finalY);
        doc.text(`Total Descontos: ${formatCurrency(dados.totais.descontos)}`, 140, finalY + 5);
        doc.setFontSize(12);
        doc.setFont('helvetica', 'bold');
        doc.text(`LÍQUIDO A RECEBER: ${formatCurrency(dados.totais.liquido)}`, 140, finalY + 15);

        doc.save(`Holerite_${funcionario.nome.split(' ')[0]}_${periodo.replace('/', '-')}.pdf`);
    };

    return (
        <ResponsiveModal
            isOpen={isOpen}
            onClose={onClose}
            title="Recibo de Pagamento"
            subtitle={`Referência: ${periodo}`}
            headerIcon={<Clock className="w-6 h-6" />}
            headerColor="indigo"
            size="xl"
            footer={
                <div className="flex w-full gap-3 sm:justify-end">
                    <button
                        onClick={handlePrint}
                        className="flex-1 sm:flex-none flex items-center justify-center gap-2 px-6 py-3 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-white rounded-xl font-bold hover:bg-gray-200"
                    >
                        <Printer className="w-5 h-5" />
                        Imprimir
                    </button>
                    <button
                        onClick={handleDownloadPDF}
                        className="flex-1 sm:flex-none flex items-center justify-center gap-2 px-6 py-3 bg-indigo-600 text-white rounded-xl font-bold hover:bg-indigo-700 shadow-lg shadow-indigo-500/20"
                    >
                        <Download className="w-5 h-5" />
                        Download PDF
                    </button>
                </div>
            }
        >
            <div className="space-y-8 p-1">
                {/* Cabeçalho do Holerite */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 bg-gray-50 dark:bg-gray-900/50 p-6 rounded-2xl border border-gray-100 dark:border-gray-800">
                    <div className="space-y-4">
                        <div>
                            <p className="text-[10px] text-gray-400 font-black uppercase mb-1">Empregador</p>
                            <h4 className="font-bold text-gray-800 dark:text-white tracking-tight">{estabelecimento?.razao_social || 'MERCADINHO SYS'}</h4>
                            <p className="text-xs text-gray-500">{estabelecimento?.cnpj}</p>
                        </div>
                        <div>
                            <p className="text-[10px] text-gray-400 font-black uppercase mb-1">Local</p>
                            <p className="text-xs text-gray-600 dark:text-gray-400">{estabelecimento?.endereco}, {estabelecimento?.cidade} - {estabelecimento?.estado}</p>
                        </div>
                    </div>
                    <div className="space-y-4">
                        <div>
                            <p className="text-[10px] text-gray-400 font-black uppercase mb-1">Colaborador</p>
                            <h4 className="font-bold text-gray-800 dark:text-white tracking-tight">{funcionario.nome}</h4>
                            <p className="text-xs text-blue-600 font-bold">{funcionario.cargo}</p>
                        </div>
                        <div className="flex gap-8">
                            <div>
                                <p className="text-[10px] text-gray-400 font-black uppercase mb-1">CPF</p>
                                <p className="text-xs font-bold text-gray-700 dark:text-gray-300">{funcionario.cpf || '---'}</p>
                            </div>
                            <div>
                                <p className="text-[10px] text-gray-400 font-black uppercase mb-1">Admissão</p>
                                <p className="text-xs font-bold text-gray-700 dark:text-gray-300">{formatDate(funcionario.data_admissao)}</p>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Tabela de Vencimentos e Descontos */}
                <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 overflow-hidden shadow-sm">
                    <table className="w-full text-left">
                        <thead className="bg-gray-50 dark:bg-gray-900/50">
                            <tr>
                                <th className="px-6 py-3 text-[10px] font-black text-gray-400 uppercase">Descrição</th>
                                <th className="px-6 py-3 text-[10px] font-black text-gray-400 uppercase text-center">Referência</th>
                                <th className="px-6 py-3 text-[10px] font-black text-gray-400 uppercase text-right">Proventos</th>
                                <th className="px-6 py-3 text-[10px] font-black text-gray-400 uppercase text-right">Descontos</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                            {dados.vencimentos.map((item, idx) => (
                                <tr key={`v-${idx}`} className="text-sm">
                                    <td className="px-6 py-4 font-bold text-gray-700 dark:text-gray-300">{item.descricao}</td>
                                    <td className="px-6 py-4 text-center text-gray-500 font-medium">{item.referencia}</td>
                                    <td className="px-6 py-4 text-right font-bold text-green-600 dark:text-green-400">{formatCurrency(item.valor)}</td>
                                    <td className="px-6 py-4 text-right text-gray-300">---</td>
                                </tr>
                            ))}
                            {dados.descontos.map((item, idx) => (
                                <tr key={`d-${idx}`} className="text-sm">
                                    <td className="px-6 py-4 font-bold text-gray-700 dark:text-gray-300">{item.descricao}</td>
                                    <td className="px-6 py-4 text-center text-gray-500 font-medium">{item.referencia}</td>
                                    <td className="px-6 py-4 text-right text-gray-300">---</td>
                                    <td className="px-6 py-4 text-right font-bold text-red-500">{formatCurrency(item.valor)}</td>
                                </tr>
                            ))}
                        </tbody>
                        <tfoot className="bg-indigo-50/50 dark:bg-indigo-900/20 border-t border-indigo-100 dark:border-indigo-800">
                            <tr className="font-bold text-gray-800 dark:text-white">
                                <td colSpan={2} className="px-6 py-4">RESUMO DE VALORES</td>
                                <td className="px-6 py-4 text-right text-green-700 dark:text-green-300">{formatCurrency(dados.totais.bruto)}</td>
                                <td className="px-6 py-4 text-right text-red-600 dark:text-red-400">{formatCurrency(dados.totais.descontos)}</td>
                            </tr>
                        </tfoot>
                    </table>
                </div>

                {/* Valor Líquido Rodapé */}
                <div className="flex flex-col sm:flex-row justify-between items-center bg-indigo-600 p-8 rounded-3xl text-white shadow-xl shadow-indigo-600/20">
                    <div className="text-center sm:text-right">
                        <p className="text-4xl font-black">{formatCurrency(dados.totais.liquido)}</p>
                        <div className="flex items-center gap-2 mt-2 justify-center sm:justify-end">
                            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                            <span className="text-[10px] font-black uppercase tracking-widest opacity-80">Processamento Concluído</span>
                        </div>
                    </div>
                </div>

                <div className="text-center opacity-30 select-none">
                    <p className="text-[9px] font-black uppercase tracking-[0.5em] text-gray-400">
                        Documento Digital • Autenticidade Garantida pelo Sistema
                    </p>
                </div>
            </div>
        </ResponsiveModal>
    );
};

export default HoleriteModal;
