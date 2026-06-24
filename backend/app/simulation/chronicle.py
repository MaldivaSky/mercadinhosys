from datetime import datetime, date, time, timedelta
from sqlalchemy import func
from decimal import Decimal
import random
import uuid
from app.models import (
    db, Estabelecimento, Funcionario, Cliente, Produto, Venda, VendaItem, 
    Pagamento, MovimentacaoEstoque, RegistroPonto, Despesa, 
    DashboardMetrica, HistoricoPrecos, ContaReceber,
    FuncionarioBeneficio, ProdutoLote, Caixa, MovimentacaoCaixa,
    PedidoCompra, PedidoCompraItem, ContaPagar, Entrega, Motorista, Veiculo, TaxaEntrega
)
from app.simulation.dna_factory import DNAFactory, ScenarioDNA
from app.simulation.injectors import RealisticInjector
from app.simulation.enterprise_injector import EnterpriseInjector
from app.simulation.fiscal_simulator import FiscalSimulator
from flask import g

def round_qty(val):
    return Decimal(str(val)).quantize(Decimal("0.001"))

class ChronicleSimulator:
    """O Coração do Gêmeo Digital: Simula a vida de múltiplos Mercadinhos por 6 meses."""
    
    def __init__(self, app):
        self.app = app

    def run_full_simulation(self, months=6):
        print(f"[SIM] [GEMEO DIGITAL] Iniciando Simulação Master de {months} meses...")
        DNAFactory.create_simulation_tenants()
        all_ests = DNAFactory.get_all_tenants()
        
        for est in all_ests:
            dna = self._identify_dna(est)
            print(f"\n[TENANT] {est.nome_fantasia} (ID: {est.id}) | DNA: {dna.nome}")
            RealisticInjector.inject_all_modules(est.id)
            
            admin = Funcionario.query.filter_by(estabelecimento_id=est.id, role="ADMIN").first()
            if not admin: continue
            
            self.simulate_history(est, dna, months, admin.id)
        
        print("\n[OK] [GEMEO DIGITAL] Simulação Master Concluída!")

    def _identify_dna(self, est):
        for key, d in DNAFactory.SCENARIOS.items():
            if d.nome in est.nome_fantasia: return d
        return random.choice(list(DNAFactory.SCENARIOS.values()))

    def simulate_history(self, est, dna, months, admin_id):
        # Injetar Vendedores, Atacado/Varejo
        vendedores_ativos = EnterpriseInjector.inject_sfa_structure(est.id)
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months * 30)
        
        print(f"   [...] Gerando {months*30} dias de transações...")
        
        batch_size = 30
        days_to_simulate = months * 30
        
        for i in range(0, days_to_simulate, batch_size):
            for d_idx in range(i, min(i + batch_size, days_to_simulate)):
                curr_dt = start_date + timedelta(days=d_idx)
                self._simulate_day(est, dna, curr_dt, admin_id)
                
                # Liquidar Fiados e Pagar Contas (Magnitude Senior)
                if curr_dt.day in [10, 20]:
                    self._liquidate_financeiro(est, curr_dt)
            
            db.session.commit()
            print(f"   [DIA] {curr_dt.strftime('%d/%m/%Y')} concluído...")

    def _liquidate_financeiro(self, est, curr_dt):
        """Simula o recebimento de fiados e pagamento de fornecedores."""
        # Receber Fiados (80% de chance para cada conta vencida)
        contas_rec = ContaReceber.query.filter_by(estabelecimento_id=est.id, status="aberto").all()
        for c in contas_rec:
            if c.data_vencimento <= curr_dt.date() and random.random() < 0.8:
                c.status = "pago"
                c.data_recebimento = curr_dt.date()
                c.valor_recebido = c.valor_atual

        # Pagar Fornecedores (Sempre paga no vencimento para manter crédito)
        contas_pag = ContaPagar.query.filter_by(estabelecimento_id=est.id, status="aberto").all()
        for cp in contas_pag:
            if cp.data_vencimento <= curr_dt.date():
                cp.status = "pago"
                cp.data_pagamento = curr_dt.date()
                cp.valor_pago = cp.valor_atual

    def _simulate_day(self, est, dna, dt, admin_id):
        day = dt.day
        wd = dt.weekday()
        
        # 0. Coletar Motoristas e Veículos para Delivery
        motoristas = Motorista.query.filter_by(estabelecimento_id=est.id, ativo=True).all()
        veiculos = Veiculo.query.filter_by(estabelecimento_id=est.id, ativo=True).all()
        taxas = TaxaEntrega.query.filter_by(estabelecimento_id=est.id, ativo=True).all()
        
        # 1. ABERTURA DE CAIXA (07:00)
        abertura_ts = datetime.combine(dt.date(), time(7, 0))
        caixa = Caixa(
            estabelecimento_id=est.id, funcionario_id=admin_id,
            numero_caixa="PDV-01", status="aberto",
            saldo_inicial=Decimal("500.00"), saldo_atual=Decimal("500.00"),
            data_abertura=abertura_ts
        )
        db.session.add(caixa)
        db.session.flush()

        # 1.1 Movimentação de abertura (saldo inicial / troco)
        db.session.add(MovimentacaoCaixa(
            caixa_id=caixa.id, estabelecimento_id=est.id, tipo="abertura",
            valor=caixa.saldo_inicial, forma_pagamento="dinheiro",
            descricao="Abertura de Caixa (troco inicial)", created_at=abertura_ts
        ))

        # 2. RH: Ponto
        if wd < 6:
            funcs = Funcionario.query.filter_by(estabelecimento_id=est.id, ativo=True).all()
            for f in funcs:
                db.session.add(RegistroPonto(
                    estabelecimento_id=est.id, funcionario_id=f.id, data=dt.date(),
                    hora=time(8, random.randint(0,15)), tipo_registro="entrada", status="normal"
                ))
                db.session.add(RegistroPonto(
                    estabelecimento_id=est.id, funcionario_id=f.id, data=dt.date(),
                    hora=time(18, random.randint(0,15)), tipo_registro="saida", status="normal"
                ))

        # 3. FINANCEIRO: Despesas mensais (Dia 1)
        if day == 1:
            self._gerar_despesas_mensais(est, dt)

        # 3.1 Despesas variáveis esporádicas (manutenção, marketing, desnecessárias)
        self._gerar_despesas_esporadicas(est, dt)

        # 4. REABASTECIMENTO (Se o estoque estiver baixo)
        if day % 7 == 0: # Checagem semanal
            self._handle_replenishment(est, dt, admin_id)

        # 5. ALTERAÇÃO DE PREÇOS (Volatility - 5% chance por dia)
        if random.random() < 0.05:
            p = Produto.query.filter_by(estabelecimento_id=est.id).order_by(func.random()).first()
            if p:
                old_venda = p.preco_venda
                p.preco_venda = p.preco_venda * Decimal(str(random.uniform(0.95, 1.10)))
                db.session.add(HistoricoPrecos(
                    estabelecimento_id=est.id, produto_id=p.id, funcionario_id=admin_id,
                    preco_custo_anterior=p.preco_custo, preco_venda_anterior=old_venda,
                    margem_anterior=40, preco_custo_novo=p.preco_custo,
                    preco_venda_novo=p.preco_venda, margem_nova=40,
                    motivo="Ajuste de Mercado (Simulation)", data_alteracao=datetime.combine(dt.date(), time(9,0))
                ))

        # 5. VENDAS: Transações Reais
        products = Produto.query.filter_by(estabelecimento_id=est.id).all()
        clients = Cliente.query.filter_by(estabelecimento_id=est.id).all()
        if products:
            speed = 1.0 if any(s.nome in est.nome_fantasia for s in DNAFactory.SCENARIOS.values()) else 0.2
            qty = int(dna.giro_velocidade * speed * random.uniform(0.7, 1.3))
            
            for _ in range(qty):
                ts = datetime.combine(dt.date(), time(random.randint(7, 21), random.randint(0, 59)))
                venda = self._create_sale(est, ts, caixa, admin_id, products, clients)
                
                # 5.1 SIMULAÇÃO DE DELIVERY (20% de chance)
                if venda and random.random() < 0.20 and motoristas and veiculos:
                    self._create_delivery(est, venda, ts, motoristas, veiculos, taxas)

        # 6. FECHAMENTO DE CAIXA (22:00)
        fechamento_ts = datetime.combine(dt.date(), time(22, 0))
        caixa.status = "fechado"
        caixa.data_fechamento = fechamento_ts
        caixa.saldo_final = caixa.saldo_atual
        db.session.add(MovimentacaoCaixa(
            caixa_id=caixa.id, estabelecimento_id=est.id, tipo="fechamento",
            valor=caixa.saldo_atual, descricao="Fechamento de Caixa Automático",
            created_at=fechamento_ts
        ))

    def _gerar_despesas_mensais(self, est, dt):
        """Despesas FIXAS mensais: aluguel, folha de pagamento, benefícios, contador."""
        d = dt.date()

        # Aluguel
        db.session.add(Despesa(
            estabelecimento_id=est.id, descricao="Aluguel do ponto comercial",
            categoria="Aluguel", tipo="fixa", valor=Decimal("2500.00"),
            data_despesa=d, recorrente=True, forma_pagamento="boleto"
        ))

        # Folha de pagamento (soma dos salários do time)
        funcs = Funcionario.query.filter_by(estabelecimento_id=est.id, ativo=True).all()
        total_folha = sum((Decimal(str(f.salario_base or 0)) for f in funcs), Decimal("0"))
        if total_folha > 0:
            db.session.add(Despesa(
                estabelecimento_id=est.id, descricao=f"Folha de pagamento ({len(funcs)} funcionários)",
                categoria="Folha de Pagamento", tipo="fixa", valor=total_folha,
                data_despesa=d, recorrente=True, forma_pagamento="transferencia"
            ))

        # Benefícios (VT + VA + plano de saúde) por funcionário
        total_beneficios = Decimal("0")
        for f in funcs:
            for fb in FuncionarioBeneficio.query.filter_by(estabelecimento_id=est.id, funcionario_id=f.id, ativo=True).all():
                total_beneficios += Decimal(str(fb.valor or 0))
        if total_beneficios > 0:
            db.session.add(Despesa(
                estabelecimento_id=est.id, descricao="Benefícios (VT, VA, Plano de Saúde)",
                categoria="Benefícios", tipo="fixa", valor=total_beneficios,
                data_despesa=d, recorrente=True, forma_pagamento="boleto"
            ))

        # Contador / contabilidade
        db.session.add(Despesa(
            estabelecimento_id=est.id, descricao="Honorários contábeis",
            categoria="Administrativa", tipo="fixa", valor=Decimal("600.00"),
            data_despesa=d, recorrente=True, forma_pagamento="boleto"
        ))

        # Energia e água (consumo do mês)
        db.session.add(Despesa(
            estabelecimento_id=est.id, descricao="Energia elétrica e água",
            categoria="Utilidades", tipo="variavel",
            valor=Decimal(str(round(random.uniform(800, 1800), 2))),
            data_despesa=d, recorrente=True, forma_pagamento="boleto"
        ))

    def _gerar_despesas_esporadicas(self, est, dt):
        """Despesas VARIÁVEIS esporádicas — incluindo gastos desnecessários para o BI sinalizar."""
        d = dt.date()

        # Manutenção (2% dos dias)
        if random.random() < 0.02:
            db.session.add(Despesa(
                estabelecimento_id=est.id,
                descricao=random.choice(["Conserto de freezer", "Manutenção de balança", "Troca de lâmpadas", "Reparo no ar-condicionado"]),
                categoria="Manutenção", tipo="variavel",
                valor=Decimal(str(round(random.uniform(150, 900), 2))),
                data_despesa=d, forma_pagamento="pix"
            ))

        # Marketing (1.5% dos dias)
        if random.random() < 0.015:
            db.session.add(Despesa(
                estabelecimento_id=est.id,
                descricao=random.choice(["Panfletos promocionais", "Impulsionamento Instagram", "Banner de fachada"]),
                categoria="Marketing", tipo="variavel",
                valor=Decimal(str(round(random.uniform(100, 600), 2))),
                data_despesa=d, forma_pagamento="cartao_credito"
            ))

        # DESPESAS DESNECESSÁRIAS — para o sistema apontar o erro de gestão (3% dos dias)
        if random.random() < 0.03:
            desc, val = random.choice([
                ("Assinatura de streaming na TV da loja", 89.90),
                ("Cafeteira gourmet importada", 1200.00),
                ("Decoração sofisticada não essencial", 850.00),
                ("Almoço executivo do sócio (pessoal)", 320.00),
                ("Aplicativo pago sem uso real", 199.00),
                ("Brindes caros para poucos clientes", 680.00),
            ])
            db.session.add(Despesa(
                estabelecimento_id=est.id, descricao=desc,
                categoria="Despesa Desnecessária", tipo="variavel",
                valor=Decimal(str(val)), data_despesa=d, forma_pagamento="cartao_credito",
                observacoes="Gasto sem retorno para o negócio — revisar"
            ))

    def _handle_replenishment(self, est, dt, admin_id):
        """Simula a recompra de mercadorias quando o estoque baixa."""
        low_stock_prods = Produto.query.filter(
            Produto.estabelecimento_id == est.id,
            Produto.quantidade < 20
        ).limit(10).all()

        if not low_stock_prods: return

        forn = Fornecedor.query.filter_by(estabelecimento_id=est.id).first()
        if not forn: return

        print(f"      [COMPRA] Reabastecendo {len(low_stock_prods)} produtos para {est.nome_fantasia}...")
        
        total_pedido = Decimal("0.00")
        pedido = PedidoCompra(
            estabelecimento_id=est.id, fornecedor_id=forn.id, funcionario_id=admin_id,
            numero_pedido=f"SUP-{uuid.uuid4().hex[:6].upper()}",
            status="recebido", data_pedido=dt, data_recebimento=dt.date()
        )
        db.session.add(pedido)
        db.session.flush()

        for p in low_stock_prods:
            qty_to_buy = 100
            valor_item = p.preco_custo * Decimal(str(qty_to_buy))
            db.session.add(PedidoCompraItem(
                pedido_id=pedido.id, produto_id=p.id, produto_nome=p.nome,
                estabelecimento_id=est.id,
                quantidade_solicitada=Decimal(str(qty_to_buy)),
                quantidade_recebida=Decimal(str(qty_to_buy)),
                preco_unitario=p.preco_custo, total_item=valor_item, status="recebido"
            ))
            p.quantidade += qty_to_buy
            total_pedido += valor_item

        pedido.total = total_pedido

        # Gerar Conta a Pagar (30 dias depois)
        db.session.add(ContaPagar(
            estabelecimento_id=est.id, fornecedor_id=forn.id, pedido_compra_id=pedido.id,
            numero_documento=f"DUP-{pedido.numero_pedido}",
            valor_original=total_pedido, valor_atual=total_pedido,
            data_emissao=dt.date(), data_vencimento=dt.date() + timedelta(days=30),
            status="aberto"
        ))

    def _create_sale(self, est, ts, caixa, admin_id, products, clients):
        client = random.choice(clients) if clients else None
        
        is_b2b = False
        vendedor_id = admin_id
        
        if client and client.observacoes and client.observacoes.startswith('B2B|'):
            is_b2b = True
            vendedor_id = int(client.observacoes.split('|')[1])
        
        tipo_venda = "atacado" if is_b2b else "balcao"
        
        venda = Venda(
            estabelecimento_id=est.id, cliente_id=client.id if client else None, 
            funcionario_id=vendedor_id, caixa_id=caixa.id, data_venda=ts, 
            status="finalizada", tipo_venda=tipo_venda,
            codigo=f"V-{uuid.uuid4().hex[:8].upper()}", subtotal=0, total=0
        )
        db.session.add(venda)
        db.session.flush()
        
        total = Decimal("0.00")
        items_count = random.randint(10, 50) if is_b2b else random.randint(1, 5)
        for p in random.sample(products, min(len(products), items_count)):
            qty = Decimal(str(random.uniform(10, 100))) if is_b2b else Decimal(str(random.uniform(1, 3)))
            
            # Negociação SFA: Vendedor dá desconto em atacado até o preco_minimo
            preco_aplicado = p.preco_venda
            if is_b2b:
                desconto_maximo = float(p.preco_venda - p.preco_minimo)
                desconto_aplicado = random.uniform(0, desconto_maximo)
                preco_aplicado = p.preco_venda - Decimal(str(desconto_aplicado))
                
            item_total = preco_aplicado * qty
            custo_unit = Decimal(str(p.preco_custo or 0))
            margem_real = (preco_aplicado - custo_unit) * qty
            
            db.session.add(VendaItem(
                venda_id=venda.id, produto_id=p.id, produto_nome=p.nome,
                estabelecimento_id=est.id,
                quantidade=round_qty(qty), preco_unitario=preco_aplicado, total_item=item_total,
                custo_unitario=custo_unit, margem_lucro_real=margem_real
            ))
            
            p.quantidade_vendida = (Decimal(str(p.quantidade_vendida or 0)) + qty)
            p.total_vendido = (Decimal(str(p.total_vendido or 0)) + item_total)
            p.ultima_venda = ts
            total += item_total
            
        venda.subtotal = total
        venda.total = total
        venda.quantidade_itens = items_count
        
        # Processamento Fiscal e Financeiro Enterprise
        FiscalSimulator.processar_venda_fiscal_financeira(est.id, venda, ts, tipo_venda, caixa)
        
        return venda

    def _create_delivery(self, est, venda, ts, motoristas, veiculos, taxas):
        """Cria um registro de entrega ultra-realista (Magnitude Senior)."""
        m = random.choice(motoristas)
        v = random.choice(veiculos)
        tx = random.choice(taxas) if taxas else None
        
        dist = Decimal(str(random.uniform(1.5, 12.0)))
        km_total = dist * 2 
        
        # Consumo estimado
        preco_litro = Decimal("5.80")
        consumo = v.consumo_medio or Decimal("15.0")
        custo_fuel = (km_total / consumo) * preco_litro
        
        entrega = Entrega(
            estabelecimento_id=est.id, venda_id=venda.id, cliente_id=venda.cliente_id,
            motorista_id=m.id, veiculo_id=v.id, taxa_entrega_id=tx.id if tx else None,
            codigo_rastreamento=f"TRK{uuid.uuid4().hex[:8].upper()}",
            status="entregue", data_prevista=ts + timedelta(minutes=40),
            data_saida=ts + timedelta(minutes=10), data_entrega=ts + timedelta(minutes=35),
            distancia_km=dist, km_percorridos=km_total,
            custo_combustivel=custo_fuel,
            taxa_entrega=tx.taxa_fixa if tx else Decimal("10.00"),
            endereco_cep=venda.cliente.cep if venda.cliente else "69000-000",
            endereco_logradouro=venda.cliente.logradouro if venda.cliente else "Rua Principal",
            endereco_numero=venda.cliente.numero if venda.cliente else "100",
            endereco_bairro=venda.cliente.bairro if venda.cliente else "Centro",
            endereco_cidade="Manaus", endereco_estado="AM"
        )
        venda.tipo_venda = "delivery"
        m.total_entregas += 1
        v.total_entregas += 1
        db.session.add(entrega)
