#!/usr/bin/env bash
# Start script for Render.com

set -o errexit  # Exit on error

echo "🚀 Starting MercadinhoSys Backend..."

# 1) Aplicar migrações Alembic no Postgres (obrigatório para colunas/tabelas novas)
export FLASK_APP=run:app
echo "📋 Applying database migrations (flask db upgrade)..."
python -m flask db upgrade || { echo "⚠️ Migration failed, continuing with create_all fallback..."; true; }

# 2) Garantir que todas as tabelas existam (create_all não altera tabelas já existentes)
echo "📋 Ensuring database tables exist..."
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all(); print('✅ Tables OK')"

# 3) Fallback: garantir colunas críticas que migrações podem ter pulado (ex: margem_lucro_real)
echo "📋 Checking critical columns..."
python -c "
from app import create_app, db
from sqlalchemy import text
app = create_app()
with app.app_context():
    try:
        db.session.execute(text('ALTER TABLE venda_itens ADD COLUMN IF NOT EXISTS margem_lucro_real NUMERIC(10,2)'))
        db.session.commit()
        print('✅ venda_itens.margem_lucro_real OK')
    except Exception as e:
        db.session.rollback()
        print('⚠️ Column check:', e)
"

# Verificar se precisa fazer seed
echo "🌱 Checking if database needs seeding..."
NEEDS_SEED=$(python -c "from app import create_app, db; from app.models import Estabelecimento; app = create_app(); app.app_context().push(); print('yes' if Estabelecimento.query.count() == 0 else 'no')")

if [ "$NEEDS_SEED" = "yes" ]; then
    echo "🌱 Seeding database with initial data..."
    python seed_cloud.py
else
    echo "✅ Database already has data, skipping seed"
fi

# Iniciar servidor
echo "🚀 Starting Gunicorn server..."
exec gunicorn run:app \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --threads 4 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
