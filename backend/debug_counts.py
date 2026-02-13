
from app import create_app
from app.models import Produto
from datetime import datetime, timedelta

app = create_app('development')
with app.app_context():
    hoje = datetime.utcnow().date()
    vencidos = Produto.query.filter(Produto.data_validade < hoje).count()
    vence_15 = Produto.query.filter(Produto.data_validade >= hoje, Produto.data_validade <= hoje + timedelta(days=15)).count()
    total = Produto.query.count()
    print(f"DEBUG_COUNTS: total={total}, vencidos={vencidos}, vence_15={vence_15}")
