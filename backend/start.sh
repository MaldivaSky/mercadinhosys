#!/usr/bin/env bash
# Start script for Render.com
#
# IMPORTANTE: NÃO usar `set -o errexit`. Um erro transitório em QUALQUER passo
# de pré-boot (migração, create_all, checagem de seed) não pode derrubar o
# deploy inteiro — era isso que gerava "Exited with status 1 while running your
# code". O gunicorn precisa SEMPRE subir; a aplicação trata erros de banco por
# requisição.

echo "🚀 Starting MercadinhoSys Backend..."
export FLASK_APP=run:app

# 1) Migrações Alembic (best-effort, nunca fatal)
echo "📋 Applying database migrations (flask db upgrade)..."
python -m flask db upgrade || echo "⚠️ Migration falhou — seguindo (não fatal)."

# 2) Garantir tabelas (create_all não altera tabelas existentes) — best-effort
echo "📋 Ensuring database tables exist..."
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all(); print('✅ Tables OK')" \
    || echo "⚠️ create_all falhou — seguindo (não fatal)."

# 3) Seed só se o banco estiver vazio. Se a checagem falhar por qualquer motivo,
#    assume 'no' e segue (nunca derruba o boot).
echo "🌱 Checking if database needs seeding..."
NEEDS_SEED=$(python -c "from app import create_app, db; from app.models import Estabelecimento; app = create_app(); app.app_context().push(); print('yes' if Estabelecimento.query.count() == 0 else 'no')" 2>/dev/null || echo "no")

if [ "$NEEDS_SEED" = "yes" ]; then
    echo "🌱 Seeding database with initial data..."
    python seed_cloud_light.py || echo "⚠️ Seed falhou — seguindo."
else
    echo "✅ Banco já tem dados (ou checagem indisponível) — pulando seed."
fi

# 4) Servidor — SEMPRE executa.
# MEMÓRIA (Render Starter ~512MB): 1 worker + threads (app I/O-bound);
# --max-requests recicla o worker e devolve memória; /dev/shm evita heartbeat em disco.
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
