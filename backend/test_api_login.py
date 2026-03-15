
import sys
import os
from app import create_app
from app.models import db, Funcionario

app = create_app()
client = app.test_client()

with app.app_context():
    print(f"DEBUG: App using DB URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    # 1. Check user existence
    u = Funcionario.query.filter_by(username='maldivas').first()
    if u:
        print(f"✅ DB check: User 'maldivas' exists. ativo={u.ativo}, status={u.status}")
    else:
        print("❌ DB check: User 'maldivas' NOT FOUND!")
    
    # 2. API Test
    payload = {
        "identifier": "maldivas",
        "senha": "maldivas123"
    }
    print(f"DEBUG: Attempting login with: {payload}")
    response = client.post("/api/auth/login", json=payload)
    
    print(f"DEBUG: Response Status: {response.status_code}")
    print(f"DEBUG: Response Data: {response.get_json()}")
