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

if login_response.status_code != 200:
    print('Erro no login:', login_response.status_code, login_response.text)
    exit(1)

token = login_response.json()['data']['access_token']
headers = {'Authorization': f'Bearer {token}'}

print('Login realizado com sucesso!')

# Testar GET /api/clientes/
clientes_response = requests.get('http://localhost:5000/api/clientes/', headers=headers)
print('GET /api/clientes/ status:', clientes_response.status_code)

if clientes_response.status_code == 200:
    data = clientes_response.json()
    print('✅ API de clientes funcionando!')
    print(f'Total de clientes: {data.get("total", 0)}')
else:
    print('❌ Erro na API de clientes:', clientes_response.text[:500])