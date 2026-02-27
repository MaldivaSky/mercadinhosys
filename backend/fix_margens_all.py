import os
from app import create_app, db
from app.models import VendaItem, Produto

# Absolute path for SQLite
db_path = r"C:\Users\rafae\OneDrive\Desktop\mercadinhosys\backend\instance\mercadinho.db"
os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
os.environ["CLOUD_ENABLED"] = "false"

app = create_app()

with app.app_context():
    itens = VendaItem.query.all()
    count = 0
    from app.models import Venda
    print(f"Total de vendas banco (mercadinho.db): {Venda.query.count()}")
    for item in itens:
        produto = Produto.query.get(item.produto_id)
        if produto and item.preco_unitario:
            custo = float(produto.preco_custo or 0)
            if custo == 0:
                 custo = 0

            item.margem_lucro_real = (float(item.preco_unitario) - custo) * float(item.quantidade)
            count += 1
    
    db.session.commit()
    print(f"Forced recálculo de lucro no SQLite mercadinho.db. Atualizados {count} itens.")
