from app import create_app
from app.models import db, Funcionario

app = create_app('development')
with app.app_context():
    users = Funcionario.query.all()
    print(f'Total usuarios: {len(users)}')
    for u in users[:5]:
        print(f'ID: {u.id}, Nome: {u.nome}, Email: {u.email}, Estabelecimento: {u.estabelecimento_id}')
