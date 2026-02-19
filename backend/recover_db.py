import os

# BANCO DE PRODUÇÃO lido da variável de ambiente (configurada no Render/Aiven dashboard)
# NUNCA coloque credenciais diretamente no código!
PROD_DB_URL = os.getenv("DATABASE_URL")

if not PROD_DB_URL:
    raise RuntimeError("DATABASE_URL não está definida. Configure no Render Dashboard.")

# Ajuste para SQLAlchemy (postgres -> postgresql)
if PROD_DB_URL.startswith("postgres://"):
    PROD_DB_URL = PROD_DB_URL.replace("postgres://", "postgresql://", 1)

# Forçar a aplicação a usar este banco
os.environ['DATABASE_URL'] = PROD_DB_URL
os.environ['FLASK_ENV'] = 'production'

from app import create_app, db
from sqlalchemy import text

print(f"🚀 Conectando ao banco de PRODUÇÃO...")
app = create_app()

with app.app_context():
    try:
        # Tenta criar as tabelas faltantes (estabelecimentos, leads, etc)
        print("🛠️ Verificando e criando tabelas faltantes...")
        db.create_all()
        print("✅ create_all() concluído.")

        # Verificação extra de colunas do Stripe
        with db.engine.connect() as conn:
            # Verificar se a tabela existe
            res = conn.execute(text("SELECT to_regclass('public.estabelecimentos');")).scalar()
            if res:
                print("✅ Tabela 'estabelecimentos' encontrada.")
                
                # Injetar colunas manualmente se o create_all ignorou tabela existente
                print("💉 Garantindo colunas do Stripe via SQL direto...")
                conn.execute(text("ALTER TABLE estabelecimentos ADD COLUMN IF NOT EXISTS stripe_customer_id VARCHAR(255);"))
                conn.execute(text("ALTER TABLE estabelecimentos ADD COLUMN IF NOT EXISTS stripe_subscription_id VARCHAR(255);"))
                conn.commit()
                print("✅ Colunas Stripe verificadas/adicionadas com sucesso.")
            else:
                print("❌ ERRO GRAVE: Tabela 'estabelecimentos' não foi criada.")

        print("\n🎉 SUCESSO: O banco de produção foi corrigido!")
        print("Aguarde 30s e tente acessar o sistema online novamente.")

    except Exception as e:
        print(f"\n❌ ERRO FATAL: {str(e)}")
