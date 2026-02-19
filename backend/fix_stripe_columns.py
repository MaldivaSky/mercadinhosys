import psycopg2
import sys

# Configuração de conexão padrão do Docker exposto no localhost
DB_CONFIG = {
    "host": "localhost",
    "port": "5432",
    "dbname": "mercadinhosys",
    "user": "mercadinho_user",
    "password": "mercadinho_secure_pass_2024"
}

try:
    print("Conectando ao banco de dados...")
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True
    cur = conn.cursor()

    print("Adicionando colunas do Stripe...")
    
    # Adicionar stripe_customer_id
    cur.execute("ALTER TABLE estabelecimentos ADD COLUMN IF NOT EXISTS stripe_customer_id VARCHAR(255);")
    print("- stripe_customer_id: OK")

    # Adicionar stripe_subscription_id
    cur.execute("ALTER TABLE estabelecimentos ADD COLUMN IF NOT EXISTS stripe_subscription_id VARCHAR(255);")
    print("- stripe_subscription_id: OK")
    
    # Atualizar status para evitar Null
    cur.execute("UPDATE estabelecimentos SET stripe_customer_id = '' WHERE stripe_customer_id IS NULL;")
    
    print("\nSUCESSO: Banco de dados corrigido!")
    cur.close()
    conn.close()

except Exception as e:
    print(f"\nERRO CRÍTICO: {e}")
    sys.exit(1)
