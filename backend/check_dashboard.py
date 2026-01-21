import requests
import json

# Fazer login
login_response = requests.post('http://localhost:5000/api/auth/login',
                              json={'email': 'admin@empresa.com', 'senha': 'admin123'})
token = login_response.json()['data']['access_token']

# Buscar dados do dashboard
headers = {'Authorization': f'Bearer {token}'}
dashboard_response = requests.get('http://localhost:5000/api/dashboard/cientifico', headers=headers)

print('=== DADOS DO DASHBOARD ===')
data = dashboard_response.json()['data']

print('HOJE:')
print(json.dumps(data['hoje'], indent=2, ensure_ascii=False))

print('\nMÊS:')
print(json.dumps(data['mes'], indent=2, ensure_ascii=False))

print('\nANÁLISE PRODUTOS:')
print(json.dumps(data['analise_produtos'], indent=2, ensure_ascii=False))

print('\nANÁLISE FINANCEIRA:')
print(json.dumps(data['analise_financeira'], indent=2, ensure_ascii=False))

print('\nANÁLISE TEMPORAL:')
print(json.dumps(data['analise_temporal'], indent=2, ensure_ascii=False))

print('\nINSIGHTS CIENTÍFICOS:')
print(json.dumps(data['insights_cientificos'], indent=2, ensure_ascii=False))