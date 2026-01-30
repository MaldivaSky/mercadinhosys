import requests
import json

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
else:
    print(f'❌ Erro: {create_response.text[:500]}')