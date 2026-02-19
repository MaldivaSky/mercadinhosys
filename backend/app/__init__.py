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
from datetime import datetime
from dotenv import load_dotenv
from urllib.parse import urlparse

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

    # Handler global para erros 500
    @app.errorhandler(500)
    def handle_500_error(e):
        import traceback
        logger.error(f"[ERRO 500] {e}\n{traceback.format_exc()}")
        return jsonify({
            "success": False,
            "error": "Erro interno no servidor",
            "message": str(e),
        }), 500

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
    if runtime_db_url:
        if runtime_db_url.startswith("postgres://"):
            runtime_db_url = runtime_db_url.replace("postgres://", "postgresql://", 1)
        app.config["SQLALCHEMY_DATABASE_URI"] = runtime_db_url
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

    cache.init_app(app)
    mail.init_app(app)

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
    cors_origins = app.config.get('CORS_ORIGINS', [])
    
    # Se não houver CORS configurado, permitir todos em desenvolvimento
    if not cors_origins:
        if config_name == 'development':
            cors_origins = ["http://localhost:3000", "http://localhost:5173"]
        else:
            # Em produção sem CORS configurado, usar domínios padrão do Vercel/Render
            logger.warning("⚠️ CORS_ORIGINS não configurado! Usando domínios padrão.")
            cors_origins = [
                "https://mercadinhosys.vercel.app",
                "https://*.vercel.app",
                "https://*.onrender.com"
            ]
    
    # Log de CORS para debug
    logger.info(f"🌐 CORS configurado para: {cors_origins}")
    
    CORS(
        app,
        resources={r"/api/*": {"origins": cors_origins}},
        supports_credentials=False,
        allow_headers=["Content-Type", "Authorization", "Accept", "X-Requested-With", "Origin"],
        expose_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        max_age=3600,
    )


    
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
    
    if not skip_db_setup and not (is_production and is_cloud):
        with app.app_context():
            try:
                # Testar conexão se for Postgres
                if app.config.get("USING_POSTGRES"):
                    from sqlalchemy import text
                    logger.info("VERIFICANDO: Conexao com a Nuvem (Postgres)...")
                    db.session.execute(text("SELECT 1"))
                
                logger.info("VERIFICANDO: Tabelas no banco de dados...")
                db.create_all()
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
                    logger.warning("⚠️ FALLBACK: Mudando para banco de dados LOCAL (SQLite) devido a falha na Nuvem (Ambiente Dev/Híbrido).")
                    
                    # Tentar reconfigurar para SQLite em tempo de execução
                    basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
                    local_uri = f"sqlite:///{os.path.join(basedir, 'instance', 'mercadinho_local.db')}"
                    
                    app.config["SQLALCHEMY_DATABASE_URI"] = local_uri
                    app.config["USING_POSTGRES"] = False
                    
                    # Recriar engine/session (simplificado - idealmente reiniciaria a app, mas vamos tentar create_all local)
                    try:
                        db.create_all()
                        logger.info("SUCESSO: Banco de dados LOCAL inicializado.")
                    except Exception as le:
                        logger.error(f"ERRO FATAL: Nem o banco local pode ser inicializado: {le}")
                else:
                    logger.error(f"ERRO: Criar tabelas no bootstrap: {e}")
    
            # Em produção, sugerimos usar migrations (Flask-Migrate)
            # Rodar sync via código em cada boot é lento.
            force_sync = os.environ.get("FORCE_SCHEMA_SYNC", "false").lower() == "true"
            
            # Sincronização de Schema Crítica (SQL Direto - Anti-Erro 500)
            try:
                # Comandos SQL compatíveis com Postgres e SQLite para garantir colunas vitais
                # Nota: SQLite não suporta 'IF NOT EXISTS' em ADD COLUMN, então usamos try/except por coluna
                is_sqlite = db.engine.name == 'sqlite'
                
                sqls = [
                    # Estabelecimento
                    ("estabelecimentos", "plano", "VARCHAR(20) DEFAULT 'Basic'"),
                    ("estabelecimentos", "plano_status", "VARCHAR(20) DEFAULT 'experimental'"),
                    ("estabelecimentos", "stripe_customer_id", "VARCHAR(100)"),
                    ("estabelecimentos", "stripe_subscription_id", "VARCHAR(100)"),
                    ("estabelecimentos", "vencimento_assinatura", "TIMESTAMP"),
                    # Configurações - Visuais
                    ("configuracoes", "logo_base64", "TEXT"),
                    ("configuracoes", "tema_escuro", "BOOLEAN DEFAULT FALSE"),
                    ("configuracoes", "cor_principal", "VARCHAR(7) DEFAULT '#2563eb'"),
                    # Configurações - Vendas
                    ("configuracoes", "emitir_nfe", "BOOLEAN DEFAULT FALSE"),
                    ("configuracoes", "emitir_nfce", "BOOLEAN DEFAULT TRUE"),
                    ("configuracoes", "impressao_automatica", "BOOLEAN DEFAULT FALSE"),
                    ("configuracoes", "tipo_impressora", "VARCHAR(20) DEFAULT 'termica_80mm'"),
                    ("configuracoes", "exibir_preco_tela", "BOOLEAN DEFAULT TRUE"),
                    ("configuracoes", "permitir_venda_sem_estoque", "BOOLEAN DEFAULT FALSE"),
                    ("configuracoes", "desconto_maximo_percentual", "NUMERIC(5,2) DEFAULT 10.00"),
                    ("configuracoes", "desconto_maximo_funcionario", "NUMERIC(5,2) DEFAULT 10.00"),
                    ("configuracoes", "arredondamento_valores", "BOOLEAN DEFAULT TRUE"),
                    ("configuracoes", "formas_pagamento", "TEXT"),
                    # Configurações - Estoque
                    ("configuracoes", "controlar_validade", "BOOLEAN DEFAULT TRUE"),
                    ("configuracoes", "alerta_estoque_minimo", "BOOLEAN DEFAULT TRUE"),
                    ("configuracoes", "dias_alerta_validade", "INTEGER DEFAULT 30"),
                    ("configuracoes", "estoque_minimo_padrao", "INTEGER DEFAULT 10"),
                    # Configurações - Sistema
                    ("configuracoes", "tempo_sessao_minutos", "INTEGER DEFAULT 30"),
                    ("configuracoes", "tentativas_senha_bloqueio", "INTEGER DEFAULT 3"),
                    ("configuracoes", "alertas_email", "BOOLEAN DEFAULT FALSE"),
                    ("configuracoes", "alertas_whatsapp", "BOOLEAN DEFAULT FALSE"),
                    ("configuracoes", "horas_extras_percentual", "NUMERIC(5,2) DEFAULT 50.00")
                ]

                import traceback
                for table, col, col_type in sqls:
                    try:
                        # No Postgres (Render), o 'ADD COLUMN IF NOT EXISTS' é o ideal
                        if not is_sqlite:
                            db.session.execute(text(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col} {col_type}"))
                        else:
                            # No SQLite, tentamos adicionar. Se falhar (já existe), o except cuida.
                            db.session.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}"))
                        db.session.commit()
                    except Exception as inner_e:
                        db.session.rollback()
                        logger.critical(f"❌ FALHA EM COLUNA {table}.{col}: {str(inner_e)}\n{traceback.format_exc()}")
                
                logger.info("✅ Auto-reparo de schema concluído no boot.")
            except Exception as e:
                import traceback
                logger.critical(f"🔴 ERRO FATAL NO BOOTSTRAP DO SCHEMA: {str(e)}\n{traceback.format_exc()}")
    else:
        logger.info("INFO: Bootstrap de DB pulado (otimizacao).")

    # ==================== REGISTRO DE BLUEPRINTS ====================

    # Auth - IMPORTANTE: blueprint se chama 'auth_bp' no arquivo
    try:
        from app.routes.auth import auth_bp

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

    # Fornecedores FIX
    try:
        from app.routes.fornecedores_fix import fornecedores_fix_bp
        app.register_blueprint(fornecedores_fix_bp, url_prefix="/api/fornecedores")
        logger.info("✅ Blueprint fornecedores_fix registrado em /api/fornecedores")
    except Exception as e:
        logger.error(f"❌ Erro ao registrar fornecedores_fix: {e}")

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

    # Configuração
    try:
        from app.routes.configuracao import configuracao_bp

        app.register_blueprint(configuracao_bp)
        logger.info("✅ Blueprint configuracao registrado com prefixo próprio (/api/configuracao)")
    except Exception as e:
        logger.error(f"❌ Erro ao registrar configuracao: {e}")

    # Dashboard
    try:
        from app.routes.dashboard import dashboard_bp

        app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")
        logger.info("✅ Blueprint dashboard registrado em /api/dashboard")
    except Exception as e:
        import traceback
        logger.error(f"❌ Erro ao registrar dashboard: {e}\n{traceback.format_exc()}")

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

    # SaaS & Planos
    try:
        from app.routes.saas import saas_bp
        app.register_blueprint(saas_bp, url_prefix="/api/saas")
        logger.info("✅ Blueprint SaaS registrado em /api/saas")
    except Exception as e:
        logger.error(f"❌ Erro ao registrar saas: {e}")

    # Debug Tool (Temporário)
    try:
        from app.routes.debug import debug_bp
        app.register_blueprint(debug_bp)
        logger.info("⚠️ Blueprint DEBUG registrado")
    except Exception as e:
        logger.error(f"Erro debug bp: {e}")

    # Dashboard Científico - verifica se existe a pasta
    try:
        dashboard_cientifico_path = os.path.join(
            os.path.dirname(__file__), "dashboard_cientifico"
        )
        if os.path.exists(dashboard_cientifico_path):
            from flask import Blueprint

            # Cria blueprint dinâmico para dashboard científico
            cientifico_bp = Blueprint(
                "cientifico", __name__, url_prefix="/api/cientifico"
            )

            # Importa o orchestrator do dashboard científico
            from app.dashboard_cientifico.orchestration import DashboardOrchestrator
            from app.decorators.decorator_jwt import gerente_ou_admin_required
            from flask_jwt_extended import get_jwt

            @cientifico_bp.route("/dashboard/<int:estabelecimento_id>", methods=["GET"])
            @gerente_ou_admin_required
            def get_dashboard_cientifico(estabelecimento_id):
                try:
                    claims = get_jwt()
                    if int(claims.get("estabelecimento_id") or 0) != int(estabelecimento_id):
                        return jsonify({"success": False, "error": "Acesso negado"}), 403
                    orchestrator = DashboardOrchestrator(estabelecimento_id)
                    return jsonify(orchestrator.get_scientific_dashboard(days=30))
                except Exception as e:
                    status = 503 if "Banco de dados indisponível" in str(e) else 500
                    return jsonify({"success": False, "error": str(e)}), status

            @cientifico_bp.route(
                "/analise/<int:estabelecimento_id>/<string:tipo>", methods=["GET"]
            )
            @gerente_ou_admin_required
            def get_analise_detalhada(estabelecimento_id, tipo):
                try:
                    claims = get_jwt()
                    if int(claims.get("estabelecimento_id") or 0) != int(estabelecimento_id):
                        return jsonify({"success": False, "error": "Acesso negado"}), 403
                    orchestrator = DashboardOrchestrator(estabelecimento_id)
                    return jsonify(orchestrator.get_detailed_analysis(tipo, days=90))
                except Exception as e:
                    status = 503 if "Banco de dados indisponível" in str(e) else 500
                    return jsonify({"success": False, "error": str(e)}), status

            @cientifico_bp.route("/health", methods=["GET"])
            @gerente_ou_admin_required
            def health_cientifico():
                return jsonify(
                    {
                        "status": "operational",
                        "module": "dashboard_cientifico",
                        "timestamp": datetime.now().isoformat(),
                    }
                )

            app.register_blueprint(cientifico_bp)
            dashboard_cientifico_disponivel = True
            logger.info("✅ Dashboard Científico registrado em /api/cientifico")
        else:
            logger.info("ℹ️ Pasta dashboard_cientifico não encontrada")
    except Exception as e:
        logger.warning(f"⚠️ Dashboard Científico não disponível: {e}")

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
                "timestamp": datetime.now().isoformat(),
                "dashboard_cientifico": (
                    "disponível"
                    if dashboard_cientifico_disponivel
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
                        "/api/cientifico" if dashboard_cientifico_disponivel else None
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
        logger.error(f"Erro interno: {error}")
        return (
            jsonify(
                {
                    "error": "Erro interno",
                    "message": "Serviço temporariamente indisponível",
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
    Dashboard Científico: {'✅ Disponível' if dashboard_cientifico_disponivel else '❌ Não disponível'}
    {'='*60}
    """
    )

    from app.routes.stripe_routes import stripe_bp
    app.register_blueprint(stripe_bp)
    
    return app
