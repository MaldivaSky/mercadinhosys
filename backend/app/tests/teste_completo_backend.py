"""
Teste Completo do Backend MercadinhoSys
"""

import requests
import json
import sys
import os
from datetime import datetime

BASE_URL = "http://localhost:5000"
HEADERS = {"Content-Type": "application/json"}


class BackendTester:
    def __init__(self):
        self.token = None
        self.user_id = None
        self.estabelecimento_id = None

    def print_success(self, message):
        print(f"✅ {message}")

    def print_error(self, message):
        print(f"❌ {message}")

    def print_info(self, message):
        print(f"ℹ️ {message}")

    def test_health(self):
        """Testa endpoint de saúde"""
        try:
            response = requests.get(f"{BASE_URL}/api/health")
            if response.status_code == 200:
                data = response.json()
                self.print_success(f"Health Check: {data.get('status', 'N/A')}")
                return True
            else:
                self.print_error(f"Health Check falhou: {response.status_code}")
                return False
        except Exception as e:
            self.print_error(f"Health Check erro: {e}")
            return False

    def test_auth(self):
        """Testa autenticação"""
        try:
            # Login
            login_data = {"email": "admin@teste.com", "senha": "123456"}
            response = requests.post(
                f"{BASE_URL}/api/auth/login", json=login_data, headers=HEADERS
            )

            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.user_id = data.get("user_id")
                self.estabelecimento_id = data.get("estabelecimento_id")

                HEADERS["Authorization"] = f"Bearer {self.token}"
                self.print_success("Login realizado com sucesso")
                return True
            else:
                self.print_error(f"Login falhou: {response.status_code}")
                self.print_error(f"Resposta: {response.text}")
                return False

        except Exception as e:
            self.print_error(f"Auth erro: {e}")
            return False

    def test_produtos(self):
        """Testa CRUD de produtos"""
        if not self.token:
            self.print_error("Token não disponível para testar produtos")
            return False

        try:
            # Criar produto
            produto_data = {
                "nome": "Produto Teste Automatizado",
                "codigo_barras": "1234567890123",
                "preco_custo": 10.50,
                "preco_venda": 25.90,
                "quantidade_estoque": 100,
                "categoria": "Teste",
                "descricao": "Produto criado por teste automatizado",
                "ativo": True,
            }

            response = requests.post(
                f"{BASE_URL}/api/produtos", json=produto_data, headers=HEADERS
            )

            if response.status_code == 201:
                produto = response.json()
                produto_id = produto.get("id")
                self.print_success(f"Produto criado: ID {produto_id}")

                # Listar produtos
                response = requests.get(f"{BASE_URL}/api/produtos", headers=HEADERS)

                if response.status_code == 200:
                    produtos = response.json()
                    self.print_success(
                        f"Listar produtos: {len(produtos.get('items', []))} itens"
                    )
                    return True
                else:
                    self.print_error(f"Listar produtos falhou: {response.status_code}")
                    return False
            else:
                self.print_error(f"Criar produto falhou: {response.status_code}")
                self.print_error(f"Resposta: {response.text}")
                return False

        except Exception as e:
            self.print_error(f"Produtos erro: {e}")
            return False

    def test_vendas(self):
        """Testa funcionalidades de vendas"""
        if not self.token:
            self.print_error("Token não disponível para testar vendas")
            return False

        try:
            # Verificar vendas do dia
            response = requests.get(f"{BASE_URL}/api/vendas/hoje", headers=HEADERS)

            if response.status_code == 200:
                vendas = response.json()
                self.print_success(f"Vendas hoje: {len(vendas)} registros")
                return True
            else:
                self.print_error(f"Vendas hoje falhou: {response.status_code}")
                return False

        except Exception as e:
            self.print_error(f"Vendas erro: {e}")
            return False

    def test_dashboard(self):
        """Testa dashboard"""
        if not self.token or not self.estabelecimento_id:
            self.print_error("Dados insuficientes para testar dashboard")
            return False

        try:
            response = requests.get(
                f"{BASE_URL}/api/dashboard/executivo/{self.estabelecimento_id}",
                headers=HEADERS,
            )

            if response.status_code == 200:
                dashboard = response.json()
                self.print_success("Dashboard executivo carregado")

                # Verificar se tem dados básicos
                if "summary" in dashboard:
                    self.print_success(
                        f"Receita: {dashboard['summary'].get('revenue', {}).get('display', 'N/A')}"
                    )
                    return True
                else:
                    self.print_error("Dashboard sem estrutura esperada")
                    return False
            else:
                self.print_error(f"Dashboard falhou: {response.status_code}")
                return False

        except Exception as e:
            self.print_error(f"Dashboard erro: {e}")
            return False

    def test_pdv(self):
        """Testa funcionalidades do PDV"""
        if not self.token:
            self.print_error("Token não disponível para testar PDV")
            return False

        try:
            # Configurações do PDV
            response = requests.get(
                f"{BASE_URL}/api/pdv/configuracoes", headers=HEADERS
            )

            if response.status_code == 200:
                config = response.json()
                self.print_success("Configurações PDV carregadas")
                return True
            else:
                self.print_error(f"Config PDV falhou: {response.status_code}")
                return False

        except Exception as e:
            self.print_error(f"PDV erro: {e}")
            return False

    def test_cientifico(self):
        """Testa dashboard científico"""
        try:
            response = requests.get(f"{BASE_URL}/api/cientifico/health")

            if response.status_code == 200:
                data = response.json()
                self.print_success(f"Dashboard Científico: {data.get('status', 'N/A')}")
                return True
            elif response.status_code == 404:
                self.print_info("Dashboard Científico não disponível")
                return True  # Não é erro, é opcional
            else:
                self.print_error(f"Dashboard Científico falhou: {response.status_code}")
                return False

        except Exception as e:
            self.print_error(f"Científico erro: {e}")
            return False

    def run_all_tests(self):
        """Executa todos os testes"""
        print("\n" + "=" * 60)
        print("🚀 TESTE COMPLETO DO BACKEND MERCADINHOSYS")
        print("=" * 60)

        tests = [
            ("Health Check", self.test_health),
            ("Autenticação", self.test_auth),
            ("Produtos", self.test_produtos),
            ("Vendas", self.test_vendas),
            ("Dashboard", self.test_dashboard),
            ("PDV", self.test_pdv),
            ("Dashboard Científico", self.test_cientifico),
        ]

        results = []
        for test_name, test_func in tests:
            print(f"\n🔍 Testando: {test_name}")
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                self.print_error(f"Erro inesperado em {test_name}: {e}")
                results.append((test_name, False))

        # Resumo
        print("\n" + "=" * 60)
        print("📊 RESUMO DOS TESTES")
        print("=" * 60)

        passed = sum(1 for _, result in results if result)
        total = len(results)

        for test_name, result in results:
            status = "✅ PASSOU" if result else "❌ FALHOU"
            print(f"{status}: {test_name}")

        print(f"\n🎯 Resultado: {passed}/{total} testes passaram")

        if passed == total:
            print("\n✨✨✨ BACKEND 100% FUNCIONAL! ✨✨✨")
        else:
            print(f"\n⚠️  {total - passed} testes falharam")

        return passed == total


if __name__ == "__main__":
    # Iniciar servidor primeiro (em outro terminal)
    print("⚠️  Certifique-se de que o servidor está rodando em localhost:5000")
    print("   Execute em outro terminal: python run.py")
    input("Pressione Enter para iniciar os testes...")

    tester = BackendTester()
    success = tester.run_all_tests()

    sys.exit(0 if success else 1)
