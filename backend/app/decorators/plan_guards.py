from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt

PLAN_HIERARCHY = {
    'Gratuito': 1,
    'Pro': 2,
    'Superadmin': 99
}

def plan_required(min_plan='Gratuito'):
    """
    Decorator para exigir um plano mínimo para acesso à rota.
    Super Admins sempre têm acesso ignorando o plano.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flask_jwt_extended import verify_jwt_in_request
            verify_jwt_in_request()
            claims = get_jwt()
            
            # 1. Super Admin Bypass (Total)
            if claims.get('is_super_admin'):
                print(f"DEBUG: SUPER ADMIN BYPASS PLANO ATIVADO PARA: {claims.get('sub')}")
                return f(*args, **kwargs)
            
            # 2. Busca em Tempo Real
            try:
                from app.models import Estabelecimento
                est_id = claims.get('estabelecimento_id')
                if not est_id or est_id == 'all':
                    return f(*args, **kwargs)
                
                est = Estabelecimento.query.get(est_id)
                if not est:
                    return jsonify({"success": False, "error": "Estabelecimento não encontrado"}), 404
                
                current_plan = est.plano or 'Gratuito'
                current_status = est.plano_status or 'ativo'
            except Exception:
                current_plan = claims.get('plano', 'Gratuito')
                current_status = claims.get('plano_status', 'ativo')

            # Normalização Sênior (SÓ PRO E GRATUITO EXISTEM AGORA)
            def normalize_plan(p):
                """Normalização Sênior unificada com o sistema de autenticação"""
                s = str(p or 'Gratuito').lower().strip()
                if any(x in s for x in ['pro', 'premium', 'elite', 'advanced', 'enterprise', 'master', 'pago', 'basic', 'basico']):
                    return 'Pro'
                return 'Gratuito'

            user_plan_norm = normalize_plan(current_plan)
            min_plan_norm = normalize_plan(min_plan)
            
            user_level = PLAN_HIERARCHY.get(user_plan_norm, 1)
            required_level = PLAN_HIERARCHY.get(min_plan_norm, 1)
            
            if user_level < required_level:
                return jsonify({
                    "success": False,
                    "error": f"Acesso Negado: O Plano {user_plan_norm} não inclui esta ferramenta. Upgrade para Pro necessário.",
                    "code": "PLAN_RESTRICTED"
                }), 403
            
            if current_status in ['suspenso', 'cancelado']:
                return jsonify({
                    "success": False,
                    "error": "Assinatura inativa. Regularize seu acesso.",
                    "code": "SUBSCRIPTION_INACTIVE"
                }), 403
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def quota_required(model_name):
    """
    Decorator para validar cotas do plano Gratuito antes de salvar.
    Modelos suportados: 'produto', 'cliente', 'fornecedor', 'funcionario'
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flask_jwt_extended import verify_jwt_in_request
            verify_jwt_in_request()
            claims = get_jwt()
            
            if claims.get('is_super_admin'):
                return f(*args, **kwargs)

            try:
                from app.models import Estabelecimento, Produto, Cliente, Fornecedor, Funcionario
                est_id = claims.get('estabelecimento_id')
                est = Estabelecimento.query.get(est_id)
                
                plano = (est.plano or 'Gratuito').title()
                if plano in ['Pro', 'Enterprise', 'Premium', 'Advanced']:
                    # Plano Pro tem cotas ilimitadas (exceto funcionários que é 3)
                    if model_name == 'funcionario':
                        count = Funcionario.query.filter_by(estabelecimento_id=est_id, ativo=True).count()
                        if count >= 3:
                            return jsonify({"success": False, "error": "Limite de 3 funcionários atingido no Plano Pro."}), 403
                    return f(*args, **kwargs)

                # Regras Plano Gratuito
                if model_name == 'produto':
                    count = Produto.query.filter_by(estabelecimento_id=est_id).count()
                    if count >= 100:
                        return jsonify({"success": False, "error": "Limite de 100 produtos atingido (Plano Gratuito)."}), 403
                elif model_name == 'cliente':
                    count = Cliente.query.filter_by(estabelecimento_id=est_id).count()
                    if count >= 200:
                        return jsonify({"success": False, "error": "Limite de 200 clientes atingido (Plano Gratuito)."}), 403
                elif model_name == 'fornecedor':
                    count = Fornecedor.query.filter_by(estabelecimento_id=est_id).count()
                    if count >= 50:
                        return jsonify({"success": False, "error": "Limite de 50 fornecedores atingido (Plano Gratuito)."}), 403
                elif model_name == 'funcionario':
                    count = Funcionario.query.filter_by(estabelecimento_id=est_id, ativo=True).count()
                    if count >= 1:
                        return jsonify({"success": False, "error": "Limite de 1 funcionário atingido (Plano Gratuito)."}), 403

            except Exception as e:
                from flask import current_app
                current_app.logger.error(f"Erro ao validar quota: {e}")
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def permission_required(resource):
    """
    Decorator para validar permissão de acesso ao recurso baseada no cargo e plano.
    Garante que o 'Caixa' tenha acessos diferentes no Gratuito vs Pro.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flask_jwt_extended import verify_jwt_in_request
            verify_jwt_in_request()
            claims = get_jwt()
            
            # 1. Admin/Super Admin Bypass (Total e Insensível a Maiúsculas)
            role = (claims.get('role') or '').upper()
            is_admin_role = role in ['ADMIN', 'ADMINISTRADOR', 'PROPRIETARIO', 'GERENTE', 'DONO', 'MASTER']
            if claims.get('is_super_admin') or is_admin_role:
                return f(*args, **kwargs)

            # 2. Obter Plano Atual (Tempo Real)
            try:
                from app.models import Estabelecimento
                est_id = claims.get('estabelecimento_id')
                est = Estabelecimento.query.get(est_id)
                plano = (est.plano or 'Gratuito').title()
                
                # Normalização Pro
                if plano in ['Pro', 'Enterprise', 'Premium', 'Advanced']:
                    plano = 'Pro'
                else:
                    plano = 'Gratuito'
            except:
                plano = claims.get('plano', 'Gratuito').title()

            role = (claims.get('role') or '').lower()
            
            # 3. REGRAS POR CARGO (Mapeamento solicitado pelo usuário)
            if role == 'caixa':
                # No Gratuito: PDV, Clientes, Vendas
                # No Pro: PDV, Clientes, Vendas + Ponto
                allowed_gratuito = ['pdv', 'clientes', 'vendas', 'gestao_caixa']
                allowed_pro = ['pdv', 'clientes', 'vendas', 'gestao_caixa', 'ponto']
                
                allowed_list = allowed_pro if plano == 'Pro' else allowed_gratuito
                
                if resource not in allowed_list:
                    return jsonify({
                        "success": False,
                        "error": f"Acesso Negado: O cargo 'Caixa' no Plano {plano} não tem permissão para acessar '{resource}'."
                    }), 403
            
            # 4. Outros cargos no Plano Pro (Estoque, Gerente) liberados
            if plano == 'Pro':
                return f(*args, **kwargs)
            
            # 5. No Plano Gratuito, recursos avançados (Ponto) negados para todos
            if resource == 'ponto' and plano == 'Gratuito':
                return jsonify({
                    "success": False,
                    "error": "O Controle de Ponto está disponível apenas no Plano Pro."
                }), 403

            return f(*args, **kwargs)
        return decorated_function
    return decorator
