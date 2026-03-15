"""
MercadinhoSys - Decoradores de Autenticação e Autorização
Implementa controle de acesso baseado em roles (RBAC)
"""

from functools import wraps
from flask import jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.models import Funcionario

def super_admin_required(f):
    """
    Decorator que exige que o usuário seja Super Admin (SaaS Owner)
    Permite acesso global a todos os dados do sistema
    """
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        try:
            # Obter ID do usuário do token
            current_user_id = get_jwt_identity()
            if not current_user_id:
                return jsonify({
                    "success": False,
                    "error": "Não autorizado",
                    "message": "Token inválido ou ausente"
                }), 401
            
            # Buscar usuário no banco
            user = Funcionario.query.get(current_user_id)
            if not user:
                return jsonify({
                    "success": False,
                    "error": "Não autorizado",
                    "message": "Usuário não encontrado"
                }), 401
            
            # Verificar se é Super Admin
            if not user.is_super_admin:
                return jsonify({
                    "success": False,
                    "error": "Acesso negado",
                    "message": "Acesso restrito ao Super Admin"
                }), 403
            
            # NORMALIZAÇÃO DE STATUS (Utilizando utilitário centralizado)
            from app.utils.auth_utils import normalize_status, is_user_active
            raw_status = getattr(user, 'status', 'ativo')
            status_val = normalize_status(raw_status)

            if not is_user_active(status_val):
                return jsonify({
                    "success": False,
                    "error": "Acesso bloqueado",
                    "message": f"Sua conta Super Admin está {status_val}. (REF: {raw_status})"
                }), 403
            
            # Adicionar metadata ao request para uso posterior
            request.current_user = user
            request.is_super_admin = True
            
            return f(*args, **kwargs)
            
        except Exception as e:
            current_app.logger.error(f"❌ Erro no decorator super_admin_required: {e}")
            return jsonify({
                "success": False,
                "error": "Erro interno de autenticação"
            }), 500
    
    return decorated_function

def tenant_or_super_admin_required(f):
    """
    Decorator que permite acesso ao:
    - Super Admin: acesso global a todos os tenants
    - Usuário comum: acesso apenas aos dados do seu estabelecimento
    
    O estabelecimento_id é extraído dos kwargs da rota ou do JWT token
    """
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        try:
            # Obter ID do usuário do token
            current_user_id = get_jwt_identity()
            if not current_user_id:
                return jsonify({
                    "success": False,
                    "error": "Não autorizado",
                    "message": "Token inválido ou ausente"
                }), 401
            
            # Buscar usuário no banco
            user = Funcionario.query.get(current_user_id)
            if not user:
                return jsonify({
                    "success": False,
                    "error": "Não autorizado",
                    "message": "Usuário não encontrado"
                }), 401
            
            # Verificar se é Super Admin
            if user.is_super_admin:
                request.current_user = user
                request.is_super_admin = True
                request.tenant_access = "global"
                return f(*args, **kwargs)
            
            # Para usuários comuns, verificar acesso ao tenant
            # Obter estabelecimento_id dos kwargs ou do JWT
            target_estabelecimento_id = kwargs.get('estabelecimento_id')
            
            # Se não estiver nos kwargs, tentar obter do JWT
            if not target_estabelecimento_id:
                jwt_claims = get_jwt()
                target_estabelecimento_id = jwt_claims.get('estabelecimento_id')
            
            # Se ainda não tiver, tentar do query params
            if not target_estabelecimento_id:
                target_estabelecimento_id = request.args.get('estabelecimento_id')
            
            # Converter para int se necessário
            if target_estabelecimento_id:
                try:
                    target_estabelecimento_id = int(target_estabelecimento_id)
                except (ValueError, TypeError):
                    return jsonify({
                        "success": False,
                        "error": "Parâmetro inválido",
                        "message": "estabelecimento_id deve ser um número"
                    }), 400
            
            # Verificar se o usuário tem acesso ao estabelecimento
            if target_estabelecimento_id and user.estabelecimento_id != target_estabelecimento_id:
                return jsonify({
                    "success": False,
                    "error": "Acesso negado",
                    "message": "Você não tem acesso a este estabelecimento"
                }), 403
            
            # NORMALIZAÇÃO DE STATUS (Utilizando utilitário centralizado)
            from app.utils.auth_utils import normalize_status, is_user_active
            raw_status = getattr(user, 'status', 'ativo')
            status_val = normalize_status(raw_status)

            if not is_user_active(status_val):
                return jsonify({
                    "success": False,
                    "error": "Acesso bloqueado",
                    "message": f"Sua conta está {status_val}. (REF: {raw_status})"
                }), 403
            
            # Adicionar metadata ao request
            request.current_user = user
            request.is_super_admin = False
            request.tenant_access = "restricted"
            request.allowed_estabelecimento_id = user.estabelecimento_id
            
            return f(*args, **kwargs)
            
        except Exception as e:
            current_app.logger.error(f"❌ Erro no decorator tenant_or_super_admin_required: {e}")
            return jsonify({
                "success": False,
                "error": "Erro interno de autenticação"
            }), 500
    
    return decorated_function

def role_required(*allowed_roles):
    """
    Decorator que exige que o usuário tenha uma das roles especificadas
    Uso: @role_required('ADMIN', 'GERENTE')
    """
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def decorated_function(*args, **kwargs):
            try:
                # Obter ID do usuário do token
                current_user_id = get_jwt_identity()
                if not current_user_id:
                    return jsonify({
                        "success": False,
                        "error": "Não autorizado",
                        "message": "Token inválido ou ausente"
                    }), 401
                
                # Buscar usuário no banco
                user = Funcionario.query.get(current_user_id)
                if not user:
                    return jsonify({
                        "success": False,
                        "error": "Não autorizado",
                        "message": "Usuário não encontrado"
                    }), 401
                
                # NORMALIZAÇÃO DE STATUS AGRESSIVA (Utilizando utilitário centralizado)
                from app.utils.auth_utils import normalize_status, is_user_active
                raw_status = getattr(user, 'status', 'ativo')
                status_val = normalize_status(raw_status)

                # Super Admin tem acesso a tudo (bypass de status se for realmente super)
                if user.is_super_admin:
                    request.current_user = user
                    request.is_super_admin = True
                    return f(*args, **kwargs)
                
                # Verificar Bloqueio
                if not is_user_active(status_val):
                     return jsonify({
                        "success": False,
                        "error": "Acesso bloqueado",
                        "message": f"Sua conta está {status_val}. Contate o administrador. (REF: {raw_status})"
                    }), 403

                # Verificar role do usuário
                if not user.role or user.role.upper() not in [role.upper() for role in allowed_roles]:
                    return jsonify({
                        "success": False,
                        "error": "Acesso negado",
                        "message": f"Acesso restrito às roles: {', '.join(allowed_roles)}"
                    }), 403
                
                # Adicionar metadata ao request
                request.current_user = user
                request.is_super_admin = False
                
                return f(*args, **kwargs)
                
            except Exception as e:
                current_app.logger.error(f"❌ Erro no decorator role_required: {e}")
                return jsonify({
                    "success": False,
                    "error": "Erro interno de autenticação"
                }), 500
        
        return decorated_function
    return decorator

def get_current_user_info():
    """
    Helper function para obter informações do usuário atual
    Retorna None se não houver usuário autenticado
    """
    if hasattr(request, 'current_user'):
        return {
            'id': request.current_user.id,
            'nome': request.current_user.nome,
            'email': request.current_user.email,
            'role': request.current_user.role,
            'estabelecimento_id': request.current_user.estabelecimento_id,
            'is_super_admin': getattr(request, 'is_super_admin', False),
            'tenant_access': getattr(request, 'tenant_access', None)
        }
    return None

def can_access_estabelecimento(estabelecimento_id: int) -> bool:
    """
    Helper function para verificar se o usuário atual pode acessar um estabelecimento
    """
    user_info = get_current_user_info()
    if not user_info:
        return False
    
    # Super Admin pode acessar tudo
    if user_info['is_super_admin']:
        return True
    
    # Usuário comum só pode acessar seu próprio estabelecimento
    return user_info['estabelecimento_id'] == estabelecimento_id
