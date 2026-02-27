from app import create_app, db
from app.models import VendaItem, Produto

app = create_app()

with app.app_context():
    # Itens com margem ausente ou zero (que podem ter sido vendas recém-feitas)
    itens = VendaItem.query.filter((VendaItem.margem_lucro_real == None) | (VendaItem.margem_lucro_real == 0)).all()
    count = 0
    for item in itens:
        produto = Produto.query.get(item.produto_id)
        if produto and item.preco_unitario:
            custo = produto.preco_custo or 0
            item.margem_lucro_real = (float(item.preco_unitario) - float(custo)) * float(item.quantidade)
            count += 1
    
    db.session.commit()
    print(f"Atualizados {count} itens com margem de lucro real.")
