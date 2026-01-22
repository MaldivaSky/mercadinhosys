import requests
import json

# Login first
login_url = "http://127.0.0.1:5000/api/auth/login"
login_data = {"username": "admin", "senha": "admin123"}

print("=" * 60)
print("TESTE - DASHBOARD CIENTÍFICO - CURVA ABC")
print("=" * 60)

print("\n🔐 Fazendo login...")
login_response = requests.post(login_url, json=login_data)

if login_response.status_code != 200:
    print(f"❌ Erro no login: {login_response.text}")
    exit(1)

token = login_response.json()["data"]["access_token"]
print(f"✅ Login bem-sucedido")

headers = {"Authorization": f"Bearer {token}"}

# Test dashboard científico
print("\n📊 Testando /api/dashboard/cientifico...")
response = requests.get(
    "http://127.0.0.1:5000/api/dashboard/cientifico",
    headers=headers
)

print(f"Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    
    if data.get("success"):
        print(f"✅ Dashboard carregado com sucesso")
        
        # Verificar estrutura de dados
        if "data" in data:
            dashboard_data = data["data"]
            
            # Verificar analise_produtos
            if "analise_produtos" in dashboard_data:
                analise = dashboard_data["analise_produtos"]
                
                # Verificar curva_abc
                if "curva_abc" in analise:
                    curva_abc = analise["curva_abc"]
                    print(f"\n📈 CURVA ABC:")
                    print(f"   Pareto 80/20: {curva_abc.get('pareto_80_20', False)}")
                    print(f"   Total de produtos: {len(curva_abc.get('produtos', []))}")
                    
                    # Mostrar resumo
                    if "resumo" in curva_abc:
                        resumo = curva_abc["resumo"]
                        print(f"\n   RESUMO:")
                        for classe, dados in resumo.items():
                            print(f"   Classe {classe}:")
                            print(f"      - Quantidade: {dados.get('quantidade', 0)}")
                            print(f"      - Faturamento: R$ {dados.get('faturamento_total', 0):,.2f}")
                            print(f"      - Percentual: {dados.get('percentual', 0):.1f}%")
                    
                    # Mostrar primeiros 10 produtos
                    produtos = curva_abc.get("produtos", [])
                    if produtos:
                        print(f"\n   TOP 10 PRODUTOS:")
                        for i, produto in enumerate(produtos[:10], 1):
                            print(f"   {i}. {produto.get('nome', 'SEM NOME')}")
                            print(f"      - Faturamento: R$ {produto.get('faturamento', 0):,.2f}")
                            print(f"      - Classificação: {produto.get('classificacao', 'N/A')}")
                            print(f"      - Quantidade vendida: {produto.get('quantidade_vendida', 0)}")
                            print(f"      - % Acumulado: {produto.get('percentual_acumulado', 0):.1f}%")
                    else:
                        print(f"\n   ⚠️ Nenhum produto encontrado na curva ABC")
                
                # Verificar produtos_estrela
                if "produtos_estrela" in analise:
                    estrelas = analise["produtos_estrela"]
                    print(f"\n⭐ PRODUTOS ESTRELA: {len(estrelas)} produtos")
                    for i, produto in enumerate(estrelas[:5], 1):
                        print(f"   {i}. {produto.get('nome', 'SEM NOME')}")
                        print(f"      - Faturamento: R$ {produto.get('faturamento', 0):,.2f}")
                        print(f"      - Quantidade: {produto.get('quantidade_vendida', 0)}")
                
                # Verificar produtos_lentos
                if "produtos_lentos" in analise:
                    lentos = analise["produtos_lentos"]
                    print(f"\n⚠️ PRODUTOS LENTOS: {len(lentos)} produtos")
                    for i, produto in enumerate(lentos[:5], 1):
                        print(f"   {i}. {produto.get('nome', 'SEM NOME')}")
            
            # Verificar dados do mês
            if "mes" in dashboard_data:
                mes = dashboard_data["mes"]
                print(f"\n💰 DADOS DO MÊS:")
                print(f"   Total vendas: R$ {mes.get('total_vendas', 0):,.2f}")
                print(f"   Lucro bruto: R$ {mes.get('lucro_bruto', 0):,.2f}")
                print(f"   Margem lucro: {mes.get('margem_lucro', 0):.1f}%")
                print(f"   ROI mensal: {mes.get('roi_mensal', 0):.1f}%")
        
        # Salvar resposta completa para análise
        with open("backend/dashboard_response.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Resposta completa salva em: backend/dashboard_response.json")
    else:
        print(f"❌ Dashboard retornou success=False")
        print(f"Dados: {json.dumps(data, indent=2)}")
else:
    print(f"❌ Erro: {response.text}")

print("\n" + "=" * 60)
