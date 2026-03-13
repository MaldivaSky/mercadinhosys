"""
MercadinhoSys - Rotas de Delivery
Módulo profissional para gerenciamento de entregas
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import (
    db, Entregador, DeliveryConfig, PedidoDelivery, 
    DeliveryRastreamento, DeliveryMetricas, Cliente, VendaItem, Produto
)
from app.decorators.rbac import tenant_or_super_admin_required
from datetime import datetime, date, timedelta
from decimal import Decimal
import json
import secrets
import logging

delivery_bp = Blueprint("delivery", __name__)
logger = logging.getLogger(__name__)

# ==================== ENTREGADORES ====================

@delivery_bp.route("/entregadores", methods=["GET"])
@tenant_or_super_admin_required
def listar_entregadores():
    """Lista todos os entregadores do estabelecimento"""
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        ativos = request.args.get("ativos", type=bool)
        
        query = Entregador.query.filter_by(estabelecimento_id=request.allowed_estabelecimento_id)
        
        if ativos is not None:
            query = query.filter_by(ativo=ativos)
        
        entregadores = query.order_by(Entregador.nome).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            "success": True,
            "entregadores": [e.to_dict() for e in entregadores.items],
            "total": entregadores.total,
            "pages": entregadores.pages,
            "current_page": entregadores.page
        })
        
    except Exception as e:
        logger.error(f"Erro ao listar entregadores: {e}")
        return jsonify({"success": False, "error": "Erro interno"}), 500

@delivery_bp.route("/entregadores", methods=["POST"])
@tenant_or_super_admin_required
def criar_entregador():
    """Cria um novo entregador"""
    try:
        data = request.get_json()
        
        # Validações
        required_fields = ["nome", "cpf", "telefone", "data_contratacao"]
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    "success": False,
                    "error": f"Campo obrigatório: {field}"
                }), 400
        
        # Verificar CPF duplicado
        if Entregador.query.filter_by(cpf=data["cpf"]).first():
            return jsonify({
                "success": False,
                "error": "CPF já cadastrado"
            }), 400
        
        entregador = Entregador(
            estabelecimento_id=request.allowed_estabelecimento_id,
            nome=data["nome"],
            cpf=data["cpf"],
            rg=data.get("rg"),
            telefone=data["telefone"],
            whatsapp=data.get("whatsapp"),
            email=data.get("email"),
            data_nascimento=datetime.strptime(data.get("data_nascimento", "1990-01-01"), "%Y-%m-%d").date(),
            data_contratacao=datetime.strptime(data["data_contratacao"], "%Y-%m-%d").date(),
            tipo_veiculo=data.get("tipo_veiculo", "moto"),
            placa_veiculo=data.get("placa_veiculo"),
            modelo_veiculo=data.get("modelo_veiculo"),
            taxa_entrega_padrao=Decimal(str(data.get("taxa_entrega_padrao", "5.00"))),
            comissao_por_entrega=Decimal(str(data.get("comissao_por_entrega", "0.00"))),
            forma_pagamento_padrao=data.get("forma_pagamento_padrao", "PIX")
        )
        
        db.session.add(entregador)
        db.session.commit()
        
        logger.info(f"Entregador {entregador.nome} criado com sucesso")
        
        return jsonify({
            "success": True,
            "message": "Entregador criado com sucesso",
            "entregador": entregador.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao criar entregador: {e}")
        return jsonify({"success": False, "error": "Erro interno"}), 500

@delivery_bp.route("/entregadores/<int:id>", methods=["PUT"])
@tenant_or_super_admin_required
def atualizar_entregador(id):
    """Atualiza dados do entregador"""
    try:
        entregador = Entregador.query.filter_by(
            id=id, 
            estabelecimento_id=request.allowed_estabelecimento_id
        ).first_or_404()
        
        data = request.get_json()
        
        # Atualizar campos permitidos
        campos_atualizaveis = [
            "nome", "telefone", "whatsapp", "email", "tipo_veiculo",
            "placa_veiculo", "modelo_veiculo", "ativo", "disponivel_entrega",
            "taxa_entrega_padrao", "comissao_por_entrega", "forma_pagamento_padrao"
        ]
        
        for campo in campos_atualizaveis:
            if campo in data:
                if campo in ["taxa_entrega_padrao", "comissao_por_entrega"]:
                    setattr(entregador, campo, Decimal(str(data[campo])))
                else:
                    setattr(entregador, campo, data[campo])
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Entregador atualizado com sucesso",
            "entregador": entregador.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao atualizar entregador {id}: {e}")
        return jsonify({"success": False, "error": "Erro interno"}), 500

# ==================== CONFIGURAÇÕES ====================

@delivery_bp.route("/config", methods=["GET"])
@tenant_or_super_admin_required
def get_config():
    """Obtém configurações de delivery do estabelecimento"""
    try:
        config = DeliveryConfig.query.filter_by(
            estabelecimento_id=request.allowed_estabelecimento_id
        ).first()
        
        if not config:
            # Criar configuração padrão
            config = DeliveryConfig(
                estabelecimento_id=request.allowed_estabelecimento_id,
                formas_pagamento_entrega=json.dumps(["dinheiro", "pix", "cartao"]),
                bairros_atendidos=json.dumps(["Centro", "Bairro Novo", "Vila Industrial"])
            )
            db.session.add(config)
            db.session.commit()
        
        return jsonify({
            "success": True,
            "config": config.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter config delivery: {e}")
        return jsonify({"success": False, "error": "Erro interno"}), 500

@delivery_bp.route("/config", methods=["PUT"])
@tenant_or_super_admin_required
def update_config():
    """Atualiza configurações de delivery"""
    try:
        config = DeliveryConfig.query.filter_by(
            estabelecimento_id=request.allowed_estabelecimento_id
        ).first_or_404()
        
        data = request.get_json()
        
        # Atualizar campos
        campos_numericos = [
            "taxa_entrega_fixa", "taxa_entrega_por_km", "km_minimo_cobranca",
            "taxa_entrega_gratuita_valor", "taxa_entrega_gratuita_km", "raio_entrega_km"
        ]
        
        for campo in campos_numericos:
            if campo in data:
                setattr(config, campo, Decimal(str(data[campo])))
        
        campos_texto_json = ["bairros_atendidos", "formas_pagamento_entrega"]
        for campo in campos_texto_json:
            if campo in data:
                setattr(config, campo, json.dumps(data[campo]))
        
        campos_simples = [
            "tempo_preparo_padrao", "tempo_entrega_padrao", "aceita_pagamento_entrega",
            "rastreamento_entrega", "notificacao_cliente", "integracao_maps"
        ]
        for campo in campos_simples:
            if campo in data:
                setattr(config, campo, data[campo])
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Configurações atualizadas com sucesso",
            "config": config.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao atualizar config delivery: {e}")
        return jsonify({"success": False, "error": "Erro interno"}), 500

# ==================== PEDIDOS DELIVERY ====================

@delivery_bp.route("/pedidos", methods=["GET"])
@tenant_or_super_admin_required
def listar_pedidos():
    """Lista pedidos de delivery"""
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        status = request.args.get("status")
        data_inicio = request.args.get("data_inicio")
        data_fim = request.args.get("data_fim")
        
        query = PedidoDelivery.query.filter_by(
            estabelecimento_id=request.allowed_estabelecimento_id
        )
        
        if status:
            query = query.filter_by(status=status)
        
        if data_inicio:
            query = query.filter(PedidoDelivery.created_at >= datetime.strptime(data_inicio, "%Y-%m-%d"))
        
        if data_fim:
            query = query.filter(PedidoDelivery.created_at <= datetime.strptime(data_fim, "%Y-%m-%d 23:59:59"))
        
        pedidos = query.order_by(PedidoDelivery.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            "success": True,
            "pedidos": [p.to_dict() for p in pedidos.items],
            "total": pedidos.total,
            "pages": pedidos.pages,
            "current_page": pedidos.page
        })
        
    except Exception as e:
        logger.error(f"Erro ao listar pedidos delivery: {e}")
        return jsonify({"success": False, "error": "Erro interno"}), 500

@delivery_bp.route("/pedidos", methods=["POST"])
@tenant_or_super_admin_required
def criar_pedido():
    """Cria um novo pedido de delivery"""
    try:
        data = request.get_json()
        
        # Validações básicas
        required_fields = [
            "nome_cliente", "telefone_cliente", "endereco_entrega",
            "valor_produtos", "forma_pagamento", "itens"
        ]
        
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    "success": False,
                    "error": f"Campo obrigatório: {field}"
                }), 400
        
        # Gerar código único
        codigo = f"DEL{datetime.now().strftime('%Y%m%d')}{secrets.token_hex(2).upper()}"
        
        # Calcular taxa de entrega
        config = DeliveryConfig.query.filter_by(
            estabelecimento_id=request.allowed_estabelecimento_id
        ).first()
        
        taxa_entrega = Decimal("0.00")
        if config:
            if data.get("distancia_km"):
                distancia = Decimal(str(data["distancia_km"]))
                if distancia >= config.km_minimo_cobranca:
                    taxa_entrega = config.taxa_entrega_fixa + (distancia * config.taxa_entrega_por_km)
            else:
                taxa_entrega = config.taxa_entrega_fixa
        
        valor_total = Decimal(str(data["valor_produtos"])) + taxa_entrega
        
        # Criar pedido
        pedido = PedidoDelivery(
            estabelecimento_id=request.allowed_estabelecimento_id,
            cliente_id=data.get("cliente_id"),
            codigo_pedido=codigo,
            nome_cliente=data["nome_cliente"],
            telefone_cliente=data["telefone_cliente"],
            whatsapp_cliente=data.get("whatsapp_cliente"),
            cep_entrega=data["endereco_entrega"]["cep"],
            logradouro_entrega=data["endereco_entrega"]["logradouro"],
            numero_entrega=data["endereco_entrega"]["numero"],
            complemento_entrega=data["endereco_entrega"].get("complemento"),
            bairro_entrega=data["endereco_entrega"]["bairro"],
            cidade_entrega=data["endereco_entrega"]["cidade"],
            estado_entrega=data["endereco_entrega"]["estado"],
            referencia_entrega=data["endereco_entrega"].get("referencia"),
            latitude_entrega=data["endereco_entrega"].get("latitude"),
            longitude_entrega=data["endereco_entrega"].get("longitude"),
            valor_produtos=Decimal(str(data["valor_produtos"])),
            taxa_entrega=taxa_entrega,
            valor_total=valor_total,
            distancia_km=Decimal(str(data.get("distancia_km", 0))),
            forma_pagamento=data["forma_pagamento"],
            pagamento_na_entrega=data.get("pagamento_na_entrega", False),
            troco_para=Decimal(str(data["troco_para"])) if data.get("troco_para") else None,
            observacoes_pedido=data.get("observacoes_pedido"),
            observacoes_entrega=data.get("observacoes_entrega")
        )
        
        db.session.add(pedido)
        db.session.flush()  # Obter ID
        
        # Adicionar itens do pedido
        for item_data in data["itens"]:
            item = VendaItem(
                pedido_delivery_id=pedido.id,
                produto_id=item_data["produto_id"],
                quantidade=item_data["quantidade"],
                preco_unitario=Decimal(str(item_data["preco_unitario"])),
                total_item=Decimal(str(item_data["total_item"]))
            )
            db.session.add(item)
        
        # Calcular previsão de entrega
        if config:
            tempo_total = config.tempo_preparo_padrao + config.tempo_entrega_padrao
            pedido.data_previsao_entrega = datetime.now() + timedelta(minutes=tempo_total)
        
        db.session.commit()
        
        logger.info(f"Pedido delivery {codigo} criado com sucesso")
        
        return jsonify({
            "success": True,
            "message": "Pedido criado com sucesso",
            "pedido": pedido.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao criar pedido delivery: {e}")
        return jsonify({"success": False, "error": "Erro interno"}), 500

@delivery_bp.route("/pedidos/<int:id>/status", methods=["PUT"])
@tenant_or_super_admin_required
def atualizar_status_pedido(id):
    """Atualiza status do pedido de delivery"""
    try:
        pedido = PedidoDelivery.query.filter_by(
            id=id,
            estabelecimento_id=request.allowed_estabelecimento_id
        ).first_or_404()
        
        data = request.get_json()
        novo_status = data.get("status")
        
        if novo_status not in ["pendente", "preparando", "pronto", "entregando", "entregue", "cancelado"]:
            return jsonify({
                "success": False,
                "error": "Status inválido"
            }), 400
        
        # Atualizar status e datas
        pedido.status = novo_status
        
        if novo_status == "entregando":
            pedido.data_inicio_entrega = datetime.now()
            pedido.entregador_id = data.get("entregador_id")
        elif novo_status == "entregue":
            pedido.data_entrega_real = datetime.now()
            
            # Atualizar métricas do entregador
            if pedido.entregador:
                entregador = pedido.entregador
                entregador.total_entregas += 1
                if pedido.distancia_km:
                    entregador.total_km_percorridos += pedido.distancia_km
                
                db.session.add(entregador)
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": f"Status atualizado para {novo_status}",
            "pedido": pedido.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao atualizar status pedido {id}: {e}")
        return jsonify({"success": False, "error": "Erro interno"}), 500

# ==================== MÉTRICAS ====================

@delivery_bp.route("/metricas", methods=["GET"])
@tenant_or_super_admin_required
def get_metricas():
    """Obtém métricas consolidadas de delivery"""
    try:
        # Período padrão: últimos 30 dias
        dias = request.args.get("dias", 30, type=int)
        data_inicio = date.today() - timedelta(days=dias)
        
        # Métricas gerais
        metricas = db.session.query(
            db.func.count(PedidoDelivery.id).label('total_pedidos'),
            db.func.sum(PedidoDelivery.valor_total).label('faturamento_total'),
            db.func.sum(PedidoDelivery.taxa_entrega).label('total_taxas'),
            db.func.avg(PedidoDelivery.distancia_km).label('distancia_media')
        ).filter(
            PedidoDelivery.estabelecimento_id == request.allowed_estabelecimento_id,
            PedidoDelivery.created_at >= data_inicio,
            PedidoDelivery.status != 'cancelado'
        ).first()
        
        # Pedidos por status
        pedidos_por_status = db.session.query(
            PedidoDelivery.status,
            db.func.count(PedidoDelivery.id).label('quantidade')
        ).filter(
            PedidoDelivery.estabelecimento_id == request.allowed_estabelecimento_id,
            PedidoDelivery.created_at >= data_inicio
        ).group_by(PedidoDelivery.status).all()
        
        # Top entregadores
        top_entregadores = db.session.query(
            Entregador.nome,
            db.func.count(PedidoDelivery.id).label('entregas'),
            db.func.sum(PedidoDelivery.distancia_km).label('km_percorridos')
        ).join(
            PedidoDelivery, Entregador.id == PedidoDelivery.entregador_id
        ).filter(
            PedidoDelivery.estabelecimento_id == request.allowed_estabelecimento_id,
            PedidoDelivery.created_at >= data_inicio,
            PedidoDelivery.status == 'entregue'
        ).group_by(Entregador.id, Entregador.nome).order_by(
            db.func.count(PedidoDelivery.id).desc()
        ).limit(5).all()
        
        return jsonify({
            "success": True,
            "periodo": {
                "dias": dias,
                "data_inicio": data_inicio.isoformat(),
                "data_fim": date.today().isoformat()
            },
            "metricas_gerais": {
                "total_pedidos": metricas.total_pedidos or 0,
                "faturamento_total": float(metricas.faturamento_total or 0),
                "total_taxas": float(metricas.total_taxas or 0),
                "distancia_media": float(metricas.distancia_media or 0),
                "ticket_medio": float(metricas.faturamento_total or 0) / max(metricas.total_pedidos or 1, 1)
            },
            "pedidos_por_status": {
                item.status: item.quantidade for item in pedidos_por_status
            },
            "top_entregadores": [
                {
                    "nome": item.nome,
                    "entregas": item.entregas,
                    "km_percorridos": float(item.km_percorridos or 0)
                }
                for item in top_entregadores
            ]
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter métricas delivery: {e}")
        return jsonify({"success": False, "error": "Erro interno"}), 500
