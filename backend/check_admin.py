from app import create_app, db
from app.models import Funcionario

def check_admin():
    app = create_app()
    with app.app_context():
        admin = db.session.query(Funcionario).filter(Funcionario.username == 'admin').first()
        if admin:
            print(f"Admin found: ID={admin.id}, EstabId={admin.estabelecimento_id}, Nome={admin.nome}")
        else:
            print("Admin user not found.")

if __name__ == "__main__":
    check_admin()
