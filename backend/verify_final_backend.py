
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app

print(f"ENV MULTI_TENANT_MODE: {os.environ.get('MULTI_TENANT_MODE')}")
app = create_app()
print(f"APP CONFIG MULTI_TENANT_MODE: {app.config.get('MULTI_TENANT_MODE')}")

client = app.test_client()

with app.app_context():
    # 1. Login
    payload = {"identifier": "admin_elite", "senha": "adminElite123"}
    login_res = client.post("/api/auth/login", json=payload)
    login_data = login_res.get_json()
    
    if login_data and login_data.get('success'):
        token = login_data.get('access_token')
        print("✅ Login OK")
        
        # 2. Test /me
        me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        print(f"DEBUG: /me Status: {me_res.status_code}")
        print(f"DEBUG: /me Data: {me_res.get_json()}")
        
        # 3. Test /verify-tenant
        vt_res = client.get("/api/auth/verify-tenant", headers={"Authorization": f"Bearer {token}"})
        print(f"DEBUG: /verify-tenant Status: {vt_res.status_code}")
        print(f"DEBUG: /verify-tenant Data: {vt_res.get_json()}")
    else:
        print(f"❌ Login Failed: {login_data}")
