"""
Middleware Multi-Tenant para Isolamento Completo de Dados
Cada estabelecimento tem seu próprio banco de dados
"""

import os
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from flask import g, request
from functools import wraps
import logging

logger = logging.getLogger(__name__)

class MultiTenantManager:
    """Gerenciador de conexões multi-tenant"""
    
    def __init__(self):
        self.pools = {}  # Connection pools por tenant
        self.main_db_url = os.getenv('MAIN_DATABASE_URL')
        self.tenant_template = os.getenv('TENANT_DATABASE_TEMPLATE')
        self.multi_tenant_mode = os.getenv('MULTI_TENANT_MODE', 'false').lower() == 'true'
        
        # Pool principal para gerenciamento de tenants
        if self.main_db_url:
            self.main_pool = SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                dsn=self.main_db_url
            )
        else:
            self.main_pool = None
    
    def get_tenant_database_url(self, estabelecimento_id):
        """Gera URL do banco de dados do tenant"""
        if not self.multi_tenant_mode:
            # Modo legado - usa banco único
            return os.getenv('DATABASE_URL')
        
        return self.tenant_template.format(estabelecimento_id=estabelecimento_id)
    
    def get_connection(self, estabelecimento_id):
        """Obtém conexão do pool do tenant ou cria novo pool"""
        if not self.multi_tenant_mode:
            # Modo legado - retorna conexão do banco principal
            return self._get_legacy_connection()
        
        tenant_id = str(estabelecimento_id)
        
        # Verificar se pool já existe
        if tenant_id not in self.pools:
            db_url = self.get_tenant_database_url(estabelecimento_id)
            try:
                # Criar novo pool para o tenant
                self.pools[tenant_id] = SimpleConnectionPool(
                    minconn=1,
                    maxconn=5,
                    dsn=db_url
                )
                logger.info(f"Pool criado para tenant {estabelecimento_id}")
            except Exception as e:
                logger.error(f"Erro ao criar pool para tenant {estabelecimento_id}: {e}")
                raise
        
        # Retornar conexão do pool
        return self.pools[tenant_id].getconn()
    
    def _get_legacy_connection(self):
        """Modo legado - conexão única"""
        db_url = os.getenv('DATABASE_URL')
        if not hasattr(self, '_legacy_pool'):
            self._legacy_pool = SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                dsn=db_url
            )
        return self._legacy_pool.getconn()
    
    def release_connection(self, estabelecimento_id, connection):
        """Libera conexão de volta para o pool"""
        if not self.multi_tenant_mode:
            self._legacy_pool.putconn(connection)
            return
        
        tenant_id = str(estabelecimento_id)
        if tenant_id in self.pools:
            self.pools[tenant_id].putconn(connection)
    
    def create_tenant_database(self, estabelecimento_id, estabelecimento_nome):
        """Cria banco de dados para novo tenant"""
        if not self.multi_tenant_mode:
            return False
        
        try:
            # Conectar ao banco principal
            conn = self.main_pool.getconn()
            cursor = conn.cursor()
            
            # Nome do banco
            db_name = f"tenant_{estabelecimento_id}"
            
            # Criar banco de dados
            cursor.execute(f"CREATE DATABASE {db_name}")
            conn.commit()
            
            # Conectar ao novo banco e criar schema
            tenant_url = self.get_tenant_database_url(estabelecimento_id)
            tenant_conn = psycopg2.connect(tenant_url)
            tenant_cursor = tenant_conn.cursor()
            
            # Criar schema básico
            tenant_cursor.execute("""
                CREATE TABLE IF NOT EXISTS configuracoes (
                    id SERIAL PRIMARY KEY,
                    estabelecimento_id INTEGER DEFAULT 1,
                    cor_principal VARCHAR(20) DEFAULT '#2563eb',
                    tema_escuro BOOLEAN DEFAULT false,
                    logo_url TEXT,
                    logo_base64 TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS produtos (
                    id SERIAL PRIMARY KEY,
                    nome VARCHAR(255) NOT NULL,
                    preco_venda DECIMAL(10,2) NOT NULL,
                    estoque_atual INTEGER DEFAULT 0,
                    ativo BOOLEAN DEFAULT true,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS vendas (
                    id SERIAL PRIMARY KEY,
                    numero_cupom VARCHAR(50) UNIQUE NOT NULL,
                    data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    valor_total DECIMAL(10,2) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                INSERT INTO configuracoes (estabelecimento_id) VALUES (1);
            """)
            
            tenant_conn.commit()
            tenant_cursor.close()
            tenant_conn.close()
            
            cursor.close()
            self.main_pool.putconn(conn)
            
            logger.info(f"Banco criado para tenant {estabelecimento_id} - {estabelecimento_nome}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao criar banco para tenant {estabelecimento_id}: {e}")
            return False
    
    def close_all_pools(self):
        """Fecha todos os pools de conexão"""
        for pool in self.pools.values():
            pool.closeall()
        self.pools.clear()
        
        if self.main_pool:
            self.main_pool.closeall()
        
        if hasattr(self, '_legacy_pool'):
            self._legacy_pool.closeall()

# Instância global
tenant_manager = MultiTenantManager()

def get_tenant_connection():
    """Middleware para obter conexão do tenant atual"""
    from functools import wraps
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Obter estabelecimento_id do token JWT
            from flask_jwt_extended import get_jwt
            claims = get_jwt()
            estabelecimento_id = claims.get('estabelecimento_id')
            
            if not estabelecimento_id:
                return {'success': False, 'error': 'Estabelecimento não encontrado no token'}, 401
            
            # Obter conexão do tenant
            try:
                connection = tenant_manager.get_connection(estabelecimento_id)
                g.tenant_connection = connection
                g.estabelecimento_id = estabelecimento_id
                
                result = f(*args, **kwargs)
                
                # Liberar conexão
                tenant_manager.release_connection(estabelecimento_id, connection)
                return result
                
            except Exception as e:
                logger.error(f"Erro de conexão tenant {estabelecimento_id}: {e}")
                return {'success': False, 'error': 'Erro de conexão com banco de dados'}, 500
        
        return decorated_function
    return decorator

def with_tenant_db(f):
    """Decorator para operações com banco do tenant"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(g, 'tenant_connection'):
            from flask_jwt_extended import get_jwt
            claims = get_jwt()
            estabelecimento_id = claims.get('estabelecimento_id')
            
            if not estabelecimento_id:
                return {'success': False, 'error': 'Estabelecimento não encontrado'}, 401
            
            connection = tenant_manager.get_connection(estabelecimento_id)
            g.tenant_connection = connection
            g.estabelecimento_id = estabelecimento_id
        
        try:
            result = f(*args, **kwargs)
            return result
        finally:
            if hasattr(g, 'tenant_connection'):
                tenant_manager.release_connection(g.estabelecimento_id, g.tenant_connection)
                delattr(g, 'tenant_connection')
    
    return decorated_function
