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
from flask import g

def round_qty(val):
    return Decimal(str(val)).quantize(Decimal("0.001"))

class ChronicleSimulator:
    """O Coração do Gêmeo Digital: Simula a vida de múltiplos Mercadinhos por 6 meses."""
    
    def __init__(self, app):
        self.app = app

    def run_full_simulation(self, months=6):
        print(f"🚀 [GEMEO DIGITAL] Iniciando Simulação Master de {months} meses...")
        DNAFactory.create_simulation_tenants()
        all_ests = DNAFactory.get_all_tenants()
        
        for est in all_ests:
            dna = self._identify_dna(est)
            print(f"\n🏢 {est.nome_fantasia} (ID: {est.id}) | DNA: {dna.nome}")
            RealisticInjector.inject_all_modules(est.id)
            
            admin = Funcionario.query.filter_by(estabelecimento_id=est.id, role="ADMIN").first()
            if not admin: continue
            
            self.simulate_history(est, dna, months, admin.id)
        
        print("\n🎉 [GEMEO DIGITAL] Simulação Master Concluída!")

    def _identify_dna(self, est):
        for key, d in DNAFactory.SCENARIOS.items():
            if d.nome in est.nome_fantasia: return d
        return random.choice(list(DNAFactory.SCENARIOS.values()))

    def simulate_history(self, est, dna, months, admin_id):
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months * 30)
        
        print(f"   ⏳ Gerando {months*30} dias de transações...")
        
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
            print(f"   📅 {curr_dt.strftime('%d/%m/%Y')} concluído...")

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

        # 3. FINANCEIRO: Despesas Fixas (Dia 1)
        if day == 1:
            db.session.add(Despesa(
                estabelecimento_id=est.id, descricao="Aluguel Mensal", categoria="Fixo", 
                valor=Decimal("2500.00"), data_despesa=dt.date()
            ))
            # Despesas Desnecessárias (Magnitude Sênior)
            if random.random() < 0.3:
                db.session.add(Despesa(
                    estabelecimento_id=est.id, descricao="Assinatura Software Gourmet", 
                    categoria="Variavel", valor=Decimal("450.00"), data_despesa=dt.date()
                ))

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

    def _handle_replenishment(self, est, dt, admin_id):
        """Simula a recompra de mercadorias quando o estoque baixa."""
        low_stock_prods = Produto.query.filter(
            Produto.estabelecimento_id == est.id,
            Produto.quantidade < 20
        ).limit(10).all()

        if not low_stock_prods: return

        forn = Fornecedor.query.filter_by(estabelecimento_id=est.id).first()
        if not forn: return

        print(f"      🛒 Reabastecendo {len(low_stock_prods)} produtos para {est.nome_fantasia}...")
        
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
        
        # Diversidade de Pagamento baseada em DNA
        # 10% de chance de Fiado (ContaReceber) se for ELITE/BOM
        is_fiado = random.random() < 0.10 and client is not None
        forma_pgto = "fiado" if is_fiado else random.choice(["dinheiro", "cartao_debito", "cartao_credito", "pix"])
        
        venda = Venda(
            estabelecimento_id=est.id, cliente_id=client.id if client else None, 
            funcionario_id=admin_id, caixa_id=caixa.id, data_venda=ts, 
            status="finalizada", tipo_venda="balcao",
            codigo=f"V-{uuid.uuid4().hex[:8].upper()}", subtotal=0, total=0
        )
        db.session.add(venda)
        db.session.flush()
        
        total = Decimal("0.00")
        items_count = random.randint(1, 5)
        for p in random.sample(products, min(len(products), items_count)):
            qty = Decimal(str(random.uniform(1, 3)))
            item_total = p.preco_venda * qty
            db.session.add(VendaItem(
                venda_id=venda.id, produto_id=p.id, produto_nome=p.nome,
                estabelecimento_id=est.id,
                quantidade=round_qty(qty), preco_unitario=p.preco_venda, total_item=item_total
            ))
            total += item_total
            
        venda.subtotal = total
        venda.total = total
        venda.quantidade_itens = items_count
        
        if is_fiado:
            # Gerar Conta a Receber
            db.session.add(ContaReceber(
                estabelecimento_id=est.id, cliente_id=client.id, venda_id=venda.id,
                numero_documento=f"DUP-{venda.codigo}", valor_original=total, valor_atual=total,
                data_emissao=ts.date(), data_vencimento=ts.date() + timedelta(days=30),
                status="aberto"
            ))
        else:
            # Pagamento Imediato
            db.session.add(Pagamento(
                venda_id=venda.id, estabelecimento_id=est.id, valor=total, 
                forma_pagamento=forma_pgto, status="aprovado", data_pagamento=ts
            ))
            
            # Movimentação de Caixa (Apenas se for Dinheiro ou PIX entra no saldo imediato)
            if forma_pgto in ["dinheiro", "pix"]:
                db.session.add(MovimentacaoCaixa(
                    caixa_id=caixa.id, estabelecimento_id=est.id, tipo="entrada",
                    valor=total, venda_id=venda.id, descricao=f"Venda {venda.codigo}",
                    created_at=ts
                ))
                caixa.saldo_atual += total
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
