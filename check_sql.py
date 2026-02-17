
import os
import sys

# Adiciona o backend ao path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app import create_app, db
from app.models import Produto

def check_sql_generation():
    app = create_app()
    with app.app_context():
        query = Produto.query
        print(f"SQL Gerado: {query}")

if __name__ == "__main__":
    check_sql_generation()
