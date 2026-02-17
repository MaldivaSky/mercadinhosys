import os
import sys
import traceback

# Adicionar o diretório backend ao sys.path
backend_dir = os.path.abspath(os.path.join(os.getcwd(), "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Configurar variáveis mínimas para evitar crashes de falta de env
os.environ["SECRET_KEY"] = "test"
os.environ["JWT_SECRET_KEY"] = "test"
os.environ["FLASK_ENV"] = "development"
# Usar SQLite para teste rápido de inicialização
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

try:
    print("🚀 Tentando importar create_app...")
    from app import create_app
    print("✅ create_app importado com sucesso.")
    
    print("🛠️ Tentando criar a app...")
    app = create_app("development")
    print("✅ App criada com sucesso.")
    
    print("🔍 Testando registro de blueprints...")
    for blueprint in app.blueprints:
        print(f"  - {blueprint}")
        
    print("✅ Inicialização completa sem erros.")
except Exception as e:
    print(f"❌ Erro durante a inicialização: {e}")
    traceback.print_exc()
