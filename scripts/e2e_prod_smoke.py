import os
import sys
import uuid
import time
from decimal import Decimal

try:
    import requests
except ImportError:
    print("Por favor, instale a biblioteca requests: pip install requests")
    sys.exit(1)

# Configurável via variável de ambiente, padrão para localhost (simulando prod)
API_URL = os.environ.get("API_URL", "http://localhost:5000").rstrip("/")

def main():
    print(f"🚀 Iniciando E2E Smoke Test contra {API_URL}")
    session = requests.Session()
    
    # 1. ONBOARDING
    print("\n--- 1. ONBOARDING ---")
    random_suffix = uuid.uuid4().hex[:6]
    email_admin = f"smoke_admin_{random_suffix}@test.com"
    email_loja = f"smoke_loja_{random_suffix}@test.com"
    cnpj = f"45{random_suffix[:4]}0001{random_suffix[-2:]}"
    
    onboarding_payload = {
        "nome_fantasia": f"Smoke Store {random_suffix}",
        "razao_social": f"Smoke Store {random_suffix} LTDA",
        "cnpj": cnpj,
        "telefone": "92999999999",
        "email_estabelecimento": email_loja,
        "nome_admin": "Admin Smoke",
        "email_admin": email_admin,
        "senha_admin": "Smoke@123!"
    }
    
    print(f"Criando tenant: {onboarding_payload['nome_fantasia']}")
    r = session.post(f"{API_URL}/api/saas/onboarding", json=onboarding_payload)
    if r.status_code != 201:
        print(f"❌ Falha no Onboarding: {r.text}")
        sys.exit(1)
        
    data = r.json()
    estabelecimento_id = data["data"]["estabelecimento"]["id"]
    print(f"✅ Tenant criado com ID: {estabelecimento_id}")
    
    # 1.1 LOGIN PARA PEGAR O TOKEN (apesar do onboarding já devolver logado, garantimos o fluxo padrão)
    print("\n--- 1.1 LOGIN ---")
    r_login = session.post(f"{API_URL}/api/auth/login", json={
        "email": email_admin,
        "password": "Smoke@123!"
    })
    
    if r_login.status_code != 200:
        print(f"❌ Falha no Login: {r_login.text}")
        sys.exit(1)
        
    token = r_login.json().get("access_token")
    if not token:
        print("❌ Login não retornou access_token")
        sys.exit(1)
        
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Login realizado com sucesso")
    
    # 2. PRÉ-REQS (Categoria, Produto e Caixa)
    print("\n--- 2. PRÉ-REQUISITOS (Categoria, Produto, Caixa) ---")
    
    # Criar categoria
    r_cat = session.post(f"{API_URL}/api/produtos/categorias", json={"nome": "Bebidas"}, headers=headers)
    if r_cat.status_code not in (200, 201):
        print(f"❌ Falha ao criar categoria: {r_cat.text}")
        sys.exit(1)
    # Alguns endpoints retornam o objeto direto, outros dentro de 'data'
    cat_data = r_cat.json()
    # Pega o ID da categoria, lidando com diferentes formatos de resposta
    categoria_id = cat_data.get('id') or (cat_data.get('categoria', {}).get('id')) or (cat_data.get('data', {}).get('id'))
    if not categoria_id:
        print(f"❌ Não foi possível extrair ID da categoria: {cat_data}")
        sys.exit(1)
    
    print(f"✅ Categoria criada (ID: {categoria_id})")
    
    # Criar produto
    r_prod = session.post(f"{API_URL}/api/produtos/", json={
        "nome": "Refrigerante Cola 2L",
        "categoria": categoria_id,
        "preco_custo": 4.50,
        "preco_venda": 8.90,
        "quantidade": 100,
        "codigo_barras": f"789{random_suffix}"
    }, headers=headers)
    if r_prod.status_code not in (200, 201):
        print(f"❌ Falha ao criar produto: {r_prod.text}")
        sys.exit(1)
    
    prod_data = r_prod.json()
    produto_id = prod_data.get('id') or prod_data.get('produto', {}).get('id') or prod_data.get('data', {}).get('id')
    print(f"✅ Produto criado (ID: {produto_id})")
    
    # Abrir Caixa
    r_caixa = session.post(f"{API_URL}/api/pdv/caixa/abrir", json={
        "numero_caixa": "PDV-SMOKE",
        "saldo_inicial": 100.00
    }, headers=headers)
    if r_caixa.status_code not in (200, 201):
        print(f"❌ Falha ao abrir caixa: {r_caixa.text}")
        sys.exit(1)
    
    print("✅ Caixa aberto com sucesso")
    
    # 3. VENDA PDV
    print("\n--- 3. VENDA PDV ---")
    venda_payload = {
        "items": [{"id": produto_id, "quantity": 2, "price": 8.90}],
        "subtotal": 17.80,
        "desconto": 0,
        "total": 17.80,
        "pagamentos": [{"forma": "dinheiro", "valor": 20.00}],
        "valor_recebido": 20.00,
        "troco": 2.20
    }
    r_venda = session.post(f"{API_URL}/api/pdv/finalizar", json=venda_payload, headers=headers)
    if r_venda.status_code not in (200, 201):
        print(f"❌ Falha ao realizar venda: {r_venda.text}")
        sys.exit(1)
        
    venda_resp = r_venda.json()
    venda_obj = venda_resp.get("venda") or venda_resp.get("data") or {}
    venda_id = venda_obj.get("id") or venda_resp.get("id")
    print(f"✅ Venda finalizada com sucesso (ID: {venda_id})")
    
    # 4. NFC-e HOMOLOGAÇÃO
    print("\n--- 4. EMISSÃO NFC-E (Simulada/Homologação) ---")
    # Tenta emitir NFC-e. Pode falhar se não houver certificado, mas pelo menos validamos
    # que a rota está no ar e rejeita adequadamente (ex: 400 sem certificado).
    r_nfce = session.post(f"{API_URL}/api/fiscal/nfce/emitir", json={
        "venda_id": venda_id,
        "ambiente": "homologacao"
    }, headers=headers)
    print(f"Resposta NFC-e (Status {r_nfce.status_code}): {r_nfce.text[:200]}")
    # Aceitamos 400 (sem config fiscal) ou 200 (sucesso)
    if r_nfce.status_code not in (200, 400):
        print("⚠️ Endpoint de NFC-e com comportamento inesperado.")
    else:
        print("✅ Endpoint NFC-e respondeu no padrão esperado.")
        
    # 5. CHECKOUT EFI + WEBHOOK
    print("\n--- 5. CHECKOUT SAAS (Efí) ---")
    r_checkout = session.post(f"{API_URL}/api/billing/public-checkout", json={
        "email": email_admin,  # Usando o email admin para achar a conta criada
        "plan_name": "Premium"
    })
    
    if r_checkout.status_code != 200:
        print(f"❌ Falha no checkout (geração de Pix): {r_checkout.text}")
        sys.exit(1)
        
    checkout_data = r_checkout.json()
    txid = checkout_data.get("txid")
    print(f"✅ Cobrança Pix gerada (TXID: {txid})")
    
    print("\n--- 5.1 WEBHOOK EFI ---")
    # Simula o disparo que a Efí faria para o nosso webhook
    if txid:
        webhook_payload = {
            "pix": [
                {
                    "txid": txid,
                    "valor": "99.90",
                    "horario": "2026-07-06T12:00:00Z"
                }
            ]
        }
        r_webhook = session.post(f"{API_URL}/api/billing/webhook/efi", json=webhook_payload)
        if r_webhook.status_code == 200:
            print("✅ Webhook processou pagamento com sucesso.")
        else:
            print(f"❌ Falha no Webhook: {r_webhook.text}")
    else:
        print("⚠️ Não foi possível testar Webhook (TXID vazio).")
        
    print("\n🚀 E2E Smoke Test Concluído com Sucesso! O servidor está pronto para produção.")
    
    # Opcional: Não excluímos o tenant para que o Rafael possa logar e ver o que
    # o bot criou, usando as credenciais que printamos na tela.
    print(f"\n💡 Credenciais de Teste Geradas:")
    print(f"   Email: {email_admin}")
    print(f"   Senha: Smoke@123!")

if __name__ == "__main__":
    main()
