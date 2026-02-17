
from app import create_app

# Configuração mínima do app para contexto
app = create_app()

# update config if needed (though create_app should load it)
app.config['MAIL_DEBUG'] = True
app.config['DEBUG'] = True

from app.utils.email_service import enviar_cupom_fiscal
from app.models import Configuracao

def get_db_logo():
    with app.app_context():
        config = Configuracao.query.first()
        if config and config.logo_base64:
            return config.logo_base64
        elif config and config.logo_url:
            return config.logo_url
    return None

def testar_envio():
    # Dados simulados de uma venda
    venda_data = {
        "venda": {
            "codigo": "TEST-DB-LOGO-123",
            "data": "17/12/2024 14:30:00"
        },
        "comprovante": {
            "cliente": "Cliente Teste DB Logo",
            "funcionario": "Operador Caixa",
            "itens": [
                {"nome": "Produto A", "codigo": "123", "quantidade": 2, "preco_unitario": 10.00, "total": 20.00},
                {"nome": "Produto B", "codigo": "456", "quantidade": 1, "preco_unitario": 5.50, "total": 5.50}
            ],
            "subtotal": 25.50,
            "desconto": 0.00,
            "total": 25.50,
            "forma_pagamento": "Dinheiro",
            "valor_recebido": 30.00,
            "troco": 4.50
        },
        "estabelecimento": {
            "nome_fantasia": "Mercadinho Sys Demo",
            "razao_social": "Mercadinho Sys Ltda",
            "cnpj": "12.345.678/0001-90",
            "inscricao_estadual": "123.456.789",
            "telefone": "(11) 98765-4321",
            "email": "contato@mercadinhosys.com.br",
            "endereco": "Rua Exemplo, 123 - Centro - São Paulo/SP",
            "logo_url": get_db_logo()
        }
    }
    
    print("Tentando enviar email de teste com logo do BANCO...")
    # Email destino (usando o mesmo do remetente para teste)
    email_destino = "rafaelmaldivas@gmail.com"
    
    with app.app_context():
        sucesso, msg = enviar_cupom_fiscal(venda_data, email_destino)
        if sucesso:
            print(f"✅ Email enviado com sucesso!")
        else:
            print(f"❌ Erro ao enviar email: {msg}")

if __name__ == "__main__":
    testar_envio()
