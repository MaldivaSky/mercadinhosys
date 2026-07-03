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

# 3) Seed só quando o banco estiver vazio (se já semeou com seed_cloud_light, pula)
echo "🌱 Checking if database needs seeding..."
NEEDS_SEED=$(python -c "from app import create_app, db; from app.models import Estabelecimento; app = create_app(); app.app_context().push(); print('yes' if Estabelecimento.query.count() == 0 else 'no')")

if [ "$NEEDS_SEED" = "yes" ]; then
    echo "🌱 Seeding database with initial data..."
    python seed_cloud_light.py || { echo "⚠️ Seed failed, continuing..."; true; }
else
    echo "✅ Database already has data, skipping seed"
fi

# Sincronização de schema removida (redundante com migrations)

# Iniciar servidor
# MEMÓRIA (Render Starter ~512MB): 1 worker em vez de 2 — a app é I/O-bound
# (queries ao Postgres), então +threads compensa a concorrência sem duplicar
# o interpretador Python inteiro (~200MB+ por worker com as libs carregadas).
# --max-requests recicla o worker periodicamente e devolve memória de qualquer
# vazamento lento; o jitter evita reciclagens sincronizadas em pico.
# --worker-tmp-dir /dev/shm evita heartbeat em disco (recomendação Render).
echo "🚀 Starting Gunicorn server..."
exec gunicorn run:app \
    --bind 0.0.0.0:$PORT \
    --workers 1 \
    --threads 8 \
    --max-requests 300 \
    --max-requests-jitter 60 \
    --worker-tmp-dir /dev/shm \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
