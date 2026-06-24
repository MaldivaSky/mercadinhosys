import random
import uuid
from decimal import Decimal
from datetime import timedelta
from app.models import db, DocumentoFiscal, ContaReceber, Pagamento, MovimentacaoCaixa

class FiscalSimulator:
    """
    Simulador Fiscal e Financeiro Enterprise.
    Forja NFe (Modelo 55) para Atacado, NFCe (Modelo 65) para Varejo, 
    e opera como um webhook falso do Efí Bank para Contas a Receber (Boletos/Pix).
    """

    @classmethod
    def processar_venda_fiscal_financeira(cls, est_id, venda, ts, tipo_venda, caixa):
        """
        Recebe uma venda recém-criada, emite o documento fiscal apropriado
        e gera a estrutura financeira de cobrança (Boletos B2B ou Pix B2C).
        """
        if tipo_venda == 'atacado':
            cls._emitir_nfe_b2b(est_id, venda, ts)
            cls._gerar_cobranca_efi_bank(est_id, venda, ts, caixa)
        else:
            cls._emitir_nfce_b2c(est_id, venda, ts)
            cls._pagamento_imediato_varejo(est_id, venda, ts, caixa)

    @classmethod
    def _emitir_nfe_b2b(cls, est_id, venda, ts):
        """Emite NF-e Modelo 55 (Atacado)"""
        chave = f"35{ts.strftime('%y%m')}{est_id:014d}55001{random.randint(100000000, 999999999)}1"
        doc = DocumentoFiscal(
            estabelecimento_id=est_id,
            venda_id=venda.id,
            referencia=f"NFE-{venda.codigo}",
            tipo="nfe",
            status="autorizado",
            ambiente="producao",
            chave_acesso=chave,
            protocolo=f"135{random.randint(10000000000, 99999999999)}",
            valor_total=venda.total,
            xml_autorizado="<xml>Mock NFe Produção</xml>",
            danfe_url=f"https://nfe.fazenda.gov.br/portal/danfe?chave={chave}",
            data_emissao=ts
        )
        db.session.add(doc)

    @classmethod
    def _emitir_nfce_b2c(cls, est_id, venda, ts):
        """Emite NFC-e Modelo 65 (Varejo) - 80% de chance para simular sonegação ou não emissão"""
        if random.random() > 0.80: return
        
        chave = f"35{ts.strftime('%y%m')}{est_id:014d}65001{random.randint(100000000, 999999999)}1"
        doc = DocumentoFiscal(
            estabelecimento_id=est_id,
            venda_id=venda.id,
            referencia=f"NFCE-{venda.codigo}",
            tipo="nfce",
            status="autorizado",
            ambiente="producao",
            chave_acesso=chave,
            protocolo=f"135{random.randint(10000000000, 99999999999)}",
            valor_total=venda.total,
            xml_autorizado="<xml>Mock NFCe Produção</xml>",
            danfe_url=f"https://nfce.fazenda.gov.br/portal/danfe?chave={chave}",
            data_emissao=ts
        )
        db.session.add(doc)

    @classmethod
    def _gerar_cobranca_efi_bank(cls, est_id, venda, ts, caixa):
        """Simula a geração de um Boleto 30 dias via API do Efí Bank (Faturado B2B)"""
        cr = ContaReceber(
            estabelecimento_id=est_id,
            cliente_id=venda.cliente_id,
            venda_id=venda.id,
            numero_documento=f"BOL-{venda.codigo}",
            valor_original=venda.total,
            valor_atual=venda.total,
            data_emissao=ts.date(),
            data_vencimento=(ts + timedelta(days=30)).date(),
            status="aberto",
            observacoes="Boleto Efí Bank Gerado via API"
        )
        db.session.add(cr)
        
        # Pagamento tipo FIADO (Faturado), não entra no caixa imediatamente
        db.session.add(Pagamento(
            venda_id=venda.id, estabelecimento_id=est_id, valor=venda.total,
            forma_pagamento="boleto", status="pendente", data_pagamento=ts
        ))

    @classmethod
    def _pagamento_imediato_varejo(cls, est_id, venda, ts, caixa):
        """Varejo paga na hora no Balcão. PIX, Débito, Crédito, Dinheiro."""
        forma = random.choice(["pix", "cartao_debito", "cartao_credito", "dinheiro"])
        db.session.add(Pagamento(
            venda_id=venda.id, estabelecimento_id=est_id, valor=venda.total,
            forma_pagamento=forma, status="aprovado", data_pagamento=ts
        ))
        
        db.session.add(MovimentacaoCaixa(
            caixa_id=caixa.id, estabelecimento_id=est_id, tipo="venda",
            valor=venda.total, forma_pagamento=forma, venda_id=venda.id,
            descricao=f"Venda Balcão {venda.codigo}", created_at=ts
        ))
        
        if forma == "dinheiro":
            caixa.saldo_atual += venda.total
