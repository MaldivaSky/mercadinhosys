
import os
from dotenv import load_dotenv
from app import create_app, db
from app.models import PedidoCompra, PedidoCompraItem, Produto, ProdutoLote
from sqlalchemy import func

load_dotenv()
app = create_app(os.getenv('FLASK_ENV', 'development'))
with app.app_context():
    pedidos = PedidoCompra.query.all()
    print(f"Total de pedidos de compra: {len(pedidos)}")
    for p in pedidos:
        print(f"ID: {p.id}, Numero: {p.numero_pedido}, Status: {p.status}, Fornecedor: {p.fornecedor.nome_fantasia if p.fornecedor else 'N/A'}")
        for item in p.itens:
            print(f"  Item: {item.produto_nome}, Solicitada: {item.quantidade_solicitada}, Recebida: {item.quantidade_recebida}, Status: {item.status}")
            produto = item.produto
            if produto:
                print(f"    Produto Estoque: {produto.quantidade}")
        
        lotes = ProdutoLote.query.filter_by(pedido_compra_id=p.id).all()
        print(f"  Lotes criados para este pedido: {len(lotes)}")
        for l in lotes:
            print(f"    Lote: {l.numero_lote}, Qtd: {l.quantidade}, Validade: {l.data_validade}")
    
    print("\nUltimos 10 Lotes no sistema:")
    lotes_gerais = ProdutoLote.query.order_by(ProdutoLote.id.desc()).limit(10).all()
    for l in lotes_gerais:
        print(f"ID: {l.id}, Produto: {l.produto_id}, Qtd: {l.quantidade}, Pedido: {l.pedido_compra_id}")
