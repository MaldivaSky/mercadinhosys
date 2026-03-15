import requests
import json

def test_login():
    url = "http://localhost:5000/api/auth/login"
    payload = {
        "identifier": "admin_elite",
        "username": "admin_elite",
        "senha": "adminElite123",
        "password": "adminElite123"
    }
    headers = {
        "Content-Type": "application/json",
        "X-Tenant-ID": "admin_elite"
    }
    
    print(f"Testing login at {url}...")
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Body: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('access_token')
            if token:
                print("\nLogin Successful! Testing /me...")
                me_url = "http://localhost:5000/api/auth/me"
                me_headers = {"Authorization": f"Bearer {token}"}
                me_response = requests.get(me_url, headers=me_headers, timeout=10)
                print(f"Me Status: {me_response.status_code}")
                print(f"Me Body: {json.dumps(me_response.json(), indent=2)}")
                
                print("\nTesting /verify-tenant...")
                vt_url = "http://localhost:5000/api/auth/verify-tenant"
                vt_response = requests.get(vt_url, headers=me_headers, timeout=10)
                print(f"VT Status: {vt_response.status_code}")
                print(f"VT Body: {json.dumps(vt_response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_login()
