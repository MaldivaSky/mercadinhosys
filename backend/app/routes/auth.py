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
        estabelecimento_id = data.get("estabelecimento_id", 4)  # Default para 4

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

        # Verificar status
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

        # Identity como string (user_id)
        identity = str(funcionario.id)

        # Claims adicionais
        additional_claims = {
            "username": funcionario.username,
            "nome": funcionario.nome,
            "estabelecimento_id": funcionario.estabelecimento_id,
            "status": status,
        }

        # Adicionar role
        if hasattr(funcionario, "role"):
            additional_claims["role"] = funcionario.role
        else:
            cargo = funcionario.cargo
            if cargo == "dono":
                additional_claims["role"] = "admin"
            elif cargo == "gerente":
                additional_claims["role"] = "gerente"
            else:
                additional_claims["role"] = "funcionario"

        # Criar tokens
        access_token = create_access_token(
            identity=identity,
            additional_claims=additional_claims,
            expires_delta=timedelta(hours=8),
        )

        refresh_token = create_refresh_token(
            identity=identity, additional_claims=additional_claims
        )

        current_app.logger.info(f"Login bem-sucedido: {username} ({funcionario.nome})")

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Login realizado com sucesso",
                    "data": {
                        "access_token": access_token,
                        "refresh_token": refresh_token,
                        "user": {
                            "id": funcionario.id,
                            "nome": funcionario.nome,
                            "username": funcionario.username,
                            "email": funcionario.email,
                            "cargo": funcionario.cargo,
                            "role": additional_claims["role"],
                            "status": status,
                            "estabelecimento_id": funcionario.estabelecimento_id,
                        },
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
        claims = get_jwt()

        # Extrair claims adicionais
        additional_claims = {
            "username": claims.get("username"),
            "nome": claims.get("nome"),
            "estabelecimento_id": claims.get("estabelecimento_id"),
            "status": claims.get("status"),
            "role": claims.get("role"),
        }

        access_token = create_access_token(
            identity=current_user,
            additional_claims=additional_claims,
            expires_delta=timedelta(hours=8),
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
        current_user_id = get_jwt_identity()
        claims = get_jwt()

        # Buscar funcionário para garantir que ainda existe
        funcionario = Funcionario.query.get(int(current_user_id))

        if not funcionario:
            return jsonify({"success": False, "error": "Usuário não encontrado"}), 404

        # Usar dados do token (mais rápidos)
        user_data = {
            "id": int(current_user_id),
            "username": claims.get("username"),
            "nome": claims.get("nome"),
            "estabelecimento_id": claims.get("estabelecimento_id"),
            "role": claims.get("role"),
            "status": claims.get("status"),
        }

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Token válido",
                    "data": {"user": user_data, "is_valid": True},
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
        current_user_id = get_jwt_identity()
        current_app.logger.info(f"Logout: {current_user_id}")

        return (
            jsonify({"success": True, "message": "Logout realizado com sucesso"}),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Erro no logout: {str(e)}")
        return jsonify({"success": False, "error": "Erro no logout"}), 500
