# decorator.py - VERSÃO CORRIGIDA
from functools import wraps
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from flask import jsonify


def funcionario_required(f):
    """Decorator para exigir autenticação de funcionário"""

    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        current_user_id = get_jwt_identity()
        claims = get_jwt()  # ✅ Agora pega os claims adicionais

        # Verifica se o usuário está autenticado
        if not current_user_id:
            return jsonify({"error": "Token inválido ou expirado"}), 401

        # Verifica se não está bloqueado - agora usa claims
        if claims.get("status") != "ativo":
            return (
                jsonify(
                    {
                        "error": "Acesso bloqueado",
                        "message": f"Sua conta está {claims.get('status')}. Contate o administrador.",
                    }
                ),
                403,
            )

        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    """Decorator para exigir autenticação de administrador"""

    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        current_user_id = get_jwt_identity()
        claims = get_jwt()  # ✅ Agora pega os claims adicionais

        # Verifica se o usuário está autenticado
        if not current_user_id:
            return jsonify({"error": "Token inválido ou expirado"}), 401

        # Verifica se é admin - agora usa claims (Case Insensitive)
        role = claims.get("role", "").lower()
        if role != "admin":
            return (
                jsonify(
                    {
                        "error": "Acesso restrito",
                        "message": "Apenas administradores podem acessar esta funcionalidade",
                    }
                ),
                403,
            )

        # Verifica se não está bloqueado - agora usa claims
        status = claims.get("status", "").lower()
        if status != "ativo":
            return jsonify({"error": "Acesso bloqueado"}), 403

        return f(*args, **kwargs)

    return decorated_function


def gerente_ou_admin_required(f):
    """Decorator para exigir autenticação de gerente ou admin"""

    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        current_user_id = get_jwt_identity()
        claims = get_jwt()  # ✅ Agora pega os claims adicionais

        # Verifica se o usuário está autenticado
        if not current_user_id:
            return jsonify({"error": "Token inválido ou expirado"}), 401

        # Verifica se é gerente ou admin - agora usa claims (Case Insensitive)
        role = claims.get("role", "").lower()
        allowed_roles = ["gerente", "admin", "administrador"]
        
        if role not in allowed_roles:
            return (
                jsonify(
                    {
                        "error": "Acesso restrito",
                        "message": "Apenas gerentes ou administradores podem acessar",
                    }
                ),
                403,
            )

        # Verifica se não está bloqueado - agora usa claims
        status = claims.get("status", "").lower()
        if status != "ativo":
            return jsonify({"error": "Acesso bloqueado"}), 403

        return f(*args, **kwargs)

    return decorated_function


def gerente_required(f):
    """Decorator para exigir autenticação de gerente"""

    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        current_user_id = get_jwt_identity()
        claims = get_jwt()  # ✅ Agora pega os claims adicionais

        # Verifica se o usuário está autenticado
        if not current_user_id:
            return jsonify({"error": "Token inválido ou expirado"}), 401

        # Verifica se é gerente - agora usa claims
        if claims.get("role") != "gerente":
            return (
                jsonify(
                    {
                        "error": "Acesso restrito",
                        "message": "Apenas gerentes podem acessar esta funcionalidade",
                    }
                ),
                403,
            )

        # Verifica se não está bloqueado - agora usa claims
        if claims.get("status") != "ativo":
            return jsonify({"error": "Acesso bloqueado"}), 403

        return f(*args, **kwargs)

    return decorated_function
