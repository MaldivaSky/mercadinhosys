
import os
import sys

# Adiciona o backend ao path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app import create_app, db

def check_app_db():
    app = create_app()
    with app.app_context():
        print(f"URL do Banco: {db.engine.url.render_as_string(hide_password=True)}")

if __name__ == "__main__":
    check_app_db()
