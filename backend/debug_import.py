
import sys
import os
import logging

# Add backend directory to path
sys.path.append(os.getcwd())

logging.basicConfig(level=logging.INFO)

def check_import():
    print("--- Verificando Import de PracticalModels ---")
    try:
        from app.dashboard_cientifico.models_layer import PracticalModels
        print("Import de PracticalModels: SUCESSO")
    except Exception as e:
        print(f"ERRO DE IMPORT: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_import()
