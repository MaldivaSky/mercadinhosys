#!/usr/bin/env python
"""
Check what status values exist for vendas
"""

import os
import sys
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import Venda, Estabelecimento
from sqlalchemy import func

app = create_app()

with app.app_context():
    print("\n" + "="*80)
    print("🔍 VERIFICAR STATUS DAS VENDAS")
    print("="*80)
    
    estabelecimento = Estabelecimento.query.first()
    if not estabelecimento:
        print("❌ Nenhum estabelecimento encontrado")
        sys.exit(1)
    
    # Get distinct status values
    status_values = db.session.query(func.distinct(Venda.status)).filter(
        Venda.estabelecimento_id == estabelecimento.id
    ).all()
    
    print(f"\n📊 Status únicos encontrados:")
    for status in status_values:
        count = Venda.query.filter(
            Venda.estabelecimento_id == estabelecimento.id,
            Venda.status == status[0]
        ).count()
        print(f"  - '{status[0]}': {count} vendas")
    
    # Check timeseries with correct status
    print(f"\n📈 Testando timeseries com diferentes status:")
    
    start_date = datetime.utcnow() - timedelta(days=30)
    
    for status in status_values:
        count = db.session.query(func.count(Venda.id)).filter(
            Venda.estabelecimento_id == estabelecimento.id,
            Venda.data_venda >= start_date,
            Venda.status == status[0]
        ).scalar()
        
        total = db.session.query(func.sum(Venda.total)).filter(
            Venda.estabelecimento_id == estabelecimento.id,
            Venda.data_venda >= start_date,
            Venda.status == status[0]
        ).scalar()
        
        print(f"  - Status '{status[0]}': {count} vendas, R$ {float(total or 0):.2f}")
    
    print("\n" + "="*80)
