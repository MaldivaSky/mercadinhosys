import re

with open('backend/app/dashboard_cientifico/data_layer.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Substituir o trecho do get_sellers_performance
old_snippet = """        # 1. Query Current Period
        current_query = db.session.query(
            Venda.funcionario_id,
            func.sum(Venda.total).label('total_atual'),
            func.count(Venda.id).label('qtd_atual')
        ).filter(
            Venda.estabelecimento_id == estabelecimento_id,
            Venda.status == 'finalizada',
            Venda.data_venda >= start_current,
            Venda.data_venda <= now
        ).group_by(Venda.funcionario_id).all()"""

new_snippet = """        # 1. Query Current Period
        q_current = db.session.query(
            Venda.funcionario_id,
            func.sum(Venda.total).label('total_atual'),
            func.count(Venda.id).label('qtd_atual')
        ).filter(
            Venda.status == 'finalizada',
            Venda.data_venda >= start_current,
            Venda.data_venda <= now
        )
        if estabelecimento_id != 'all':
            q_current = q_current.filter(Venda.estabelecimento_id == estabelecimento_id)
            
        current_query = q_current.group_by(Venda.funcionario_id).all()"""

code = code.replace(old_snippet, new_snippet)

old_snippet2 = """        # 2. Query Previous Period
        previous_query = db.session.query(
            Venda.funcionario_id,
            func.sum(Venda.total).label('total_passado')
        ).filter(
            Venda.estabelecimento_id == estabelecimento_id,
            Venda.status == 'finalizada',
            Venda.data_venda >= start_previous,
            Venda.data_venda < start_current
        ).group_by(Venda.funcionario_id).all()"""

new_snippet2 = """        # 2. Query Previous Period
        q_prev = db.session.query(
            Venda.funcionario_id,
            func.sum(Venda.total).label('total_passado')
        ).filter(
            Venda.status == 'finalizada',
            Venda.data_venda >= start_previous,
            Venda.data_venda < start_current
        )
        if estabelecimento_id != 'all':
            q_prev = q_prev.filter(Venda.estabelecimento_id == estabelecimento_id)
            
        previous_query = q_prev.group_by(Venda.funcionario_id).all()"""

code = code.replace(old_snippet2, new_snippet2)

old_snippet3 = """        # 3. Retrieve Vendedores info
        seller_ids = list(set(list(current_map.keys()) + list(previous_map.keys())))
        if not seller_ids:
            return []

        funcionarios = db.session.query(Funcionario.id, Funcionario.nome).filter(
            Funcionario.estabelecimento_id == estabelecimento_id,
            Funcionario.id.in_(seller_ids)
        ).all()"""

new_snippet3 = """        # 3. Retrieve Vendedores info
        seller_ids = [s for s in set(list(current_map.keys()) + list(previous_map.keys())) if s is not None]
        if not seller_ids:
            return []

        q_func = db.session.query(Funcionario.id, Funcionario.nome).filter(
            Funcionario.id.in_(seller_ids)
        )
        if estabelecimento_id != 'all':
            q_func = q_func.filter(Funcionario.estabelecimento_id == estabelecimento_id)
            
        funcionarios = q_func.all()"""

code = code.replace(old_snippet3, new_snippet3)

with open('backend/app/dashboard_cientifico/data_layer.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("DataLayer Patched for 'all'")
