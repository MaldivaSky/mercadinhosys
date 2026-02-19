
import sys
import os
import logging
from flask import Flask

# Add backend directory to path
sys.path.append(os.getcwd())

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_startup():
    print("--- Verificando Inicialização do App ---")
    try:
        from app import create_app
        print("Import de create_app: SUCESSO")
        
        app = create_app()
        print("Criação do App: SUCESSO")
        
        print("Verificando Blueprints registrados:")
        for rule in app.url_map.iter_rules():
            if 'cientifico' in str(rule):
                print(f"  Rota Encontrada: {rule}")
                
    except Exception as e:
        print(f"ERRO CRÍTICO NA INICIALIZAÇÃO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_startup()
