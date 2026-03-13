"""
Rotas de Autenticação Multi-Tenant
Autenticação global com redirecionamento para banco do tenant
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt
from werkzeug.security import check_password_hash
from datetime import timedelta
import psycopg2
import os
from app.middleware.multi_tenant import tenant_manager

auth_bp = Blueprint('auth_multi_tenant', __name__)

def get_main_connection():
    """Obtém conexão com banco principal de autenticação"""
    main_url = os.getenv('MAIN_DATABASE_URL')
    return psycopg2.connect(main_url)

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login multi-tenant - autentica global e redireciona para tenant"""
    try:
        data = request.get_json()
        username = data.get('username')
        senha = data.get('senha')
        
        if not username or not senha:
            return jsonify({
                'success': False,
                'error': 'Username e senha são obrigatórios'
            }), 400
        
        # Conectar ao banco principal para autenticação
        conn = get_main_connection()
        cursor = conn.cursor()
        
        # Buscar usuário com informações do estabelecimento (Filtro rigoroso e isolado)
        cursor.execute("""
            SELECT u.id, u.nome, u.email, u.senha_hash, u.role, u.estabelecimento_id,
                   e.nome_fantasia, e.database_name, e.status, e.razao_social, e.cnpj
            FROM tenant_management.usuarios u
            JOIN tenant_management.estabelecimentos e ON u.estabelecimento_id = e.id
            WHERE (LOWER(u.email) = LOWER(%s) OR LOWER(u.nome) = LOWER(%s)) 
              AND u.ativo = true 
              AND e.status = 'active'
            ORDER BY u.id ASC
        """, (username, username))
        
        all_matches = cursor.fetchall()
        
        if not all_matches:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Usuário ou senha inválidos ou estabelecimento inativo'
            }), 401
        
        # Se houver múltiplos (raro num sistema bem gerido, mas possível se não houver UNIQUE),
        # por enquanto pegamos o primeiro, mas registramos o conflito se necessário.
        user_data = all_matches[0]
        
        (user_id, user_nome, user_email, senha_hash, role, estabelecimento_id,
         estabelecimento_nome, database_name, estabelecimento_status, razao_social, cnpj) = user_data
        
        # Verificar senha
        if not check_password_hash(senha_hash, senha):
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Usuário ou senha inválidos'
            }), 401
        
        cursor.close()
        conn.close()
        
        # Verificar se banco do tenant existe e está acessível
        try:
            tenant_conn = tenant_manager.get_connection(estabelecimento_id)
            tenant_manager.release_connection(estabelecimento_id, tenant_conn)
        except Exception as e:
            # Tentar criar banco se não existir
            if tenant_manager.create_tenant_database(estabelecimento_id, estabelecimento_nome):
                tenant_conn = tenant_manager.get_connection(estabelecimento_id)
                tenant_manager.release_connection(estabelecimento_id, tenant_conn)
            else:
                return jsonify({
                    'success': False,
                    'error': f'Banco de dados do estabelecimento {estabelecimento_nome} não está disponível'
                }), 500
        
        # Criar token JWT com informações do tenant (Isolamento de Elite)
        additional_claims = {
            'role': role,
            'estabelecimento_id': estabelecimento_id,
            'estabelecimento_nome': estabelecimento_nome,
            'database_name': database_name,
            'user_id': user_id
        }
        
        access_token = create_access_token(
            identity=user_email,
            additional_claims=additional_claims,
            expires_delta=timedelta(hours=24)
        )
        
        return jsonify({
            'success': True,
            'data': {
                'access_token': access_token,
                'user': {
                    'id': user_id,
                    'nome': user_nome,
                    'email': user_email,
                    'role': role,
                    'estabelecimento_id': estabelecimento_id,
                    'estabelecimento_nome': estabelecimento_nome,
                    'database_name': database_name
                },
                'estabelecimento': {
                    'id': estabelecimento_id,
                    'nome': estabelecimento_nome,
                    'razao_social': razao_social,
                    'cnpj': cnpj,
                    'database_name': database_name,
                    'status': estabelecimento_status
                }
            },
            'message': f'Login realizado com sucesso - {estabelecimento_nome}'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Erro interno no servidor'
        }), 500

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Obtém informações do usuário atual com dados do tenant"""
    try:
        claims = get_jwt()
        user_email = claims['sub']
        estabelecimento_id = claims.get('estabelecimento_id')
        
        # Buscar dados atualizados do usuário
        conn = get_main_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT u.id, u.nome, u.email, u.role, u.estabelecimento_id,
                   e.nome_fantasia, e.razao_social, e.cnpj
            FROM tenant_management.usuarios u
            JOIN tenant_management.estabelecimentos e ON u.estabelecimento_id = e.id
            WHERE u.email = %s AND u.ativo = true
        """, (user_email,))
        
        user_data = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not user_data:
            return jsonify({
                'success': False,
                'error': 'Usuário não encontrado'
            }), 404
        
        (user_id, user_nome, user_email, role, estab_id, estab_nome, estab_razao, estab_cnpj) = user_data
        
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
                'estabelecimento_cnpj': estab_cnpj
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
        
        if not estabelecimento_id:
            return jsonify({
                'success': False,
                'error': 'Estabelecimento não encontrado no token'
            }), 400
        
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
