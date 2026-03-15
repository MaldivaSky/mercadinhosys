import requests
import json
from app import create_app
app = create_app()

BASE_URL = 'http://localhost:5000/api'

# Test 1: Login maldivas
print("🧪 TEST 1: SUPER ADMIN LOGIN")
login_payload = {
    "identifier": "maldivas",
    "senha": "Mald1v@$" 
}
r_login = requests.post(f'{BASE_URL}/auth/login', json=login_payload)
print(f"Login status: {r_login.status_code}")
if r_login.status_code == 200:
    data = r_login.json()
    token = data['access_token']
    user = data['data']['user']
    print(f"✅ LOGIN OK - User: {user['username']}, Role: {user['role']}, Super: {user['is_super_admin']}")
else:
    print(f"❌ LOGIN FAIL: {r_login.text}")

# Test 2: Configuracao with token
print("\n🧪 TEST 2: CONFIGURACAO (com token)")
headers = {'Authorization': f'Bearer {token}'}
r_config = requests.get(f'{BASE_URL}/configuracao/', headers=headers)
print(f"Config status: {r_config.status_code}")
print(f"Config OK: {r_config.json() if r_config.ok else r_config.text}")

# Test 3: Dashboard with token
print("\n🧪 TEST 3: DASHBOARD (com token)")
r_dash = requests.get(f'{BASE_URL}/dashboard', headers=headers)
print(f"Dashboard status: {r_dash.status_code}")
print(f"Dashboard OK: {r_dash.json() if r_dash.ok else r_dash.text}")

print("\n✅ ALL TESTS COMPLETE")
