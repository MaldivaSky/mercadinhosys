import sys
import os
from datetime import datetime, timedelta

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app import create_app, db
from app.models import Venda
from sqlalchemy import func

app = create_app()

with app.app_context():
    estabelecimento_id = 1
    end_dt = datetime.now()
    start_dt = end_dt - timedelta(days=30)
    
    print(f"Audit for Est {estabelecimento_id} - Last 30 Days")
    print(f"Period: {start_dt.date()} to {end_dt.date()}")
    
    # 1. Logic like Dashboard (Status: finalizada, Field: data_venda)
    dash_total = db.session.query(func.sum(Venda.total)).filter(
        Venda.estabelecimento_id == estabelecimento_id,
        Venda.data_venda >= start_dt.date(),
        Venda.data_venda <= end_dt.date(),
        Venda.status == 'finalizada'
    ).scalar() or 0
    print(f"Dashboard-style logic (finalizada, data_venda): R$ {float(dash_total):,.2f}")
    
    # 2. Logic like SalesPage (Status: Any, Field: coalesce)
    campo_data = func.coalesce(Venda.data_venda, Venda.created_at)
    sales_total_any = db.session.query(func.sum(Venda.total)).filter(
        Venda.estabelecimento_id == estabelecimento_id,
        campo_data >= start_dt,
        campo_data <= end_dt
    ).scalar() or 0
    print(f"SalesPage-style logic (Any status, coalesce): R$ {float(sales_total_any):,.2f}")
    
    # 3. Logic like SalesPage but filtered by 'finalizada'
    sales_total_finalizada = db.session.query(func.sum(Venda.total)).filter(
        Venda.estabelecimento_id == estabelecimento_id,
        campo_data >= start_dt,
        campo_data <= end_dt,
        Venda.status == 'finalizada'
    ).scalar() or 0
    print(f"SalesPage-style logic (finalizada, coalesce): R$ {float(sales_total_finalizada):,.2f}")
    
    # 4. Check status counts
    status_counts = db.session.query(Venda.status, func.count(Venda.id), func.sum(Venda.total)).filter(
        Venda.estabelecimento_id == estabelecimento_id,
        campo_data >= start_dt,
        campo_data <= end_dt
    ).group_by(Venda.status).all()
    
    print("\nStatus counts in last 30 days:")
    for status, count, total in status_counts:
        print(f"- {status}: {count} sales, Total: R$ {float(total or 0):,.2f}")
