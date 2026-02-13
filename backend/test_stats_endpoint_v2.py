
from app import create_app
from app.models import db, Funcionario
from flask_jwt_extended import create_access_token
import json

app = create_app('development')
with app.app_context():
    # Get a real user to make a token
    user = Funcionario.query.filter_by(ativo=True).first()
    if not user:
        print("No active user found")
        exit(1)
    
    token = create_access_token(identity=user.username, additional_claims={
        "estabelecimento_id": user.estabelecimento_id, 
        "role": user.role,
        "status": "ativo"
    })
    
    client = app.test_client()
    response = client.get('/api/produtos/estatisticas', headers={"Authorization": f"Bearer {token}"})
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.get_json()
        print(f"Total Produtos: {data['estatisticas']['total_produtos']}")
        print(f"Validade: {json.dumps(data['estatisticas']['validade'], indent=2)}")
    else:
        print(f"Error: {response.get_data(as_text=True)}")
