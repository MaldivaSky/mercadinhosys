import React, { useEffect, useRef, useState } from 'react';
import { Printer, X, Eye } from 'lucide-react';
import { pdvService, ComprovanteVendaResponse } from '../pdvService';

interface CupomFiscalModalProps {
    aberto: boolean;
    vendaId: number | null;
    onFechar: () => void;
}

const FORMA_PAGAMENTO_LABEL: Record<string, string> = {
    dinheiro: 'DINHEIRO',
    pix: 'PIX',
    cartao_credito: 'CARTÃO DE CRÉDITO',
    cartao_debito: 'CARTÃO DE DÉBITO',
    fiado: 'FIADO / CRÉDITO',
};

const formatBRL = (v: number) =>
    v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

const CupomFiscalModal: React.FC<CupomFiscalModalProps> = ({ aberto, vendaId, onFechar }) => {
    const [dados, setDados] = useState<ComprovanteVendaResponse | null>(null);
    const [carregando, setCarregando] = useState(false);
    const [erro, setErro] = useState<string | null>(null);
    const cupomRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (!aberto || !vendaId) return;
        setDados(null);
        setErro(null);
        setCarregando(true);
        pdvService.obterComprovante(vendaId)
            .then(setDados)
            .catch(() => setErro('Não foi possível carregar o comprovante.'))
            .finally(() => setCarregando(false));
    }, [aberto, vendaId]);

    const handleImprimir = () => {
        if (!cupomRef.current) return;
        const conteudo = cupomRef.current.innerHTML;
        const janela = window.open('', '_blank', 'width=400,height=700');
        if (!janela) return;
        janela.document.write(`<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8"/>
  <title>Cupom Fiscal</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Courier+Prime:wght@400;700&display=swap');
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: 'Courier Prime', 'Courier New', monospace;
      font-size: 12px;
      color: #111;
      background: #fff;
      width: 80mm;
      max-width: 80mm;
      padding: 4mm;
    }
    @media print {
      body { width: 80mm; padding: 2mm; }
      .no-print { display: none !important; }
    }
    ${CUPOM_CSS}
  </style>
</head>
<body>${conteudo}</body>
</html>`);
        janela.document.close();
        setTimeout(() => {
            janela.print();
            janela.close();
        }, 300);
    };

    if (!aberto) return null;

    const est = dados?.estabelecimento;
    const comp = dados?.comprovante;
    const venda = dados?.venda;

    const dataHora = venda?.data
        ? venda.data
        : new Date().toLocaleString('pt-BR');

    const formaLabel = comp?.forma_pagamento
        ? (FORMA_PAGAMENTO_LABEL[comp.forma_pagamento.toLowerCase().replace(/\s/g, '_')] || comp.forma_pagamento.toUpperCase())
        : '—';

    return (
        <div className="fixed inset-0 z-[200] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
            <div className="relative w-full max-w-sm bg-white rounded-2xl shadow-2xl flex flex-col max-h-[90vh]">

                {/* Header do modal */}
                <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100">
                    <div className="flex items-center gap-2">
                        <div className="w-9 h-9 bg-slate-900 rounded-xl flex items-center justify-center">
                            <Eye className="w-5 h-5 text-white" />
                        </div>
                        <div>
                            <p className="text-sm font-black text-slate-900 uppercase tracking-tight">Comprovante</p>
                            <p className="text-[10px] text-slate-400 font-semibold">{venda?.codigo || '—'}</p>
                        </div>
                    </div>
                    <button onClick={onFechar}
                        className="p-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-500 transition-colors">
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {/* Body rolável */}
                <div className="flex-1 overflow-y-auto p-4">
                    {carregando && (
                        <div className="flex flex-col items-center justify-center py-16 gap-3">
                            <div className="w-10 h-10 border-4 border-slate-200 border-t-slate-800 rounded-full animate-spin" />
                            <p className="text-xs text-slate-400 font-semibold">Carregando comprovante...</p>
                        </div>
                    )}
                    {erro && (
                        <div className="py-12 text-center text-sm text-red-500 font-semibold">{erro}</div>
                    )}

                    {dados && comp && (
                        /* ══════════════ CUPOM VISUAL ══════════════ */
                        <div
                            ref={cupomRef}
                            className="cupom-papel font-mono text-xs text-black bg-white select-none"
                            style={{ fontFamily: "'Courier Prime', 'Courier New', monospace", lineHeight: '1.5' }}
                        >
                            {/* ── Cabeçalho ── */}
                            <div className="text-center pb-2 border-b border-dashed border-black mb-2">
                                {est?.nome_fantasia && (
                                    <p className="font-black text-sm uppercase tracking-wide">{est.nome_fantasia}</p>
                                )}
                                {est?.razao_social && <p className="text-[10px]">{est.razao_social}</p>}
                                {est?.cnpj && <p className="text-[10px]">CNPJ: {est.cnpj}</p>}
                                {est?.endereco && <p className="text-[10px]">{est.endereco}</p>}
                                {est?.telefone && <p className="text-[10px]">Tel: {est.telefone}</p>}
                            </div>

                            {/* ── Identificação do cupom ── */}
                            <div className="text-center border-b border-dashed border-black pb-2 mb-2">
                                <p className="font-black text-sm">CUPOM NÃO FISCAL</p>
                                <p className="text-[10px]">Nº {venda?.codigo}</p>
                                <p className="text-[10px]">{dataHora}</p>
                                <p className="text-[10px]">Cliente: {comp.cliente || 'Consumidor Final'}</p>
                                <p className="text-[10px]">Operador: {comp.funcionario}</p>
                            </div>

                            {/* ── Itens ── */}
                            <div className="border-b border-dashed border-black pb-2 mb-2">
                                <p className="font-black text-[10px] uppercase mb-1">ITEM  DESCRIÇÃO                 QTD    VL.UN  TOTAL</p>
                                {comp.itens.map((item, i) => (
                                    <div key={i} className="text-[10px] leading-snug">
                                        <span className="font-bold">{String(i + 1).padStart(3, '0')}  </span>
                                        <span>{item.nome.slice(0, 22).padEnd(22, ' ')}</span>
                                        <span>{String(item.quantidade).padStart(4, ' ')}x </span>
                                        <span>{formatBRL(item.preco_unitario).padStart(7, ' ')}  </span>
                                        <span className="font-bold">{formatBRL(item.total).padStart(9, ' ')}</span>
                                    </div>
                                ))}
                            </div>

                            {/* ── Totais ── */}
                            <div className="border-b border-dashed border-black pb-2 mb-2 text-[11px]">
                                <div className="flex justify-between">
                                    <span>SUBTOTAL</span>
                                    <span>{formatBRL(comp.subtotal)}</span>
                                </div>
                                {(comp.desconto ?? 0) > 0 && (
                                    <div className="flex justify-between">
                                        <span>DESCONTO</span>
                                        <span className="text-green-700">- {formatBRL(comp.desconto)}</span>
                                    </div>
                                )}
                                <div className="flex justify-between font-black text-sm mt-1">
                                    <span>TOTAL</span>
                                    <span>{formatBRL(comp.total)}</span>
                                </div>
                            </div>

                            {/* ── Pagamento ── */}
                            <div className="border-b border-dashed border-black pb-2 mb-2 text-[10px]">
                                <div className="flex justify-between">
                                    <span className="font-bold">FORMA PGT.</span>
                                    <span>{formaLabel}</span>
                                </div>
                                {(comp.valor_recebido ?? 0) > 0 && (
                                    <div className="flex justify-between">
                                        <span>VALOR RECEBIDO</span>
                                        <span>{formatBRL(comp.valor_recebido)}</span>
                                    </div>
                                )}
                                {(comp.troco ?? 0) > 0 && (
                                    <div className="flex justify-between font-bold">
                                        <span>TROCO</span>
                                        <span>{formatBRL(comp.troco)}</span>
                                    </div>
                                )}
                            </div>

                            {/* ── Rodapé ── */}
                            <div className="text-center text-[10px] mt-2">
                                <p className="font-bold">{comp.rodape || 'Obrigado pela preferência!'}</p>
                                <p className="text-[9px] mt-1 text-slate-500">
                                    Documento sem valor fiscal • MercadinhoSys
                                </p>
                                <p className="text-[9px]">
                                    *** {new Date().getFullYear()} ***
                                </p>
                            </div>
                        </div>
                    )}
                </div>

                {/* Footer com botões */}
                {dados && (
                    <div className="px-4 py-3 border-t border-slate-100 flex gap-2">
                        <button
                            onClick={onFechar}
                            className="flex-1 py-3 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-sm transition-colors"
                        >
                            Fechar
                        </button>
                        <button
                            onClick={handleImprimir}
                            className="flex-1 py-3 rounded-xl bg-slate-900 hover:bg-slate-700 text-white font-bold text-sm flex items-center justify-center gap-2 transition-colors shadow-lg"
                        >
                            <Printer className="w-4 h-4" />
                            Imprimir
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
};

// CSS interno do cupom para a janela de impressão
const CUPOM_CSS = `
.cupom-papel { width: 100%; }
p { margin: 0; padding: 0; }
`;

export default CupomFiscalModal;
