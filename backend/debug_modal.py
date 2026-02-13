
from app import create_app
from app.models import db, Funcionario
from flask_jwt_extended import create_access_token
import json

app = create_app('development')
with app.app_context():
    user = Funcionario.query.filter_by(ativo=True).first()
    token = create_access_token(identity=user.username, additional_claims={
        "estabelecimento_id": user.estabelecimento_id, 
        "role": user.role,
        "status": "ativo"
    })
    
    client = app.test_client()
    response = client.get('/api/produtos/?vencidos=true', headers={"Authorization": f"Bearer {token}"})
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.get_json()
        print(f"Vencidos encontrados: {len(data['produtos'])}")
        if len(data['produtos']) > 0:
            print(f"Primeiro: {data['produtos'][0]['nome']} - {data['produtos'][0]['data_validade']}")
    else:
        print(f"Error: {response.get_data(as_text=True)}")
