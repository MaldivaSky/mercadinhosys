from app import create_app
from app.models import Funcionario

app = create_app()

with app.app_context():
    users = Funcionario.query.all()
    print(f"Total de usuários: {len(users)}")
    for user in users[:5]:
        print(f"  - Username: {user.username}, Nome: {user.nome}, Role: {user.role}")
