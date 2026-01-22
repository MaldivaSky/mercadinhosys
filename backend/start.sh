#!/usr/bin/env bash
# Start script for Render.com

set -o errexit  # Exit on error

echo "🚀 Starting MercadinhoSys Backend..."

# Criar tabelas se não existirem
echo "📋 Creating database tables..."
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all(); print('✅ Tables created')"

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
