# server_emergencia.py - Servidor 100% funcional EMERGÊNCIA
import os
import sys
from pathlib import Path

# Configura paths
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from flask import Flask, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user,
)
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
import json

print("🚨 SERVIDOR DE EMERGÊNCIA - INICIANDO...")

app = Flask(__name__)
app.config["SECRET_KEY"] = "emergencia-mercadinho-2026"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"  # Banco em memória
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

CORS(
    app,
    supports_credentials=True,
    origins=["http://localhost:3000", "http://localhost:5173"],
)
db = SQLAlchemy(app)
login_manager = LoginManager(app)


# ================= MODELOS SIMPLIFICADOS =================
class Estabelecimento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome_fantasia = db.Column(db.String(100), nullable=False)
    cnpj = db.Column(db.String(20), nullable=False)
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(100))


class Funcionario(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    estabelecimento_id = db.Column(db.Integer, nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), nullable=False, unique=True)
    senha_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default="funcionario")
    ativo = db.Column(db.Boolean, default=True)

    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def check_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)


@login_manager.user_loader
def load_user(user_id):
    return Funcionario.query.get(int(user_id))


# ================= INICIALIZAÇÃO =================
with app.app_context():
    db.create_all()

    # Cria dados iniciais
    if not Estabelecimento.query.first():
        print("📝 Criando dados iniciais...")

        estab = Estabelecimento(
            nome_fantasia="Mercadinho de Emergência",
            cnpj="11.111.111/0001-11",
            telefone="(11) 1111-1111",
            email="contato@emergencia.com",
        )
        db.session.add(estab)
        db.session.commit()

        admin = Funcionario(
            estabelecimento_id=estab.id,
            nome="Administrador",
            username="admin",
            role="admin",
        )
        admin.set_senha("admin123")
        db.session.add(admin)

        vendedor = Funcionario(
            estabelecimento_id=estab.id,
            nome="Vendedor Teste",
            username="vendedor",
            role="funcionario",
        )
        vendedor.set_senha("vendedor123")
        db.session.add(vendedor)

        db.session.commit()
        print("✅ Dados criados!")


# ================= ROTAS =================
@app.route("/")
def home():
    return jsonify(
        {
            "status": "online",
            "sistema": "MercadinhoSys - Modo Emergência",
            "mensagem": "Sistema funcionando com banco em memória",
        }
    )


@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json()

    if not data or not data.get("username") or not data.get("senha"):
        return (
            jsonify({"success": False, "message": "Username e senha são obrigatórios"}),
            400,
        )

    username = data.get("username")
    senha = data.get("senha")

    user = Funcionario.query.filter_by(username=username, ativo=True).first()

    if user and user.check_senha(senha):
        login_user(user)

        session["user_id"] = user.id
        session["username"] = user.username
        session["role"] = user.role

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Login realizado com sucesso",
                    "data": {
                        "user": {
                            "id": user.id,
                            "nome": user.nome,
                            "username": user.username,
                            "role": user.role,
                        }
                    },
                }
            ),
            200,
        )

    return jsonify({"success": False, "message": "Credenciais inválidas"}), 401


@app.route("/api/auth/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    session.clear()
    return jsonify({"success": True, "message": "Logout realizado"})


@app.route("/api/auth/check", methods=["GET"])
def check_auth():
    if current_user.is_authenticated:
        return jsonify(
            {
                "authenticated": True,
                "user": {
                    "id": current_user.id,
                    "username": current_user.username,
                    "nome": current_user.nome,
                },
            }
        )
    return jsonify({"authenticated": False})


@app.route("/api/produtos", methods=["GET"])
@login_required
def listar_produtos():
    # Lista fictícia de produtos para teste
    produtos = [
        {"id": 1, "nome": "Arroz 5kg", "preco": 25.90, "estoque": 50},
        {"id": 2, "nome": "Feijão 1kg", "preco": 8.50, "estoque": 100},
        {"id": 3, "nome": "Açúcar 5kg", "preco": 18.90, "estoque": 30},
        {"id": 4, "nome": "Óleo 900ml", "preco": 7.90, "estoque": 80},
        {"id": 5, "nome": "Café 500g", "preco": 22.50, "estoque": 45},
    ]
    return jsonify({"success": True, "data": produtos})


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🚀 SERVIDOR DE EMERGÊNCIA INICIADO!")
    print("=" * 60)
    print("🔗 URL: http://localhost:5001")
    print("👤 Credenciais:")
    print("   • admin / admin123")
    print("   • vendedor / vendedor123")
    print("\n📡 Endpoints disponíveis:")
    print("   POST /api/auth/login")
    print("   POST /api/auth/logout")
    print("   GET  /api/auth/check")
    print("   GET  /api/produtos")
    print("=" * 60)

    app.run(debug=True, port=5001, use_reloader=False)
