#!/usr/bin/env python3
"""
Script para verificar dados de produtos no banco
"""
from app import create_app, db
from app.models import Produto
from sqlalchemy import func

app = create_app()

with app.app_context():
    print("=" * 80)
    print("VERIFICAÇÃO DE DADOS DE PRODUTOS")
    print("=" * 80)
    
    # Total de produtos
    total = Produto.query.count()
    print(f"\n📦 Total de produtos: {total}")
    
    # Produtos com vendas
    com_vendas = Produto.query.filter(Produto.quantidade_vendida > 0).count()
    print(f"✅ Produtos com quantidade_vendida > 0: {com_vendas}")
    
    # Produtos com total_vendido
    com_total = Produto.query.filter(Produto.total_vendido > 0).count()
    print(f"💰 Produtos com total_vendido > 0: {com_total}")
    
    # Produtos com ultima_venda
    com_data = Produto.query.filter(Produto.ultima_venda.isnot(None)).count()
    print(f"📅 Produtos com ultima_venda: {com_data}")
    
    # Soma total vendido
    soma_total = db.session.query(func.sum(Produto.total_vendido)).scalar() or 0
    print(f"💵 Soma total_vendido: R$ {soma_total:,.2f}")
    
    # Top 5 produtos mais vendidos
    print("\n" + "=" * 80)
    print("TOP 5 PRODUTOS MAIS VENDIDOS")
    print("=" * 80)
    
    top5 = Produto.query.filter(Produto.quantidade_vendida > 0)\
        .order_by(Produto.total_vendido.desc())\
        .limit(5)\
        .all()
    
    for i, p in enumerate(top5, 1):
        print(f"\n{i}. {p.nome}")
        print(f"   ID: {p.id}")
        print(f"   Quantidade vendida: {p.quantidade_vendida}")
        print(f"   Total vendido: R$ {p.total_vendido:,.2f}")
        print(f"   Última venda: {p.ultima_venda}")
        print(f"   Preço venda: R$ {p.preco_venda:,.2f}")
        print(f"   Preço custo: R$ {p.preco_custo:,.2f}")
    
    # Produtos SEM vendas
    print("\n" + "=" * 80)
    print("PRODUTOS SEM VENDAS")
    print("=" * 80)
    
    sem_vendas = Produto.query.filter(
        (Produto.quantidade_vendida == 0) | (Produto.quantidade_vendida.is_(None))
    ).limit(5).all()
    
    for p in sem_vendas:
        print(f"- {p.nome} (ID: {p.id}) - quantidade_vendida: {p.quantidade_vendida}, total_vendido: {p.total_vendido}")
    
    print("\n" + "=" * 80)
    print("VERIFICAÇÃO CONCLUÍDA")
    print("=" * 80)
