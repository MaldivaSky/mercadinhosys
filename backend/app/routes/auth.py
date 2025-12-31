from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    get_jwt,
)
from datetime import datetime, timedelta
from app import db
from app.models import Funcionario, Estabelecimento
import traceback

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json()

        if not data:
            return jsonify({"success": False, "error": "Dados não fornecidos"}), 400

        username = data.get("username")
        senha = data.get("senha")
        estabelecimento_id = data.get("estabelecimento_id", 1)

        if not username or not senha:
            return (
                jsonify(
                    {"success": False, "error": "Username e senha são obrigatórios"}
                ),
                400,
            )

        # Buscar funcionário pelo username e estabelecimento_id
        funcionario = Funcionario.query.filter_by(
            username=username, estabelecimento_id=estabelecimento_id
        ).first()

        if not funcionario:
            current_app.logger.warning(
                f"Tentativa de login com username não encontrado: {username}"
            )
            return jsonify({"success": False, "error": "Credenciais inválidas"}), 401

        # Verificar senha
        if not funcionario.check_senha(senha):
            current_app.logger.warning(f"Senha incorreta para username: {username}")
            return jsonify({"success": False, "error": "Credenciais inválidas"}), 401

        # Verificar status (usando o campo ativo ou status)
        # Se tiver o campo status, usa ele, senão usa o ativo
        if hasattr(funcionario, "status"):
            status = funcionario.status
        else:
            status = "ativo" if funcionario.ativo else "inativo"

        if status != "ativo":
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Conta inativa",
                        "message": f"Sua conta está {status}. Contate o administrador.",
                    }
                ),
                403,
            )

        # Preparar os dados para o token
        identity_data = {
            "user_id": funcionario.id,
            "username": funcionario.username,
            "nome": funcionario.nome,
            "estabelecimento_id": funcionario.estabelecimento_id,
            "status": status,
        }

        # Adicionar role se existir
        if hasattr(funcionario, "role"):
            identity_data["role"] = funcionario.role
        else:
            # Mapear cargo para role
            cargo = funcionario.cargo
            if cargo == "dono":
                identity_data["role"] = "admin"
            elif cargo == "gerente":
                identity_data["role"] = "gerente"
            else:
                identity_data["role"] = "funcionario"

        access_token = create_access_token(
            identity=identity_data, expires_delta=timedelta(hours=8)
        )

        refresh_token = create_refresh_token(identity=identity_data)

        current_app.logger.info(f"Login bem-sucedido: {username} ({funcionario.nome})")

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Login realizado com sucesso",
                    "data": {
                        "access_token": access_token,
                        "refresh_token": refresh_token,
                        "user": funcionario.to_dict(),
                        "token_type": "bearer",
                        "expires_in": 28800,
                    },
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Erro no login: {str(e)}\n{traceback.format_exc()}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Erro interno no servidor",
                    "message": str(e),
                }
            ),
            500,
        )


@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    try:
        current_user = get_jwt_identity()
        access_token = create_access_token(
            identity=current_user, expires_delta=timedelta(hours=8)
        )

        return (
            jsonify(
                {
                    "success": True,
                    "access_token": access_token,
                    "token_type": "bearer",
                    "expires_in": 28800,
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Erro no refresh token: {str(e)}")
        return jsonify({"success": False, "error": "Token inválido ou expirado"}), 401


@auth_bp.route("/validate", methods=["GET"])
@jwt_required()
def validate_token():
    try:
        current_user = get_jwt_identity()
        funcionario = Funcionario.query.get(current_user.get("user_id"))

        if not funcionario:
            return jsonify({"success": False, "error": "Usuário não encontrado"}), 404

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Token válido",
                    "data": {"user": funcionario.to_dict(), "is_valid": True},
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Erro na validação do token: {str(e)}")
        return jsonify({"success": False, "error": "Token inválido"}), 401


@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    try:
        current_user = get_jwt_identity()
        current_app.logger.info(f"Logout: {current_user.get('username')}")

        return (
            jsonify({"success": True, "message": "Logout realizado com sucesso"}),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Erro no logout: {str(e)}")
        return jsonify({"success": False, "error": "Erro no logout"}), 500

# Outras rotas (alterar senha, setup, etc.) podem ser adicionadas depois
