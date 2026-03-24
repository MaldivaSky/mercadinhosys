import random
import uuid
from datetime import datetime, date, timedelta, time
from decimal import Decimal, ROUND_HALF_UP
from app.models import (
    db, Venda, VendaItem, Pagamento, MovimentacaoEstoque, 
    Caixa, MovimentacaoCaixa, Produto, Cliente, ProdutoLote,
    HistoricoPrecos, ContaReceber, CategoriaProduto, Funcionario, Despesa, Auditoria
)
from sqlalchemy import func
from app.simulation.dna_factory import DNAFactory
from app.simulation.injectors import RealisticInjector
from flask import g
import json
import os

def round_qty(val):
    if val is None: return Decimal('0.000')
    return Decimal(str(val)).quantize(Decimal('0.000'), rounding=ROUND_HALF_UP)

class ChronicleSimulator:
    """Motor de Simulação MASTER: Cronologia, Lotes, Balança (Peso) e Realidade Brasileira."""
    
    def __init__(self, app):
        self.app = app

    def run_full_simulation(self, months=6):
        with self.app.app_context():
            print(f"INICIANDO GEMEO DIGITAL MASTER: {months} meses de historia pura...")
            
            tenants = DNAFactory.create_simulation_tenants()
            
            for key, est in tenants.items():
                dna = DNAFactory.get_dna(key)
                g.estabelecimento_id = est.id
                
                print(f"Processando DNA {key}: {dna.nome}...")
                
                # Injetar Base Master e Gerar Time Realista
                equipe_info = RealisticInjector.inject_funcionarios_time(est.id, scenario_key=key)
                
                # Obter o ID real do funcionário admin para auditoria master
                admin_username = next(f['u'] for f in equipe_info if f['c'] == "Gerente")
                funcionario_obj = Funcionario.query.filter_by(username=admin_username).first()
                if not funcionario_obj:
                    # Fallback de segurança se falhar a query
                    db.session.commit()
                    funcionario_obj = Funcionario.query.filter_by(username=admin_username).first()
                
                funcionario_id_for_simulation = funcionario_obj.id
                
                # Injetar Infra (Fornecedores e Produtos)
                RealisticInjector.inject_fornecedores(est.id)
                RealisticInjector.inject_clientes(est.id)
                RealisticInjector.inject_produtos_reais(est.id)
                
                # 2. Simular Ciclo de Vida
                self.simulate_history(est, dna, months, funcionario_id_for_simulation)
                
            print("GEMEO DIGITAL: Simulacao Master finalizada com Magnitude Senior!")

    def _sync_lote_vigente(self, produto):
        """Sincroniza os campos lote e data_validade do Produto com o lote FIFO ativo."""
        lote = ProdutoLote.query.filter(
            ProdutoLote.produto_id == produto.id,
            ProdutoLote.quantidade > 0,
            ProdutoLote.ativo == True
        ).order_by(ProdutoLote.data_validade.asc()).first()
        
        if lote:
            produto.lote = lote.numero_lote
            produto.data_validade = lote.data_validade
        else:
            produto.lote = None
            produto.data_validade = None

    def simulate_history(self, est, dna, months, funcionario_id):
        """Simulação de vendas, reajustes, quebras e inadimplência"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months * 30)
        current_date = start_date
        
        # Garantir Caixa Master
        caixa = Caixa.query.filter_by(estabelecimento_id=est.id).order_by(Caixa.id.desc()).first()
        if not caixa:
            caixa = Caixa(
                estabelecimento_id=est.id, funcionario_id=funcionario_id,
                numero_caixa=str(1),
                status="aberto", 
                saldo_inicial=Decimal("5000.00"), 
                saldo_atual=Decimal("5000.00"), 
                data_abertura=start_date
            )
            db.session.add(caixa)
            db.session.commit()

        # Injetar para os listeners
        g.estabelecimento_id = est.id

        try:
            while current_date <= end_date:
                day = current_date.day
                weekday = current_date.weekday()
                
                # Sazonalidade Realista
                multi = 1.6 if day <= 8 else 1.0
                if weekday >= 4: multi *= 1.4
                
                if day == 1:
                    self.apply_economic_pulse(est, current_date, funcionario_id)
                
                if weekday == 0: 
                    self.simulate_inventory_shrinkage(est, current_date)
                
                # Monitoramento Diário de Estoque: Magnitude Senior Proativa
                self.simulate_expiration_and_restock(est, current_date, funcionario_id)

                # Simulação de RH: Ponto e Frequência
                if weekday < 6: # Empresa funciona de Segunda a Sábado no Simulado
                    self.simulate_ponto(est, current_date)

                qty_vendas = int(dna.giro_velocidade * multi * random.uniform(0.8, 1.2))
                
                for _ in range(qty_vendas):
                    ts = current_date + timedelta(hours=random.randint(7, 21), minutes=random.randint(0, 59))
                    try:
                        self.generate_master_sale(est, dna, ts, caixa, funcionario_id)
                    except Exception as e:
                        db.session.rollback()
                        print(f"⚠️ Erro ao gerar venda em {ts}: {str(e)}")
                        continue
                
                db.session.commit()
                if day == 1:
                    try:
                        self.simulate_monthly_expenses(est, dna, current_date, funcionario_id)
                        self.simulate_beneficios(est, current_date)
                    except Exception as e:
                        db.session.rollback()
                        print(f"⚠️ Erro ao simular despesas mensais: {str(e)}")
                    print(f"📅 {dna.nome} | Mês {current_date.month}/{current_date.year} concluído.")
                
                current_date += timedelta(days=1)
        except Exception as e:
            db.session.rollback()
            print(f"❌ ERRO CRÍTICO NA SIMULAÇÃO: {str(e)}")
            raise e

    def simulate_monthly_expenses(self, est, dna, date_obj, funcionario_id):
        """Injeta custos operacionais reais para evitar Lucro = Faturamento."""
        
        # 1. Aluguel e Infra (Varia por DNA)
        base_rent = {
            "Elite": Decimal("12000.00"), "Bom": Decimal("7500.00"), "Razoavel": Decimal("4500.00"), 
            "Mal": Decimal("3000.00"), "Pessimo": Decimal("1500.00")
        }
        rent_val = base_rent.get(dna.nome, Decimal("2000.00")) * Decimal(str(random.uniform(0.9, 1.1)))
        
        infra = [
            ("Aluguel Comercial", rent_val, "fixa"),
            ("Energia Elétrica", (rent_val * Decimal("0.15")).quantize(Decimal("0.01")), "variavel"),
            ("Internet e Software", Decimal("350.00"), "fixa"),
            ("Contabilidade", Decimal("1200.00"), "fixa")
        ]
        
        for desc, val, tipo in infra:
            exp = Despesa(
                estabelecimento_id=est.id, descricao=desc, 
                categoria="Operacional", tipo=tipo, valor=val,
                data_despesa=date_obj.date()
            )
            db.session.add(exp)
            
            # Auditoria de Despesa (Monitor Master)
            meta_exp = Auditoria(
                estabelecimento_id=est.id, usuario_id=funcionario_id,
                tipo_evento="despesas_insert",
                descricao=f"Despesa registrada: {desc} (R$ {val:.2f})",
                valor=val, data_evento=date_obj,
                detalhes_json={"categoria": "Operacional", "tipo": tipo}
            )
            db.session.add(meta_exp)

        # 2. Folha de Pagamento (Baseado nos funcionários reais)
        equipe = Funcionario.query.filter_by(estabelecimento_id=est.id, ativo=True).all()
        for f in equipe:
            salario = Decimal(str(f.salario_base or "1412.00"))
            custo_total = (salario * Decimal("1.30")).quantize(Decimal("0.01"))
            exp = Despesa(
                estabelecimento_id=est.id, descricao=f"Folha de Pagamento - {f.nome}",
                categoria="RH", tipo="fixa", valor=custo_total,
                data_despesa=date_obj.date()
            )
            db.session.add(exp)
            
            aud_rh = Auditoria(
                estabelecimento_id=est.id, usuario_id=funcionario_id,
                tipo_evento="despesas_insert",
                descricao=f"Folha de Pagamento: {f.nome} (R$ {custo_total:.2f})",
                valor=custo_total, data_evento=date_obj,
                detalhes_json={"categoria": "RH", "funcionario": f.nome}
            )
            db.session.add(aud_rh)

        # 3. Impostos (Simples Nacional aproximado: 10% do faturamento)
        start_month = date_obj - timedelta(days=30)
        from app.models import Venda
        revenue = db.session.query(func.sum(Venda.total)).filter(
            Venda.estabelecimento_id == est.id,
            Venda.data_venda >= start_month,
            Venda.data_venda < date_obj,
            Venda.status == 'finalizada'
        ).scalar() or Decimal("0.00")
        
        imposto = (Decimal(str(revenue)) * Decimal("0.10")).quantize(Decimal("0.01"))
        if imposto > 0:
            exp = Despesa(
                estabelecimento_id=est.id, descricao="Impostos (Simples Nacional)",
                categoria="Tributário", tipo="variavel", valor=imposto,
                data_despesa=date_obj.date()
            )
            db.session.add(exp)
            
            aud_tax = Auditoria(
                estabelecimento_id=est.id, usuario_id=funcionario_id,
                tipo_evento="despesas_insert",
                descricao=f"Impostos provisionados (R$ {imposto:.2f})",
                valor=imposto, data_evento=date_obj,
                detalhes_json={"categoria": "Tributário", "base_calculo": float(revenue)}
            )
            db.session.add(aud_tax)

    def simulate_ponto(self, est, date_obj):
        """Simula batidas de ponto realistas para toda a equipe"""
        from app.models import RegistroPonto, Funcionario
        equipe = Funcionario.query.filter_by(estabelecimento_id=est.id, ativo=True).all()
        
        for f in equipe:
            # Pular se for domingo (já filtrado na chamada, mas segurança extra)
            if date_obj.weekday() == 6: continue
            
            # 1. Entrada (07:50 - 08:15)
            h_in = 8
            m_in = random.randint(-10, 15)
            # Atraso ocasional
            if random.random() < 0.05: m_in += random.randint(15, 60)
            
            ts_in = datetime.combine(date_obj.date(), time(h_in + (1 if m_in >= 60 else 0), m_in % 60))
            
            p_in = RegistroPonto(
                estabelecimento_id=est.id, funcionario_id=f.id,
                data=date_obj.date(), hora=ts_in.time(),
                tipo_registro="entrada", status="normal" if m_in <= 10 else "atraso",
                minutos_atraso=max(0, m_in - 5)
            )
            db.session.add(p_in)
            
            # 2. Almoço Saída (12:00)
            ts_out_lunch = datetime.combine(date_obj.date(), time(12, random.randint(0, 5)))
            p_out_l = RegistroPonto(
                estabelecimento_id=est.id, funcionario_id=f.id,
                data=date_obj.date(), hora=ts_out_lunch.time(),
                tipo_registro="intervalo_saida"
            )
            db.session.add(p_out_l)
            
            # 3. Almoço Retorno (13:00)
            ts_in_lunch = datetime.combine(date_obj.date(), time(13, random.randint(0, 5)))
            p_in_l = RegistroPonto(
                estabelecimento_id=est.id, funcionario_id=f.id,
                data=date_obj.date(), hora=ts_in_lunch.time(),
                tipo_registro="intervalo_retorno"
            )
            db.session.add(p_in_l)
            
            # 4. Saída (17:30 - 18:30)
            h_out = 17
            m_out = random.randint(30, 90) # 17:30 até 18:30
            ts_out = datetime.combine(date_obj.date(), time(h_out + (1 if m_out >= 60 else 0), m_out % 60))
            
            p_out = RegistroPonto(
                estabelecimento_id=est.id, funcionario_id=f.id,
                data=date_obj.date(), hora=ts_out.time(),
                tipo_registro="saida"
            )
            db.session.add(p_out)

    def simulate_beneficios(self, est, date_obj):
        """Simula pagamento de benefícios (Vale Refeição, VT, etc)"""
        from app.models import Beneficio, Funcionario, Despesa
        equipe = Funcionario.query.filter_by(estabelecimento_id=est.id, ativo=True).all()
        
        for f in equipe:
            # Vale Refeição (R$ 600)
            vr = Decimal("600.00")
            exp_vr = Despesa(
                estabelecimento_id=est.id, descricao=f"Vale Refeição - {f.nome}",
                categoria="RH", tipo="fixa", valor=vr,
                data_despesa=date_obj.date()
            )
            db.session.add(exp_vr)
            
            # Vale Transporte (R$ 250)
            vt = Decimal("250.00")
            exp_vt = Despesa(
                estabelecimento_id=est.id, descricao=f"Vale Transporte - {f.nome}",
                categoria="RH", tipo="fixa", valor=vt,
                data_despesa=date_obj.date()
            )
            db.session.add(exp_vt)

    def apply_economic_pulse(self, est, date_obj, funcionario_id):
        """Reajustes de preços mensais (Inflação real brasileira)"""
        prods = Produto.query.filter_by(estabelecimento_id=est.id).limit(10).all()
        pulse = random.uniform(1.005, 1.03) # 0.5% a 3%
        for p in prods:
            old_v, old_c = p.preco_venda, p.preco_custo
            p.preco_venda *= Decimal(str(pulse))
            p.preco_custo *= Decimal(str(pulse))
            m_old = Produto.calcular_markup_de_preco(old_c, old_v)
            m_new = Produto.calcular_markup_de_preco(p.preco_custo, p.preco_venda)
            
            h = HistoricoPrecos(
                estabelecimento_id=est.id, produto_id=p.id,
                funcionario_id=funcionario_id,
                preco_custo_anterior=old_c, preco_venda_anterior=old_v,
                margem_anterior=m_old,
                preco_custo_novo=p.preco_custo, preco_venda_novo=p.preco_venda,
                margem_nova=m_new,
                data_alteracao=date_obj, motivo="Reajuste Master (Mercado)"
            )
            db.session.add(h)

    def simulate_inventory_shrinkage(self, est, date_obj):
        """Simula perdas e quebras de perecíveis (Senior ERP Logic)"""
        perishables = Produto.query.join(CategoriaProduto).filter(
            Produto.estabelecimento_id == est.id,
            CategoriaProduto.nome.in_(["Açougue", "Hortifruti", "Padaria"]),
            Produto.quantidade > 0
        ).all()
        
        for p in perishables:
            # Perda de 0.5% a 2% por semana
            quebra = float(p.quantidade) * random.uniform(0.005, 0.02)
            if quebra <= 0.001: continue # Evita micro-perdas irrelevantes
            
            quebra_decimal = round_qty(quebra)
            ant = round_qty(p.quantidade)
            
            # Consome do estoque via FIFO para garantir integridade dos lotes
            lotes_afetados = p.consumir_estoque_fifo(quebra_decimal)
            atu = p.quantidade

            # Registrar Movimentação
            lote_id = lotes_afetados[0]['lote_id'] if lotes_afetados else None
            mov = MovimentacaoEstoque(
                estabelecimento_id=est.id, produto_id=p.id,
                quantidade=quebra_decimal, tipo="saida", motivo="QUEBRA/PERDA NATURAL (AVARIA)",
                quantidade_anterior=ant, quantidade_atual=atu,
                lote_id=lote_id, created_at=date_obj
            )
            db.session.add(mov)

            # Sincroniza informações de lote no produto
            self._sync_lote_vigente(p)

            # Gerar Despesa de Prejuízo (Realismo Financeiro)
            valor_prejuizo = (quebra_decimal * p.preco_custo).quantize(Decimal("0.01"))
            if valor_prejuizo > 0:
                exp = Despesa(
                    estabelecimento_id=est.id, 
                    descricao=f"Prejuízo/Quebra: {p.nome} ({quebra_decimal} {p.unidade_medida})",
                    categoria="Prejuízo Produtos", tipo="variavel", valor=valor_prejuizo,
                    data_despesa=date_obj.date(), forma_pagamento="Ajuste de Estoque"
                )
                db.session.add(exp)

                aud = Auditoria(
                    estabelecimento_id=est.id, tipo_evento="estoque_ajuste",
                    descricao=f"Perda/Quebra registrada: {p.nome} - Prejuízo: R$ {valor_prejuizo}",
                    valor=valor_prejuizo, data_evento=date_obj,
                    detalhes_json={"produto": p.nome, "quantidade": float(quebra_decimal)}
                )
                db.session.add(aud)

    def simulate_expiration_and_restock(self, est, date_obj, funcionario_id):
        from app.models import Fornecedor, PedidoCompra, PedidoCompraItem, Produto, ProdutoLote, ContaPagar, Auditoria
        import json
        
        # 1. Romover Vencidos
        vencidos = ProdutoLote.query.filter(
            ProdutoLote.estabelecimento_id == est.id,
            ProdutoLote.quantidade > 0,
            ProdutoLote.data_validade < date_obj.date()
        ).all()
        
        for lote in vencidos:
            produto = Produto.query.get(lote.produto_id)
            if not produto: continue
            
            qtd_perdida = round_qty(lote.quantidade)
            lote.quantidade = 0
            lote.ativo = False
            lote.motivo_inativacao = "Validade expirada"
            
            ant = round_qty(produto.quantidade)
            produto.quantidade = round_qty(ant - qtd_perdida)
            atu = produto.quantidade
            
            mov = MovimentacaoEstoque(
                estabelecimento_id=est.id, produto_id=produto.id,
                quantidade=qtd_perdida, tipo="saida", motivo="DESCARTE: PRODUTO VENCIDO",
                quantidade_anterior=ant, quantidade_atual=atu,
                lote_id=lote.id, created_at=date_obj
            )
            db.session.add(mov)

            # Sincroniza informações de lote no produto
            self._sync_lote_vigente(produto)

            # Financeiro: Registro de Prejuízo
            valor_perda = (qtd_perdida * lote.preco_custo_unitario).quantize(Decimal("0.01"))
            if valor_perda > 0:
                exp = Despesa(
                    estabelecimento_id=est.id,
                    descricao=f"Descarte Vencimento: {produto.nome} (Lote {lote.numero_lote})",
                    categoria="Prejuízo Produtos", tipo="variavel", valor=valor_perda,
                    data_despesa=date_obj.date(), forma_pagamento="Ajuste de Estoque"
                )
                db.session.add(exp)

                aud = Auditoria(
                    estabelecimento_id=est.id, usuario_id=funcionario_id,
                    tipo_evento="estoque_ajuste",
                    descricao=f"Produto Vencido Descartado: {produto.nome} (R$ {valor_perda})",
                    valor=valor_perda, data_evento=date_obj,
                    detalhes_json={"lote": lote.numero_lote, "motivo": "vencimento"}
                )
                db.session.add(aud)

        db.session.commit()
        
        db.session.commit()
        
        # 2. Processar Recebimentos Pendentes (Realismo Senior: O pedido leva tempo para chegar)
        pedidos_pendentes = PedidoCompra.query.filter(
            PedidoCompra.estabelecimento_id == est.id,
            PedidoCompra.status == "pendente",
            PedidoCompra.data_previsao_entrega <= date_obj.date()
        ).all()
        
        for pedido in pedidos_pendentes:
            pedido.status = "recebido"
            pedido.data_recebimento = date_obj.date()
            
            # Ao receber, gera a despesa/conta a pagar
            cp = ContaPagar(
                estabelecimento_id=est.id,
                fornecedor_id=pedido.fornecedor_id,
                pedido_compra_id=pedido.id,
                numero_documento=f"DUP-{pedido.numero_pedido}",
                observacoes=f"Recebimento de Mercadorias: {pedido.numero_pedido}",
                valor_original=pedido.total,
                valor_atual=pedido.total,
                data_emissao=date_obj.date(),
                data_vencimento=date_obj.date() + timedelta(days=30),
                status="pago" if (date_obj.date() + timedelta(days=30)) < datetime.now().date() else "aberto",
                created_at=date_obj
            )
            db.session.add(cp)
            
            # Registrar Entrada de Estoque por Itens do Pedido
            for pi in pedido.itens: # Assume que PedidoCompra tem relacionamento 'itens'
                p = pi.produto
                if not p: continue
                
                qtd = pi.quantidade_recebida # Aqui assume que o software permite conferência
                custo = pi.preco_unitario
                
                # Criar Lote ao Receber
                lote = ProdutoLote(
                    estabelecimento_id=est.id,
                    produto_id=p.id,
                    numero_lote=f"L{date_obj.strftime('%Y%m%d')}-{p.id}-{random.randint(1000,9999)}",
                    quantidade=pi.quantidade_recebida,
                    quantidade_inicial=pi.quantidade_recebida,
                    preco_custo_unitario=pi.preco_unitario,
                    data_fabricacao=date_obj.date() - timedelta(days=random.randint(5, 30)),
                    data_validade=date_obj.date() + timedelta(days=random.randint(15, 180)),
                    ativo=True,
                    created_at=date_obj
                )
                db.session.add(lote)
                db.session.flush()
                
                ant = round_qty(p.quantidade)
                p.quantidade = round_qty(ant + Decimal(str(pi.quantidade_recebida)))
                atu = p.quantidade
                
                mov = MovimentacaoEstoque(
                    estabelecimento_id=est.id, produto_id=p.id,
                    quantidade=pi.quantidade_recebida, tipo="entrada", motivo=f"Recebimento PC {pedido.numero_pedido}",
                    quantidade_anterior=ant, quantidade_atual=atu,
                    pedido_compra_id=pedido.id, lote_id=lote.id,
                    created_at=date_obj
                )
                db.session.add(mov)
                self._sync_lote_vigente(p)

            db.session.commit()

        # 3. Gerar Novos Pedidos (Estoque < Mínimo)
        produtos_baixo_estoque = Produto.query.filter(
            Produto.estabelecimento_id == est.id,
            Produto.quantidade <= Produto.quantidade_minima
        ).all()
        
        if not produtos_baixo_estoque:
            return
            
        fornecedores_disponiveis = Fornecedor.query.filter_by(estabelecimento_id=est.id).all()
        if not fornecedores_disponiveis: return
        
        pedidos_por_forn = {}
        for p in produtos_baixo_estoque:
            # Evita duplicar pedido se já houver um pendente para este produto
            ja_pedido = db.session.query(PedidoCompraItem).join(PedidoCompra).filter(
                PedidoCompra.estabelecimento_id == est.id,
                PedidoCompra.status == 'pendente',
                PedidoCompraItem.produto_id == p.id
            ).first()
            if ja_pedido: continue

            forn = random.choice(fornecedores_disponiveis)
            if forn.id not in pedidos_por_forn:
                pedidos_por_forn[forn.id] = []
            
            qtd_comprar = float(p.quantidade_minima) * random.uniform(2.0, 4.0)
            if p.unidade_medida != "KG":
                if qtd_comprar < 10: qtd_comprar = 20
                qtd_comprar = int(qtd_comprar)
            else:
                if qtd_comprar < 5: qtd_comprar = 10.0
                qtd_comprar = round(qtd_comprar, 3)
            
            pedidos_por_forn[forn.id].append({
                'produto': p,
                'qtd': qtd_comprar,
                'custo': float(p.preco_custo) if p.preco_custo else 5.0
            })
            
        for forn_id, itens in pedidos_por_forn.items():
            if not itens: continue
            
            valor_total = sum([i['qtd'] * i['custo'] for i in itens])
            pedido = PedidoCompra(
                estabelecimento_id=est.id,
                fornecedor_id=forn_id,
                funcionario_id=funcionario_id,
                numero_pedido=f"PC-{uuid.uuid4().hex[:6].upper()}",
                data_pedido=date_obj,
                data_previsao_entrega=date_obj.date() + timedelta(days=random.randint(2, 5)),
                status="pendente", # REALISMO: Inicia como pendente
                total=valor_total,
                created_at=date_obj
            )
            db.session.add(pedido)
            db.session.flush()

            # Auditoria de Compra
            auditoria_compra = Auditoria(
                estabelecimento_id=est.id,
                usuario_id=funcionario_id,
                tipo_evento="pedido_compra",
                descricao=f"Pedido de Compra Automático {pedido.numero_pedido} gerado (Estoque Baixo)",
                valor=valor_total,
                data_evento=date_obj,
                detalhes_json={"fornecedor_id": forn_id, "itens": len(itens)}
            )
            db.session.add(auditoria_compra)
            
            for item in itens:
                p = item['produto']
                qtd = item['qtd']
                custo = item['custo']
                
                pi = PedidoCompraItem(
                    pedido_id=pedido.id,
                    produto_id=p.id,
                    produto_nome=p.nome,
                    produto_unidade=p.unidade_medida,
                    quantidade_solicitada=qtd,
                    quantidade_recebida=qtd, # Previsão
                    preco_unitario=custo,
                    total_item=qtd * custo
                )
                db.session.add(pi)

    def generate_master_sale(self, est, dna, ts, caixa, funcionario_id):
        # Selecionar cesta de compras (1 a 15 produtos)
        num_items = random.randint(1, 15)
        available = Produto.query.filter(Produto.estabelecimento_id == est.id, Produto.quantidade > 0.001).limit(50).all()
        if not available: return
        
        basket = random.sample(available, min(len(available), num_items))
        
        cliente = Cliente.query.filter_by(estabelecimento_id=est.id).order_by(db.func.random()).first()
        cliente = cliente if random.random() < 0.4 else None # 40% identificados
        
        # DNA Social: Inadimplência e Propensão ao Fiado
        forma = random.choice(["dinheiro", "pix", "cartao_debito", "cartao_credito"])
        
        # Chance de ser fiado baseada no DNA (Elite raramente, Péssimo frequentemente)
        propensao_fiado = dna.inadimplencia_rate * 1.5 
        if cliente and random.random() < propensao_fiado:
            forma = "fiado"
        
        if not g.get('estabelecimento_id'):
            g.estabelecimento_id = est.id

        venda = Venda(
            estabelecimento_id=est.id, cliente_id=cliente.id if cliente else None,
            funcionario_id=funcionario_id, codigo=f"V-{uuid.uuid4().hex[:12].upper()}",
            status="finalizada", data_venda=ts, created_at=ts, forma_pagamento=forma
        )
        db.session.add(venda)
        db.session.flush()
        
        total_venda = Decimal("0.00")
        items_count = 0
        for p in basket:
            # Selecionar lote FIFO MASTER
            lote = ProdutoLote.query.filter(
                ProdutoLote.produto_id == p.id, 
                ProdutoLote.quantidade > 0,
                ProdutoLote.data_validade >= ts.date()
            ).order_by(ProdutoLote.data_validade.asc()).first()
            
            if not lote: continue
            
            if p.unidade_medida == "KG":
                # Pesagem real: carne varia de 300g a 2.5kg normalmente no varejo
                qtd = round(random.uniform(0.200, 3.500), 3)
            else:
                qtd = random.randint(1, 6)
            
            # BLOQUEIO ANTI-NEGATIVO: Não vende o que não tem. ERP Realism.
            qtd_disponivel = float(lote.quantidade)
            if qtd > qtd_disponivel:
                qtd = qtd_disponivel
                
            if qtd <= 0: continue
            
            preco_un = p.preco_venda * Decimal(str(random.uniform(0.98, 1.02)))
            total_item = (preco_un * Decimal(str(qtd))).quantize(Decimal("0.01"))
            
            custo_un = lote.preco_custo_unitario or Decimal("0.00")
            margem_item = preco_un - custo_un
            lucro_real = (margem_item * Decimal(str(qtd))).quantize(Decimal("0.01"))
            
            vi = VendaItem(
                venda_id=venda.id, produto_id=p.id, produto_nome=p.nome,
                produto_codigo=p.codigo_barras, produto_unidade=p.unidade_medida,
                quantidade=qtd, preco_unitario=preco_un, total_item=total_item,
                custo_unitario=custo_un, margem_item=margem_item,
                margem_lucro_real=lucro_real,
                created_at=ts
            )
            db.session.add(vi)
            
            # Subtração Blindada (Simulation)
            lote.quantidade = round_qty(lote.quantidade - Decimal(str(qtd)))
            
            ant = round_qty(p.quantidade)
            p.quantidade = round_qty(ant - Decimal(str(qtd)))
            atu = p.quantidade
            
            total_venda += total_item
            items_count += 1
            
            mov = MovimentacaoEstoque(
                estabelecimento_id=est.id, produto_id=p.id, 
                quantidade=qtd, tipo="saida", motivo=f"Venda {venda.codigo}",
                quantidade_anterior=ant, quantidade_atual=atu,
                venda_id=venda.id, lote_id=lote.id,
                created_at=ts
            )
            db.session.add(mov)
            self._sync_lote_vigente(p)

        if items_count == 0:
            db.session.delete(venda)
            # Rollback flush effect
            return

        venda.total = total_venda
        venda.subtotal = total_venda
        venda.quantidade_itens = items_count
        
        # Auditoria de Venda (Monitor Master)
        aud_venda = Auditoria(
            estabelecimento_id=est.id,
            usuario_id=funcionario_id,
            tipo_evento="vendas_insert",
            descricao=f"Venda {venda.codigo} finalizada com sucesso (Total: R$ {total_venda:.2f})",
            valor=total_venda,
            data_evento=ts,
            detalhes_json={"forma_pagamento": forma, "itens": len(basket)}
        )
        db.session.add(aud_venda)
        
        # Financeiro Master
        if forma == "fiado":
            vencido = random.random() < dna.inadimplencia_rate
            cr = ContaReceber(
                estabelecimento_id=est.id, cliente_id=cliente.id,
                venda_id=venda.id, # VÍNCULO MASTER
                numero_documento=f"DUP-{venda.codigo}",
                observacoes=f"Venda {venda.codigo} - {cliente.nome}",
                valor_original=total_venda, valor_atual=total_venda,
                data_emissao=ts.date(),
                data_vencimento=ts.date() + timedelta(days=30),
                status="atrasado" if vencido and (ts.date() + timedelta(days=30)) < date.today() else "aberto",
                created_at=ts
            )
            db.session.add(cr)
        else:
            if forma == "dinheiro":
                caixa.saldo_atual += Decimal(str(total_venda))
                mc = MovimentacaoCaixa(
                    caixa_id=caixa.id, 
                    estabelecimento_id=est.id,
                    tipo="entrada", valor=total_venda,
                    forma_pagamento="dinheiro", venda_id=venda.id,
                    descricao=f"Venda {venda.codigo}",
                    created_at=ts
                )
                db.session.add(mc)
            
            pag = Pagamento(
                venda_id=venda.id, estabelecimento_id=est.id,
                forma_pagamento=forma, valor=total_venda,
                status="aprovado", data_pagamento=ts
            )
            db.session.add(pag)

