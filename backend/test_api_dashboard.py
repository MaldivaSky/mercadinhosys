#!/usr/bin/env python3
"""
Teste da API do dashboard científico
"""
import requests
import json

# Testar o endpoint do dashboard científico
# Primeiro preciso fazer login para obter o token

# Simular login
login_data = {
    'email': 'admin',
    'senha': 'admin123'
}

try:
    # Fazer login
    login_response = requests.post('http://localhost:5000/api/auth/login', json=login_data)
    print(f"Status do login: {login_response.status_code}")
    print(f"Resposta do login: {login_response.text}")
    
    if login_response.status_code == 200:
        login_data_resp = login_response.json()
        print(f"Chaves na resposta: {login_data_resp.keys()}")
        
        # Verificar se tem token
        if 'access_token' in login_data_resp.get('data', {}):
            token = login_data_resp['data']['access_token']
            print('✅ Login realizado com sucesso!')
        elif 'token' in login_data_resp.get('data', {}):
            token = login_data_resp['data']['token']
            print('✅ Login realizado com sucesso (token)!')
        else:
            print('❌ Token não encontrado na resposta')
            exit(1)

        # Fazer requisição ao dashboard científico
        headers = {'Authorization': f'Bearer {token}'}
        dashboard_response = requests.get('http://localhost:5000/api/dashboard/cientifico', headers=headers)

        if dashboard_response.status_code == 200:
            data = dashboard_response.json()['data']
            print('✅ Dashboard científico via API funcionando!')
            print(f'📊 Total vendas hoje: R$ {data["hoje"]["total_vendas"]:.2f}')
            print(f'📈 Curva ABC - Total produtos: {len(data["analise_produtos"]["curva_abc"]["produtos"])}')
            print(f'⭐ Produtos estrela: {len(data["analise_produtos"]["produtos_estrela"])}')
            print(f'🐌 Produtos lentos: {len(data["analise_produtos"]["produtos_lentos"])}')
            print(f'🔮 Previsão demanda: {len(data["analise_produtos"]["previsao_demanda"])}')

            # Verificar resumo ABC
            resumo = data["analise_produtos"]["curva_abc"]["resumo"]
            print(f'📊 Classe A: {resumo["A"]["quantidade"]} produtos ({resumo["A"]["percentual"]:.1f}%)')
            print(f'📊 Classe B: {resumo["B"]["quantidade"]} produtos ({resumo["B"]["percentual"]:.1f}%)')
            print(f'📊 Classe C: {resumo["C"]["quantidade"]} produtos ({resumo["C"]["percentual"]:.1f}%)')
        else:
            print(f'❌ Erro na API do dashboard: {dashboard_response.status_code}')
            print(dashboard_response.text)
    else:
        print(f'❌ Erro no login: {login_response.status_code}')
        print(login_response.text)

except requests.exceptions.ConnectionError:
    print('❌ Servidor não está rodando. Inicie o backend primeiro.')
except Exception as e:
    print(f'❌ Erro: {e}')