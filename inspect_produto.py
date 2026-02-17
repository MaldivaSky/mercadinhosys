
import os
import sys

# Adiciona o backend ao path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app import create_app
from app.models import Produto
from sqlalchemy import inspect as sqla_inspect

def inspect_produto_class():
    app = create_app()
    with app.app_context():
        print(f"--- INSPEÇÃO DA CLASSE PRODUTO ---")
        
        # 1. Atributos da classe (incluindo @property e métodos)
        attrs = dir(Produto)
        print(f"Total de atributos: {len(attrs)}")
        
        preco_attrs = [a for a in attrs if 'preco' in a.lower()]
        print(f"Atributos com 'preco': {preco_attrs}")
        
        if 'precocusto' in attrs:
            print("!!! ACHOU 'precocusto' na classe !!!")
        else:
            print("Não achou 'precocusto' literal na classe.")

        # 2. Inspecionar colunas do banco via SQLAlchemy
        mapper = sqla_inspect(Produto)
        print("\n--- COLUNAS MAPEADAS PELO SQLALCHEMY ---")
        for column in mapper.attrs:
            if hasattr(column, 'key'):
                col_name = column.key
                if 'preco' in col_name.lower():
                    print(f"Coluna: {col_name}")
                if col_name == 'precocusto':
                    print("!!! ACHOU COLUNA 'precocusto' !!!")

        # 3. Verificar se há algum mixin ou base class que possa estar injetando isso
        print("\n--- CLASSES BASE ---")
        for base in Produto.__mro__:
            print(f"Base: {base}")

if __name__ == "__main__":
    inspect_produto_class()
