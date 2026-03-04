
import sys
import os
import random
from datetime import date, datetime, timedelta, time as dtime
from decimal import Decimal

# Absolute path correction
BASE_DIR = r"c:\Users\rafae\OneDrive\Desktop\mercadinhosys"
sys.path.insert(0, os.path.join(BASE_DIR, "backend"))

from app import create_app, db
from app.models import (
    Estabelecimento, Funcionario, Cliente, Produto, Categoria, 
    Venda, VendaItem, Despesa, ContaPagar, RegistroPonto, 
    Fornecedor, BancoHoras
)

app = create_app()

def quick_seed():
    with app.app_context():
        print("🚀 Iniciando Quick Seed (Últimos 7 dias)...")
        
        estab = Estabelecimento.query.first()
        if not estab:
            print("❌ Erro: Nenhum estabelecimento encontrado. Rode o seed principal primeiro.")
            return
            
        ESTAB_ID = estab.id
        TODAY = date.today()
        
        # Get core objects
        funcionarios = Funcionario.query.filter_by(estabelecimento_id=ESTAB_ID).all()
        clientes = Cliente.query.filter_by(estabelecimento_id=ESTAB_ID).all()
        produtos = Produto.query.filter_by(estabelecimento_id=ESTAB_ID).all()
        fornecedores = Fornecedor.query.filter_by(estabelecimento_id=ESTAB_ID).all()
        
        if not (funcionarios and produtos and fornecedores):
            print("❌ Erro: Dados básicos faltando.")
            return

        caixa_id = next((f.id for f in funcionarios if 'caixa' in f.cargo.lower()), funcionarios[0].id)
        
        # 1. Seeding Vendas (Last 7 days)
        print("🛒 Gerando Vendas...")
        vendas_n = 0
        for i in range(7, -1, -1):
            dia = TODAY - timedelta(days=i)
            n = random.randint(15, 25)
            for _ in range(n):
                h = random.randint(8, 20)
                dt_v = datetime.combine(dia, dtime(h, random.randint(0,59)))
                
                prods_v = random.sample(produtos, min(len(produtos), random.randint(1, 5)))
                total = 0.0
                itens = []
                for p in prods_v:
                    q = random.randint(1, 3)
                    prec = float(p.preco_venda)
                    cust = float(p.preco_custo)
                    sub = round(prec * q, 2)
                    total += sub
                    itens.append((p, q, prec, cust, sub))
                
                v = Venda(
                    estabelecimento_id=ESTAB_ID,
                    funcionario_id=caixa_id,
                    total=round(total, 2),
                    subtotal=round(total, 2),
                    valor_recebido=round(total, 2),
                    forma_pagamento=random.choice(["dinheiro", "pix", "cartao_credito"]),
                    status="finalizada",
                    data_venda=dt_v,
                    quantidade_itens=len(itens)
                )
                db.session.add(v)
                db.session.flush()
                
                for p, q, prec, cust, sub in itens:
                    db.session.add(VendaItem(
                        venda_id=v.id, produto_id=p.id,
                        produto_nome=p.nome, quantidade=q,
                        preco_unitario=prec, custo_unitario=cust, total_item=sub
                    ))
                vendas_n += 1
            print(f"  📅 {dia} ok")
        db.session.commit()

        # 2. Seeding Despesas (Last 7 days)
        print("💸 Gerando Despesas...")
        desp_n = 0
        categorias_lista = ["aluguel", "energia_eletrica", "agua", "telefone", "internet", "material_escritorio", "manutencao", "outros"]
        for i in range(7, -1, -1):
            dia = TODAY - timedelta(days=i)
            if random.random() < 0.5:
                d = Despesa(
                    estabelecimento_id=ESTAB_ID,
                    descricao=f"Despesa Rapida {dia}",
                    categoria=random.choice(categorias_lista),
                    valor=round(random.uniform(50, 400), 2),
                    data_despesa=dia,
                    tipo="variavel",
                    recorrente=False
                )
                db.session.add(d)
                desp_n += 1
        
        db.session.commit()
        print(f"✅ SUCESSO! {vendas_n} Vendas e {desp_n} Despesas criadas na Postgres.")

if __name__ == "__main__":
    quick_seed()
