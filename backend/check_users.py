from app import create_app
from app.models import db, Funcionario, Estabelecimento
app = create_app()
with app.app_context():
    funcs = Funcionario.query.all()
    ests = Estabelecimento.query.all()
    print(f"Total Funcionarios: {len(funcs)}")
    for f in funcs:
        print(f" - {f.username} (ID: {f.id}, Role: {f.role}, Estab: {f.estabelecimento_id})")
    print(f"Total Estabelecimentos: {len(ests)}")
    for e in ests:
        print(f" - {e.nome_fantasia} (ID: {e.id})")
