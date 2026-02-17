"""
Sincronização de schema para Postgres em produção (Render).
Garante que colunas críticas existam mesmo quando migrações falham.
Executa ADD COLUMN IF NOT EXISTS para cada coluna necessária.
"""
import os
import sys

# Garantir que DATABASE_URL está configurado
db_url = os.environ.get("DATABASE_URL") or os.environ.get("AIVEN_DATABASE_URL") or os.environ.get("POSTGRES_URL")
if not db_url:
    print("⚠️ schema_sync: DATABASE_URL não definida, pulando sync")
    sys.exit(0)

# Se for SQLite, não precisa de sync
if "sqlite" in db_url.lower():
    print("✅ schema_sync: SQLite detectado, pulando sync")
    sys.exit(0)

# Converter postgres:// para postgresql://
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

def run_sync():
    from app import create_app, db
    from sqlalchemy import text
    
    app = create_app()
    with app.app_context():
        alteras = [
            # venda_itens
            "ALTER TABLE venda_itens ADD COLUMN IF NOT EXISTS margem_lucro_real NUMERIC(10,2)",
            # produtos - colunas que podem estar faltando
            "ALTER TABLE produtos ADD COLUMN IF NOT EXISTS margem_lucro NUMERIC(10,2)",
            "ALTER TABLE produtos ADD COLUMN IF NOT EXISTS tipo VARCHAR(50)",
            "ALTER TABLE produtos ADD COLUMN IF NOT EXISTS classificacao_abc VARCHAR(1)",
            "ALTER TABLE produtos ADD COLUMN IF NOT EXISTS total_vendido FLOAT DEFAULT 0",
            "ALTER TABLE produtos ADD COLUMN IF NOT EXISTS quantidade_vendida INTEGER DEFAULT 0",
            "ALTER TABLE produtos ADD COLUMN IF NOT EXISTS ultima_venda TIMESTAMP",
            "ALTER TABLE produtos ADD COLUMN IF NOT EXISTS fabricante VARCHAR(100)",
            # fornecedores
            "ALTER TABLE fornecedores ADD COLUMN IF NOT EXISTS valor_total_comprado NUMERIC(12,2) DEFAULT 0",
            "ALTER TABLE fornecedores ADD COLUMN IF NOT EXISTS total_compras INTEGER DEFAULT 0",
            "ALTER TABLE fornecedores ADD COLUMN IF NOT EXISTS classificacao VARCHAR(20) DEFAULT 'REGULAR'",
            "ALTER TABLE fornecedores ADD COLUMN IF NOT EXISTS prazo_entrega INTEGER DEFAULT 7",
        ]
        ok = 0
        for sql in alteras:
            try:
                db.session.execute(text(sql))
                db.session.commit()
                ok += 1
            except Exception as e:
                db.session.rollback()
                # Log mas não falhar - coluna pode já existir com tipo diferente
                print(f"⚠️ schema_sync: {sql[:60]}... -> {e}")
        print(f"✅ schema_sync: {ok}/{len(alteras)} colunas verificadas")

if __name__ == "__main__":
    try:
        run_sync()
    except Exception as e:
        print(f"❌ schema_sync falhou: {e}")
        sys.exit(1)
