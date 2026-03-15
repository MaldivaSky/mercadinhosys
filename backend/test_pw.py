from app import create_app
from app.models import db, Funcionario
from werkzeug.security import check_password_hash

app = create_app()
with app.app_context():
    f = Funcionario.query.filter_by(username='admin_elite').first()
    if f:
        pw = "adminElite123"
        print(f"User: {f.username}")
        print(f"Hash in DB: {f.senha}")
        is_ok = f.check_password(pw)
        print(f"f.check_password('{pw}'): {is_ok}")
        is_ok_direct = check_password_hash(f.senha, pw)
        print(f"check_password_hash(f.senha, '{pw}'): {is_ok_direct}")
    else:
        print("User admin_elite not found")
