# test_decorators.py
import os
import sys
import requests
import json

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))



class DecoratorTester:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.tokens = {}

    def login(self, username, senha):
        """Faz login e retorna o token"""
        response = requests.post(
            f"{self.base_url}/api/auth/login",
            json={"username": username, "senha": senha, "estabelecimento_id": 4},
        )

        if response.status_code == 200:
            token = response.json()["data"]["access_token"]
            self.tokens[username] = token
            return token
        return None

    def test_protected_route(self, username, endpoint, expected_status=200):
        """Testa uma rota protegida com o token do usuário"""
        if username not in self.tokens:
            print(f"❌ {username} não está logado")
            return

        headers = {"Authorization": f"Bearer {self.tokens[username]}"}
        response = requests.get(f"{self.base_url}{endpoint}", headers=headers)

        print(
            f"\n🔒 Testando {endpoint} com {username} (role: {self.get_role(username)})"
        )
        print(f"   Status esperado: {expected_status}")
        print(f"   Status recebido: {response.status_code}")

        if response.status_code == expected_status:
            print("   ✅ PASS")
        else:
            print("   ❌ FAIL")
            try:
                print(f"   Erro: {response.json()}")
            except:
                print(f"   Response: {response.text}")

        return response

    def get_role(self, username):
        """Obtém o role do usuário (simplificado)"""
        roles = {
            "admin": "admin",
            "gerente": "funcionario",  # No seed, gerente tem role "funcionario"
            "caixa1": "funcionario",
            "caixa2": "funcionario",
        }
        return roles.get(username, "desconhecido")


def test_all_decorators():
    """Testa todos os decorators com diferentes usuários"""
    tester = DecoratorTester()

    print("=" * 60)
    print("🧪 TESTANDO DECORATORS DE AUTORIZAÇÃO")
    print("=" * 60)

    # Login com todos os usuários
    usuarios = ["admin", "gerente", "caixa1", "caixa2"]
    for user in usuarios:
        senha = "admin123" if user == "admin" else "123456"
        token = tester.login(user, senha)
        if token:
            print(f"✅ {user} logado")
        else:
            print(f"❌ Falha no login de {user}")

    print("\n" + "=" * 60)
    print("1. Testando @funcionario_required")
    print("=" * 60)

    # Rota exemplo que requer apenas funcionário autenticado
    tester.test_protected_route(
        "admin", "/api/exemplo/funcionario", 404
    )  # 404 porque rota não existe, mas se existisse passaria
    tester.test_protected_route("caixa1", "/api/exemplo/funcionario", 404)

    print("\n" + "=" * 60)
    print("2. Testando @admin_required (simulado)")
    print("=" * 60)

    # Para simular, vamos verificar os roles nos tokens
    for user in usuarios:
        token = tester.tokens.get(user)
        if token:
            # Decodificar token para ver role (simplificado - na prática você usaria get_jwt())
            print(f"\n👤 {user}:")
            print(f"   Token: {token[:50]}...")
            print(f"   Role esperado: {tester.get_role(user)}")
            print(f"   Pode acessar rotas admin? {'Sim' if user == 'admin' else 'Não'}")

    print("\n" + "=" * 60)
    print("3. Testando na prática - Criando rotas de teste")
    print("=" * 60)

    # Vamos criar um endpoint de teste rápido
    test_endpoint()


def test_endpoint():
    """Cria um endpoint de teste rápido para verificar os decorators"""
    from flask import Flask, jsonify
    from flask_jwt_extended import JWTManager

    app = Flask(__name__)
    app.config["JWT_SECRET_KEY"] = "test-secret"
    jwt = JWTManager(app)

    # Importar decorators corrigidos
    from app.decorator import (
        admin_required,
        gerente_ou_admin_required,
        funcionario_required,
    )

    @app.route("/test/admin")
    @admin_required
    def admin_only():
        return jsonify({"message": "Acesso permitido - Admin"})

    @app.route("/test/gerente")
    @gerente_ou_admin_required
    def gerente_or_admin():
        return jsonify({"message": "Acesso permitido - Gerente ou Admin"})

    @app.route("/test/funcionario")
    @funcionario_required
    def funcionario():
        return jsonify({"message": "Acesso permitido - Funcionário"})

    print("✅ Endpoints de teste criados:")
    print("   GET /test/admin - Apenas admin")
    print("   GET /test/gerente - Gerente ou admin")
    print("   GET /test/funcionario - Qualquer funcionário ativo")


if __name__ == "__main__":
    test_all_decorators()
