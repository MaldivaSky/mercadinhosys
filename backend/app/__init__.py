from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import config
import os

# Inicializa as extensões
db = SQLAlchemy()
migrate = Migrate(app=db)
jwt = JWTManager()


def create_app(config_name="default"):
    """Factory function para criar a aplicação Flask"""
    app = Flask(__name__)

    # Carrega configurações
    app.config.from_object(config[config_name])

    # Inicializa extensões
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Cria pasta de uploads se não existir
    if not os.path.exists(app.config["UPLOAD_FOLDER"]):
        os.makedirs(app.config["UPLOAD_FOLDER"])

    # Registra blueprints (rotas)
    from app.routes.produtos import produtos_bp
    from app.routes.vendas import vendas_bp
    from app.routes.clientes import clientes_bp

    app.register_blueprint(produtos_bp, url_prefix="/api/produtos")
    app.register_blueprint(vendas_bp, url_prefix="/api/vendas")
    app.register_blueprint(clientes_bp, url_prefix="/api/clientes")

    # Rota de saúde
    @app.route("/api/health")
    def health_check():
        return jsonify({"status": "healthy", "service": "mercadinhosys-api"})

    # Rota inicial
    @app.route("/")
    def index():
        return jsonify(
            {
                "message": "API do Sistema Mercadinho",
                "version": "1.0.0",
                "endpoints": {
                    "produtos": "/api/produtos",
                    "vendas": "/api/vendas",
                    "clientes": "/api/clientes",
                    "health": "/api/health",
                },
            }
        )

    # Manipulador de erros
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Recurso não encontrado"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({"error": "Erro interno do servidor"}), 500

    return app
