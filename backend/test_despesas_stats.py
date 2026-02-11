import sys
sys.path.insert(0, '.')
from app import create_app
from flask_jwt_extended import create_access_token

app = create_app()

with app.app_context():
    # Criar token de teste
    access_token = create_access_token(
        identity=1,
        additional_claims={"estabelecimento_id": 1, "role": "admin"}
    )
    
    # Testar endpoint
    with app.test_client() as client:
        response = client.get(
            '/api/despesas/estatisticas',
            headers={'Authorization': f'Bearer {access_token}'}
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.get_json()
            print("✅ Endpoint funcionando!")
            print(f"Total despesas: {data['estatisticas']['total_despesas']}")
            print(f"Soma total: R$ {data['estatisticas']['soma_total']:.2f}")
            print(f"Média: R$ {data['estatisticas']['media_valor']:.2f}")
        else:
            print(f"❌ Erro: {response.get_json()}")
