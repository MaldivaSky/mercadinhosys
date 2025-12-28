from flask import Blueprint, request, jsonify
from app import db
from app.models import Venda, VendaItem, Produto, Cliente
from datetime import datetime
import uuid

vendas_bp = Blueprint("vendas", __name__)


@vendas_bp.route("/", methods=["POST"])
def criar_venda():
    """Cria uma nova venda"""
    try:
        data = request.get_json()

        # Validações básicas
        if not data.get("itens") or len(data["itens"]) == 0:
            return jsonify({"error": "A venda deve conter itens"}), 400

        # Gera código único para a venda
        codigo_venda = (
            f"VENDA-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        )

        # Cria a venda
        venda = Venda(
            codigo=codigo_venda,
            cliente_id=data.get("cliente_id"),
            funcionario_id=data.get("funcionario_id", 1),  # Default para admin
            forma_pagamento=data.get("forma_pagamento", "dinheiro"),
            observacoes=data.get("observacoes", ""),
            status="finalizada",
        )

        db.session.add(venda)
        db.session.flush()  # Gera ID da venda

        # Processa itens da venda
        subtotal = 0
        for item_data in data["itens"]:
            produto = Produto.query.get(item_data["produto_id"])
            if not produto:
                return (
                    jsonify(
                        {"error": f'Produto {item_data["produto_id"]} não encontrado'}
                    ),
                    404,
                )

            # Verifica estoque
            if produto.quantidade < item_data["quantidade"]:
                return (
                    jsonify({"error": f"Estoque insuficiente para {produto.nome}"}),
                    400,
                )

            # Calcula valores
            preco_unitario = item_data.get("preco_unitario", produto.preco_venda)
            desconto_item = item_data.get("desconto", 0)
            total_item = (preco_unitario * item_data["quantidade"]) - desconto_item

            # Cria item da venda
            venda_item = VendaItem(
                venda_id=venda.id,
                produto_id=produto.id,
                quantidade=item_data["quantidade"],
                preco_unitario=preco_unitario,
                desconto=desconto_item,
                total_item=total_item,
            )

            db.session.add(venda_item)

            # Atualiza estoque do produto
            produto.quantidade -= item_data["quantidade"]

            # Atualiza subtotal
            subtotal += total_item

        # Calcula totais da venda
        desconto_venda = data.get("desconto", 0)
        venda.subtotal = subtotal
        venda.desconto = desconto_venda
        venda.total = subtotal - desconto_venda

        db.session.commit()

        return jsonify(venda.to_dict()), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@vendas_bp.route("/", methods=["GET"])
def listar_vendas():
    """Lista vendas com filtros"""
    try:
        # Filtros
        data_inicio = request.args.get("data_inicio")
        data_fim = request.args.get("data_fim")
        cliente_id = request.args.get("cliente_id", type=int)

        # Query base
        query = Venda.query

        # Aplica filtros
        if data_inicio:
            query = query.filter(
                Venda.created_at >= datetime.fromisoformat(data_inicio)
            )
        if data_fim:
            query = query.filter(Venda.created_at <= datetime.fromisoformat(data_fim))
        if cliente_id:
            query = query.filter_by(cliente_id=cliente_id)

        # Ordenação
        query = query.order_by(Venda.created_at.desc())

        # Paginação
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        vendas = query.paginate(page=page, per_page=per_page, error_out=False)

        return (
            jsonify(
                {
                    "vendas": [venda.to_dict() for venda in vendas.items],
                    "total": vendas.total,
                    "pagina": vendas.page,
                    "por_pagina": vendas.per_page,
                    "total_paginas": vendas.pages,
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@vendas_bp.route("/<int:id>", methods=["GET"])
def obter_venda(id):
    """Obtém uma venda específica"""
    try:
        venda = Venda.query.get_or_404(id)
        return jsonify(venda.to_dict()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 404


@vendas_bp.route("/hoje", methods=["GET"])
def vendas_hoje():
    """Retorna o total de vendas de hoje"""
    try:
        hoje = datetime.now().date()

        # Total de vendas hoje
        total_hoje = (
            db.session.query(db.func.sum(Venda.total))
            .filter(db.func.date(Venda.created_at) == hoje)
            .scalar()
            or 0
        )

        # Quantidade de vendas hoje
        quantidade_hoje = Venda.query.filter(
            db.func.date(Venda.created_at) == hoje
        ).count()

        return (
            jsonify(
                {
                    "total_hoje": float(total_hoje),
                    "quantidade_hoje": quantidade_hoje,
                    "data": hoje.isoformat(),
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@vendas_bp.route("/dashboard", methods=["GET"])
def dashboard_vendas():
    """Dados para dashboard de vendas"""
    try:
        # Vendas dos últimos 7 dias
        sete_dias_atras = datetime.now().date().replace(day=datetime.now().day - 7)

        vendas_7_dias = (
            db.session.query(
                db.func.date(Venda.created_at).label("data"),
                db.func.sum(Venda.total).label("total"),
            )
            .filter(db.func.date(Venda.created_at) >= sete_dias_atras)
            .group_by(db.func.date(Venda.created_at))
            .order_by(db.func.date(Venda.created_at))
            .all()
        )

        # Formata dados
        dados_vendas = [
            {"data": data.isoformat(), "total": float(total)}
            for data, total in vendas_7_dias
        ]

        return (
            jsonify(
                {
                    "vendas_7_dias": dados_vendas,
                    "periodo": {
                        "inicio": sete_dias_atras.isoformat(),
                        "fim": datetime.now().date().isoformat(),
                    },
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500
