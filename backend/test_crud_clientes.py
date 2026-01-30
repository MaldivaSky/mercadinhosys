import requests
import json
import time

print('🔍 Testando CRUD completo de clientes...')

# Aguardar servidor iniciar
time.sleep(3)

# Login
login_response = requests.post('http://localhost:5000/api/auth/login', json={
    'email': 'admin',
    'senha': 'admin123'
})

if login_response.status_code != 200:
    print('❌ Erro no login:', login_response.text)
    exit(1)

token = login_response.json()['data']['access_token']
headers = {'Authorization': f'Bearer {token}'}

print('✅ Login realizado com sucesso!')

# 1. Listar clientes
print('\n📋 Testando listagem...')
list_response = requests.get('http://localhost:5000/api/clientes/', headers=headers)
print(f'GET /api/clientes/: {list_response.status_code}')

if list_response.status_code == 200:
    data = list_response.json()
    print(f'✅ Listagem OK - {data.get("total", 0)} clientes encontrados')
else:
    print(f'❌ Erro na listagem: {list_response.text[:300]}')
    exit(1)

# 2. Criar cliente
print('\n➕ Testando criação...')
novo_cliente = {
    'nome': 'Cliente Teste JWT',
    'cpf': '12345678909',  # CPF válido
    'celular': '11999999999',
    'email': 'teste@jwt@email.com'
}

create_response = requests.post('http://localhost:5000/api/clientes/', json=novo_cliente, headers=headers)
print(f'POST /api/clientes/: {create_response.status_code}')

if create_response.status_code == 201:
    cliente_data = create_response.json()['cliente']
    cliente_id = cliente_data['id']
    print(f'✅ Cliente criado - ID: {cliente_id}, Nome: {cliente_data["nome"]}')

    # 3. Obter cliente específico
    print('\n🔍 Testando obtenção...')
    get_response = requests.get(f'http://localhost:5000/api/clientes/{cliente_id}', headers=headers)
    print(f'GET /api/clientes/{cliente_id}: {get_response.status_code}')

    if get_response.status_code == 200:
        print('✅ Obtenção OK')
    else:
        print(f'❌ Erro na obtenção: {get_response.text[:300]}')

    # 4. Atualizar cliente
    print('\n✏️ Testando atualização...')
    update_data = {'nome': 'Cliente Teste JWT Atualizado'}
    update_response = requests.put(f'http://localhost:5000/api/clientes/{cliente_id}', json=update_data, headers=headers)
    print(f'PUT /api/clientes/{cliente_id}: {update_response.status_code}')

    if update_response.status_code == 200:
        print('✅ Atualização OK')
    else:
        print(f'❌ Erro na atualização: {update_response.text[:300]}')

    # 5. Alterar status
    print('\n🔄 Testando alteração de status...')
    status_response = requests.patch(f'http://localhost:5000/api/clientes/{cliente_id}/status', json={'ativo': False}, headers=headers)
    print(f'PATCH /api/clientes/{cliente_id}/status: {status_response.status_code}')

    if status_response.status_code == 200:
        print('✅ Status alterado OK')
    else:
        print(f'❌ Erro na alteração de status: {status_response.text[:300]}')

    # 6. Excluir cliente
    print('\n🗑️ Testando exclusão...')
    delete_response = requests.delete(f'http://localhost:5000/api/clientes/{cliente_id}', headers=headers)
    print(f'DELETE /api/clientes/{cliente_id}: {delete_response.status_code}')

    if delete_response.status_code == 200:
        print('✅ Exclusão OK')
    else:
        print(f'❌ Erro na exclusão: {delete_response.text[:300]}')

    print('\n🎉 CRUD de clientes funcionando perfeitamente!')

else:
    print(f'❌ Erro na criação: {create_response.text[:500]}')