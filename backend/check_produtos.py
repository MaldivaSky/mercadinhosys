from app import create_app
from app.dashboard_cientifico.data_layer import DataLayer

app = create_app()

with app.app_context():
    # Testar get_top_products
    top_products = DataLayer.get_top_products(1, 30, 10)
    print(f'Total de produtos retornados: {len(top_products)}')
    print('Top produtos:')
    for i, produto in enumerate(top_products, 1):
        print(f'{i}. {produto["nome"]} - Qtd: {produto["quantidade_vendida"]}, Faturamento: R$ {produto["faturamento"]:.2f}')

    # Testar se há vendas com itens
    from app.models import Venda, ItemVenda
    vendas_com_itens = db.session.query(Venda).join(ItemVenda).filter(Venda.estabelecimento_id == 1).count()
    print(f'\nVendas com itens: {vendas_com_itens}')

    # Verificar se há produtos
    from app.models import Produto
    total_produtos = Produto.query.filter_by(estabelecimento_id=1).count()
    print(f'Total de produtos no estabelecimento: {total_produtos}')