
import sys
import os
import json
from datetime import datetime, date
from decimal import Decimal
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Funcionario, Estabelecimento
from flask_jwt_extended import create_access_token

def test_dashboard_live():
    app = create_app()
    client = app.test_client()
    
    with app.app_context():
        print("🔍 Iniciando Teste LIVE do Dashboard (Simulando Request)...")
        
        # 1. Pegar Admin
        admin = Funcionario.query.filter_by(role='admin').first()
        if not admin:
            # Tentar achar qualquer um
            admin = Funcionario.query.first()
            if not admin:
                print("❌ Nenhum funcionário encontrado para login!")
                return
            print(f"⚠️ Usando funcionário {admin.nome} ({admin.role}) - pode falhar se não for admin")
        else:
            print(f"👤 Logando como Admin: {admin.nome} (ID: {admin.id})")
            
        # 2. Gerar Token
        access_token = create_access_token(
            identity=str(admin.id), 
            additional_claims={
                "estabelecimento_id": admin.estabelecimento_id, 
                "role": admin.role,
                "status": "ativo"
            }
        )
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        # 3. Fazer Request
        url = f"/api/cientifico/dashboard/{admin.estabelecimento_id}"
        print(f"🌐 GET {url}")
        
        response = client.get(url, headers=headers)
        
        print(f"📥 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.get_json()
            print("✅ Sucesso! Dashboard carregado.")
            # Verificar alguns campos
            print(f"   - Tendência: {data.get('summary', {}).get('sales_trend', {}).get('trend')}")
            print(f"   - Total Vendas: {data.get('summary', {}).get('revenue', {}).get('value')}")
            print(f"   - RH Metrics: {data.get('rh', {}).get('custo_folha_estimado')}")
        else:
            print(f"❌ ERRO: {response.status_code}")
            print(response.get_data(as_text=True))

if __name__ == "__main__":
    test_dashboard_live()
