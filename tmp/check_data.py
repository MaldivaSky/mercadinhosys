
import sys
import os
sys.path.append(os.getcwd())

from app import create_app, db
from app.models import Venda, VendaItem, Estabelecimento
from sqlalchemy import func
import json

app = create_app('development')
with app.app_context():
    est_id = 1 # Supondo que o user está logado no establishment 1
    
    print(f"--- Diagnóstico Establishment {est_id} ---")
    
    # 1. Verificar total de vendas sem filtro de status
    total_raw = db.session.query(func.count(Venda.id), func.sum(Venda.total)).filter(Venda.estabelecimento_id == est_id).first()
    print(f"Total Vendas (Sem filtro status): Count={total_raw[0]}, Sum={total_raw[1]}")
    
    # 2. Verificar vendas 'finalizada'
    total_finalizada = db.session.query(func.count(Venda.id), func.sum(Venda.total)).filter(Venda.estabelecimento_id == est_id, Venda.status == 'finalizada').first()
    print(f"Total Vendas (status='finalizada'): Count={total_finalizada[0]}, Sum={total_finalizada[1]}")
    
    # 3. Verificar outros status
    outros_status = db.session.query(Venda.status, func.count(Venda.id)).filter(Venda.estabelecimento_id == est_id).group_by(Venda.status).all()
    print(f"Outros Status: {outros_status}")
    
    # 4. Verificar Lucro (VendaItem) para vendas 'finalizada'
    lucro_total = db.session.query(func.sum(VendaItem.margem_lucro_real)).join(Venda, Venda.id == VendaItem.venda_id).filter(
        Venda.estabelecimento_id == est_id,
        Venda.status == 'finalizada'
    ).scalar()
    print(f"Lucro Total (finalizada): {lucro_total}")
    
    # 5. Verificar datas
    datas = db.session.query(func.min(Venda.data_venda), func.max(Venda.data_venda)).filter(Venda.estabelecimento_id == est_id).first()
    print(f"Range Datas: Min={datas[0]}, Max={datas[1]}")
    
    # 6. Verificar Pedidos de Compra
    from app.models import PedidoCompra
    total_pedidos = db.session.query(func.count(PedidoCompra.id)).filter(PedidoCompra.estabelecimento_id == est_id).scalar()
    print(f"Total Pedidos Compra: {total_pedidos}")
