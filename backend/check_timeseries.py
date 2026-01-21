from app import create_app
from app.dashboard_cientifico.data_layer import DataLayer

app = create_app()

with app.app_context():
    # Testar get_sales_timeseries
    timeseries = DataLayer.get_sales_timeseries(1, 30)  # estabelecimento_id=1, últimos 30 dias
    print(f'Total de dias com vendas: {len(timeseries)}')
    print('Primeiros 5 dias:')
    for dia in timeseries[:5]:
        print(f'Data: {dia["data"]}, Total: {dia["total"]}, Quantidade: {dia["quantidade"]}')

    print('\nÚltimos 5 dias:')
    for dia in timeseries[-5:]:
        print(f'Data: {dia["data"]}, Total: {dia["total"]}, Quantidade: {dia["quantidade"]}')

    # Verificar se há dados vazios
    vazios = [dia for dia in timeseries if dia["total"] == 0]
    print(f'\nDias com vendas zeradas: {len(vazios)}')