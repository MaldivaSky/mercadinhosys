import sys
sys.path.append('.')
from app import create_app, db
from app.models import Estabelecimento, Funcionario

app = create_app()
with app.app_context():
    estabelecimento = Estabelecimento.query.first()
    print('Estabelecimento:', estabelecimento.id if estabelecimento else 'None')
    admin = Funcionario.query.filter_by(username='admin').first()
    print('Admin estabelecimento_id:', admin.estabelecimento_id if admin else 'None')
    if admin and estabelecimento and admin.estabelecimento_id is None:
        admin.estabelecimento_id = estabelecimento.id
        db.session.commit()
        print('Corrigido')
    else:
        print('Não precisa corrigir')