from flask import Blueprint, jsonify, request, g
from sqlalchemy.orm import joinedload
from app.models import db, TabelaPreco, TabelaPrecoItem, Rota, PedidoVenda, PedidoVendaItem, Cliente, Produto, MetaVendedor, ProdutoFoco
from datetime import datetime, timezone
import json

bp = Blueprint("sfa", __name__)

@bp.route("/sfa/tabelas", methods=["GET"])
def get_tabelas():
    try:
        tabelas = TabelaPreco.query.all()
        return jsonify({"status": "success", "data": [t.to_dict() for t in tabelas]}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.route("/sfa/rotas", methods=["GET"])
def get_rotas():
    try:
        vendedor_id = request.args.get("vendedor_id")
        q = Rota.query
        if vendedor_id:
            q = q.filter_by(vendedor_id=vendedor_id)
        rotas = q.all()
        return jsonify({"status": "success", "data": [r.to_dict() for r in rotas]}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.route("/sfa/sync-data", methods=["GET"])
def sync_data():
    """Baixa o roteiro do dia, clientes, produtos e tabelas do vendedor para o PWA (Offline)"""
    try:
        vendedor_id = request.args.get("vendedor_id")
        
        # 1. Rotas do vendedor
        q_rotas = Rota.query
        if vendedor_id:
            q_rotas = q_rotas.filter_by(vendedor_id=vendedor_id)
        rotas = q_rotas.all()
        rota_ids = [r.id for r in rotas]
        
        # 2. Clientes das rotas
        clientes = Cliente.query.filter(Cliente.rota_id.in_(rota_ids)).all() if rota_ids else []
        
        # 3. Produtos (Apenas os essenciais)
        produtos = Produto.query.filter_by(ativo=True).all()
        
        # 4. Tabelas de Preço (Atacado, Varejo, etc)
        tabelas = TabelaPreco.query.filter_by(ativa=True).all()
        tabelas_itens = TabelaPrecoItem.query.all()

        return jsonify({
            "status": "success",
            "data": {
                "rotas": [r.to_dict() for r in rotas],
                "clientes": [c.to_dict() for c in clientes],
                "produtos": [p.to_dict() for p in produtos],
                "tabelas_preco": [t.to_dict() for t in tabelas],
                "tabelas_preco_itens": [i.to_dict() for i in tabelas_itens],
            }
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.route("/sfa/sync-pedidos", methods=["POST"])
def sync_pedidos():
    """Recebe pedidos feitos offline (Pré-Venda) e reserva estoque pendente"""
    try:
        data = request.json
        pedidos = data.get("pedidos", [])
        
        synced = []
        for p_data in pedidos:
            offline_uuid = p_data.get("offline_uuid")
            
            # Idempotencia: verifica se já existe
            if offline_uuid:
                existente = PedidoVenda.query.filter_by(offline_uuid=offline_uuid).first()
                if existente:
                    synced.append(existente.codigo)
                    continue
                    
            novo_pedido = PedidoVenda(
                estabelecimento_id=g.estabelecimento_id if hasattr(g, "estabelecimento_id") else p_data.get("estabelecimento_id"),
                cliente_id=p_data.get("cliente_id"),
                vendedor_id=p_data.get("vendedor_id"),
                codigo=p_data.get("codigo", f"PED-SFA-{int(datetime.utcnow().timestamp())}"),
                status="pendente",
                subtotal=p_data.get("subtotal", 0),
                desconto=p_data.get("desconto", 0),
                total=p_data.get("total", 0),
                condicao_pagamento=p_data.get("condicao_pagamento"),
                observacoes=p_data.get("observacoes"),
                offline_uuid=offline_uuid
            )
            db.session.add(novo_pedido)
            db.session.flush() # Para gerar ID
            
            for i_data in p_data.get("itens", []):
                item = PedidoVendaItem(
                    estabelecimento_id=novo_pedido.estabelecimento_id,
                    pedido_id=novo_pedido.id,
                    produto_id=i_data.get("produto_id"),
                    quantidade=i_data.get("quantidade"),
                    preco_unitario=i_data.get("preco_unitario"),
                    desconto=i_data.get("desconto", 0),
                    total_item=i_data.get("total_item")
                )
                db.session.add(item)
                
            synced.append(novo_pedido.codigo)
            
        db.session.commit()
        return jsonify({"status": "success", "message": f"{len(synced)} pedidos sincronizados", "pedidos_sincronizados": synced}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.route("/sfa/pedidos/<int:pedido_id>/aprovar", methods=["POST"])
def aprovar_pedido(pedido_id):
    """Backoffice aprova o pedido, reserva o limite de crédito e abate o estoque (Faturamento)"""
    try:
        pedido = PedidoVenda.query.get(pedido_id)
        if not pedido:
            return jsonify({"status": "error", "message": "Pedido não encontrado"}), 404
            
        if pedido.status != "pendente":
            return jsonify({"status": "error", "message": f"Pedido já está {pedido.status}"}), 400
            
        cliente = Cliente.query.get(pedido.cliente_id)
        if cliente:
            limite_disponivel = float(cliente.limite_credito or 0) - float(cliente.saldo_devedor or 0)
            if float(pedido.total) > limite_disponivel:
                return jsonify({"status": "error", "message": "Limite de crédito excedido"}), 400
                
            cliente.saldo_devedor = float(cliente.saldo_devedor or 0) + float(pedido.total)
            
        # Baixa de estoque simplificada
        for item in pedido.itens:
            produto = Produto.query.get(item.produto_id)
            if produto:
                produto.movimentar_estoque(float(item.quantidade), "saida", f"Pedido {pedido.codigo}", pedido.vendedor_id)
                
        pedido.status = "faturado"
        db.session.commit()
        
        return jsonify({"status": "success", "message": "Pedido aprovado e faturado"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

import calendar
from sqlalchemy import func, case, and_

@bp.route("/sfa/kpi/vendedor", methods=["GET"])
def kpi_vendedor():
    """Retorna os indicadores cruciais para o Vendedor (Metas, Positivação, Foco)"""
    try:
        vendedor_id = request.args.get("vendedor_id")
        if not vendedor_id:
            return jsonify({"status": "error", "message": "vendedor_id é obrigatório"}), 400
            
        hoje = datetime.now(timezone.utc).date()
        ano, mes = hoje.year, hoje.month
        
        # 1. Obter a Meta do Vendedor para o mês atual
        meta = MetaVendedor.query.filter_by(vendedor_id=vendedor_id, mes=mes, ano=ano).first()
        meta_faturamento = float(meta.meta_faturamento) if meta else 0.0
        meta_positivacao = int(meta.meta_positivacao) if meta else 0
        
        # 2. Vendas do mês atual deste vendedor
        pedidos = PedidoVenda.query.filter(
            PedidoVenda.vendedor_id == vendedor_id,
            db.extract('month', PedidoVenda.data_cadastro) == mes,
            db.extract('year', PedidoVenda.data_cadastro) == ano,
            PedidoVenda.status != 'cancelado'
        ).all()
        
        faturamento_realizado = sum(float(p.total) for p in pedidos)
        
        # 3. Positivação (Base de Clientes vs Compradores)
        base_clientes = Cliente.query.filter_by(vendedor_id=vendedor_id, ativo=True).count()
        clientes_positivados = len(set(p.cliente_id for p in pedidos))
        
        # 4. Tendência Matemática
        _, ultimo_dia_mes = calendar.monthrange(ano, mes)
        dias_corridos = max(hoje.day, 1)
        tendencia = (faturamento_realizado / dias_corridos) * ultimo_dia_mes
        
        # 5. Produtos Foco
        produtos_foco = ProdutoFoco.query.filter(
            ProdutoFoco.data_inicio <= hoje,
            ProdutoFoco.data_fim >= hoje,
            ProdutoFoco.ativo == True
        ).all()
        
        foco_vendido = 0
        foco_detalhes = []
        if produtos_foco:
            foco_ids = [pf.produto_id for pf in produtos_foco]
            # Conta o que foi vendido desses produtos por esse vendedor neste mes
            itens_foco = db.session.query(
                Produto.nome,
                func.sum(PedidoVendaItem.quantidade).label('qtd_vendida')
            ).join(PedidoVendaItem, Produto.id == PedidoVendaItem.produto_id)\
             .join(PedidoVenda, PedidoVenda.id == PedidoVendaItem.pedido_id)\
             .filter(
                PedidoVenda.vendedor_id == vendedor_id,
                db.extract('month', PedidoVenda.data_cadastro) == mes,
                db.extract('year', PedidoVenda.data_cadastro) == ano,
                PedidoVenda.status != 'cancelado',
                Produto.id.in_(foco_ids)
             ).group_by(Produto.nome).all()
             
            for f in itens_foco:
                foco_detalhes.append({
                    "produto": f.nome,
                    "quantidade": float(f.qtd_vendida)
                })
                foco_vendido += float(f.qtd_vendida)
                
        return jsonify({
            "status": "success",
            "data": {
                "meta": {
                    "faturamento": meta_faturamento,
                    "positivacao": meta_positivacao or base_clientes
                },
                "realizado": {
                    "faturamento": faturamento_realizado,
                    "tendencia": tendencia,
                    "dias_corridos": dias_corridos,
                    "total_dias": ultimo_dia_mes
                },
                "carteira": {
                    "base_clientes": base_clientes,
                    "positivados": clientes_positivados,
                    "nao_compraram": max(0, base_clientes - clientes_positivados)
                },
                "produto_foco": {
                    "total_itens_vendidos": foco_vendido,
                    "detalhes": foco_detalhes
                }
            }
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
