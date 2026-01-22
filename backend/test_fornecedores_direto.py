"""Teste direto da rota de fornecedores"""
from app import create_app
from app.models import db, Fornecedor, Funcionario
from flask_jwt_extended import create_access_token

app = create_app()

with app.app_context():
    # Pegar um funcionário admin
    admin = Funcionario.query.filter_by(username='admin').first()
    
    if not admin:
        print("❌ Admin não encontrado")
        exit(1)
    
    print(f"✅ Admin encontrado: {admin.nome}")
    print(f"   Estabelecimento ID: {admin.estabelecimento_id}")
    
    # Criar token JWT
    additional_claims = {
        "estabelecimento_id": admin.estabelecimento_id,
        "role": admin.role,
        "status": admin.status,
        "nome": admin.nome
    }
    
    token = create_access_token(
        identity=admin.id,
        additional_claims=additional_claims
    )
    
    print(f"\n✅ Token criado: {token[:50]}...")
    
    # Testar a rota diretamente
    with app.test_client() as client:
        print("\n🔍 Testando GET /api/fornecedores...")
        
        response = client.get(
            '/api/fornecedores',
            headers={'Authorization': f'Bearer {token}'},
            query_string={'por_pagina': 10}
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.get_json()
            print(f"✅ Sucesso!")
            print(f"Total: {data.get('total')}")
            print(f"Fornecedores: {len(data.get('fornecedores', []))}")
            
            if data.get('fornecedores'):
                print(f"\n📦 Primeiro fornecedor:")
                primeiro = data['fornecedores'][0]
                print(f"   ID: {primeiro.get('id')}")
                print(f"   Nome Fantasia: {primeiro.get('nome_fantasia')}")
                print(f"   CNPJ: {primeiro.get('cnpj')}")
                print(f"   Produtos Ativos: {primeiro.get('produtos_ativos')}")
        else:
            print(f"❌ Erro {response.status_code}")
            print(response.get_data(as_text=True))
