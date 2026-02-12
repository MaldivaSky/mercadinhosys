
import os
from dotenv import load_dotenv
from app import create_app, db
from app.models import PedidoCompra, ProdutoLote

load_dotenv()
app = create_app(os.getenv('FLASK_ENV', 'development'))
with app.app_context():
    print(f"Pedidos: {PedidoCompra.query.count()}")
    print(f"Lotes: {ProdutoLote.query.count()}")
    
    ultimo_pedido = PedidoCompra.query.order_by(PedidoCompra.id.desc()).first()
    if ultimo_pedido:
        print(f"Ultimo Pedido: ID={ultimo_pedido.id}, Status={ultimo_pedido.status}")
        lotes = ProdutoLote.query.filter_by(pedido_compra_id=ultimo_pedido.id).all()
        print(f"Lotes do ultimo pedido: {len(lotes)}")
