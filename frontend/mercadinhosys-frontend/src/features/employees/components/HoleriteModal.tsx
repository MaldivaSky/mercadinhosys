
import { X, Printer, Download } from 'lucide-react';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
import { useEffect, useState } from 'react';
import settingsService, { Estabelecimento } from '../../settings/settingsService';

interface HoleriteModalProps {
    isOpen: boolean;
    onClose: () => void;
    funcionario: {
        nome: string;
        cargo: string;
        salario_base: number;
        beneficios: number;
        horas_extras_horas: number;
        custo_horas_extras: number;
        atrasos_minutos: number;
        faltas: number;
        total_estimado: number;
    };
    periodo: {
        inicio: string;
        fim: string;
    };
}

export default function HoleriteModal({ isOpen, onClose, funcionario, periodo }: HoleriteModalProps) {
    const [estabelecimento, setEstabelecimento] = useState<Estabelecimento | null>(null);

    useEffect(() => {
        if (isOpen) {
            loadEstabelecimento();
        }
    }, [isOpen]);

    const loadEstabelecimento = async () => {
        try {
            const data = await settingsService.getEstabelecimento();
            setEstabelecimento(data);
        } catch (error) {
            console.error('Erro ao carregar dados do estabelecimento:', error);
        }
    };

    if (!isOpen) return null;

    // Calculos de impostos (Estimativa 2024/2025)
    const calcularHolerite = () => {
        const salarioBase = funcionario.salario_base;
        const horasExtras = funcionario.custo_horas_extras;

        // DSR sobre Horas Extras (Estimativa 1/6)
        const dsrExtras = horasExtras > 0 ? horasExtras / 6 : 0;

        const vencimentosBrutos = salarioBase + horasExtras + dsrExtras + funcionario.beneficios;

        // INSS (Tabela Progressiva 2024)
        let inss = 0;
        const tetoINSS = 7786.02;
        const baseINSS = Math.min(vencimentosBrutos, tetoINSS);

        if (baseINSS <= 1412.00) {
            inss = baseINSS * 0.075;
        } else if (baseINSS <= 2666.68) {
            inss = (baseINSS * 0.09) - 21.18;
        } else if (baseINSS <= 4000.03) {
            inss = (baseINSS * 0.12) - 101.18;
        } else if (baseINSS <= tetoINSS) {
            inss = (baseINSS * 0.14) - 181.18;
        } else {
            inss = 908.85; // Teto (estimado)
        }

        // IRRF (Tabela Progressiva 2026 - Lei 15.270/2025)
        // Base = Bruto - INSS - Dependentes (assumindo 0)
        const baseIRRF = vencimentosBrutos - inss;
        let irrf = 0;

        // Isenção até R$ 5.000,00
        if (baseIRRF <= 5000.00) {
            irrf = 0;
        } else if (baseIRRF <= 7500.00) {
            // Faixa 1 (Estimada com base na isenção de 5k)
            irrf = (baseIRRF * 0.075) - 375.00;
        } else if (baseIRRF <= 10000.00) {
            // Faixa 2
            irrf = (baseIRRF * 0.15) - 937.50;
        } else if (baseIRRF <= 12500.00) {
            // Faixa 3
            irrf = (baseIRRF * 0.225) - 1687.50;
        } else {
            // Faixa 4
            irrf = (baseIRRF * 0.275) - 2312.50;
        }

        // Faltas e Atrasos (Cálculo Estimado)
        // Assumindo 220h mensais
        const valorHora = salarioBase / 220;
        const descontoFaltas = funcionario.faltas * (valorHora * 7.33); // ~7h20 por dia
        const descontoAtrasos = (funcionario.atrasos_minutos / 60) * valorHora;
        const totalDescontoFaltas = descontoFaltas + descontoAtrasos;

        const totalDescontos = inss + irrf + totalDescontoFaltas;
        const liquido = vencimentosBrutos - totalDescontos;
        const fgts = vencimentosBrutos * 0.08;

        return {
            vencimentosBrutos,
            inss,
            irrf,
            totalDescontoFaltas,
            dsrExtras,
            totalDescontos,
            liquido,
            fgts,
            baseINSS,
            baseIRRF,
            baseFGTS: vencimentosBrutos
        };
    };

    const dados = calcularHolerite();

    // Format reference period
    const getReferenciaFull = () => {
        if (periodo.inicio) {
            const date = new Date(periodo.inicio);
            return date.toLocaleDateString('pt-BR', { month: 'long', year: 'numeric' }).toUpperCase();
        }
        return new Date().toLocaleDateString('pt-BR', { month: 'long', year: 'numeric' }).toUpperCase();
    };

    const gerarPDF = () => {
        const doc = new jsPDF();
        const referencia = getReferenciaFull();

        // Configurações visuais
        doc.setFont("helvetica", "bold");
        doc.setFontSize(14);
        doc.text("RECIBO DE PAGAMENTO DE SALÁRIO", 105, 15, { align: "center" });

        // Cabeçalho da Empresa
        doc.setFontSize(10);
        doc.setFont("helvetica", "normal");
        doc.rect(10, 20, 190, 25);
        doc.text(`EMPREGADORA: ${estabelecimento?.razao_social?.toUpperCase() || 'EMPRESA NÃO CONFIGURADA'}`, 15, 26);
        doc.text(`CNPJ: ${estabelecimento?.cnpj || '00.000.000/0000-00'}`, 15, 31);
        doc.text(`ENDEREÇO: ${estabelecimento?.logradouro || ''}, ${estabelecimento?.numero || ''} - ${estabelecimento?.bairro || ''}`, 15, 36);
        doc.text(`REFERÊNCIA: ${referencia}`, 150, 26);

        // Dados do Funcionário
        doc.line(10, 35, 200, 35);
        doc.text(`FUNCIONÁRIO: ${funcionario.nome.toUpperCase()}`, 15, 41);
        doc.text(`CARGO: ${funcionario.cargo.toUpperCase()}`, 120, 41);

        // Corpo do Holerite (Tabela)
        const items = [
            ["001", "SALÁRIO BASE", "30 DIAS", `R$ ${funcionario.salario_base.toFixed(2)}`, ""],
        ];

        if (funcionario.beneficios > 0) {
            items.push(["002", "BENEFÍCIOS / ADICIONAIS", "-", `R$ ${funcionario.beneficios.toFixed(2)}`, ""]);
        }

        if (funcionario.horas_extras_horas > 0) {
            items.push(["003", "HORAS EXTRAS 50%", `${funcionario.horas_extras_horas.toFixed(2)} H`, `R$ ${funcionario.custo_horas_extras.toFixed(2)}`, ""]);
            items.push(["004", "DSR S/ HORAS EXTRAS", "-", `R$ ${dados.dsrExtras.toFixed(2)}`, ""]);
        }

        if (dados.inss > 0) {
            items.push(["101", "INSS", "TABELA", "", `R$ ${dados.inss.toFixed(2)}`]);
        }

        if (dados.irrf > 0) {
            items.push(["102", "IRRF", "TABELA", "", `R$ ${dados.irrf.toFixed(2)}`]);
        }

        if (dados.totalDescontoFaltas > 0) {
            items.push(["103", "FALTAS / ATRASOS", "-", "", `R$ ${dados.totalDescontoFaltas.toFixed(2)}`]);
        }

        // Preencher linhas vazias para dar altura fixa
        while (items.length < 10) {
            items.push(["", "", "", "", ""]);
        }

        autoTable(doc, {
            startY: 45,
            head: [["CÓD", "DESCRIÇÃO", "REFERÊNCIA", "VENCIMENTOS", "DESCONTOS"]],
            body: items,
            theme: 'plain',
            styles: { fontSize: 9, cellPadding: 2, lineWidth: 0.1, lineColor: [0, 0, 0] },
            headStyles: { fillColor: [220, 220, 220], textColor: [0, 0, 0], fontStyle: 'bold' },
            columnStyles: {
                0: { cellWidth: 15, halign: 'center' },
                1: { cellWidth: 80 },
                2: { cellWidth: 25, halign: 'center' },
                3: { cellWidth: 35, halign: 'right' },
                4: { cellWidth: 35, halign: 'right' }
            }
        });

        // Rodapé de Totais
        const finalY = (doc as any).lastAutoTable.finalY;

        // Retângulo totais
        doc.rect(10, finalY, 190, 15);

        // Texto totais
        doc.setFont("helvetica", "bold");
        doc.text("TOTAL VENCIMENTOS", 110, finalY + 5);
        doc.text(`R$ ${dados.vencimentosBrutos.toFixed(2)}`, 110, finalY + 11);

        doc.text("TOTAL DESCONTOS", 155, finalY + 5);
        doc.text(`R$ ${dados.totalDescontos.toFixed(2)}`, 155, finalY + 11);

        // Líquido
        doc.rect(155, finalY + 15, 45, 12, 'F');
        doc.setFillColor(200, 200, 200); // highlight bg
        doc.setTextColor(0, 0, 0);
        doc.text("LÍQUIDO A RECEBER", 157, finalY + 20);
        doc.setFontSize(12);
        doc.text(`R$ ${dados.liquido.toFixed(2)}`, 157, finalY + 25);

        // Rodapé Bases
        doc.setFontSize(8);
        doc.setFont("helvetica", "normal");
        doc.rect(10, finalY + 15, 140, 12);

        doc.text("SALÁRIO BASE", 12, finalY + 19);
        doc.text(`R$ ${funcionario.salario_base.toFixed(2)}`, 12, finalY + 24);

        doc.text("SAL. CONTR. INSS", 45, finalY + 19);
        doc.text(`R$ ${dados.baseINSS.toFixed(2)}`, 45, finalY + 24);

        doc.text("BASE CÁLC. FGTS", 80, finalY + 19);
        doc.text(`R$ ${dados.baseFGTS.toFixed(2)}`, 80, finalY + 24);

        doc.text("FGTS DO MÊS", 115, finalY + 19);
        doc.text(`R$ ${dados.fgts.toFixed(2)}`, 115, finalY + 24);

        doc.text("BASE CÁLC. IRRF", 12, finalY + 32);
        doc.text(`R$ ${dados.baseIRRF.toFixed(2)}`, 12, finalY + 36);

        // Declaração
        doc.line(10, finalY + 50, 130, finalY + 50);
        doc.text("Assinatura do Funcionário", 40, finalY + 55);
        doc.text(new Date().toLocaleDateString(), 150, finalY + 50);

        doc.save(`holerite-${funcionario.nome.replace(/\s+/g, '_')}-${new Date().toISOString().split('T')[0]}.pdf`);
    };

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-y-auto">
                {/* Header Modal */}
                <div className="flex items-center justify-between p-6 border-b border-gray-100 bg-gray-50 rounded-t-xl">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-blue-100 text-blue-700 rounded-lg">
                            <Printer className="w-6 h-6" />
                        </div>
                        <div>
                            <h2 className="text-xl font-bold text-gray-900">Prévia do Holerite</h2>
                            <p className="text-sm text-gray-500">
                                Competência: {getReferenciaFull()}
                            </p>
                        </div>
                    </div>
                    <button onClick={onClose} className="p-2 hover:bg-gray-200 rounded-full transition-colors text-gray-500">
                        <X className="w-6 h-6" />
                    </button>
                </div>

                {/* Content - Simulação Visual Holerite */}
                <div className="p-8 bg-white print-container">
                    <div className="border border-gray-800 p-1 bg-white">
                        {/* Header Holerite */}
                        <div className="border-b border-gray-800 pb-4 mb-4">
                            <div className="flex justify-between items-start">
                                <div>
                                    <h1 className="font-bold text-lg text-gray-900">{estabelecimento?.razao_social?.toUpperCase() || 'SUPERMERCADO EXEMPLO LTDA'}</h1>
                                    <p className="text-xs text-gray-600">CNPJ: {estabelecimento?.cnpj || '00.000.000/0001-00'}</p>
                                    <p className="text-xs text-gray-600">
                                        {estabelecimento ? `${estabelecimento.logradouro}, ${estabelecimento.numero} - ${estabelecimento.bairro}` : 'Endereço não configurado'}
                                    </p>
                                </div>
                                <div className="text-right">
                                    <h2 className="font-bold text-gray-900">RECIBO DE PAGAMENTO DE SALÁRIO</h2>
                                    <p className="text-sm font-bold mt-1 border border-gray-300 px-2 py-1 inline-block">
                                        {getReferenciaFull()}
                                    </p>
                                </div>
                            </div>
                        </div>

                        {/* Funcionário */}
                        <div className="grid grid-cols-2 gap-4 mb-6 text-sm border-b border-gray-300 pb-4">
                            <div>
                                <span className="block text-xs text-gray-500 font-bold uppercase">Funcionário</span>
                                <span className="font-bold text-gray-900">{funcionario.nome.toUpperCase()}</span>
                            </div>
                            <div>
                                <span className="block text-xs text-gray-500 font-bold uppercase">Cargo</span>
                                <span className="font-bold text-gray-900">{funcionario.cargo.toUpperCase()}</span>
                            </div>
                        </div>

                        {/* Tabela de Verbas */}
                        <div className="mb-6">
                            <table className="w-full text-sm border-collapse border border-gray-300">
                                <thead>
                                    <tr className="bg-gray-100">
                                        <th className="border border-gray-300 px-2 py-1 text-center w-16">CÓD</th>
                                        <th className="border border-gray-300 px-2 py-1 text-left">DESCRIÇÃO</th>
                                        <th className="border border-gray-300 px-2 py-1 text-center w-24">REF.</th>
                                        <th className="border border-gray-300 px-2 py-1 text-right w-32">VENCIMENTOS</th>
                                        <th className="border border-gray-300 px-2 py-1 text-right w-32">DESCONTOS</th>
                                    </tr>
                                </thead>
                                <tbody className="font-mono text-xs">
                                    <tr>
                                        <td className="border-l border-r border-gray-300 px-2 py-1 text-center">001</td>
                                        <td className="border-l border-r border-gray-300 px-2 py-1">SALÁRIO BASE</td>
                                        <td className="border-l border-r border-gray-300 px-2 py-1 text-center">30</td>
                                        <td className="border-l border-r border-gray-300 px-2 py-1 text-right">{funcionario.salario_base.toFixed(2)}</td>
                                        <td className="border-l border-r border-gray-300 px-2 py-1 text-right"></td>
                                    </tr>
                                    {funcionario.beneficios > 0 && (
                                        <tr>
                                            <td className="border-l border-r border-gray-300 px-2 py-1 text-center">002</td>
                                            <td className="border-l border-r border-gray-300 px-2 py-1">BENEFÍCIOS / ADIC.</td>
                                            <td className="border-l border-r border-gray-300 px-2 py-1 text-center">-</td>
                                            <td className="border-l border-r border-gray-300 px-2 py-1 text-right">{funcionario.beneficios.toFixed(2)}</td>
                                            <td className="border-l border-r border-gray-300 px-2 py-1 text-right"></td>
                                        </tr>
                                    )}
                                    {funcionario.horas_extras_horas > 0 && (
                                        <>
                                            <tr>
                                                <td className="border-l border-r border-gray-300 px-2 py-1 text-center">003</td>
                                                <td className="border-l border-r border-gray-300 px-2 py-1">HORAS EXTRAS 50%</td>
                                                <td className="border-l border-r border-gray-300 px-2 py-1 text-center">{funcionario.horas_extras_horas.toFixed(2)}</td>
                                                <td className="border-l border-r border-gray-300 px-2 py-1 text-right">{funcionario.custo_horas_extras.toFixed(2)}</td>
                                                <td className="border-l border-r border-gray-300 px-2 py-1 text-right"></td>
                                            </tr>
                                            <tr>
                                                <td className="border-l border-r border-gray-300 px-2 py-1 text-center">004</td>
                                                <td className="border-l border-r border-gray-300 px-2 py-1">DSR S/ H. EXTRAS</td>
                                                <td className="border-l border-r border-gray-300 px-2 py-1 text-center">-</td>
                                                <td className="border-l border-r border-gray-300 px-2 py-1 text-right">{dados.dsrExtras.toFixed(2)}</td>
                                                <td className="border-l border-r border-gray-300 px-2 py-1 text-right"></td>
                                            </tr>
                                        </>
                                    )}
                                    {dados.inss > 0 && (
                                        <tr>
                                            <td className="border-l border-r border-gray-300 px-2 py-1 text-center">101</td>
                                            <td className="border-l border-r border-gray-300 px-2 py-1">INSS</td>
                                            <td className="border-l border-r border-gray-300 px-2 py-1 text-center">TAB</td>
                                            <td className="border-l border-r border-gray-300 px-2 py-1 text-right"></td>
                                            <td className="border-l border-r border-gray-300 px-2 py-1 text-right text-red-600">{dados.inss.toFixed(2)}</td>
                                        </tr>
                                    )}
                                    {dados.irrf > 0 && (
                                        <tr>
                                            <td className="border-l border-r border-gray-300 px-2 py-1 text-center">102</td>
                                            <td className="border-l border-r border-gray-300 px-2 py-1">IRRF</td>
                                            <td className="border-l border-r border-gray-300 px-2 py-1 text-center">TAB</td>
                                            <td className="border-l border-r border-gray-300 px-2 py-1 text-right"></td>
                                            <td className="border-l border-r border-gray-300 px-2 py-1 text-right text-red-600">{dados.irrf.toFixed(2)}</td>
                                        </tr>
                                    )}
                                    {dados.totalDescontoFaltas > 0 && (
                                        <tr>
                                            <td className="border-l border-r border-gray-300 px-2 py-1 text-center">103</td>
                                            <td className="border-l border-r border-gray-300 px-2 py-1">FALTAS E ATRASOS</td>
                                            <td className="border-l border-r border-gray-300 px-2 py-1 text-center">-</td>
                                            <td className="border-l border-r border-gray-300 px-2 py-1 text-right"></td>
                                            <td className="border-l border-r border-gray-300 px-2 py-1 text-right text-red-600">{dados.totalDescontoFaltas.toFixed(2)}</td>
                                        </tr>
                                    )}
                                    {/* Linhas vazias para preencher espaço */}
                                    {[...Array(5)].map((_, i) => (
                                        <tr key={`empty-${i}`}>
                                            <td className="border-l border-r border-gray-300 px-2 py-1 text-center">&nbsp;</td>
                                            <td className="border-l border-r border-gray-300 px-2 py-1">&nbsp;</td>
                                            <td className="border-l border-r border-gray-300 px-2 py-1 text-center">&nbsp;</td>
                                            <td className="border-l border-r border-gray-300 px-2 py-1 text-right">&nbsp;</td>
                                            <td className="border-l border-r border-gray-300 px-2 py-1 text-right">&nbsp;</td>
                                        </tr>
                                    ))}
                                </tbody>
                                <tfoot className="bg-gray-100 font-bold border-t-2 border-gray-400">
                                    <tr>
                                        <td colSpan={3} className="border border-gray-300 px-3 py-2 text-right">TOTAIS</td>
                                        <td className="border border-gray-300 px-3 py-2 text-right text-blue-700">{dados.vencimentosBrutos.toFixed(2)}</td>
                                        <td className="border border-gray-300 px-3 py-2 text-right text-red-700">{dados.totalDescontos.toFixed(2)}</td>
                                    </tr>
                                </tfoot>
                            </table>
                        </div>

                        {/* Rodapé Líquido e Bases */}
                        <div className="flex border border-gray-300">
                            <div className="flex-1 p-3 border-r border-gray-300 bg-gray-50">
                                <div className="grid grid-cols-4 gap-4 text-xs">
                                    <div>
                                        <span className="block font-bold text-gray-500">Salário Base</span>
                                        <span className="block text-gray-900">R$ {funcionario.salario_base.toFixed(2)}</span>
                                    </div>
                                    <div>
                                        <span className="block font-bold text-gray-500">Sal. Contr. INSS</span>
                                        <span className="block text-gray-900">R$ {dados.baseINSS.toFixed(2)}</span>
                                    </div>
                                    <div>
                                        <span className="block font-bold text-gray-500">Base Cálc. FGTS</span>
                                        <span className="block text-gray-900">R$ {dados.baseFGTS.toFixed(2)}</span>
                                    </div>
                                    <div>
                                        <span className="block font-bold text-gray-500">FGTS do Mês</span>
                                        <span className="block text-gray-900">R$ {dados.fgts.toFixed(2)}</span>
                                    </div>
                                    <div>
                                        <span className="block font-bold text-gray-500">Base Cálc. IRRF</span>
                                        <span className="block text-gray-900">R$ {dados.baseIRRF.toFixed(2)}</span>
                                    </div>
                                    <div>
                                        <span className="block font-bold text-gray-500">Faixa IRRF</span>
                                        <span className="block text-gray-900">{dados.irrf > 0 ? "Tabela" : "Isento"}</span>
                                    </div>
                                </div>
                            </div>
                            <div className="w-1/3 p-3 flex flex-col justify-center items-end bg-blue-50">
                                <span className="text-xs font-bold text-gray-500 uppercase mb-1">Líquido a Receber</span>
                                <span className="text-2xl font-bold text-blue-900 bg-white px-4 py-2 rounded border border-blue-200 shadow-sm block w-full text-right">
                                    R$ {dados.liquido.toFixed(2)}
                                </span>
                            </div>
                        </div>

                        <div className="mt-8 pt-8 border-t border-dashed border-gray-400 text-xs text-gray-500 flex justify-between items-end">
                            <div>
                                Declaro ter recebido a importância líquida discriminada neste recibo.
                                <div className="mt-6 border-t border-gray-900 w-64 pt-1">
                                    Assinatura do Funcionário
                                </div>
                            </div>
                            <div className="text-right">
                                {new Date().toLocaleDateString('pt-BR')}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Footer Actions */}
                <div className="p-6 border-t border-gray-100 bg-gray-50 flex justify-end gap-3 rounded-b-xl">
                    <button
                        onClick={onClose}
                        className="px-6 py-2.5 border border-gray-300 rounded-lg hover:bg-gray-100 transition-colors font-medium text-gray-700"
                    >
                        Fechar
                    </button>
                    <button
                        onClick={gerarPDF}
                        className="px-6 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2 font-medium shadow-md hover:shadow-lg transform active:scale-95"
                    >
                        <Download className="w-5 h-5" />
                        Baixar PDF (Oficial)
                    </button>
                </div>
            </div>
        </div>
    );
}
