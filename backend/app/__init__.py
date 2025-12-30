from flask import Flask, jsonify, request  # ✅ ADICIONE "request" AQUI!
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import config
import os

# Inicializa as extensões
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()


def create_app(config_name="default"):
    """Factory function para criar a aplicação Flask"""
    app = Flask(__name__)

    # Carrega configurações
    app.config.from_object(config[config_name])

    # Inicializa extensões com o app
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

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

    # 🎯 CADA BLUEPRINT COM SEU PRÓPRIO NAMESPACE
    app.register_blueprint(produtos_bp, url_prefix="/api/produtos")
    app.register_blueprint(fornecedores_bp, url_prefix="/api/fornecedores")
    app.register_blueprint(funcionarios_bp, url_prefix="/api/funcionarios")
    app.register_blueprint(clientes_bp, url_prefix="/api/clientes")
    app.register_blueprint(vendas_bp, url_prefix="/api/vendas")
    app.register_blueprint(config_bp, url_prefix="/api/config")
    app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")
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
                "endpoints": [
                    "/api/produtos",
                    "/api/vendas",
                    "/api/clientes",
                    "/api/funcionarios",
                    "/api/fornecedores",
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
                    "health": "/api/health",
                },
                "status": "operacional",
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

    return app
