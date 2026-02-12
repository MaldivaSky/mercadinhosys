
import os
from dotenv import load_dotenv
from app import create_app, db
import sqlalchemy as sa

load_dotenv()
app = create_app(os.getenv('FLASK_ENV', 'development'))
with app.app_context():
    inspector = sa.inspect(db.engine)
    tables = inspector.get_table_names()
    print(f"Tabelas: {tables}")
    if 'produto_lotes' in tables:
        print("Tabela 'produto_lotes' existe.")
        columns = inspector.get_columns('produto_lotes')
        for col in columns:
            print(f"  Coluna: {col['name']} ({col['type']})")
    else:
        print("Tabela 'produto_lotes' NÃO existe!")
