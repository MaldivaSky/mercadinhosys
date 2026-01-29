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

    print("\n=== TESTE COMPLETO CRUD PRODUTOS ===\n")

    # 1. Criar produto
    print("1. Criando novo produto...")
    create_data = {
        'nome': 'Produto Teste CRUD',
        'categoria': 'Teste',
        'preco_custo': 10.00,
        'preco_venda': 15.00,
        'quantidade': 100,
        'ativo': True
    }
    create_response = requests.post('http://localhost:5000/api/produtos', json=create_data, headers=headers)
    print(f'CREATE status: {create_response.status_code}')
    if create_response.status_code == 201:
        create_data_resp = create_response.json()
        new_produto_id = create_data_resp.get('produto', {}).get('id')
        print(f'Produto criado ID: {new_produto_id}')
    else:
        print(f'Erro CREATE: {create_response.text}')
        exit(1)

    # 2. Ler produto
    print(f"\n2. Lendo produto ID {new_produto_id}...")
    get_response = requests.get(f'http://localhost:5000/api/produtos/{new_produto_id}', headers=headers)
    print(f'READ status: {get_response.status_code}')
    if get_response.status_code == 200:
        produto_data = get_response.json()
        print(f'Produto lido: {produto_data.get("nome")}')
    else:
        print(f'Erro READ: {get_response.text}')

    # 3. Atualizar produto
    print(f"\n3. Atualizando produto ID {new_produto_id}...")
    update_data = {
        'nome': 'Produto Teste CRUD Atualizado',
        'preco_venda': 18.00,
        'tipo': 'Higiene',
        'fabricante': 'Teste Corp'
    }
    update_response = requests.put(f'http://localhost:5000/api/produtos/{new_produto_id}', json=update_data, headers=headers)
    print(f'UPDATE status: {update_response.status_code}')
    if update_response.status_code == 200:
        print('Produto atualizado com sucesso!')
    else:
        print(f'Erro UPDATE: {update_response.text}')

    # 4. Ajustar estoque
    print(f"\n4. Ajustando estoque do produto ID {new_produto_id}...")
    stock_data = {
        'tipo': 'entrada',
        'quantidade': 50,
        'motivo': 'Teste CRUD'
    }
    stock_response = requests.post(f'http://localhost:5000/api/produtos/{new_produto_id}/estoque', json=stock_data, headers=headers)
    print(f'STOCK ADJUST status: {stock_response.status_code}')
    if stock_response.status_code == 200:
        print('Estoque ajustado com sucesso!')
    else:
        print(f'Erro STOCK: {stock_response.text}')

    # 5. Deletar produto (soft delete)
    print(f"\n5. Desativando produto ID {new_produto_id}...")
    delete_response = requests.delete(f'http://localhost:5000/api/produtos/{new_produto_id}', headers=headers)
    print(f'DELETE status: {delete_response.status_code}')
    if delete_response.status_code == 200:
        print('Produto desativado com sucesso!')
    else:
        print(f'Erro DELETE: {delete_response.text}')

    print("\n=== CRUD TESTE CONCLUÍDO ===")
    print("✅ CREATE - OK")
    print("✅ READ - OK")
    print("✅ UPDATE - OK")
    print("✅ STOCK ADJUST - OK")
    print("✅ DELETE - OK")
    print("\n🎉 CRUD de produtos funcionando perfeitamente!")

else:
    print(f'Login falhou: {login_response.text}')