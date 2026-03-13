"""
MercadinhoSys API - Factory Flask
Arquitetura modular com blueprints por funcionalidade
"""

from flask import Flask, jsonify, request
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_caching import Cache
from flask_mail import Mail
from app.models import db
from config import config
import os
import logging
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

# Função para horário de Manaus (GMT-4)
def get_manaus_time():
    """Retorna datetime atual no fuso de Manaus (GMT-4)"""
    utc_now = datetime.now(timezone.utc)
    manaus_tz = timezone(timedelta(hours=-4))
    return utc_now.astimezone(manaus_tz)

# Inicializa as extensões
migrate = Migrate()
jwt = JWTManager()
cache = Cache()
mail = Mail()

# Logger básico
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app(config_name=None):
    """Factory function para criar a aplicação Flask"""

    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "default")

    load_dotenv()
    app = Flask(__name__)


    # Carrega configurações
    app.config.from_object(config[config_name])

    # Configurar JSON Provider Customizado (Decimal, Date, etc)
    from app.utils.json_provider import CustomJSONProvider
    app.json = CustomJSONProvider(app)

    db_source = None
    runtime_db_url = (
        os.environ.get("DATABASE_URL_TARGET")
        or os.environ.get("DB_PRIMARY")
        or os.environ.get("DATABASE_URL")
        or os.environ.get("POSTGRES_URL")
        or os.environ.get("AIVEN_DATABASE_URL")
    )
    # DETECTAR MODO MULTI-TENANT (não afeta modo normal)
    multi_tenant_mode = os.getenv('MULTI_TENANT_MODE', 'false').lower() == 'true'
    main_db_url = os.getenv('MAIN_DATABASE_URL')
    
    if multi_tenant_mode and main_db_url:
        # Modo Multi-Tenant - usar banco principal para autenticação
        runtime_db_url = main_db_url
        app.config["MULTI_TENANT_MODE"] = True
        logger.info("🏢 MODO MULTI-TENANT ATIVADO")
    else:
        # Modo normal - manter ordem original para não quebrar conexão existente
        runtime_db_url = (
            os.environ.get("AIVEN_DATABASE_URL")
            or os.environ.get("POSTGRES_URL") 
            or os.environ.get("DATABASE_URL_TARGET")
            or os.environ.get("DB_PRIMARY")
            or os.environ.get("DATABASE_URL")
        )
    
    if runtime_db_url:
        if runtime_db_url.startswith("postgres://"):
            runtime_db_url = runtime_db_url.replace("postgres://", "postgresql://", 1)
        app.config["SQLALCHEMY_DATABASE_URI"] = runtime_db_url
        
        # OTIMIZAÇÃO DE ELITE: Connection Pooling para Aiven (Postgres Cloud)
        # Ajustado para evitar "SSL connection has been closed unexpectedly" e timeouts
        # OTIMIZAÇÃO DE ELITE: Connection Pooling (Somente para Postgres/Aiven)
        # Se for SQLite (Local/Docker sem env), não aplica configs de pool do Postgres
        if "postgres" in runtime_db_url:
            app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
                "pool_size": 5, # Aiven tem limites estritos de conexão
                "max_overflow": 10,
                "pool_recycle": 3600, # 1 hora
                "pool_pre_ping": True,
                "connect_args": {
                    "connect_timeout": 30,
                    "application_name": "mercadinhosys_backend_prod",
                    "keepalives": 1,
                    "keepalives_idle": 30,
                    "keepalives_interval": 10,
                    "keepalives_count": 5,
                    "sslmode": "require" if all(h not in runtime_db_url for h in ["localhost", "127.0.0.1", "::1", "postgres", "db"]) else "disable"
                }
            }
        else:
             # Configuração simples para SQLite (evita erros de SSL/Pool)
             app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
                 "pool_pre_ping": True
             }
        
        for key in ["DATABASE_URL_TARGET", "DB_PRIMARY", "DATABASE_URL", "POSTGRES_URL", "AIVEN_DATABASE_URL"]:
            if os.environ.get(key):
                db_source = key
                break

    # Inicializa extensões
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # Callbacks JWT: unificar falhas de autenticação como 401 (ERP/API padrão)
    # Evita 422 para token inválido; frontend trata apenas 401 (refresh ou redirect)
    @jwt.invalid_token_loader
    def custom_invalid_token_callback(error_string):
        logger.warning("[JWT] Token inválido ou malformado (não logamos o valor)")
        return jsonify({
            "success": False,
            "error": "Não autorizado",
            "msg": "Token inválido ou expirado. Faça login novamente.",
        }), 401

    @jwt.expired_token_loader
    def custom_expired_token_callback(_jwt_header, _jwt_data):
        logger.info("[JWT] Token expirado")
        return jsonify({
            "success": False,
            "error": "Não autorizado",
            "msg": "Token expirado. Faça login novamente.",
        }), 401

    @jwt.unauthorized_loader
    def custom_unauthorized_callback(error_string):
        logger.info("[JWT] Requisição sem token válido")
        return jsonify({
            "success": False,
            "error": "Não autorizado",
            "msg": error_string or "Token não informado.",
        }), 401

    mail.init_app(app)


    @app.errorhandler(404)
    def handle_404_error(e):
        return jsonify({
            "success": False,
            "error": "Rota não encontrada",
            "path": request.path,
            "method": request.method
        }), 404

    db_uri = app.config.get("SQLALCHEMY_DATABASE_URI")
    redacted_db_uri = db_uri
    if db_uri:
        try:
            parsed = urlparse(db_uri)
            if parsed.password:
                username = parsed.username or ""
                host = parsed.hostname or ""
                port = f":{parsed.port}" if parsed.port else ""
                auth = f"{username}:****@" if username else ""
                redacted_db_uri = parsed._replace(netloc=f"{auth}{host}{port}").geturl()
        except Exception:
            redacted_db_uri = db_uri
    logger.info(f"DB URI: {redacted_db_uri}")
    logger.info(f"DB SOURCE: {db_source or 'config'}")
    
    # Inicializa Flask-Login
    from app.models import login_manager
    login_manager.init_app(app)

    # CORS - Configuração COMPLETA para produção
    import re
    
    # Configuração de CORS - Robusta para Vercel/Render e Local
    cors_origins = None
    if app.config.get("CORS_ORIGINS"):
        cors_origins = app.config["CORS_ORIGINS"]
    
    if not cors_origins:
        # Fallbacks dinâmicos se não houver env
        if os.getenv("VERCEL_URL"):
            cors_origins = [f"https://{os.getenv('VERCEL_URL')}", "https://mercadinhosys.vercel.app"]
        else:
            cors_origins = ["*"] # Desenvolvimento ou fallback absoluto
    
    CORS(app, resources={r"/api/*": {
        "origins": cors_origins,
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        "allow_headers": ["Content-Type", "Authorization", "X-Requested-With", "Access-Control-Allow-Origin"],
        "expose_headers": ["Content-Range", "X-Content-Range"],
        "supports_credentials": True,
        "max_age": 600
    }})
    logger.info(f"🌐 CORS configurado (Regex habilitado para Vercel/Render)")


    
    # Cria pastas necessárias
    for folder in ["instance", "instance/uploads", "logs", "backups"]:
        if not os.path.exists(folder):
            os.makedirs(folder)

    # ==================== BOOTSTRAP: CRIAR TABELAS E COLUNAS CRÍTICAS ====================
    # Otimização para Vercel/Render: Pular setup se SKIP_DB_SETUP=true ou se em produção após primeiro deploy
    skip_db_setup = os.environ.get("SKIP_DB_SETUP", "false").lower() == "true"
    
    # Em produção, o setup pesado em cada requisição causa timeouts (Render/Vercel).
    is_production = config_name == "production"
    is_cloud = os.environ.get("VERCEL") == "1" or os.environ.get("RENDER") == "1"
    
    if not skip_db_setup:
        with app.app_context():
            try:
                # Testar conexão se for Postgres
                if app.config.get("USING_POSTGRES"):
                    from sqlalchemy import text
                    logger.info("VERIFICANDO: Conexao com a Nuvem (Postgres)...")
                    db.session.execute(text("SELECT 1"))
                
                logger.info("VERIFICANDO: Tabelas no banco de dados...")
                db.create_all()
                
                # Garantir que a tabela de histórico de login também seja criada explicitamente se omitida
                from sqlalchemy import text
                db.session.execute(text("CREATE TABLE IF NOT EXISTS login_history (id SERIAL PRIMARY KEY, username VARCHAR(150), ip_address VARCHAR(45), dispositivo VARCHAR(200), success BOOLEAN, observacoes TEXT, token_hash INTEGER, funcionario_id INTEGER, estabelecimento_id INTEGER, data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"))
                db.session.commit()
                
                logger.info("SUCESSO: Tabelas verificadas/criadas.")
            except Exception as e:
                logger.error(f"ERRO: Falha ao conectar na Nuvem: {e}")
                
                # FALLBACK LOGIC - RESTRITO
                # Em produção (Render/Vercel), NÃO fazer fallback automático para SQLite 
                # pois isso cria um banco vazio e esconde o erro real de conexão.
                hybrid_mode = os.environ.get("HYBRID_MODE", "online").lower()
                force_local = os.environ.get("FORCE_LOCAL_FALLBACK", "false").lower() == "true"
                
                # Se for PROD e não for forçado, não faz fallback!
                if is_production and not force_local:
                    logger.critical("🚫 PRODUÇÃO: Conexão com banco falhou. Fallback para SQLite BLOQUEADO para evitar perda de dados aparente.")
                    logger.critical("Verifique DATABASE_URL e firewall.")
                    # Não relançamos o erro para não derrubar o container em loop, mas a app ficará instável/erro 500
                elif hybrid_mode != "offline" and app.config.get("USING_POSTGRES"):
                    logger.error("❌ ERRO CRÍTICO: Falha ao conectar ao Postgres. Fallback para SQLite DESATIVADO para manter integridade.")
                    # Mantém o URI original para tentar reconexão nas próximas requests
                    pass
                    
                    # Recriar engine/session (simplificado - idealmente reiniciaria a app, mas vamos tentar create_all local)
                    try:
                        db.create_all()
                        logger.info("SUCESSO: Banco de dados LOCAL inicializado.")
                    except Exception as le:
                        logger.error(f"ERRO FATAL: Nem o banco local pode ser inicializado: {le}")
                else:
                    logger.error(f"ERRO: Criar tabelas no bootstrap: {e}")

    else:
        logger.info("INFO: db.create_all() pulado (SKIP_DB_SETUP=true). Schema sync ainda sera executado.")

    # ==================== SCHEMA SYNC ====================
    # Pode ser pulado com SKIP_SCHEMA_SYNC=true (ex: durante seed que já fez drop_all+create_all)
    if os.environ.get("SKIP_SCHEMA_SYNC", "false").lower() == "true":
        logger.info("⏭️ Schema Sync pulado (SKIP_SCHEMA_SYNC=true).")
    else:
        with app.app_context():
            try:
                from sqlalchemy import text as _sync_text
                is_sqlite = db.engine.name == 'sqlite'

                schema_sqls = [
                    # Estabelecimento - SaaS
                    ("estabelecimentos", "plano",                   "VARCHAR(20)  DEFAULT 'Basic'"),
                    ("estabelecimentos", "plano_status",            "VARCHAR(20)  DEFAULT 'experimental'"),
                    ("estabelecimentos", "stripe_customer_id",      "VARCHAR(100)"),
                    ("estabelecimentos", "stripe_subscription_id",  "VARCHAR(100)"),
                    ("estabelecimentos", "vencimento_assinatura",   "TIMESTAMP"),
                    ("estabelecimentos", "pagarme_id",              "VARCHAR(100)"),
                    # Estabelecimento - Endereço completo
                    ("estabelecimentos", "cep",                     "VARCHAR(9)   DEFAULT '00000-000'"),
                    ("estabelecimentos", "logradouro",              "VARCHAR(200) DEFAULT 'Nao Informado'"),
                    ("estabelecimentos", "numero",                  "VARCHAR(10)  DEFAULT 'S/N'"),
                    ("estabelecimentos", "complemento",             "VARCHAR(100)"),
                    ("estabelecimentos", "bairro",                  "VARCHAR(100) DEFAULT 'Centro'"),
                    ("estabelecimentos", "cidade",                  "VARCHAR(100) DEFAULT 'Cidade'"),
                    ("estabelecimentos", "estado",                  "VARCHAR(2)   DEFAULT 'SP'"),
                    ("estabelecimentos", "pais",                    "VARCHAR(50)  DEFAULT 'Brasil'"),
                    # Configurações
                    ("configuracoes", "logo_base64",                "TEXT"),
                    ("configuracoes", "tema_escuro",                "BOOLEAN DEFAULT FALSE"),
                    ("configuracoes", "cor_principal",              "VARCHAR(7) DEFAULT '#2563eb'"),
                    ("configuracoes", "emitir_nfe",                 "BOOLEAN DEFAULT FALSE"),
                    ("configuracoes", "emitir_nfce",                "BOOLEAN DEFAULT TRUE"),
                    ("configuracoes", "impressao_automatica",       "BOOLEAN DEFAULT FALSE"),
                    ("configuracoes", "tipo_impressora",            "VARCHAR(20) DEFAULT 'termica_80mm'"),
                    ("configuracoes", "exibir_preco_tela",          "BOOLEAN DEFAULT TRUE"),
                    ("configuracoes", "permitir_venda_sem_estoque", "BOOLEAN DEFAULT FALSE"),
                    ("configuracoes", "desconto_maximo_percentual", "NUMERIC(5,2) DEFAULT 10.00"),
                    ("configuracoes", "desconto_maximo_funcionario","NUMERIC(5,2) DEFAULT 10.00"),
                    ("configuracoes", "arredondamento_valores",     "BOOLEAN DEFAULT TRUE"),
                    ("configuracoes", "formas_pagamento",           "TEXT"),
                    ("configuracoes", "controlar_validade",         "BOOLEAN DEFAULT TRUE"),
                    ("configuracoes", "alerta_estoque_minimo",      "BOOLEAN DEFAULT TRUE"),
                    ("configuracoes", "dias_alerta_validade",       "INTEGER DEFAULT 30"),
                    ("configuracoes", "estoque_minimo_padrao",      "INTEGER DEFAULT 10"),
                    ("configuracoes", "tempo_sessao_minutos",       "INTEGER DEFAULT 30"),
                    ("configuracoes", "tentativas_senha_bloqueio",  "INTEGER DEFAULT 3"),
                    ("configuracoes", "alertas_email",              "BOOLEAN DEFAULT FALSE"),
                    ("configuracoes", "alertas_whatsapp",           "BOOLEAN DEFAULT FALSE"),
                    ("configuracoes", "horas_extras_percentual",    "NUMERIC(5,2) DEFAULT 50.00"),
                    # Funcionarios
                    ("funcionarios", "data_demissao",               "DATE"),
                    ("funcionarios", "salario",                     "NUMERIC(10,2)"),
                    ("funcionarios", "observacoes",                 "TEXT"),
                    ("funcionarios", "foto_url",                    "TEXT"),
                    ("funcionarios", "role",                        "VARCHAR(30)  DEFAULT 'FUNCIONARIO'"),
                    ("funcionarios", "ativo",                       "BOOLEAN      DEFAULT TRUE"),
                    ("funcionarios", "permissoes_json",             "TEXT"),
                    # Produtos
                    ("produtos", "margem_lucro",                    "NUMERIC(10,2)"),
                    ("produtos", "fornecedor_id",                   "INTEGER"),
                    ("produtos", "codigo_barras",                   "VARCHAR(50)"),
                    ("produtos", "ativo",                           "BOOLEAN DEFAULT TRUE"),
                    ("produtos", "fabricante",                      "VARCHAR(100)"),
                    ("produtos", "tipo",                            "VARCHAR(50)"),
                    ("produtos", "subcategoria",                    "VARCHAR(50)"),
                    ("produtos", "ncm",                             "VARCHAR(8)"),
                    ("produtos", "origem",                          "INTEGER DEFAULT 0"),
                    ("produtos", "controlar_validade",              "BOOLEAN DEFAULT FALSE"),
                    ("produtos", "data_validade",                   "DATE"),
                    ("produtos", "lote",                            "VARCHAR(50)"),
                    ("produtos", "imagem_url",                      "VARCHAR(255)"),
                    ("produtos", "classificacao_abc",               "VARCHAR(1)"),
                    # Vendas
                    ("vendas", "valor_recebido",                    "NUMERIC(10,2) DEFAULT 0"),
                    ("vendas", "troco",                             "NUMERIC(10,2) DEFAULT 0"),
                    ("vendas", "data_cancelamento",                 "TIMESTAMP"),
                    ("vendas", "motivo_cancelamento",               "VARCHAR(255)"),
                    ("vendas", "quantidade_itens",                  "INTEGER DEFAULT 0"),
                    ("vendas", "observacoes",                       "TEXT"),
                    # Venda Itens
                    ("venda_itens", "custo_unitario",               "NUMERIC(10,2)"),
                    ("venda_itens", "margem_item",                  "NUMERIC(5,2)"),
                    ("venda_itens", "margem_lucro_real",            "NUMERIC(10,2)"),
                    # Despesas
                    ("despesas", "data_emissao",                    "DATE"),
                    ("despesas", "data_vencimento",                 "DATE"),
                ]

                from sqlalchemy import inspect as _insp
                inspector = _insp(db.engine)
                logger.info("⚡ Iniciando Schema Sync Otimizado...")
                table_columns_cache = {}
                existing_tables = inspector.get_table_names()
                added = 0

                for table, col, col_type in schema_sqls:
                    if table not in existing_tables:
                        continue
                    if table not in table_columns_cache:
                        table_columns_cache[table] = [c['name'] for c in inspector.get_columns(table)]
                    if col not in table_columns_cache[table]:
                        try:
                            logger.info(f"➕ Adicionando coluna {col} na tabela {table}...")
                            db.session.execute(_sync_text(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}"))
                            db.session.commit()
                            table_columns_cache[table].append(col)
                            added += 1
                        except Exception as e:
                            db.session.rollback()
                            logger.warning(f"⚠️ Erro ao adicionar {table}.{col}: {e}")

                logger.info(f"✅ Schema sync concluido: {added} colunas novas adicionadas.")
            except Exception as sync_err:
                db.session.rollback()
                logger.error(f"⚠️ Schema sync falhou: {sync_err}")



    # ==================== REGISTRO DE BLUEPRINTS ====================

    # Auth - IMPORTANTE: blueprint se chama 'auth_bp' no arquivo
    try:
        if app.config.get("MULTI_TENANT_MODE"):
            from app.routes.auth_multi_tenant import auth_bp
            logger.info("🏢 Usando autenticação Multi-Tenant")
        else:
            from app.routes.auth import auth_bp
            logger.info("🔐 Usando autenticação Single-Tenant")

        app.register_blueprint(auth_bp, url_prefix="/api/auth")
        logger.info("✅ Blueprint auth registrado em /api/auth")
    except Exception as e:
        logger.error(f"❌ Erro ao registrar auth: {e}")

    # Produtos
    try:
        from app.routes.produtos import produtos_bp

        app.register_blueprint(produtos_bp, url_prefix="/api/produtos")
        logger.info("✅ Blueprint produtos registrado em /api/produtos")
    except Exception as e:
        logger.error(f"❌ Erro ao registrar produtos: {e}")

    # Fornecedores
    try:
        from app.routes.fornecedores import fornecedores_bp
        app.register_blueprint(fornecedores_bp, url_prefix="/api/fornecedores")
        logger.info("✅ Blueprint fornecedores registrado em /api/fornecedores")
    except Exception as e:
        logger.error(f"❌ Erro ao registrar fornecedores: {e}")

    # Funcionarios
    try:
        from app.routes.funcionarios import funcionarios_bp

        app.register_blueprint(funcionarios_bp, url_prefix="/api/funcionarios")
        logger.info("✅ Blueprint funcionarios registrado em /api/funcionarios")
    except Exception as e:
        logger.error(f"❌ Erro ao registrar funcionarios: {e}")

    # Clientes
    try:
        from app.routes.clientes import clientes_bp

        app.register_blueprint(clientes_bp, url_prefix="/api/clientes")
        logger.info("✅ Blueprint clientes registrado em /api/clientes")
    except Exception as e:
        logger.error(f"❌ Erro ao registrar clientes: {e}")

    # Vendas
    try:
        from app.routes.vendas import vendas_bp

        app.register_blueprint(vendas_bp, url_prefix="/api/vendas")
        logger.info("✅ Blueprint vendas registrado em /api/vendas")
    except Exception as e:
        logger.error(f"❌ Erro ao registrar vendas: {e}")

    # PDV
    try:
        from app.routes.pdv import pdv_bp

        app.register_blueprint(pdv_bp, url_prefix="/api/pdv")
        logger.info("✅ Blueprint pdv registrado em /api/pdv")
    except Exception as e:
        logger.error(f"❌ Erro ao registrar pdv: {e}")

    # Caixas
    try:
        from app.routes.caixas import caixas_bp

        app.register_blueprint(caixas_bp, url_prefix="/api/caixas")
        logger.info("✅ Blueprint caixas registrado em /api/caixas")
    except Exception as e:
        logger.error(f"❌ Erro ao registrar caixas: {e}")

    # Configuração
    try:
        from app.routes.configuracao import configuracao_bp
        app.register_blueprint(configuracao_bp, url_prefix="/api/configuracao")
        logger.info("✅ Blueprint configuracao registrado em /api/configuracao")
    except Exception as e:
        logger.error(f"❌ Erro ao registrar configuracao: {e}")

    # Dashboard
    try:
        from app.routes.dashboard import dashboard_bp
        app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")
        logger.info("✅ Blueprint dashboard registrado em /api/dashboard")
        app.config['DASHBOARD_CIENTIFICO_DISPONIVEL'] = True
    except Exception as e:
        import traceback
        logger.error(f"❌ Erro ao registrar dashboard: {e}\n{traceback.format_exc()}")
        app.config['DASHBOARD_CIENTIFICO_DISPONIVEL'] = False

    # SaaS (Monitoramento & Onboarding)
    try:
        from app.routes.saas import saas_bp
        app.register_blueprint(saas_bp, url_prefix="/api/saas")
        logger.info("✅ Blueprint saas registrado em /api/saas")
    except Exception as e:
        logger.error(f"❌ Erro ao registrar saas: {e}")

    # Despesas
    try:
        from app.routes.despesas import despesas_bp

        app.register_blueprint(despesas_bp, url_prefix="/api/despesas")
        logger.info("✅ Blueprint despesas registrado em /api/despesas")
    except Exception as e:
        logger.error(f"❌ Erro ao registrar despesas: {e}")

    # Relatórios
    try:
        from app.routes.relatorios import relatorios_bp

        app.register_blueprint(relatorios_bp, url_prefix="/api/relatorios")
        logger.info("✅ Blueprint relatorios registrado em /api/relatorios")
    except Exception as e:
        logger.error(f"❌ Erro ao registrar relatorios: {e}")

    # Sync (replicação local -> Neon)
    try:
        from app.routes.sync import sync_bp
        app.register_blueprint(sync_bp)
        logger.info("✅ Blueprint sync registrado (/api/sync/replicar)")
    except Exception as e:
        logger.error(f"❌ Erro ao registrar sync: {e}")

    # Ponto (controle de ponto)
    try:
        from app.routes.ponto import ponto_bp
        app.register_blueprint(ponto_bp, url_prefix="/api/ponto")
        logger.info("✅ Blueprint ponto registrado em /api/ponto")
    except Exception as e:
        logger.error(f"❌ Erro ao registrar ponto: {e}")

    # RH (Justificativas + Benefícios + Banco de Horas)
    try:
        from app.routes.rh import rh_bp
        app.register_blueprint(rh_bp, url_prefix="/api/rh")
        logger.info("✅ Blueprint rh registrado em /api/rh")
    except Exception as e:
        logger.error(f"❌ Erro ao registrar rh: {e}")

    # Pedidos de Compra
    try:
        from app.routes.pedidos_compra import pedidos_compra_bp
        app.register_blueprint(pedidos_compra_bp, url_prefix="/api")
        logger.info("✅ Blueprint pedidos_compra registrado em /api")
    except Exception as e:
        logger.error(f"❌ Erro ao registrar pedidos_compra: {e}")

    # Monitoramento Global (SaaS Monitor)
    try:
        from app.routes.monitor import monitor_bp
        app.register_blueprint(monitor_bp, url_prefix="/api/saas/monitor")
        logger.info("✅ Blueprint SaaS Monitor registrado em /api/saas/monitor")
    except Exception as e:
        logger.error(f"❌ Erro ao registrar monitor: {e}")

    # Sincronização Híbrida
    try:
        from app.routes.sync_hybrid import sync_hybrid_bp
        app.register_blueprint(sync_hybrid_bp, url_prefix="/api/sync-hybrid")
        logger.info("✅ Blueprint Sincronização Híbrida registrado em /api/sync-hybrid")
    except Exception as e:
        logger.error(f"❌ Erro ao registrar sync_hybrid: {e}")


    # Stripe
    try:
        from app.routes.stripe_routes import stripe_bp
        app.register_blueprint(stripe_bp)
        logger.info("✅ Blueprint Stripe registrado")
    except Exception as e:
        logger.error(f"❌ Erro ao registrar stripe: {e}")

    # Onboarding SaaS
    try:
        from app.routes.onboarding import onboarding_bp
        app.register_blueprint(onboarding_bp, url_prefix="/api/onboarding")
        logger.info("✅ Blueprint SaaS Onboarding registrado em /api/onboarding")
    except Exception as e:
        logger.error(f"❌ Erro ao registrar onboarding: {e}")

    # Dashboard Científico já é tratado via dashboard_bp centralizado
    pass

    # ==================== ROTAS GLOBAIS ====================

    # Rota de saúde
    @app.route("/api/health", methods=["GET"])
    def health_check():
        from sqlalchemy import text

        try:
            db.session.execute(text("SELECT 1"))
            db_status = "connected"
        except Exception as e:
            db_status = f"error: {str(e)}"

        return jsonify(
            {
                "status": "healthy",
                "service": "mercadinhosys-api",
                "version": "2.0.0",
                "database": db_status,
                "db_source": "POSTGRES_CLOUD" if app.config.get("USING_POSTGRES") else "SQLITE_LOCAL",
                "db_url_redacted": redacted_db_uri,
                "timestamp": get_manaus_time().isoformat(),
                "dashboard_cientifico": (
                    "disponível"
                    if app.config.get('DASHBOARD_CIENTIFICO_DISPONIVEL')
                    else "não disponível"
                ),
            }
        )

    # Rota inicial
    @app.route("/", methods=["GET"])
    @app.route("/api", methods=["GET"])
    def index():
        return jsonify(
            {
                "message": "🚀 MercadinhoSys API - Sistema de Gestão para Mercados",
                "version": "2.0.0",
                "status": "operational",
                "endpoints": {
                    "auth": "/api/auth",
                    "produtos": "/api/produtos",
                    "vendas": "/api/vendas",
                    "dashboard": "/api/dashboard",
                    "pdv": "/api/pdv",
                    "relatorios": "/api/relatorios",
                    "cientifico": (
                        "/api/cientifico" if app.config.get('DASHBOARD_CIENTIFICO_DISPONIVEL') else None
                    ),
                },
                "health_check": "/api/health",
            }
        )

    # Erro de conexão com o banco (ex.: Neon pooler - remover statement_timeout em config)
    from sqlalchemy.exc import OperationalError
    @app.errorhandler(OperationalError)
    def handle_db_connection_error(exc):
        logger.error(f"[DB] Falha de conexão: {exc}")
        return (
            jsonify({
                "success": False,
                "error": "Banco de dados temporariamente indisponível",
                "message": "Verifique a configuração da conexão (Neon pooler não suporta statement_timeout).",
            }),
            503,
        )

    # Manipuladores de erro
    @app.errorhandler(404)
    def not_found(error):
        return (
            jsonify(
                {
                    "error": "Recurso não encontrado",
                    "message": "Consulte /api para ver endpoints disponíveis",
                }
            ),
            404,
        )

    @app.errorhandler(500)
    def internal_error(error):
        import traceback
        err_msg = str(error)
        tb = traceback.format_exc()
        logger.error(f"💥 [ERRO GRAVE 500]: {err_msg}\n{tb}")
        
        # Se for um erro do SQLAlchemy, o rollback é obrigatório para não travar a session
        try:
            db.session.rollback()
        except:
            pass

        return (
            jsonify(
                {
                    "success": False,
                    "error": "Erro interno no servidor",
                    "message": err_msg,
                    "code": "INTERNAL_SERVER_ERROR",
                    "timestamp": get_manaus_time().isoformat(),
                }
            ),
            500,
        )

    # ==================== ROTA PARA SERVIR UPLOADS ====================
    from flask import send_from_directory, abort

    @app.route("/uploads/<path:filename>")
    def serve_uploads(filename):
        """Serve arquivos da pasta uploads (logos, etc)"""
        # Tenta pegar do config
        upload_folder = app.config.get("UPLOAD_FOLDER")
        
        # Se não estiver no config ou for relativo, tenta resolver
        if not upload_folder:
            # Fallback para ../uploads relativo a app/
            # app.root_path é .../backend/app
            # Queremos .../backend/uploads
            upload_folder = os.path.join(os.path.dirname(app.root_path), "uploads")
        
        if not os.path.isabs(upload_folder):
            # Se for relativo (ex: 'uploads'), assume relativo ao root
            base = os.path.dirname(app.root_path)
            upload_folder = os.path.join(base, upload_folder)

        logger.info(f"Serving upload: '{filename}' from '{upload_folder}'")
        
        try:
            return send_from_directory(upload_folder, filename)
        except Exception as e:
            logger.error(f"Erro ao servir arquivo {filename}: {e}")
            abort(404)

    # Log de inicialização
    logger.info(
        f"""
    {'='*60}
    MercadinhoSys API v2.0.0 INICIALIZADA
    Ambiente: {config_name}
    Banco: {app.config.get('SQLALCHEMY_DATABASE_URI', 'SQLite')}
    Dashboard Cientifico: {'[OK] Disponivel' if app.config.get('DASHBOARD_CIENTIFICO_DISPONIVEL') else '[OFF] Nao disponivel'}
    {'='*60}
    """
    )

    # Configurar Listeners de Sincronia (Abordagem de Guerrilha)
    with app.app_context():
        try:
            from app.listeners import setup_listeners
            setup_listeners()
            
            # Iniciar Worker de Sincronia de Guerrilha (Em processo separado)
            if os.getenv("SYNC_ENABLED", "false").lower() == "true":
                from app.services.sync_worker import start_sync_worker
                start_sync_worker(app)
                
        except Exception as e:
            app.logger.error(f"Erro ao configurar listeners ou worker: {e}")

    return app
