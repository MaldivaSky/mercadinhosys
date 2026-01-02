from flask import Flask, jsonify, request
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_caching import Cache  # NOVO IMPORT
from app.models import db
from config import config
import os

# Inicializa as extensões
migrate = Migrate()
jwt = JWTManager()
cache = Cache()  # NOVA INSTÂNCIA DO CACHE

# No topo, após os imports existentes:
from app.middleware.rate_limit import limiter
from app.swagger import init_swagger
from app.utils.logger import app_logger


def create_app(config_name="default"):
    """Factory function para criar a aplicação Flask"""
    app = Flask(__name__)

    # Carrega configurações
    app.config.from_object(config[config_name])

    # Configuração do Cache (mantenha essas linhas SE já existirem, senão adicione)
    if "CACHE_TYPE" not in app.config:
        app.config["CACHE_TYPE"] = "simple"  # Para desenvolvimento
        app.config["CACHE_DEFAULT_TIMEOUT"] = 300  # 5 minutos

    # Inicializa extensões com o app
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cache.init_app(app)  # INICIALIZA O CACHE

    # Inicializa rate limiter
    limiter.init_app(app)

    # Inicializa Swagger
    init_swagger(app)

    # Log de inicialização
    app_logger.info(
        "Aplicação inicializada",
        config=config_name,
        environment=os.getenv("FLASK_ENV", "development"),
    )

    # Configuração CORS mais segura
    CORS(
        app,
        resources={
            r"/api/*": {"origins": ["http://localhost:5173", "http://localhost:3000"]}
        },
        supports_credentials=True,
    )

    # Cria pasta de uploads se não existir
    upload_folder = app.config.get("UPLOAD_FOLDER", "uploads")
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    # ✅ IMPORTAÇÃO SEGURA - Evita imports circulares
    from app.routes.produtos import produtos_bp
    from app.routes.fornecedores import fornecedores_bp
    from app.routes.funcionarios import funcionarios_bp
    from app.routes.clientes import clientes_bp
    from app.routes.vendas import vendas_bp
    from app.routes.configuracao import config_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.relatorios import relatorios_bp
    from app.routes.auth import auth_bp
    from app.routes.despesas import despesas_bp

    # 🎯 CADA BLUEPRINT COM SEU PRÓPRIO NAMESPACE
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(produtos_bp, url_prefix="/api/produtos")
    app.register_blueprint(fornecedores_bp, url_prefix="/api/fornecedores")
    app.register_blueprint(funcionarios_bp, url_prefix="/api/funcionarios")
    app.register_blueprint(clientes_bp, url_prefix="/api/clientes")
    app.register_blueprint(vendas_bp, url_prefix="/api/vendas")
    app.register_blueprint(config_bp, url_prefix="/api/config")
    app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")
    app.register_blueprint(despesas_bp, url_prefix="/api/despesas")
    app.register_blueprint(relatorios_bp, url_prefix="/api/relatorios")

    # 📊 Rota de saúde expandida
    @app.route("/api/health")
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
                "cache": "enabled" if app.config.get("CACHE_TYPE") else "disabled",
                "endpoints": [
                    "/api/produtos",
                    "/api/vendas",
                    "/api/clientes",
                    "/api/funcionarios",
                    "/api/fornecedores",
                    "/api/config",
                    "/api/dashboard",
                    "/api/relatorios",
                ],
            }
        )

    # 🏠 Rota inicial informativa
    @app.route("/")
    def index():
        return jsonify(
            {
                "message": "🚀 API do Sistema Mercadinho - Amazonas",
                "version": "2.0.0",
                "description": "Mercadosys - Sistema de gestão para pequenos e médios mercados do Amazonas.",
                "empresa": "MaldivaSky Tech - Soluções em Tecnologia",
                "endpoints": {
                    "produtos": "/api/produtos",
                    "vendas": "/api/vendas",
                    "vendas_dia": "/api/vendas/dia",
                    "estatisticas": "/api/vendas/estatisticas",
                    "clientes": "/api/clientes",
                    "funcionarios": "/api/funcionarios",
                    "fornecedores": "/api/fornecedores",
                    "configuracoes": "/api/config",
                    "dashboard": "/api/dashboard",
                    "relatorios": "/api/relatorios",
                    "health": "/api/health",
                },
                "status": "operacional",
                "analytics": "dashboard científico de dados ativado",
            }
        )

    # 📝 Rota específica para documentação do PDV
    @app.route("/api/pdv")
    def pdv_info():
        return jsonify(
            {
                "modulo": "PDV - Ponto de Venda",
                "rotas_principais": {
                    "criar_venda": {"method": "POST", "endpoint": "/api/vendas/"},
                    "vendas_dia": {"method": "GET", "endpoint": "/api/vendas/dia"},
                    "listar_vendas": {"method": "GET", "endpoint": "/api/vendas/"},
                    "detalhes_venda": {"method": "GET", "endpoint": "/api/vendas/<id>"},
                    "cancelar_venda": {
                        "method": "POST",
                        "endpoint": "/api/vendas/<id>/cancelar",
                    },
                    "estatisticas": {
                        "method": "GET",
                        "endpoint": "/api/vendas/estatisticas",
                    },
                },
                "fluxo_recomendado": "POST /api/vendas/ → GET /api/vendas/dia",
            }
        )

    # 📚 Rota de documentação da API
    @app.route("/api/docs")
    def api_docs():
        return jsonify({
            "api": "MercadinhoSys API Documentation",
            "version": "2.0.0",
            "base_url": "http://localhost:5000/api",
            "authentication": {
                "type": "JWT Bearer Token",
                "login": "POST /api/auth/login",
                "refresh": "POST /api/auth/refresh",
                "header": "Authorization: Bearer {token}"
            },
            "endpoints": {
                "auth": {
                    "login": {"method": "POST", "url": "/api/auth/login", "body": {"email": "string", "senha": "string"}},
                    "refresh": {"method": "POST", "url": "/api/auth/refresh"},
                    "validate": {"method": "GET", "url": "/api/auth/validate"},
                    "logout": {"method": "POST", "url": "/api/auth/logout"},
                    "profile": {"method": "GET", "url": "/api/auth/profile"}
                },
                "produtos": {
                    "listar": {"method": "GET", "url": "/api/produtos/estoque"},
                    "buscar": {"method": "GET", "url": "/api/produtos/search?q={termo}"},
                    "barcode": {"method": "GET", "url": "/api/produtos/barcode/{codigo}"},
                    "criar": {"method": "POST", "url": "/api/produtos/estoque"},
                    "atualizar": {"method": "PUT", "url": "/api/produtos/estoque/{id}"},
                    "deletar": {"method": "DELETE", "url": "/api/produtos/estoque/{id}"}
                },
                "vendas": {
                    "listar": {"method": "GET", "url": "/api/vendas/"},
                    "criar": {"method": "POST", "url": "/api/vendas/"},
                    "dia": {"method": "GET", "url": "/api/vendas/dia"},
                    "estatisticas": {"method": "GET", "url": "/api/vendas/estatisticas"},
                    "detalhes": {"method": "GET", "url": "/api/vendas/{id}"},
                    "cancelar": {"method": "POST", "url": "/api/vendas/{id}/cancelar"}
                },
                "clientes": {
                    "listar": {"method": "GET", "url": "/api/clientes/"},
                    "criar": {"method": "POST", "url": "/api/clientes/"},
                    "buscar": {"method": "GET", "url": "/api/clientes/buscar?q={termo}"},
                    "compras": {"method": "GET", "url": "/api/clientes/{id}/compras"}
                },
                "funcionarios": {
                    "listar": {"method": "GET", "url": "/api/funcionarios/"},
                    "criar": {"method": "POST", "url": "/api/funcionarios/"},
                    "login_pin": {"method": "POST", "url": "/api/funcionarios/login"}
                },
                "dashboard": {
                    "resumo": {"method": "GET", "url": "/api/dashboard/resumo"},
                    "admin": {"method": "GET", "url": "/api/dashboard/painel-admin"}
                }
            },
            "exemplo_uso": {
                "1_login": "POST /api/auth/login com {email, senha}",
                "2_obter_token": "Salvar o access_token retornado",
                "3_usar_api": "Incluir header: Authorization: Bearer {token}",
                "4_venda": "POST /api/vendas/ com dados da venda"
            }
        })

    # 🛡️ Manipuladores de erro aprimorados
    @app.errorhandler(404)
    def not_found(error):
        return (
            jsonify(
                {
                    "error": "Recurso não encontrado",
                    "message": "Verifique a URL ou consulte a documentação em /api/pdv",
                    "status_code": 404,
                }
            ),
            404,
        )

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"Erro interno: {str(error)}")
        return (
            jsonify(
                {
                    "error": "Erro interno do servidor",
                    "message": "Nossa equipe técnica foi notificada",
                    "status_code": 500,
                }
            ),
            500,
        )

    @app.errorhandler(405)
    def method_not_allowed(error):
        return (
            jsonify(
                {
                    "error": "Método não permitido",
                    "message": "Verifique o método HTTP (GET, POST, etc.)",
                    "status_code": 405,
                }
            ),
            405,
        )

    # 📌 Middleware para logging de requisições (CORRIGIDO!)
    @app.after_request
    def after_request(response):
        # Agora request está disponível porque importamos no topo
        app.logger.info(f"{request.method} {request.path} - {response.status_code}")
        return response

    print("✅ Aplicação Flask inicializada com sucesso!")
    print("📊 Rotas disponíveis:")
    for rule in app.url_map.iter_rules():
        if rule.endpoint != "static":
            print(f"   {rule.methods} {rule.rule}")

    print(f"📈 Dashboard científico de dados: ATIVADO")

    return app
