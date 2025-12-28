from flask import Blueprint, request, jsonify
from app import db
from app.models import Produto
from datetime import datetime
import json

produtos_bp = Blueprint("produtos", __name__)


@produtos_bp.route("/", methods=["GET"])
def listar_produtos():
    """Lista todos os produtos com filtros"""
    try:
        # Filtros
        categoria = request.args.get("categoria")
        nome = request.args.get("nome")
        ativo = request.args.get("ativo", "true").lower() == "true"

        # Query base
        query = Produto.query.filter_by(ativo=ativo)

        # Aplica filtros
        if categoria:
            query = query.filter_by(categoria=categoria)
        if nome:
            query = query.filter(Produto.nome.ilike(f"%{nome}%"))

        # Paginação
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        produtos = query.paginate(page=page, per_page=per_page, error_out=False)

        return (
            jsonify(
                {
                    "produtos": [produto.to_dict() for produto in produtos.items],
                    "total": produtos.total,
                    "pagina": produtos.page,
                    "por_pagina": produtos.per_page,
                    "total_paginas": produtos.pages,
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@produtos_bp.route("/<int:id>", methods=["GET"])
def obter_produto(id):
    """Obtém um produto específico"""
    try:
        produto = Produto.query.get_or_404(id)
        return jsonify(produto.to_dict()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 404


@produtos_bp.route("/", methods=["POST"])
def criar_produto():
    """Cria um novo produto"""
    try:
        data = request.get_json()

        # Validações básicas
        if (
            not data.get("codigo_barras")
            or not data.get("nome")
            or not data.get("preco_venda")
        ):
            return jsonify({"error": "Campos obrigatórios faltando"}), 400

        # Verifica se código de barras já existe
        if Produto.query.filter_by(codigo_barras=data["codigo_barras"]).first():
            return jsonify({"error": "Código de barras já cadastrado"}), 409

        # Cria produto
        produto = Produto(
            codigo_barras=data["codigo_barras"],
            nome=data["nome"],
            descricao=data.get("descricao", ""),
            preco_custo=data.get("preco_custo", 0),
            preco_venda=data["preco_venda"],
            quantidade=data.get("quantidade", 0),
            quantidade_minima=data.get("quantidade_minima", 10),
            categoria=data.get("categoria", "Outros"),
            ativo=data.get("ativo", True),
        )

        # Data de validade (se fornecida)
        if data.get("data_validade"):
            produto.data_validade = datetime.fromisoformat(data["data_validade"])

        db.session.add(produto)
        db.session.commit()

        return jsonify(produto.to_dict()), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@produtos_bp.route("/<int:id>", methods=["PUT"])
def atualizar_produto(id):
    """Atualiza um produto existente"""
    try:
        produto = Produto.query.get_or_404(id)
        data = request.get_json()

        # Atualiza campos
        if "nome" in data:
            produto.nome = data["nome"]
        if "descricao" in data:
            produto.descricao = data["descricao"]
        if "preco_custo" in data:
            produto.preco_custo = data["preco_custo"]
        if "preco_venda" in data:
            produto.preco_venda = data["preco_venda"]
        if "quantidade" in data:
            produto.quantidade = data["quantidade"]
        if "quantidade_minima" in data:
            produto.quantidade_minima = data["quantidade_minima"]
        if "categoria" in data:
            produto.categoria = data["categoria"]
        if "ativo" in data:
            produto.ativo = data["ativo"]
        if "data_validade" in data:
            produto.data_validade = (
                datetime.fromisoformat(data["data_validade"])
                if data["data_validade"]
                else None
            )

        db.session.commit()
        return jsonify(produto.to_dict()), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@produtos_bp.route("/<int:id>", methods=["DELETE"])
def excluir_produto(id):
    """Exclui um produto (soft delete)"""
    try:
        produto = Produto.query.get_or_404(id)
        produto.ativo = False
        db.session.commit()
        return jsonify({"message": "Produto desativado com sucesso"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@produtos_bp.route("/codigo/<string:codigo>", methods=["GET"])
def buscar_por_codigo(codigo):
    """Busca produto por código de barras"""
    try:
        produto = Produto.query.filter_by(codigo_barras=codigo, ativo=True).first()
        if produto:
            return jsonify(produto.to_dict()), 200
        else:
            return jsonify({"error": "Produto não encontrado"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@produtos_bp.route("/estoque-baixo", methods=["GET"])
def estoque_baixo():
    """Lista produtos com estoque abaixo do mínimo"""
    try:
        produtos = Produto.query.filter(
            Produto.quantidade <= Produto.quantidade_minima, Produto.ativo == True
        ).all()

        return jsonify([produto.to_dict() for produto in produtos]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
