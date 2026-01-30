import requests
import json
import time

# Aguardar o servidor iniciar
time.sleep(3)

# Login
login_response = requests.post('http://localhost:5000/api/auth/login', json={
    'email': 'admin',
    'senha': 'admin123'
})

token = login_response.json()['data']['access_token']
headers = {'Authorization': f'Bearer {token}'}

print('Testando criação de cliente com CPF válido...')

# Criar cliente com CPF válido
novo_cliente = {
    'nome': 'João Silva',
    'cpf': '12345678909',  # CPF válido
    'celular': '11999999999'
}

create_response = requests.post('http://localhost:5000/api/clientes/', json=novo_cliente, headers=headers)
print(f'Status: {create_response.status_code}')

if create_response.status_code == 201:
    print('✅ Cliente criado com sucesso!')
    cliente_data = create_response.json()['cliente']
    print(f'ID: {cliente_data["id"]}, Nome: {cliente_data["nome"]}')

    # Testar outras operações CRUD
    cliente_id = cliente_data['id']

    # Obter cliente
    get_response = requests.get(f'http://localhost:5000/api/clientes/{cliente_id}', headers=headers)
    print(f'GET /api/clientes/{cliente_id}: {get_response.status_code}')

    # Atualizar cliente
    update_response = requests.put(f'http://localhost:5000/api/clientes/{cliente_id}', json={'nome': 'João Silva Atualizado'}, headers=headers)
    print(f'PUT /api/clientes/{cliente_id}: {update_response.status_code}')

    # Alterar status
    status_response = requests.patch(f'http://localhost:5000/api/clientes/{cliente_id}/status', json={'ativo': False}, headers=headers)
    print(f'PATCH /api/clientes/{cliente_id}/status: {status_response.status_code}')

    # Excluir cliente
    delete_response = requests.delete(f'http://localhost:5000/api/clientes/{cliente_id}', headers=headers)
    print(f'DELETE /api/clientes/{cliente_id}: {delete_response.status_code}')

    print('✅ Todas as operações CRUD funcionaram!')

else:
    print(f'❌ Erro na criação: {create_response.text[:500]}')