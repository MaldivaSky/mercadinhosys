from app import create_app
from app.models import db, Funcionario
app = create_app()
with app.app_context():
    f = Funcionario.query.filter_by(username='admin_elite').first()
    if f:
        print(f"User found: {f.username}, ID: {f.id}, Role: {f.role}, Estab: {f.estabelecimento_id}")
    else:
        print("User admin_elite NOT FOUND")
        # List all usernames to see what we have
        all_usernames = [u.username for u in Funcionario.query.all()]
        print(f"Available usernames: {all_usernames}")
