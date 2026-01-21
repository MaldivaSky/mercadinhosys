# repair_migrations.py
import os
import shutil
import sys
from datetime import datetime


def repair_migrations():
    print("🔧 REPARANDO ESTRUTURA DE MIGRAÇÕES 🔧")
    print("=" * 60)

    # Verifica se a pasta migrations existe
    migrations_dir = "migrations"

    if os.path.exists(migrations_dir):
        print(f"📁 Pasta migrations encontrada em: {os.path.abspath(migrations_dir)}")

        # Lista conteúdo
        print("\n📋 Conteúdo atual:")
        for root, dirs, files in os.walk(migrations_dir):
            level = root.replace(migrations_dir, "").count(os.sep)
            indent = " " * 2 * level
            print(f"{indent}{os.path.basename(root)}/")
            subindent = " " * 2 * (level + 1)
            for file in files:
                print(f"{subindent}{file}")

    print("\n" + "=" * 60)
    print("OPÇÕES:")
    print("1. Recriar apenas o arquivo env.py faltante")
    print("2. Recriar toda a estrutura migrations")
    print("3. Verificar se o Flask-Migrate está configurado corretamente")

    choice = input("\nEscolha (1-3): ").strip()

    if choice == "1":
        recreate_env_py()
    elif choice == "2":
        recreate_full_structure()
    elif choice == "3":
        check_configuration()
    else:
        print("❌ Opção inválida")


def recreate_env_py():
    """Recria apenas o arquivo env.py"""
    print("\n🔄 Recriando env.py...")

    env_py_path = os.path.join("migrations", "env.py")

    # Conteúdo do env.py padrão para Flask-Migrate
    env_content = '''"""
Alembic environment configuration for Flask-Migrate
"""
import logging
from logging.config import fileConfig
from flask import current_app
from alembic import context
import sys
import os

# Adiciona o diretório do projeto ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuração do Alembic
config = context.config

# Configura logging
fileConfig(config.config_file_name)
logger = logging.getLogger('alembic.env')

# MetaData do SQLAlchemy
def get_metadata():
    from app import db
    return db.metadata

def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=get_metadata(),
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Run migrations in 'online' mode."""
    
    def process_revision_directives(context, revision, directives):
        if config.cmd_opts.autogenerate:
            script = directives[0]
            if script.upgrade_ops.is_empty():
                directives[:] = []

    connectable = current_app.extensions['migrate'].db.engine

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=get_metadata(),
            process_revision_directives=process_revision_directives,
            **current_app.extensions['migrate'].configure_args
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
'''

    # Cria o arquivo
    os.makedirs("migrations", exist_ok=True)
    with open(env_py_path, "w", encoding="utf-8") as f:
        f.write(env_content)

    print(f"✅ env.py criado em: {env_py_path}")

    # Cria também o __init__.py se não existir
    init_py_path = os.path.join("migrations", "__init__.py")
    if not os.path.exists(init_py_path):
        with open(init_py_path, "w", encoding="utf-8") as f:
            f.write("# Flask-Migrate migrations package\n")
        print(f"✅ __init__.py criado")

    print("\n🔍 Testando migrações...")
    os.system("flask db current")


def recreate_full_structure():
    """Recria toda a estrutura de migrações"""
    print("\n🔄 Recriando estrutura completa...")

    # Backup da pasta atual se existir
    if os.path.exists("migrations"):
        backup_name = f"migrations_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.move("migrations", backup_name)
        print(f"📦 Backup criado: {backup_name}")

    # Recria estrutura
    print("📁 Criando nova estrutura migrations...")
    os.system("flask db init")

    # Verifica
    if os.path.exists("migrations"):
        print("✅ Estrutura migrations criada com sucesso!")
        print("\n📋 Conteúdo criado:")
        for item in os.listdir("migrations"):
            print(f"  - {item}")
    else:
        print("❌ Falha ao criar migrations")

    # Gera migração inicial
    print("\n🔄 Gerando migração inicial...")
    os.system('flask db migrate -m "initial migration"')


def check_configuration():
    """Verifica configuração do Flask-Migrate"""
    print("\n🔍 Verificando configuração...")

    # Verifica se o Flask-Migrate está instalado
    try:
        import flask_migrate

        print(f"✅ Flask-Migrate instalado: {flask_migrate.__version__}")
    except ImportError:
        print("❌ Flask-Migrate não está instalado")
        print("Execute: pip install flask-migrate")
        return

    # Verifica se há um arquivo alembic.ini
    if os.path.exists("alembic.ini"):
        print("⚠️  Arquivo alembic.ini encontrado (pode causar conflito)")

    # Verifica a configuração do Flask
    print("\n📝 Verificando configuração do Flask...")

    # Testa importação
    try:
        from app import create_app, db

        app = create_app()
        with app.app_context():
            print(f"✅ Flask app criado com sucesso")
            print(
                f"✅ Database URI: {app.config.get('SQLALCHEMY_DATABASE_URI', 'Não configurado')}"
            )
            print(f"✅ Modelos carregados: {len(db.metadata.tables)} tabelas")
    except Exception as e:
        print(f"❌ Erro ao criar app: {e}")


if __name__ == "__main__":
    repair_migrations()
