"""
Script para testar endpoints do dashboard científico e identificar problemas.
"""
import sys
import os
import json
import requests
from datetime import datetime, timedelta

# Adicionar o diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_dashboard_endpoints():
    """Testa todos os endpoints do dashboard científico."""
    base_url = "http://localhost:5000"
    
    endpoints = [
        "/api/cientifico/dashboard",
        "/api/cientifico/dashboard?days=30",
        "/api/cientifico/dashboard?days=7",
        "/api/cientifico/dashboard?start_date=2026-01-01&end_date=2026-01-31",
        "/api/dashboard/financeiro",
        "/api/dashboard/vendas",
        "/api/dashboard/produtos",
        "/api/dashboard/rh",
    ]
    
    print("=" * 80)
    print("TESTANDO ENDPOINTS DO DASHBOARD")
    print("=" * 80)
    
    for endpoint in endpoints:
        url = base_url + endpoint
        print(f"\n🔍 Testando: {endpoint}")
        print(f"   URL: {url}")
        
        try:
            response = requests.get(url, timeout=10)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   Success: {data.get('success', 'N/A')}")
                
                # Verificar estrutura básica
                if endpoint.startswith("/api/cientifico"):
                    if data.get('success'):
                        dashboard_data = data.get('data', {})
                        print(f"   Tem dados: {'Sim' if dashboard_data else 'Não'}")
                        
                        # Verificar seções críticas
                        sections = ['analise_financeira', 'analise_produtos', 'analise_temporal', 'recomendacoes']
                        for section in sections:
                            section_data = dashboard_data.get(section, {})
                            print(f"   Seção '{section}': {'OK' if section_data else 'VAZIO'}")
                    else:
                        print(f"   ❌ Erro: {data.get('error', 'Desconhecido')}")
                else:
                    print(f"   Resposta: {len(response.text)} caracteres")
            else:
                print(f"   ❌ Erro HTTP: {response.status_code}")
                print(f"   Resposta: {response.text[:200]}...")
                
        except requests.exceptions.ConnectionError:
            print("   ❌ Não foi possível conectar ao servidor")
        except requests.exceptions.Timeout:
            print("   ❌ Timeout ao conectar")
        except Exception as e:
            print(f"   ❌ Erro inesperado: {e}")

def test_specific_data_issues():
    """Testa problemas específicos de dados mencionados pelo usuário."""
    print("\n" + "=" * 80)
    print("ANALISANDO PROBLEMAS ESPECÍFICOS DE DADOS")
    print("=" * 80)
    
    # Testar endpoint do dashboard científico com 30 dias
    url = "http://localhost:5000/api/cientifico/dashboard?days=30"
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success'):
                dashboard = data.get('data', {})
                
                # 1. Verificar indicadores financeiros
                financeiro = dashboard.get('analise_financeira', {})
                print("\n📊 INDICADORES FINANCEIROS:")
                if financeiro:
                    indicadores = financeiro.get('indicadores', {})
                    for key, value in indicadores.items():
                        if isinstance(value, (int, float)):
                            print(f"   {key}: R$ {value:,.2f}")
                        else:
                            print(f"   {key}: {value}")
                    
                    # Verificar se há valores zerados
                    zero_values = []
                    for key, value in indicadores.items():
                        if isinstance(value, (int, float)) and value == 0:
                            zero_values.append(key)
                    
                    if zero_values:
                        print(f"   ⚠️ Valores zerados: {', '.join(zero_values)}")
                    else:
                        print("   ✅ Nenhum indicador zerado")
                else:
                    print("   ❌ Seção financeira vazia")
                
                # 2. Verificar análise de produtos
                produtos = dashboard.get('analise_produtos', {})
                print("\n📦 ANÁLISE DE PRODUTOS:")
                if produtos:
                    abc = produtos.get('curva_abc', {})
                    if abc:
                        resumo = abc.get('resumo', {})
                        print(f"   Curva ABC: A={resumo.get('A', {}).get('quantidade', 0)}, "
                              f"B={resumo.get('B', {}).get('quantidade', 0)}, "
                              f"C={resumo.get('C', {}).get('quantidade', 0)}")
                    
                    produtos_estrela = produtos.get('produtos_estrela', [])
                    produtos_lentos = produtos.get('produtos_lentos', [])
                    print(f"   Produtos Estrela: {len(produtos_estrela)}")
                    print(f"   Produtos Lentos: {len(produtos_lentos)}")
                    
                    if len(produtos_estrela) == 0:
                        print("   ⚠️ Nenhum produto estrela encontrado")
                    if len(produtos_lentos) == 0:
                        print("   ⚠️ Nenhum produto lento encontrado")
                else:
                    print("   ❌ Seção produtos vazia")
                
                # 3. Verificar série temporal
                temporal = dashboard.get('analise_temporal', {})
                print("\n📈 ANÁLISE TEMPORAL:")
                if temporal:
                    tendencia = temporal.get('tendencia_vendas', [])
                    print(f"   Dias com dados: {len(tendencia)}")
                    
                    if len(tendencia) > 0:
                        # Verificar se há dados válidos
                        sample = tendencia[0]
                        print(f"   Exemplo de dado: {sample}")
                        
                        # Verificar valores zerados na série
                        zero_days = 0
                        for day in tendencia:
                            if day.get('vendas', 0) == 0 and day.get('valor', 0) == 0:
                                zero_days += 1
                        
                        if zero_days > 0:
                            print(f"   ⚠️ Dias com vendas zeradas: {zero_days}/{len(tendencia)}")
                        else:
                            print("   ✅ Todos os dias têm dados de vendas")
                    else:
                        print("   ❌ Série temporal vazia")
                else:
                    print("   ❌ Seção temporal vazia")
                
                # 4. Verificar recomendações
                recomendacoes = dashboard.get('recomendacoes', [])
                print(f"\n💡 RECOMENDAÇÕES: {len(recomendacoes)}")
                for i, rec in enumerate(recomendacoes[:3], 1):
                    print(f"   {i}. {rec.get('tipo', 'N/A')}: {rec.get('mensagem', 'N/A')[:50]}...")
                
            else:
                print(f"❌ Endpoint retornou success=False")
                print(f"   Erro: {data.get('error', 'Desconhecido')}")
        else:
            print(f"❌ Status HTTP: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erro ao testar endpoint: {e}")

def check_database_connection():
    """Verifica a conexão com o banco de dados."""
    print("\n" + "=" * 80)
    print("VERIFICANDO CONEXÃO COM BANCO DE DADOS")
    print("=" * 80)
    
    try:
        from app import create_app
        from app.models import db
        
        app = create_app()
        with app.app_context():
            # Testar conexão
            result = db.session.execute("SELECT 1").scalar()
            print(f"✅ Conexão com banco de dados: OK (resultado: {result})")
            
            # Contar registros básicos
            from app.models import Venda, Produto, Cliente
            
            total_vendas = db.session.query(Venda).count()
            total_produtos = db.session.query(Produto).count()
            total_clientes = db.session.query(Cliente).count()
            
            print(f"\n📊 ESTATÍSTICAS DO BANCO:")
            print(f"   Vendas: {total_vendas}")
            print(f"   Produtos: {total_produtos}")
            print(f"   Clientes: {total_clientes}")
            
            # Verificar vendas recentes
            if total_vendas > 0:
                recent_vendas = db.session.query(Venda).order_by(Venda.data_venda.desc()).limit(5).all()
                print(f"\n🕒 VENDAS RECENTES:")
                for venda in recent_vendas:
                    print(f"   {venda.data_venda}: R$ {venda.total:.2f} ({venda.status})")
            else:
                print("   ⚠️ Nenhuma venda encontrada no banco")
                
    except Exception as e:
        print(f"❌ Erro ao verificar banco: {e}")

if __name__ == "__main__":
    print("Iniciando testes do sistema MercadinhoSys...")
    
    # Verificar se o servidor está rodando
    try:
        response = requests.get("http://localhost:5000/", timeout=5)
        print("✅ Servidor backend está rodando")
    except:
        print("⚠️ Servidor backend não está respondendo. Inicie com: python run.py")
        print("   ou execute: docker-compose up -d")
        sys.exit(1)
    
    # Executar testes
    test_dashboard_endpoints()
    test_specific_data_issues()
    check_database_connection()
    
    print("\n" + "=" * 80)
    print("TESTES CONCLUÍDOS")
    print("=" * 80)