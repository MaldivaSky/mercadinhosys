from app import create_app, db
from app.models import Venda

app = create_app()

with app.app_context():
    print('Total de vendas:', Venda.query.count())
    vendas = Venda.query.limit(5).all()
    print('Primeiras 5 vendas:')
    for v in vendas:
        print(f'Data: {v.data_venda}, Total: {v.total}, Status: {v.status}')

    # Verificar vendas dos últimos 30 dias
    from datetime import datetime, timedelta
    data_inicio = datetime.now() - timedelta(days=30)
    vendas_recentes = Venda.query.filter(
        Venda.data_venda >= data_inicio,
        Venda.status == 'finalizada'
    ).count()
    print(f'Vendas finalizadas nos últimos 30 dias: {vendas_recentes}')