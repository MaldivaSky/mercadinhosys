import requests
import json
import base64

def decode_jwt(token):
    try:
        header, payload, signature = token.split('.')
        decoded_payload = base64.urlsafe_b64decode(payload + '===').decode('utf-8')
        return json.loads(decoded_payload)
    except Exception as e:
        return f"Error decoding JWT: {e}"

def test_login(username, password):
    url = "http://localhost:5000/api/auth/login"
    payload = {
        "username": username,
        "password": password
    }
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                token = data.get("access_token")
                decoded = decode_jwt(token)
                est_id = decoded.get("estabelecimento_id")
                return True, f"Login successful for {username}. Est ID: {est_id}"
            else:
                return False, f"Login failed for {username}: {data.get('message')}"
        else:
            return False, f"Request failed for {username} with status {response.status_code}: {response.text}"
    except Exception as e:
        return False, f"Exception during login for {username}: {e}"

logins = [
    ("admin_elite", "adminElite123"),
    ("admin_bom", "adminBom123"),
    ("admin_razoavel", "adminRazoavel123"),
    ("admin_mal", "adminMal123"),
    ("admin_pessimo", "adminPessimo123")
]

print("Starting login verification...")
all_success = True
for user, pw in logins:
    success, msg = test_login(user, pw)
    print(msg)
    if not success:
        all_success = False

if all_success:
    print("\n✅ All 5 logins verified successfully!")
else:
    print("\n❌ One or more logins failed verification.")
