import random
import uuid
from datetime import datetime, date, timedelta
from decimal import Decimal
from app.models import (
    db, Venda, VendaItem, Pagamento, MovimentacaoEstoque, 
    Caixa, MovimentacaoCaixa, Produto, Cliente, ProdutoLote,
    HistoricoPrecos, ContaReceber, CategoriaProduto, Funcionario, Despesa
)
from sqlalchemy import func
from app.simulation.dna_factory import DNAFactory
from app.simulation.injectors import RealisticInjector
from flask import g

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
                equipe_info = RealisticInjector.inject_funcionarios_time(est.id)
                
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
                numero_caixa=1,
                status="aberto", saldo_inicial=5000.0, saldo_atual=5000.0, 
                data_abertura=start_date
            )
            db.session.add(caixa)
            db.session.commit()

        # Injetar para os listeners
        g.estabelecimento_id = est.id

        while current_date <= end_date:
            day = current_date.day
            weekday = current_date.weekday()
            
            # Sazonalidade Realista
            # 1. Quinto dia útil (Salário)
            multi = 1.6 if day <= 8 else 1.0
            # 2. Fim de semana (Churrasco/Lazer)
            if weekday >= 4: multi *= 1.4
            
            # Pulsos de Inflação / Reajuste
            if day == 1:
                self.apply_economic_pulse(est, current_date, funcionario_id)
            
            # Simular "Quebras de Estoque" (Perda natural em Hortifruti/Açougue) e Produtos Vencidos/Reabastecimento
            if weekday == 0: # Toda segunda confere quebra
                self.simulate_inventory_shrinkage(est, current_date)
            
            # Check estoque e vencimentos terças e sextas
            if weekday in (1, 4):
                self.simulate_expiration_and_restock(est, current_date, funcionario_id)

            qty_vendas = int(dna.giro_velocidade * multi * random.uniform(0.8, 1.2))
            
            for _ in range(qty_vendas):
                ts = current_date + timedelta(hours=random.randint(7, 21), minutes=random.randint(0, 59))
                self.generate_master_sale(est, dna, ts, caixa, funcionario_id)
            
            db.session.commit()
            if day == 1:
                self.simulate_monthly_expenses(est, dna, current_date, funcionario_id)
                print(f"📅 {dna.nome} | Mês {current_date.month}/{current_date.year} concluído.")
            
            current_date += timedelta(days=1)

    def simulate_monthly_expenses(self, est, dna, date_obj, funcionario_id):
        """Injeta custos operacionais reais para evitar Lucro = Faturamento."""
        # 1. Aluguel e Infra (Varia por DNA)
        base_rent = {
            "Elite": 12000.0, "Bom": 7500.0, "Razoavel": 4500.0, 
            "Mal": 3000.0, "Pessimo": 1500.0
        }
        rent_val = base_rent.get(dna.nome, 2000.0) * random.uniform(0.9, 1.1)
        
        infra = [
            ("Aluguel Comercial", rent_val, "fixa"),
            ("Energia Elétrica", rent_val * 0.15, "variavel"),
            ("Internet e Software", 350.0, "fixa"),
            ("Contabilidade", 1200.0, "fixa")
        ]
        
        for desc, val, tipo in infra:
            exp = Despesa(
                estabelecimento_id=est.id, descricao=desc, 
                categoria="Operacional", tipo=tipo, valor=val,
                data_despesa=date_obj.date()
            )
            db.session.add(exp)

        # 2. Folha de Pagamento (Baseado nos funcionários reais)
        equipe = Funcionario.query.filter_by(estabelecimento_id=est.id, ativo=True).all()
        for f in equipe:
            salario = float(f.salario_base or 1412.0)
            # Adiciona encargos (30%)
            custo_total = salario * 1.3
            exp = Despesa(
                estabelecimento_id=est.id, descricao=f"Folha de Pagamento - {f.nome}",
                categoria="RH", tipo="fixa", valor=custo_total,
                data_despesa=date_obj.date()
            )
            db.session.add(exp)

        # 3. Impostos (Simples Nacional aproximado: 10% do faturamento)
        # Busca faturamento do mês anterior
        start_month = date_obj - timedelta(days=30)
        revenue = db.session.query(func.sum(Venda.total)).filter(
            Venda.estabelecimento_id == est.id,
            Venda.data_venda >= start_month,
            Venda.data_venda < date_obj,
            Venda.status == 'finalizada'
        ).scalar() or 0
        
        imposto = float(revenue) * 0.10
        if imposto > 0:
            exp = Despesa(
                estabelecimento_id=est.id, descricao="Impostos (Simples Nacional)",
                categoria="Tributário", tipo="variavel", valor=imposto,
                data_despesa=date_obj.date()
            )
            db.session.add(exp)

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
            if quebra <= 0: continue
            
            ant = float(p.quantidade)
            p.quantidade -= Decimal(str(quebra))
            atu = float(p.quantidade)

            mov = MovimentacaoEstoque(
                estabelecimento_id=est.id, produto_id=p.id,
                quantidade=quebra, tipo="saida", motivo="QUEBRA/PERDA NATURAL",
                quantidade_anterior=ant, quantidade_atual=atu,
                created_at=date_obj
            )
            db.session.add(mov)

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
            
            qtd_perdida = float(lote.quantidade)
            lote.quantidade = 0
            lote.status = "descartado"
            
            ant = float(produto.quantidade)
            produto.quantidade -= Decimal(str(qtd_perdida))
            atu = float(produto.quantidade)
            
            mov = MovimentacaoEstoque(
                estabelecimento_id=est.id, produto_id=produto.id,
                quantidade=qtd_perdida, tipo="saida", motivo="VENCIMENTO DE LOTE",
                quantidade_anterior=ant, quantidade_atual=atu,
                lote_id=lote.id, created_at=date_obj
            )
            db.session.add(mov)

        db.session.commit()
        
        # 2. Reabastecer (Estoque < Mínimo)
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
                data_pedido=date_obj.date(),
                data_prevista_entrega=date_obj.date() + timedelta(days=random.randint(2, 5)),
                status="recebido", 
                valor_total=valor_total,
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
                detalhes_json=json.dumps({"fornecedor_id": forn_id, "itens": len(itens)})
            )
            db.session.add(auditoria_compra)
            
            for item in itens:
                p = item['produto']
                qtd = item['qtd']
                custo = item['custo']
                
                pi = PedidoCompraItem(
                    pedido_id=pedido.id,
                    produto_id=p.id,
                    quantidade_solicitada=qtd,
                    quantidade_recebida=qtd,
                    preco_unitario=custo,
                    subtotal=qtd * custo
                )
                db.session.add(pi)
                
                validade = date_obj.date() + timedelta(days=random.randint(15, 180))
                if p.unidade_medida == "KG":
                    validade = date_obj.date() + timedelta(days=random.randint(5, 15))

                lote = ProdutoLote(
                    estabelecimento_id=est.id,
                    produto_id=p.id,
                    numero_lote=f"L{date_obj.strftime('%Y%m%d')}-{random.randint(100,999)}",
                    quantidade=qtd,
                    quantidade_inicial=qtd,
                    preco_custo_unitario=custo,
                    data_fabricacao=date_obj.date() - timedelta(days=random.randint(5, 30)),
                    data_validade=validade,
                    status="disponivel",
                    created_at=date_obj
                )
                db.session.add(lote)
                
                # Registra histórico se o custo mudou (simula negociação/inflação)
                old_c = float(p.preco_custo or 0)
                if old_c > 0 and abs(old_c - custo) > 0.01:
                    from app.models import HistoricoPrecos
                    m_old = Produto.calcular_markup_de_preco(old_c, p.preco_venda)
                    m_new = Produto.calcular_markup_de_preco(custo, p.preco_venda)
                    
                    hp = HistoricoPrecos(
                        estabelecimento_id=est.id,
                        produto_id=p.id,
                        funcionario_id=funcionario_id,
                        preco_custo_anterior=old_c,
                        preco_venda_anterior=p.preco_venda,
                        margem_anterior=m_old,
                        preco_custo_novo=custo,
                        preco_venda_novo=p.preco_venda,
                        margem_nova=m_new,
                        data_alteracao=date_obj,
                        motivo=f"Reabastecimento Automático PC-{pedido.numero_pedido}"
                    )
                    db.session.add(hp)
                    # Atualiza o produto com o novo custo
                    p.preco_custo = Decimal(str(custo))

                    auditoria_preco = Auditoria(
                        estabelecimento_id=est.id,
                        usuario_id=funcionario_id,
                        tipo_evento="alteracao_preco",
                        descricao=f"Custo do produto {p.nome} alterado na compra {pedido.numero_pedido} (De R$ {old_c:.2f} para R$ {custo:.2f})",
                        data_evento=date_obj,
                        detalhes_json=json.dumps({"produto_id": p.id, "old_custo": old_c, "new_custo": custo})
                    )
                    db.session.add(auditoria_preco)

                ant = float(p.quantidade)
                p.quantidade += Decimal(str(qtd))
                atu = float(p.quantidade)
                
                mov = MovimentacaoEstoque(
                    estabelecimento_id=est.id, produto_id=p.id,
                    quantidade=qtd, tipo="entrada", motivo=f"Recebimento PC {pedido.numero_pedido}",
                    quantidade_anterior=ant, quantidade_atual=atu,
                    pedido_compra_id=pedido.id,
                    lote_id=lote.id,
                    created_at=date_obj
                )
                db.session.add(mov)
                
            cp = ContaPagar(
                estabelecimento_id=est.id,
                fornecedor_id=forn_id,
                descricao=f"Pedido de Compra {pedido.numero_pedido}",
                valor_original=valor_total,
                valor_atual=valor_total,
                data_emissao=date_obj.date(),
                data_vencimento=date_obj.date() + timedelta(days=30),
                status="pago" if (date_obj.date() + timedelta(days=30)) < datetime.now().date() else "aberto",
                created_at=date_obj
            )
            db.session.add(cp)

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
            funcionario_id=funcionario_id, codigo=f"V-{uuid.uuid4().hex[:6].upper()}",
            status="finalizada", created_at=ts, forma_pagamento=forma
        )
        db.session.add(venda)
        db.session.flush()
        
        total_venda = 0
        for p in basket:
            # Selecionar lote FIFO MASTER
            lote = ProdutoLote.query.filter(
                ProdutoLote.produto_id == p.id, 
                ProdutoLote.quantidade > 0,
                ProdutoLote.data_validade >= ts.date()
            ).order_by(ProdutoLote.data_validade.asc()).first()
            
            if not lote: continue
            
            # Lógica MASTER de Balança/Pesagem
            if p.unidade_medida == "KG":
                # Pesagem real: carne varia de 300g a 2.5kg normalmente no varejo
                qtd = round(random.uniform(0.200, 3.500), 3)
            else:
                qtd = random.randint(1, 6)
            
            qtd = min(float(qtd), float(lote.quantidade))
            preco_un = float(p.preco_venda) * random.uniform(0.98, 1.02) # Variação na balança/desconto
            total_item = round(preco_un * qtd, 2)
            
            custo_un = float(lote.preco_custo_unitario)
            margem_item = preco_un - custo_un
            lucro_real = margem_item * qtd
            
            vi = VendaItem(
                venda_id=venda.id, produto_id=p.id, produto_nome=p.nome, 
                quantidade=qtd, preco_unitario=preco_un, total_item=total_item,
                custo_unitario=custo_un, margem_item=margem_item,
                margem_lucro_real=lucro_real,
                created_at=ts
            )
            db.session.add(vi)
            
            lote.quantidade -= Decimal(str(qtd))
            
            ant = float(p.quantidade)
            p.quantidade -= Decimal(str(qtd))
            atu = float(p.quantidade)
            
            total_venda += total_item
            
            mov = MovimentacaoEstoque(
                estabelecimento_id=est.id, produto_id=p.id, 
                quantidade=qtd, tipo="saida", motivo=f"Venda {venda.codigo}",
                quantidade_anterior=ant, quantidade_atual=atu,
                venda_id=venda.id, lote_id=lote.id,
                created_at=ts
            )
            db.session.add(mov)

        venda.total = total_venda
        venda.subtotal = total_venda
        
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
