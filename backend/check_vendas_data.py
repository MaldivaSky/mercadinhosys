#!/usr/bin/env python
"""
Check if there are sales in the database
"""

import os
import sys
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import Venda, VendaItem, Estabelecimento

app = create_app()

with app.app_context():
    print("\n" + "="*80)
    print("🔍 VERIFICAR DADOS DE VENDAS")
    print("="*80)
    
    estabelecimento = Estabelecimento.query.first()
    if not estabelecimento:
        print("❌ Nenhum estabelecimento encontrado")
        sys.exit(1)
    
    print(f"✅ Estabelecimento: {estabelecimento.razao_social}")
    
    # Count total vendas
    total_vendas = Venda.query.filter_by(estabelecimento_id=estabelecimento.id).count()
    print(f"\n📊 Total de vendas: {total_vendas}")
    
    # Count vendas nos últimos 30 dias
    data_inicio = datetime.utcnow() - timedelta(days=30)
    vendas_30d = Venda.query.filter(
        Venda.estabelecimento_id == estabelecimento.id,
        Venda.data_venda >= data_inicio
    ).count()
    print(f"📊 Vendas nos últimos 30 dias: {vendas_30d}")
    
    # Get some sample vendas
    print("\n📋 Últimas 5 vendas:")
    vendas = Venda.query.filter_by(estabelecimento_id=estabelecimento.id).order_by(Venda.data_venda.desc()).limit(5).all()
    for v in vendas:
        print(f"  - {v.data_venda}: R$ {v.total_venda} ({v.quantidade_itens} itens)")
    
    # Check if there are vendas with items
    print("\n📦 Vendas com itens:")
    vendas_com_itens = db.session.query(Venda).filter(
        Venda.estabelecimento_id == estabelecimento.id
    ).join(VendaItem).count()
    print(f"  - Total: {vendas_com_itens}")
    
    # Check data range
    if vendas:
        primeira_venda = Venda.query.filter_by(estabelecimento_id=estabelecimento.id).order_by(Venda.data_venda.asc()).first()
        ultima_venda = Venda.query.filter_by(estabelecimento_id=estabelecimento.id).order_by(Venda.data_venda.desc()).first()
        print(f"\n📅 Período de vendas:")
        print(f"  - Primeira: {primeira_venda.data_venda}")
        print(f"  - Última: {ultima_venda.data_venda}")
    
    print("\n" + "="*80)
