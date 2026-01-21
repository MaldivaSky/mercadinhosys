from app import create_app, db
from app.models import Funcionario

app = create_app()

with app.app_context():
    funcionarios = Funcionario.query.all()
    print("\n=== FUNCIONÁRIOS CADASTRADOS ===")
    for f in funcionarios:
        print(f"ID: {f.id} | username: {f.username} | email: {f.email} | ativo: {f.ativo} | estabelecimento_id: {f.estabelecimento_id}")
    print("===============================\n")
