"""
Rotas de Autenticação Multi-Tenant
Autenticação global com redirecionamento para banco do tenant
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt, get_jwt_identity
from werkzeug.security import check_password_hash
from datetime import timedelta
import psycopg2
import os
import pytz
from datetime import datetime
from app.middleware.multi_tenant import tenant_manager
from app import db
from app.models import Funcionario, Estabelecimento

auth_bp = Blueprint('auth_multi_tenant', __name__)

def get_main_connection():
    """Obtém conexão com banco principal de autenticação"""
    main_url = os.getenv('MAIN_DATABASE_URL')
    return psycopg2.connect(main_url)

def normalize_plan_name(p):
    """Garante retorno apenas de Pro ou Gratuito no motor de auth"""
    s = str(p or 'Gratuito').lower().strip()
    if any(x in s for x in ['pro', 'premium', 'elite', 'advanced', 'enterprise', 'master', 'pago']):
        return 'Pro'
    return 'Gratuito'

@auth_bp.route('/bootstrap', methods=['POST'])
def bootstrap_admin():
    """
    Endpoint de emergência para inicializar o sistema.
    Cria o primeiro estabelecimento e o administrador se o banco estiver vazio.
    """
    from werkzeug.security import generate_password_hash
    from decimal import Decimal
    
    try:
        data = request.get_json() or {}
        identifier = (data.get("email") or data.get("username") or data.get("identifier") or "").strip()
        senha = (data.get("senha") or data.get("password") or "").strip()

        if not identifier or not senha:
            return jsonify({
                "success": False,
                "error": "Email/Username e senha são obrigatórios",
                "code": "CREDENTIALS_REQUIRED"
            }), 400

        # Bloqueio de segurança: Só permite se não houver NENHUM usuário
        if Funcionario.query.first() is not None:
            return jsonify({
                "success": False,
                "error": "Bootstrap indisponível: o sistema já possui usuários",
                "code": "BOOTSTRAP_DISABLED"
            }), 409

        # Determinar email e username
        if "@" in identifier:
            email = identifier.lower()
            username = identifier.split("@", 1)[0]
        else:
            username = identifier
            email = f"{username}@mercadinhosys.com"

        # Tenta pegar primeiro estabelecimento ou cria um Mock de bootstrap
        estabelecimento = Estabelecimento.query.first()
        if estabelecimento is None:
            estabelecimento = Estabelecimento(
                nome_fantasia="Sistema Central",
                razao_social="MercadinhoSys Bootstrap",
                cnpj="00.000.000/0001-00",
                email="suporte@mercadinhosys.com",
                telefone="(00) 0000-0000",
                ativo=True,
                data_abertura=datetime.utcnow().date()
            )
            db.session.add(estabelecimento)
            db.session.flush()

        admin = Funcionario(
            estabelecimento_id=estabelecimento.id,
            nome="Administrador do Sistema",
            username=username,
            senha=generate_password_hash(senha),
            email=email,
            cpf="000.000.000-00",
            cargo="Super Admin",
            role="ADMIN",
            is_super_admin=True,
            ativo=True,
            status="ativo",
            data_admissao=datetime.utcnow().date(),
            permissoes_json='{"pdv":true,"estoque":true,"compras":true,"financeiro":true,"configuracoes":true,"relatorios":true}'
        )
        db.session.add(admin)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Sistema inicializado com sucesso. Faça login com as credenciais fornecidas.",
            "data": {"username": admin.username, "email": admin.email}
        }), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro no bootstrap multitenant: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Erro interno ao inicializar sistema",
            "message": str(e)
        }), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login multi-tenant - autentica global e redireciona para tenant"""
    try:
        data = request.get_json(silent=True) or {}
        
        # Captura flexível com validação obrigatória
        username = (data.get('identifier') or data.get('username') or data.get('email')).strip()
        senha = (data.get('senha') or data.get('password')).strip()
        
        if not username or not senha:
            return jsonify({
                'success': False,
                'error': 'Identificador e senha são obrigatórios para sua segurança.',
                'code': 'CREDENTIALS_REQUIRED'
            }), 400
        
        # 1. TENTATIVA: BANCO PRINCIPAL (POSTGRES / CLOUD)
        all_matches = []
        try:
            conn = get_main_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT f.id, f.nome, f.email, f.senha, f.role, f.estabelecimento_id,
                           e.nome_fantasia, 'postgresql' as database_name, e.ativo, e.razao_social, e.cnpj, f.is_super_admin,
                           e.plano, e.plano_status
                    FROM public.funcionarios f
                    JOIN public.estabelecimentos e ON f.estabelecimento_id = e.id
                    WHERE (LOWER(f.email) = LOWER(%s) OR LOWER(f.username) = LOWER(%s)) 
                      AND f.ativo = true 
                      AND e.ativo = true
                    ORDER BY f.id ASC
                """, (username, username))
                all_matches = cursor.fetchall()
                cursor.close()
                conn.close()
        except Exception as e:
            current_app.logger.warning(f"[AUTH] Falha conexão Postgres (possível modo offline): {str(e)}")
        
        # 2. SEGUNDA TENTATIVA: BANCO LOCAL (SQLITE) - ESSENCIAL PARA SIMULAÇÃO E DESENVOLVIMENTO
        if not all_matches:
            funcionario_local = Funcionario.query.filter(
                db.or_(
                    db.func.lower(Funcionario.username) == username.lower(),
                    db.func.lower(Funcionario.email) == username.lower()
                ),
                Funcionario.ativo == True
            ).first()

            if funcionario_local and funcionario_local.check_password(senha):
                estab = funcionario_local.estabelecimento
                is_super = bool(funcionario_local.is_super_admin)
                
                additional_claims = {
                    'role': (funcionario_local.role or 'FUNCIONARIO').upper(),
                    'status': 'ativo',
                    'is_super_admin': is_super,
                    'estabelecimento_id': "all" if is_super else (funcionario_local.estabelecimento_id or "all"),
                    'estabelecimento_nome': estab.nome_fantasia if estab else "MercadinhoSys",
                    'database_name': 'local',
                    'user_id': funcionario_local.id,
                    'plano': normalize_plan_name(estab.plano) if estab else 'Gratuito',
                    'plano_status': estab.plano_status if estab else 'ativo'
                }
                
                identity = str(funcionario_local.id)
                access_token = create_access_token(identity=identity, additional_claims=additional_claims, expires_delta=timedelta(hours=24))
                refresh_token = create_refresh_token(identity=identity, additional_claims=additional_claims)

                return jsonify({
                    'success': True,
                    'access_token': access_token,
                    'refresh_token': refresh_token,
                    'data': {
                        'user': {
                            'id': funcionario_local.id,
                            'nome': funcionario_local.nome,
                            'email': funcionario_local.email,
                            'role': funcionario_local.role,
                            'cargo': getattr(funcionario_local, 'cargo', 'Administrador'),
                            'is_super_admin': is_super,
                            'estabelecimento_id': "all" if is_super else funcionario_local.estabelecimento_id,
                            'plano': normalize_plan_name(estab.plano) if estab else 'Gratuito',
                            'plano_status': estab.plano_status if estab else 'ativo',
                            'permissoes': funcionario_local.permissoes
                        }
                    },
                    'message': 'Login realizado com sucesso (Contexto Local)'
                }), 200
            
            return jsonify({'success': False, 'error': 'Usuário ou senha inválidos'}), 401
        
        # 3. PROCESSAR RESULTADO CLOUD
        user_data = all_matches[0]
        (user_id, user_nome, user_email, senha_val, role, estabelecimento_id,
         estabelecimento_nome, database_name, estabelecimento_status, razao_social, cnpj, is_super_db,
         plano_estab, plano_status_estab) = user_data
        
        if not check_password_hash(senha_val, senha):
            return jsonify({'success': False, 'error': 'Usuário ou senha inválidos'}), 401
        
        is_super = bool(is_super_db)
        
        # Criar token JWT com informações do tenant (Isolamento de Elite)
        additional_claims = {
            'role': "ADMIN" if is_super else role,
            'status': str(user_data[8] or "ativo"),
            'is_super_admin': is_super,
            'estabelecimento_id': "all" if bool(is_super_db) else estabelecimento_id,
            'estabelecimento_nome': estabelecimento_nome,
            'database_name': database_name,
            'user_id': user_id,
            'plano': normalize_plan_name(plano_estab),
            'plano_status': plano_status_estab or 'ativo'
        }
        
        identity = str(user_id)
        access_token = create_access_token(
            identity=identity,
            additional_claims=additional_claims,
            expires_delta=timedelta(hours=24)
        )
        refresh_token = create_refresh_token(
            identity=identity,
            additional_claims=additional_claims
        )
        
        return jsonify({
            'success': True,
            'access_token': access_token,
            'refresh_token': refresh_token,
            'data': {
                'user': {
                    'id': user_id,
                    'nome': user_nome,
                    'email': user_email,
                    'role': "ADMIN" if is_super else role,
                    'cargo': 'Administrador' if is_super else 'Funcionário',
                    'status': 'ativo',
                    'plano': normalize_plan_name(plano_estab) if not is_super else 'Pro',
                    'plano_status': plano_status_estab if not is_super else 'ativo',
                    'is_super_admin': is_super,
                    'estabelecimento_id': "all" if is_super else estabelecimento_id,
                    'permissoes': {
                        "pdv": True, "estoque": True, "vendas": True, "clientes": True, "financeiro": is_super, "configuracoes": is_super
                    }
                },
                'estabelecimento': {
                    'id': estabelecimento_id,
                    'nome': estabelecimento_nome,
                    'razao_social': razao_social,
                    'cnpj': cnpj,
                    'database_name': database_name,
                    'status': estabelecimento_status,
                    'plano': plano_estab,
                    'plano_status': plano_status_estab
                }
            },
            'message': f'Login realizado com sucesso - {estabelecimento_nome}'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Erro interno no servidor'
        }), 500

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Renovar access token em modo Multi-Tenant"""
    try:
        current_user = get_jwt_identity()
        claims = get_jwt()

        # Extrair claims do token atual para manter persistência de contexto
        # IMPORTANTE: Manter exatamente os mesmos campos do /login
        additional_claims = {
            'role': claims.get('role'),
            'status': claims.get('status') or 'ativo',
            'is_super_admin': claims.get('is_super_admin'),
            'estabelecimento_id': claims.get('estabelecimento_id'),
            'estabelecimento_nome': claims.get('estabelecimento_nome'),
            'database_name': claims.get('database_name'),
            'user_id': claims.get('user_id'),
            'plano': normalize_plan_name(claims.get('plano')),
            'plano_status': claims.get('plano_status')
        }

        # Criar novo access token
        access_token = create_access_token(
            identity=current_user,
            additional_claims=additional_claims,
            expires_delta=timedelta(hours=24)
        )
        
        return jsonify({
            'success': True,
            'access_token': access_token,
            'refresh_token': request.headers.get('Authorization', '').replace('Bearer ', '') # Retorna o mesmo refresh_token se necessário
        }), 200
    except Exception as e:
        current_app.logger.error(f"Erro no refresh Multi-Tenant: {str(e)}")
        return jsonify({'success': False, 'error': 'Não foi possível renovar o acesso'}), 401

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Obtém informações do usuário atual com dados do tenant"""
    try:
        claims = get_jwt()
        user_id = get_jwt_identity() # Agora é o ID (string)
        
        # --- TENTATIVA 1: BANCO PRINCIPAL (POSTGRES) ---
        user_data = None
        try:
            conn = get_main_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT f.id, f.nome, f.email, f.role, f.estabelecimento_id,
                       e.nome_fantasia, e.razao_social, e.cnpj, e.plano, e.plano_status
                FROM public.funcionarios f
                JOIN public.estabelecimentos e ON f.estabelecimento_id = e.id
                WHERE f.id = %s AND f.ativo = true
            """, (user_id,))
            user_data = cursor.fetchone()
            cursor.close()
            conn.close()
        except Exception:
            pass
            
        # --- TENTATIVA 2: BANCO LOCAL (SQLITE FALLBACK) ---
        if not user_data:
            from app.models import Funcionario
            f = Funcionario.query.get(int(user_id))
            if f:
                estab = f.estabelecimento
                user_data = (
                    f.id, f.nome, f.email, f.role, f.estabelecimento_id,
                    estab.nome_fantasia if estab else "MercadinhoSys",
                    estab.razao_social if estab else "",
                    estab.cnpj if estab else "",
                    estab.plano if estab else "Gratuito",
                    estab.plano_status if estab else "ativo"
                )
        
        if not user_data:
            return jsonify({
                'success': False,
                'error': 'Usuário não encontrado'
            }), 404
        
        (user_id, user_nome, user_email, role, estab_id, estab_nome, estab_razao, estab_cnpj, plano, plano_status) = user_data
        
        return jsonify({
            'success': True,
            'data': {
                'id': user_id,
                'nome': user_nome,
                'email': user_email,
                'role': role,
                'estabelecimento_id': estab_id,
                'estabelecimento_nome': estab_nome,
                'estabelecimento_razao_social': estab_razao,
                'estabelecimento_cnpj': estab_cnpj,
                'plano': normalize_plan_name(plano),
                'plano_status': plano_status
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Erro ao obter dados do usuário'
        }), 500

@auth_bp.route('/verify-tenant', methods=['GET'])
@jwt_required()
def verify_tenant():
    """Verifica se o banco do tenant está acessível"""
    try:
        claims = get_jwt()
        estabelecimento_id = claims.get('estabelecimento_id')
        estabelecimento_nome = claims.get('estabelecimento_nome')
        is_local = claims.get('database_name') == 'local'
        
        if not estabelecimento_id:
            return jsonify({
                'success': False,
                'error': 'Estabelecimento não encontrado no token'
            }), 400

        # Se for banco local, já está verificado por definição do fallback
        if is_local or str(estabelecimento_id).lower() == 'all':
             return jsonify({
                'success': True,
                'data': {
                    'estabelecimento_id': estabelecimento_id,
                    'estabelecimento_nome': estabelecimento_nome,
                    'database_status': 'online',
                    'message': 'Contexto local/global verificado'
                }
            }), 200
        
        # Tentar conexão com banco do tenant
        try:
            tenant_conn = tenant_manager.get_connection(estabelecimento_id)
            tenant_manager.release_connection(estabelecimento_id, tenant_conn)
            
            return jsonify({
                'success': True,
                'data': {
                    'estabelecimento_id': estabelecimento_id,
                    'estabelecimento_nome': estabelecimento_nome,
                    'database_status': 'online',
                    'message': f'Banco do estabelecimento {estabelecimento_nome} está acessível'
                }
            }), 200
            
        except Exception as e:
            # Tentar criar banco
            if tenant_manager.create_tenant_database(estabelecimento_id, estabelecimento_nome):
                return jsonify({
                    'success': True,
                    'data': {
                        'estabelecimento_id': estabelecimento_id,
                        'estabelecimento_nome': estabelecimento_nome,
                        'database_status': 'created',
                        'message': f'Banco do estabelecimento {estabelecimento_nome} criado com sucesso'
                    }
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'error': f'Banco do estabelecimento {estabelecimento_nome} não está acessível'
                }), 500
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Erro ao verificar tenant'
        }), 500

@auth_bp.route('/list-tenants', methods=['GET'])
@jwt_required()
def list_tenants():
    """Lista todos os tenants (apenas admin)"""
    try:
        claims = get_jwt()
        user_role = claims.get('role')
        
        if user_role not in ['admin', 'ADMIN']:
            return jsonify({
                'success': False,
                'error': 'Sem permissão'
            }), 403
        
        conn = get_main_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT e.id, e.nome_fantasia, e.razao_social, e.cnpj, 
                   e.database_name, e.status, e.created_at,
                   COUNT(u.id) as usuario_count
            FROM tenant_management.estabelecimentos e
            LEFT JOIN tenant_management.usuarios u ON e.id = u.estabelecimento_id AND u.ativo = true
            GROUP BY e.id
            ORDER BY e.nome_fantasia
        """)
        
        tenants = []
        for row in cursor.fetchall():
            tenants.append({
                'id': row[0],
                'nome_fantasia': row[1],
                'razao_social': row[2],
                'cnpj': row[3],
                'database_name': row[4],
                'status': row[5],
                'created_at': row[6],
                'usuario_count': row[7]
            })
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'data': tenants
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Erro ao listar tenants'
        }), 500

@auth_bp.route("/doctor", methods=["GET"])
@jwt_required()
def auth_doctor():
    """Endpoint de Diagnóstico para verificar o estado da autenticação e a versão do código"""
    from app.utils.auth_utils import get_doctor_info
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    return jsonify(get_doctor_info(current_user_id, claims)), 200
