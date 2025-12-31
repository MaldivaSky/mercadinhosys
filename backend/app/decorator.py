from functools import wraps
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask import jsonify


def funcionario_required(f):
    """Decorator para exigir autenticação de funcionário"""

    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        current_user = get_jwt_identity()

        # Verifica se o usuário está autenticado
        if not current_user:
            return jsonify({"error": "Token inválido ou expirado"}), 401

        # Verifica se é funcionário (tem user_id)
        if "user_id" not in current_user:
            return jsonify({"error": "Token inválido"}), 401

        # Verifica se não está bloqueado
        if current_user.get("status") != "ativo":
            return (
                jsonify(
                    {
                        "error": "Acesso bloqueado",
                        "message": f"Sua conta está {current_user.get('status')}. Contate o administrador.",
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
        current_user = get_jwt_identity()

        # Verifica se o usuário está autenticado
        if not current_user:
            return jsonify({"error": "Token inválido ou expirado"}), 401

        # Verifica se é admin
        if current_user.get("role") != "admin":
            return (
                jsonify(
                    {
                        "error": "Acesso restrito",
                        "message": "Apenas administradores podem acessar esta funcionalidade",
                    }
                ),
                403,
            )

        # Verifica se não está bloqueado
        if current_user.get("status") != "ativo":
            return jsonify({"error": "Acesso bloqueado"}), 403

        return f(*args, **kwargs)

    return decorated_function


def gerente_ou_admin_required(f):
    """Decorator para exigir autenticação de gerente ou admin"""

    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        current_user = get_jwt_identity()

        # Verifica se o usuário está autenticado
        if not current_user:
            return jsonify({"error": "Token inválido ou expirado"}), 401

        # Verifica se é gerente ou admin
        allowed_roles = ["gerente", "admin"]
        if current_user.get("role") not in allowed_roles:
            return (
                jsonify(
                    {
                        "error": "Acesso restrito",
                        "message": "Apenas gerentes ou administradores podem acessar",
                    }
                ),
                403,
            )

        # Verifica se não está bloqueado
        if current_user.get("status") != "ativo":
            return jsonify({"error": "Acesso bloqueado"}), 403

        return f(*args, **kwargs)

    return decorated_function
