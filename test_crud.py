import requests
import json
import time

time.sleep(2)

# Fazer login
login_url = 'http://localhost:5000/api/auth/login'
login_data = {'username': 'admin', 'senha': 'admin123'}

login_response = requests.post(login_url, json=login_data)
print(f'Login status: {login_response.status_code}')
if login_response.status_code == 200:
    login_result = login_response.json()
    token = login_result['data']['access_token']

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    # Obter produtos
    produtos_response = requests.get('http://localhost:5000/api/produtos/estoque?pagina=1&por_pagina=1', headers=headers)
    print(f'Produtos status: {produtos_response.status_code}')
    if produtos_response.status_code == 200:
        produtos_data = produtos_response.json()
        if produtos_data.get('produtos'):
            produto = produtos_data['produtos'][0]
            produto_id = produto['id']
            print(f'Produto ID: {produto_id}, Nome: {produto.get("nome")}')

            # Dados para atualização
            update_data = {
                'nome': 'Produto Atualizado Teste',
                'preco_venda': 20.00,
                'tipo': 'Higiene',
                'fabricante': 'Teste'
            }

            # PUT
            put_response = requests.put(f'http://localhost:5000/api/produtos/{produto_id}', json=update_data, headers=headers)
            print(f'PUT status: {put_response.status_code}')
            if put_response.status_code == 200:
                print('SUCESSO! CRUD corrigido!')
                put_data = put_response.json()
                print(f'Produto atualizado: {put_data.get("produto", {}).get("nome")}')
            else:
                print(f'Erro PUT: {put_response.text}')
        else:
            print('Nenhum produto encontrado')
    else:
        print(f'Erro GET produtos: {produtos_response.text}')
else:
    print(f'Login falhou: {login_response.text}')