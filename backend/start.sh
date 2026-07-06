#!/usr/bin/env bash
# Start script for Render.com
#
# IMPORTANTE: NÃO usar `set -o errexit`. Um erro transitório de
# seed não deve derrubar o deploy, mas a migração de banco (db upgrade)
# agora é fatal para evitar schema drift no banco de produção.

echo "🚀 Starting MercadinhoSys Backend..."
export FLASK_APP=run:app

# 1) Migrações Alembic (fatal no deploy, para evitar schema drift)
echo "📋 Applying database migrations (flask db upgrade)..."
python -m flask db upgrade

# 2) NÃO chamamos db.create_all() aqui de propósito: create_app() (chamada por
# qualquer import de run:app, inclusive o próprio `flask db upgrade` acima) já
# decide sozinha se precisa rodar create_all() — só roda em banco vazio (sem
# alembic_version ainda). Chamar de novo aqui era 100% redundante e, pior,
# escondia o caso em que uma migração cria uma tabela ANTES do create_all()
# rodar: create_all() adiantava a criação da tabela a partir do models.py atual,
# e quando a migração correspondente rodava (aqui ou num deploy seguinte) o
# CREATE TABLE dela colidia (DuplicateTable), travando o alembic_version e
# impedindo todas as migrações seguintes de sempre aplicarem. Ver app/__init__.py
# (bootstrap gateado por alembic_version) para o detalhe da correção.

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
