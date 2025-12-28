from flask import Blueprint, request, jsonify
from app import db
from app.models import Cliente
import re

clientes_bp = Blueprint("clientes", __name__)


def validar_cpf(cpf):
    """Valida CPF (formato básico)"""
    if not cpf:
        return True
    cpf = re.sub(r"\D", "", cpf)
    return len(cpf) == 11


def validar_email(email):
    """Valida email (formato básico)"""
    if not email:
        return True
    return re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email)


@clientes_bp.route("/", methods=["POST"])
def criar_cliente():
    """Cria um novo cliente"""
    try:
        data = request.get_json()

        # Validações
        if not data.get("nome"):
            return jsonify({"error": "Nome é obrigatório"}), 400

        if data.get("cpf") and not validar_cpf(data["cpf"]):
            return jsonify({"error": "CPF inválido"}), 400

        if data.get("email") and not validar_email(data["email"]):
            return jsonify({"error": "Email inválido"}), 400

        # Verifica se CPF já existe
        if data.get("cpf"):
            if Cliente.query.filter_by(cpf=data["cpf"]).first():
                return jsonify({"error": "CPF já cadastrado"}), 409

        # Cria cliente
        cliente = Cliente(
            nome=data["nome"],
            cpf=data.get("cpf"),
            telefone=data.get("telefone"),
            email=data.get("email"),
            endereco=data.get("endereco"),
            ativo=data.get("ativo", True),
        )

        # Data de nascimento
        if data.get("data_nascimento"):
            from datetime import datetime

            cliente.data_nascimento = datetime.fromisoformat(data["data_nascimento"])

        db.session.add(cliente)
        db.session.commit()

        return jsonify(cliente.to_dict()), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@clientes_bp.route("/", methods=["GET"])
def listar_clientes():
    """Lista clientes com filtros"""
    try:
        nome = request.args.get("nome")
        ativo = request.args.get("ativo", "true").lower() == "true"

        query = Cliente.query.filter_by(ativo=ativo)

        if nome:
            query = query.filter(Cliente.nome.ilike(f"%{nome}%"))

        # Paginação
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        clientes = query.paginate(page=page, per_page=per_page, error_out=False)

        return (
            jsonify(
                {
                    "clientes": [cliente.to_dict() for cliente in clientes.items],
                    "total": clientes.total,
                    "pagina": clientes.page,
                    "por_pagina": clientes.per_page,
                    "total_paginas": clientes.pages,
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@clientes_bp.route("/<int:id>", methods=["GET"])
def obter_cliente(id):
    """Obtém um cliente específico"""
    try:
        cliente = Cliente.query.get_or_404(id)
        return jsonify(cliente.to_dict()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 404


@clientes_bp.route("/<int:id>", methods=["PUT"])
def atualizar_cliente(id):
    """Atualiza um cliente existente"""
    try:
        cliente = Cliente.query.get_or_404(id)
        data = request.get_json()

        # Validações
        if data.get("cpf") and not validar_cpf(data["cpf"]):
            return jsonify({"error": "CPF inválido"}), 400

        if data.get("email") and not validar_email(data["email"]):
            return jsonify({"error": "Email inválido"}), 400

        # Atualiza campos
        if "nome" in data:
            cliente.nome = data["nome"]
        if "cpf" in data:
            cliente.cpf = data["cpf"]
        if "telefone" in data:
            cliente.telefone = data["telefone"]
        if "email" in data:
            cliente.email = data["email"]
        if "endereco" in data:
            cliente.endereco = data["endereco"]
        if "ativo" in data:
            cliente.ativo = data["ativo"]
        if "data_nascimento" in data:
            from datetime import datetime

            cliente.data_nascimento = (
                datetime.fromisoformat(data["data_nascimento"])
                if data["data_nascimento"]
                else None
            )

        db.session.commit()
        return jsonify(cliente.to_dict()), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
