import sys
import importlib

# Forçar reload do módulo
if 'app.routes.produtos' in sys.modules:
    importlib.reload(sys.modules['app.routes.produtos'])
    print("✅ Módulo produtos recarregado")
else:
    print("⚠️ Módulo produtos não estava carregado")

from app import create_app
app = create_app()

print(f"\n📋 Rotas registradas em /api/produtos:")
with app.app_context():
    for rule in app.url_map.iter_rules():
        if '/produtos' in rule.rule:
            print(f"  {rule.methods} {rule.rule}")
