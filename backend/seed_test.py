"""
seed_test.py - Seed PROFISSIONAL e INTELIGENTE para MercadinhoSys v4.1
====================================================================
CONFORMIDADE TOTAL E RÍGIDA COM MODELS.PY

DADOS GERADOS:
- Estabelecimento e Configuracoes (Campos Exatos)
- Funcionarios com perfil RH 100% preenchido
- Fornecedores e Categorias com normalizacao
- Produtos com Lotes FIFO
- Vendas e Compras gerando faturamento real
- Ponto Eletronico com jornadas realistas
"""

import sys
import os
import random
import json
import uuid
from decimal import Decimal
from datetime import datetime, date, timedelta, time as dtime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configuração de encoding para Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

RESET = "--reset" in sys.argv
AIVEN = "--aiven" in sys.argv
ESTAB_ID = 1

from app.models import (
    db, Estabelecimento, Configuracao, Funcionario,
    CategoriaProduto, Produto, ProdutoLote, MovimentacaoEstoque,
    Fornecedor, Cliente, PedidoCompra, PedidoCompraItem,
    Venda, VendaItem, RegistroPonto, ContaPagar,
    Beneficio, FuncionarioBeneficio
)

TODAY      = date.today()
START_DATE = TODAY - timedelta(days=150)

def seed(app):
    with app.app_context():
        print(f"🌱 Iniciando Seed Senior v4.1 em: {db.engine.url}")
        
        if RESET:
            print("⚠️ Reseting database...")
            from sqlalchemy import text
            try:
                db.session.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
                db.session.commit()
                db.create_all()
            except Exception as e:
                print(f"⚠️ Reset fallback: {str(e)}")
                db.session.rollback()
                db.drop_all()
                db.create_all()

        # 1. ESTABELECIMENTO
        print("🏪 Criando Estabelecimento...")
        est = Estabelecimento.query.get(ESTAB_ID)
        if not est:
            est = Estabelecimento(
                id=ESTAB_ID, nome_fantasia="MERCADINHOSYS PREMIUM", razao_social="MS VAREJO LTDA",
                cnpj="12.345.678/0001-99", inscricao_estadual="123456789", telefone="(21) 3100-0000",
                email="admin@mercadinhosys.com.br", cep="20041-008", logradouro="Rua da Carioca",
                numero="100", bairro="Centro", cidade="Rio de Janeiro", estado="RJ", pais="Brasil",
                ativo=True, regime_tributario="SIMPLES NACIONAL", data_abertura=date(2020, 1, 1)
            )
            db.session.add(est)
        
        cfg = Configuracao.query.filter_by(estabelecimento_id=ESTAB_ID).first()
        if not cfg:
            cfg = Configuracao(
                estabelecimento_id=ESTAB_ID, cor_principal="#3b82f6", tema_escuro=True,
                formas_pagamento=json.dumps(["Dinheiro", "Pix", "Cartao de Credito", "Cartao de Debito", "Fiado"]),
                controlar_validade=True, alerta_estoque_minimo=True, dias_alerta_validade=30,
                estoque_minimo_padrao=10, tempo_sessao_minutos=60, tentativas_senha_bloqueio=5
            )
            db.session.add(cfg)
        db.session.flush()

        # 2. FUNCIONARIOS
        print("👥 Criando Funcionarios...")
        FUNC_LIST = [
            ("Master Admin", "admin", "ADMIN", 5000.00, "Gerente"),
            ("Ana Caixa", "ana.caixa", "CAIXA", 1850.00, "Caixa"),
            ("Pedro Estoque", "pedro.estoque", "FUNCIONARIO", 1700.00, "Estoquista"),
        ]
        func_map = {}
        for nome, user, role, sal, cargo in FUNC_LIST:
            f = Funcionario(
                estabelecimento_id=ESTAB_ID, nome=nome, username=user, role=role,
                cargo=cargo, salario_base=sal, cpf=f"{random.randint(100,999)}.000.000-00",
                rg="1234567-8", data_nascimento=date(1990, 1, 1), celular="(21) 98888-7777",
                email=f"{user}@mercadinho.com", data_admissao=START_DATE, ativo=True,
                cep="20041-008", logradouro="Rua do Seed", numero="1", bairro="Centro",
                cidade="Rio de Janeiro", estado="RJ", status="ativo",
                permissoes_json='{"pdv": true, "estoque": true, "compras": true, "financeiro": true, "configuracoes": true}'
            )
            f.set_senha("admin123" if user == "admin" else "123456")
            db.session.add(f)
            db.session.flush()
            func_map[user] = f

        # 2.1. BENEFICIOS
        print("🎁 Criando Beneficios...")
        BENEF_LIST = [
            ("Vale Alimentação", "VA Mensal", 450.00),
            ("Vale Transporte", "VT Mensal", 220.00),
            ("Plano de Saúde", "Coparticipação", 150.00),
        ]
        benef_objs = []
        for nome, desc, valor in BENEF_LIST:
            b = Beneficio(estabelecimento_id=ESTAB_ID, nome=nome, descricao=desc, valor_padrao=valor, ativo=True)
            db.session.add(b)
            benef_objs.append(b)
        db.session.flush()

        for u in ["admin", "ana.caixa", "pedro.estoque"]:
            f = func_map[u]
            for b in benef_objs:
                db.session.add(FuncionarioBeneficio(
                    funcionario_id=f.id, beneficio_id=b.id,
                    valor=b.valor_padrao, ativo=True
                ))
        db.session.flush()

        # 3. FORNECEDORES
        print("📦 Criando Fornecedores...")
        forn_objs = []
        for i in range(3):
            fn = Fornecedor(
                estabelecimento_id=ESTAB_ID, nome_fantasia=f"Fornecedor {i}", razao_social=f"FORN {i} LTDA",
                cnpj=f"00.{i}00.{i}00/0001-0{i}", telefone="(11) 4444-5555", email=f"vendas@forn{i}.com",
                cep="01001-000", logradouro="Av Paulista", numero=str(i+1), bairro="Bela Vista",
                cidade="Sao Paulo", estado="SP", ativo=True
            )
            db.session.add(fn)
            db.session.flush()
            forn_objs.append(fn)

        # 4. CATEGORIAS E PRODUTOS
        print("🏷️ Criando Categorias e Produtos...")
        cats = ["Bebidas", "Mercearia", "Limpeza", "Higiene"]
        cat_map = {}
        for c_name in cats:
            norm = CategoriaProduto.normalizar_nome_categoria(c_name)
            cat = CategoriaProduto(estabelecimento_id=ESTAB_ID, nome=norm, codigo=norm[:3].upper())
            db.session.add(cat)
            db.session.flush()
            cat_map[c_name] = cat

        prods = [
            ("Coca-Cola 2L", "Bebidas", "BEB001", 6.50, 10.99),
            ("Arroz 5kg", "Mercearia", "MER001", 18.00, 29.90),
            ("Detergente", "Limpeza", "LIM001", 1.50, 2.99),
            ("Papel Higienico", "Higiene", "HIG001", 14.00, 24.90),
        ]
        prod_objs = []
        for nome, cat, sku, custo, venda in prods:
            p = Produto(
                estabelecimento_id=ESTAB_ID, categoria_id=cat_map[cat].id,
                fornecedor_id=random.choice(forn_objs).id,
                nome=nome, codigo_interno=f"{sku}-{ESTAB_ID}", preco_custo=custo,
                preco_venda=venda, quantidade=0, quantidade_minima=10, 
                unidade_medida="un", ncm="12345678", ativo=True
            )
            db.session.add(p)
            db.session.flush()
            prod_objs.append(p)

        # 4.1 CLIENTES
        print("👥 Criando Clientes...")
        cliente_objs = []
        nomes_clientes = ["Silvio Santos", "Gugu Liberato", "Fausto Silva", "Hebe Camargo", "Rato"]
        for idx, nome in enumerate(nomes_clientes):
            c = Cliente(
                estabelecimento_id=ESTAB_ID,
                nome=nome,
                cpf=f"111.222.333-0{idx}",
                telefone="(11) 99999-0000",
                ativo=True,
                total_compras=0,
                valor_total_gasto=Decimal("0.00")
            )
            db.session.add(c)
            db.session.flush()
            cliente_objs.append(c)

        # 5. COMPRAS
        print("🛒 Gerando Pedidos de Compra...")
        for meses in [2, 1]:
            dt = TODAY - timedelta(days=meses*30)
            pc = PedidoCompra(
                estabelecimento_id=ESTAB_ID, fornecedor_id=random.choice(forn_objs).id,
                funcionario_id=func_map["admin"].id, data_pedido=dt, status="recebido",
                total=0, subtotal=0, numero_pedido=f"NF-{random.randint(1000,9999)}"
            )
            db.session.add(pc)
            db.session.flush()
            
            total_v = 0
            for p in prod_objs:
                qtd = 100
                val = float(p.preco_custo) * qtd
                total_v += val
                db.session.add(PedidoCompraItem(
                    pedido_id=pc.id, produto_id=p.id, produto_nome=p.nome,
                    quantidade_solicitada=qtd, quantidade_recebida=qtd,
                    preco_unitario=p.preco_custo, total_item=val, status="recebido"
                ))
                p.quantidade += qtd
                db.session.add(ProdutoLote(
                    estabelecimento_id=ESTAB_ID, produto_id=p.id, numero_lote=f"LOT{random.randint(100,999)}",
                    quantidade_inicial=qtd, quantidade=qtd, preco_custo_unitario=p.preco_custo,
                    data_entrada=dt, data_validade=dt+timedelta(days=365), ativo=True
                ))
                db.session.add(MovimentacaoEstoque(
                    estabelecimento_id=ESTAB_ID, produto_id=p.id, funcionario_id=func_map["admin"].id,
                    tipo="entrada", quantidade=qtd, quantidade_anterior=p.quantidade-qtd,
                    quantidade_atual=p.quantidade, custo_unitario=p.preco_custo,
                    valor_total=val, motivo="Compra"
                ))
            pc.total = total_v

        # 6. VENDAS
        print("💰 Gerando Historico de Vendas...")
        for d_off in range(30, -1, -1):
            dia = TODAY - timedelta(days=d_off)
            for _ in range(random.randint(3, 7)):
                cliente = random.choice(cliente_objs) if random.random() > 0.3 else None
                v = Venda(
                    estabelecimento_id=ESTAB_ID, funcionario_id=func_map["ana.caixa"].id,
                    cliente_id=cliente.id if cliente else None,
                    codigo=str(uuid.uuid4())[:8].upper(), data_venda=dia, status="finalizada",
                    total=0, subtotal=0, forma_pagamento="Dinheiro"
                )
                db.session.add(v)
                db.session.flush()
                
                vt = 0
                for p in random.sample(prod_objs, 2):
                    if p.quantidade > 0:
                        qv = 1
                        sv = float(p.preco_venda) * qv
                        vt += sv
                        db.session.add(VendaItem(
                            venda_id=v.id, produto_id=p.id, produto_nome=p.nome,
                            produto_codigo=p.codigo_interno, quantidade=qv,
                            preco_unitario=p.preco_venda, total_item=sv, custo_unitario=p.preco_custo
                        ))
                        p.quantidade -= qv
                        db.session.add(MovimentacaoEstoque(
                            estabelecimento_id=ESTAB_ID, produto_id=p.id, venda_id=v.id,
                            funcionario_id=func_map["ana.caixa"].id, tipo="saida", quantidade=qv,
                            quantidade_anterior=p.quantidade+qv, quantidade_atual=p.quantidade,
                            custo_unitario=p.preco_custo, valor_total=sv, motivo="Venda"
                        ))
                v.total = vt
                v.subtotal = vt
                if cliente:
                    cliente.total_compras += 1
                    cliente.valor_total_gasto += Decimal(str(vt))
                    cliente.ultima_compra = dia
                    db.session.add(cliente)

        # 7. PONTO
        print("⏰ Gerando Registros de Ponto...")
        for d_off in range(30, -1, -1):
            dia = TODAY - timedelta(days=d_off)
            if dia.weekday() == 6: continue
            for u in ["ana.caixa", "pedro.estoque"]:
                f = func_map[u]
                db.session.add(RegistroPonto(
                    funcionario_id=f.id, estabelecimento_id=ESTAB_ID, data=dia,
                    hora=dtime(8, 0), tipo_registro="entrada"
                ))
                db.session.add(RegistroPonto(
                    funcionario_id=f.id, estabelecimento_id=ESTAB_ID, data=dia,
                    hora=dtime(17, 0), tipo_registro="saida"
                ))

        db.session.commit()
        print("✅ Seed Senior v4.1 concluído com sucesso!")

if __name__ == "__main__":
    from app import create_app
    app = create_app()
    if AIVEN:
        from dotenv import load_dotenv
        load_dotenv()
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("AIVEN_DATABASE_URL").replace("postgres://", "postgresql://", 1)
    seed(app)
