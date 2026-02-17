
import os
import sys

# Adiciona o backend ao path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app import create_app
from app.models import Produto

def deep_inspect_produto():
    app = create_app()
    with app.app_context():
        print("--- DEEP INSPECT PRODUTO ---")
        
        # 1. Atributos do dicionário da classe
        for key, value in Produto.__dict__.items():
            if 'preco' in key.lower():
                print(f"Key: {key}, Type: {type(value)}")
                
        # 2. Atributos via dir()
        attrs = dir(Produto)
        for a in attrs:
            if 'precocusto' == a.lower():
                print(f"!!! ENCONTRADO ATRIBUTO: {a} !!!")

if __name__ == "__main__":
    deep_inspect_produto()
