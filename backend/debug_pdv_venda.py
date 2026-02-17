import sys
import os
from unittest.mock import MagicMock, patch
from flask import Flask, current_app

import logging

# Setup mocked flask app
from app import create_app, db
from app.models import Funcionario, Estabelecimento, Produto, Cliente, Configuracao

app = create_app()

# Add FileHandler to app logger
file_handler = logging.FileHandler('debug_pdv.log')
file_handler.setLevel(logging.DEBUG)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.DEBUG)


def simulate_sale():
    with app.app_context():
        # 1. Setup Data
        estab = Estabelecimento.query.first()
        func = Funcionario.query.filter_by(estabelecimento_id=estab.id).first()
        cliente = Cliente.query.filter_by(estabelecimento_id=estab.id).first()
        produto = Produto.query.filter_by(estabelecimento_id=estab.id).first()
        
        if not all([estab, func, cliente, produto]):
            print("❌ Dados insuficientes no DB para teste (precisa de Estab, Func, Cliente, Produto)")
            return

        print(f"--- Dados de Teste ---")
        print(f"Funcionario: {func.nome} (ID: {func.id})")
        print(f"Cliente: {cliente.nome} (Email: {cliente.email})")
        print(f"Produto: {produto.nome}")
        
        # Ensure cliente has email
        if not cliente.email:
            print("⚠️ Cliente sem email, definindo temporario...")
            cliente.email = "rafaelmaldivas@gmail.com"
            db.session.commit()

        # 2. Mock Request Data
        payload = {
            "cliente_id": cliente.id,
            "items": [
                {
                    "id": produto.id,
                    "quantity": 1,
                    "discount": 0,
                    "total": float(produto.preco_venda)
                }
            ],
            "subtotal": float(produto.preco_venda),
            "desconto": 0,
            "total": float(produto.preco_venda),
            "valor_recebido": float(produto.preco_venda),
            "troco": 0,
            "paymentMethod": "dinheiro",
            "enviar_email": True  # IMPORTANTE
        }
        
        # 3. Patch and Call
        with app.test_request_context(json=payload):
            # Patch get_jwt_identity specifically where it is used in pdv.py
            with patch('app.routes.pdv.get_jwt_identity') as mock_identity:
                mock_identity.return_value = func.id
                
                print("\n--- Chamando finalizar_venda() ---")
                from app.routes.pdv import finalizar_venda
                
                # Tentar acessar a função original (bypass decorators)
                func_to_call = finalizar_venda
                
                # Desembrulhar se estiver decorada
                while hasattr(func_to_call, '__wrapped__'):
                    func_to_call = func_to_call.__wrapped__
                
                print(f"Chamando função desembrulhada: {func_to_call}")
                
                try:
                    # Chamar a função original, que agora vai usar o get_jwt_identity mockado
                    response = func_to_call()
                    
                    if isinstance(response, tuple):
                        resp_obj, status_code = response
                        print(f"\nStatus Code: {status_code}")
                        # Se for response object
                        if hasattr(resp_obj, 'get_json'):
                            print(f"Response: {resp_obj.get_json()}")
                        else:
                            print(f"Response Body: {resp_obj}")
                    else:
                        print(f"\nResponse: {response}")
                        if hasattr(response, 'get_json'):
                            print(f"Response JSON: {response.get_json()}")
                        
                except Exception as e:
                    print(f"❌ Erro na execução: {e}")
                    import traceback
                    traceback.print_exc()

if __name__ == "__main__":
    simulate_sale()
