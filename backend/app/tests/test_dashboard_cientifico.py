#!/usr/bin/env python3
"""
Script de teste para Dashboard Científico
"""
import pytest

requests = pytest.importorskip("requests")
import json
import sys
import os

# Configurações
BASE_URL = "http://localhost:5000"
TEST_TOKEN = None  # Será obtido via login


def print_success(msg):
    print(f"✅ {msg}")


def print_error(msg):
    print(f"❌ {msg}")


def print_info(msg):
    print(f"📊 {msg}")


def test_health():
    """Testa o endpoint de saúde"""
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        if response.status_code == 200:
            data = response.json()
            print_success(f"Health Check: {data.get('status')}")
            print_success(
                f"Dashboard Científico: {data.get('dashboard_cientifico', 'não informado')}"
            )
            return True
        else:
            print_error(f"Health Check falhou: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Erro ao conectar: {e}")
        return False


def test_login():
    """Testa login para obter token JWT"""
    global TEST_TOKEN
    try:
        # Use credenciais válidas do seu sistema
        login_data = {
            "email": "admin@exemplo.com",  # Ajuste conforme seu sistema
            "senha": "admin123",
        }

        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)

        if response.status_code == 200:
            data = response.json()
            TEST_TOKEN = data.get("access_token")
            if TEST_TOKEN:
                print_success("Login realizado com sucesso")
                return True
        else:
            print_error(f"Login falhou: {response.status_code}")
            print(f"Resposta: {response.text}")
            return False

    except Exception as e:
        print_error(f"Erro no login: {e}")
        return False


def test_cientifico_info():
    """Testa informações do módulo científico"""
    try:
        headers = {}
        if TEST_TOKEN:
            headers["Authorization"] = f"Bearer {TEST_TOKEN}"

        response = requests.get(f"{BASE_URL}/api/cientifico/info", headers=headers)

        if response.status_code == 200:
            data = response.json()
            print_success(f"Módulo: {data.get('module')}")
            print_success(f"Disponível: {data.get('available', False)}")

            # Verificar dependências
            deps = data.get("dependencies", {})
            for dep, info in deps.items():
                status = "✅" if info.get("status") == "OK" else "❌"
                print(
                    f"{status} {dep}: {info.get('status')} ({info.get('version', 'N/A')})"
                )

            return True
        elif response.status_code == 401:
            print_error("Token JWT inválido ou expirado")
            return False
        else:
            print_error(f"Info falhou: {response.status_code}")
            print(f"Resposta: {response.text}")
            return False

    except Exception as e:
        print_error(f"Erro: {e}")
        return False


def test_cientifico_test():
    """Testa rota de teste"""
    try:
        response = requests.get(f"{BASE_URL}/api/cientifico/test")

        if response.status_code == 200:
            data = response.json()
            print_success(f"Teste: {data.get('message')}")
            print_success(f"Status: {data.get('status')}")
            return True
        else:
            print_error(f"Teste falhou: {response.status_code}")
            return False

    except Exception as e:
        print_error(f"Erro: {e}")
        return False


def test_cientifico_analyze():
    """Testa análise estatística"""
    try:
        headers = {"Content-Type": "application/json"}
        if TEST_TOKEN:
            headers["Authorization"] = f"Bearer {TEST_TOKEN}"

        # Dados de exemplo para análise
        sample_data = {
            "values": [10.5, 20.3, 30.1, 40.7, 50.9, 60.2, 70.6, 80.4, 90.8, 100.0]
        }

        response = requests.post(
            f"{BASE_URL}/api/cientifico/analyze", headers=headers, json=sample_data
        )

        if response.status_code == 200:
            data = response.json()
            print_success("Análise estatística realizada com sucesso!")

            # Exibir algumas métricas
            descriptive = data.get("descriptive", {})
            if descriptive:
                print_info(f"Média: {descriptive.get('mean', 'N/A')}")
                print_info(f"Mediana: {descriptive.get('median', 'N/A')}")
                print_info(f"Desvio Padrão: {descriptive.get('std', 'N/A')}")

            return True
        elif response.status_code == 503:
            print_error(
                "Módulos científicos não estão disponíveis (dependências faltando)"
            )
            return False
        elif response.status_code == 401:
            print_error("Autenticação necessária")
            return False
        else:
            print_error(f"Análise falhou: {response.status_code}")
            print(f"Resposta: {response.text}")
            return False

    except Exception as e:
        print_error(f"Erro: {e}")
        return False


def test_vendas_analytics():
    """Testa análise de vendas"""
    try:
        headers = {}
        if TEST_TOKEN:
            headers["Authorization"] = f"Bearer {TEST_TOKEN}"

        response = requests.get(
            f"{BASE_URL}/api/cientifico/vendas-analytics?dias=7", headers=headers
        )

        if response.status_code == 200:
            data = response.json()
            print_success("Análise de vendas realizada!")

            # Verificar tipo de resposta
            if "periodo" in data:
                # Resposta básica (módulos não disponíveis)
                print_info(f"Período: {data.get('periodo')}")
                print_info(f"Total Vendas: {data.get('total_vendas', 0)}")
            elif "descriptive" in data:
                # Resposta científica completa
                print_info("Análise científica completa disponível")

            return True
        else:
            print_error(f"Vendas analytics falhou: {response.status_code}")
            return False

    except Exception as e:
        print_error(f"Erro: {e}")
        return False


def test_dependencies():
    """Verifica se dependências estão instaladas"""
    print_info("Verificando dependências...")

    dependencies = ["pandas", "numpy", "scipy", "statsmodels"]
    all_ok = True

    for dep in dependencies:
        try:
            __import__(dep)
            print_success(f"{dep}: instalado")
        except ImportError:
            print_error(f"{dep}: NÃO instalado")
            all_ok = False

    return all_ok


def main():
    """Função principal de teste"""
    print("=" * 60)
    print("🚀 TESTE DO DASHBOARD CIENTÍFICO")
    print("=" * 60)

    # Verificar dependências primeiro
    if not test_dependencies():
        print("\n⚠️  Algumas dependências estão faltando!")
        print("Instale com: pip install pandas numpy scipy statsmodels")
        return

    print("\n1️⃣  Testando conexão com API...")
    if not test_health():
        print(
            "\n❌ API não está respondendo. Certifique-se de que o servidor está rodando."
        )
        print("   Execute: python run.py")
        return

    print("\n2️⃣  Testando módulo científico...")
    test_cientifico_test()

    print("\n3️⃣  Obtendo informações do módulo...")
    test_cientifico_info()

    print("\n4️⃣  Testando login para endpoints protegidos...")
    if test_login():
        print("\n5️⃣  Testando análise estatística (com autenticação)...")
        test_cientifico_analyze()

        print("\n6️⃣  Testando análise de vendas...")
        test_vendas_analytics()
    else:
        print("\n⚠️  Login falhou. Testando endpoints públicos apenas...")

    print("\n" + "=" * 60)
    print("📋 RESUMO DOS TESTES")
    print("=" * 60)
    print("URLs disponíveis para teste manual:")
    print(f"  • {BASE_URL}/api/health")
    print(f"  • {BASE_URL}/api/cientifico/test")
    print(f"  • {BASE_URL}/api/cientifico/info (requer JWT)")
    print(f"  • {BASE_URL}/api/cientifico/analyze (requer JWT)")
    print(f"  • {BASE_URL}/api/cientifico/vendas-analytics (requer JWT)")
    print("\n🎯 Para testar via curl:")
    print(f"  curl {BASE_URL}/api/cientifico/test")
    print(f"  curl -H 'Authorization: Bearer SEU_TOKEN' {BASE_URL}/api/cientifico/info")
    print("\n✅ Testes concluídos!")


if __name__ == "__main__":
    main()
