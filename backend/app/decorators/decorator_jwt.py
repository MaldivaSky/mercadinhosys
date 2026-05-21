# decorator.py - VERSÃO CORRIGIDA
from functools import wraps
from flask_jwt_extended import jwt_required as jwt_required_flask, get_jwt_identity, get_jwt
from flask import jsonify


# Alias para compatibilidade
jwt_required = jwt_required_flask


def funcionario_required(f):
    """Decorator para exigir autenticação de funcionário with CORS support"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # BYPASS CORS OPTIONS (Preflight)
        # Garante que o navegador receba 200 OK para o handshake CORS antes de validar o token
        from flask import request
        if request.method == "OPTIONS":
            return jsonify({"success": True}), 200

        # Verificação Manual do JWT
        from flask_jwt_extended import verify_jwt_in_request
        try:
            verify_jwt_in_request()
        except Exception as e:
             return jsonify({"error": "Token inválido ou expirado", "details": str(e)}), 401

        current_user_id = get_jwt_identity()
        claims = get_jwt()  # ✅ Agora pega os claims adicionais

        # BYPASS PARA SUPER ADMIN (Auditoria SaaS)
        if claims.get("is_super_admin"):
            return f(*args, **kwargs)

        # Verifica se o usuário está autenticado
        if not current_user_id:
            return jsonify({"error": "Token inválido ou expirado"}), 401

        # NORMALIZAÇÃO DE STATUS AGRESSIVA (Utilizando utilitário centralizado)
        from app.utils.auth_utils import normalize_status, is_user_active
        
        raw_status = claims.get("status")
        status_val = normalize_status(raw_status)
        
        # LOG DE DEPURAÇÃO (Centralizado e Siliconado)
        from flask import current_app
        current_app.logger.info(f"🔍 [AUTH DOCTOR] Fingerprint: MERCADINHOV2_2026_MARCH_15_V1 | User: {current_user_id} | Status: {status_val}")

        # Verifica se não está bloqueado
        if not is_user_active(status_val):
            current_app.logger.warning(f"🚫 [BLOQUEIO] Acesso negado: user={current_user_id}, status={status_val}")
            return (
                jsonify(
                    {
                        "error": "Acesso bloqueado",
                        "message": f"Sua conta está {status_val}. Contate o administrador. (REF: {raw_status})",
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

        # BYPASS PARA SUPER ADMIN (Auditoria SaaS) - Engenharia ERP Master
        if claims.get("is_super_admin"):
            return f(*args, **kwargs)

        # Verifica se o usuário está autenticado
        if not current_user_id:
            return jsonify({"error": "Token inválido ou expirado"}), 401

        # Verifica se é admin - agora usa claims (Case Insensitive)
        role = claims.get("role", "").lower()
        allowed_admin_roles = ["admin", "administrador", "proprietario", "dono", "master", "gerente"]
        if role not in allowed_admin_roles:
            return (
                jsonify(
                    {
                        "error": "Acesso restrito",
                        "message": f"Apenas administradores podem acessar esta funcionalidade. Seu role: {role}",
                    }
                ),
                403,
            )

        # NORMALIZAÇÃO DE STATUS AGRESSIVA
        from app.utils.auth_utils import normalize_status, is_user_active
        raw_status = claims.get("status")
        status_val = normalize_status(raw_status)
        
        if not is_user_active(status_val):
            return jsonify({"error": "Acesso bloqueado", "message": f"Sua conta está {status_val}"}), 403

        return f(*args, **kwargs)

    return decorated_function


def gerente_ou_admin_required(f):
    """Decorator para exigir autenticação de gerente ou admin"""

    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        current_user_id = get_jwt_identity()
        claims = get_jwt()

        # BYPASS PARA SUPER ADMIN (Auditoria SaaS) - Engenharia ERP Master
        if claims.get("is_super_admin"):
            return f(*args, **kwargs)

        # Verifica se o usuário está autenticado
        if not current_user_id:
            return jsonify({"error": "Token inválido ou expirado"}), 401

        # Verifica se é gerente ou admin - agora usa claims (Case Insensitive)
        role = (claims.get("role") or "").lower()
        allowed_roles = ["gerente", "admin", "administrador", "proprietario", "dono", "master"]
        
        if role not in allowed_roles:
            return (
                jsonify(
                    {
                        "error": "Acesso restrito",
                        "message": f"Apenas gerentes ou administradores podem acessar. Seu role: {role}",
                    }
                ),
                403,
            )

        # NORMALIZAÇÃO DE STATUS AGRESSIVA
        from app.utils.auth_utils import normalize_status, is_user_active
        raw_status = claims.get("status")
        status_val = normalize_status(raw_status)
        
        if not is_user_active(status_val):
            return jsonify({"error": "Acesso bloqueado", "message": f"Sua conta está {status_val}"}), 403

        return f(*args, **kwargs)

    return decorated_function


# Decorator unificado para Super Admin
from app.decorators.rbac import super_admin_required


def gerente_required(f):
    """Decorator para exigir autenticação de gerente"""

    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        current_user_id = get_jwt_identity()
        claims = get_jwt()  # ✅ Agora pega os claims adicionais

        # BYPASS PARA SUPER ADMIN (Auditoria SaaS) - Engenharia ERP Master
        if claims.get("is_super_admin"):
            return f(*args, **kwargs)

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

        # NORMALIZAÇÃO DE STATUS AGRESSIVA
        from app.utils.auth_utils import normalize_status, is_user_active
        raw_status = claims.get("status")
        status_val = normalize_status(raw_status)
        
        if not is_user_active(status_val):
            return jsonify({"error": "Acesso bloqueado", "message": f"Sua conta está {status_val}"}), 403

        return f(*args, **kwargs)

    return decorated_function
