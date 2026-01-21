from app import create_app
from app.models import db, Funcionario
from sqlalchemy import inspect

app = create_app()
with app.app_context():
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    print('Tables in database:', tables)
    
    # Check if there are any funcionarios
    funcionarios = Funcionario.query.all()
    print(f'Number of funcionarios: {len(funcionarios)}')
    for f in funcionarios:
        print(f'  - {f.username}: {f.email}, ativo: {f.ativo}, status: {f.status}')