# test_auth_completo.py
import requests
import json


class AuthTester:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.tokens = {}

    def test_login(self, username, senha, estabelecimento_id=4):
        """Testa o login e retorna True se bem-sucedido"""
        print(f"\n🔐 Testando login para {username}...")

        response = requests.post(
            f"{self.base_url}/api/auth/login",
            json={
                "username": username,
                "senha": senha,
                "estabelecimento_id": estabelecimento_id,
            },
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                self.tokens[username] = data["data"]
                print(f"✅ Login bem-sucedido para {username}")
                print(f"   Nome: {data['data']['user']['nome']}")
                print(f"   Role: {data['data']['user']['role']}")
                return True
            else:
                print(f"❌ {data.get('error')}")
                return False
        else:
            print(f"❌ Status {response.status_code}: {response.text}")
            return False

    def test_validate(self, username):
        """Testa a validação do token"""
        if username not in self.tokens:
            print(f"❌ {username} não está logado")
            return

        print(f"\n🔍 Validando token de {username}...")
        token = self.tokens[username]["access_token"]

        response = requests.get(
            f"{self.base_url}/api/auth/validate",
            headers={"Authorization": f"Bearer {token}"},
        )

        if response.status_code == 200:
            print("✅ Token válido")
            return True
        else:
            print(f"❌ Token inválido: {response.json()}")
            return False

    def test_refresh(self, username):
        """Testa o refresh token"""
        if username not in self.tokens:
            print(f"❌ {username} não está logado")
            return

        print(f"\n🔄 Testando refresh token para {username}...")
        refresh_token = self.tokens[username]["refresh_token"]

        response = requests.post(
            f"{self.base_url}/api/auth/refresh",
            headers={"Authorization": f"Bearer {refresh_token}"},
        )

        if response.status_code == 200:
            print("✅ Refresh token funcionou")
            # Atualiza o token
            self.tokens[username]["access_token"] = response.json()["access_token"]
            return True
        else:
            print(f"❌ Refresh falhou: {response.json()}")
            return False

    def test_logout(self, username):
        """Testa o logout"""
        if username not in self.tokens:
            print(f"❌ {username} não está logado")
            return

        print(f"\n🚪 Testando logout para {username}...")
        token = self.tokens[username]["access_token"]

        response = requests.post(
            f"{self.base_url}/api/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )

        if response.status_code == 200:
            print("✅ Logout bem-sucedido")
            # Remove tokens
            del self.tokens[username]
            return True
        else:
            print(f"❌ Logout falhou: {response.json()}")
            return False

    def run_full_test(self):
        """Executa todos os testes"""
        print("=" * 60)
        print("🧪 TESTE COMPLETO DO SISTEMA DE AUTENTICAÇÃO")
        print("=" * 60)

        # Teste com admin
        if self.test_login("admin", "admin123", 4):
            self.test_validate("admin")
            self.test_refresh("admin")
            self.test_logout("admin")

        print("\n" + "=" * 60)
        print("👥 TESTE COM TODOS OS USUÁRIOS")
        print("=" * 60)

        usuarios = [
            ("admin", "admin123"),
            ("gerente", "123456"),
            ("caixa1", "123456"),
            ("caixa2", "123456"),
        ]

        for username, senha in usuarios:
            if self.test_login(username, senha, 4):
                self.test_validate(username)
                print("-" * 40)

        print("\n" + "=" * 60)
        print("✅ TESTES CONCLUÍDOS!")
        print("=" * 60)


if __name__ == "__main__":
    tester = AuthTester()
    tester.run_full_test()
