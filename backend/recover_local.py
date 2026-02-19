import os
from sqlalchemy import text

# CONFIGURAÇÃO LOCAL (Docker)
LOCAL_DB_URL = "postgresql://mercadinho_user:mercadinho_secure_pass_2024@localhost:5432/mercadinhosys"

# Forçar o uso do banco local
os.environ['DATABASE_URL'] = LOCAL_DB_URL
os.environ['FLASK_ENV'] = 'development'

from app import create_app, db

print(f"🏠 Conectando ao banco LOCAL (Docker)...")
app = create_app()

with app.app_context():
    try:
        print("🛠️ Verificando e criando tabelas faltantes...")
        db.create_all()
        print("✅ create_all() concluído.")

        with db.engine.connect() as conn:
            # Injetar colunas manualmente
            print("💉 Garantindo colunas do Stripe via SQL...")
            conn.execute(text("ALTER TABLE estabelecimentos ADD COLUMN IF NOT EXISTS stripe_customer_id VARCHAR(255);"))
            conn.execute(text("ALTER TABLE estabelecimentos ADD COLUMN IF NOT EXISTS stripe_subscription_id VARCHAR(255);"))
            conn.commit()
            print("✅ Colunas Stripe verificadas/adicionadas com sucesso.")

        print("\n🎉 SUCESSO: O banco LOCAL foi corrigido!")

    except Exception as e:
        print(f"\n❌ ERRO FATAL: {str(e)}")
