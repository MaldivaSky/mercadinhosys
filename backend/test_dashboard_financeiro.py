import requests
import json

login_url = "http://127.0.0.1:5000/api/auth/login"
login_data = {"username": "admin", "senha": "admin123"}

print("🔐 Fazendo login...")
login_response = requests.post(login_url, json=login_data)

if login_response.status_code == 200:
    token = login_response.json()["data"]["access_token"]
    print("✅ Login bem-sucedido\n")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    print("📊 Testando /api/dashboard/cientifico...")
    response = requests.get("http://127.0.0.1:5000/api/dashboard/cientifico", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        
        if "data" in data:
            dashboard_data = data["data"]
            
            # Verificar analise_financeira
            print("\n💰 ANÁLISE FINANCEIRA:")
            if "analise_financeira" in dashboard_data:
                fin = dashboard_data["analise_financeira"]
                
                print(f"\n📋 Despesas Detalhadas:")
                if "despesas_detalhadas" in fin:
                    despesas = fin["despesas_detalhadas"]
                    print(f"   Total de tipos de despesa: {len(despesas)}")
                    for desp in despesas:
                        print(f"   - {desp.get('tipo', 'N/A')}: R$ {desp.get('valor', 0):,.2f} ({desp.get('percentual', 0):.1f}%)")
                else:
                    print("   ❌ despesas_detalhadas não encontrado")
                
                print(f"\n📊 Margens:")
                if "margens" in fin:
                    margens = fin["margens"]
                    for nome, valor in margens.items():
                        print(f"   - {nome}: {valor:.1f}%")
                else:
                    print("   ❌ margens não encontrado")
                
                print(f"\n📈 Indicadores:")
                if "indicadores" in fin:
                    ind = fin["indicadores"]
                    for nome, valor in ind.items():
                        print(f"   - {nome}: {valor}")
                else:
                    print("   ❌ indicadores não encontrado")
            else:
                print("   ❌ analise_financeira não encontrado")
            
            # Salvar JSON completo
            with open("dashboard_full.json", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"\n💾 JSON completo salvo em: dashboard_full.json")
    else:
        print(f"❌ Erro: {response.status_code}")
        print(response.text)
else:
    print(f"❌ Erro no login")
