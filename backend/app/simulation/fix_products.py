import os
import sys
from decimal import Decimal

# Add the parent directory to sys.path so we can import 'app'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app import create_app, db
from app.models import Produto, VendaItem, Venda, CategoriaProduto
from sqlalchemy import func
import datetime

def fix_all_products():
    app = create_app()
    with app.app_context():
        produtos = Produto.query.all()
        print(f"Fixing {len(produtos)} produtos...")

        default_cat = CategoriaProduto.query.first()
        if not default_cat:
            default_cat = CategoriaProduto(nome="Geral", estabelecimento_id=1)
            db.session.add(default_cat)
            db.session.commit()

        for p in produtos:
            # Fix ativo
            if p.ativo is None or p.ativo is False:
                p.ativo = True

            # Fix categoria
            if p.categoria_id is None:
                p.categoria_id = default_cat.id

            # Fix Margem and Preco
            if not p.preco_venda or p.preco_venda <= 0:
                p.preco_venda = Decimal('10.00')
            if not p.preco_custo or p.preco_custo <= 0:
                p.preco_custo = p.preco_venda * Decimal('0.6') # 40% margin
            
            p.margem_lucro = ((p.preco_venda - p.preco_custo) / p.preco_custo) * 100

            # Calculate total_vendido and quantidade_vendida
            vendas = db.session.query(
                func.sum(VendaItem.total_item).label('total'),
                func.sum(VendaItem.quantidade).label('qtd'),
                func.max(Venda.data_venda).label('ultima')
            ).join(Venda, Venda.id == VendaItem.venda_id).filter(VendaItem.produto_id == p.id).first()

            if vendas and vendas.qtd:
                p.total_vendido = Decimal(str(vendas.total or 0))
                p.quantidade_vendida = int(vendas.qtd or 0)
                p.ultima_venda = vendas.ultima
            else:
                p.total_vendido = Decimal('0')
                p.quantidade_vendida = 0
                p.ultima_venda = None

        db.session.commit()
        
        # Now update ABC classifications
        # Get faturamento for each product
        produtos = Produto.query.order_by(Produto.total_vendido.desc()).all()
        faturamento_total = sum(p.total_vendido for p in produtos if p.total_vendido)
        
        acumulado = Decimal('0')
        for p in produtos:
            if not faturamento_total or faturamento_total == 0:
                p.classificacao_abc = 'C'
            else:
                fat = p.total_vendido or Decimal('0')
                acumulado += fat
                percentual = acumulado / faturamento_total
                if percentual <= Decimal('0.80'):
                    p.classificacao_abc = 'A'
                elif percentual <= Decimal('0.95'):
                    p.classificacao_abc = 'B'
                else:
                    p.classificacao_abc = 'C'
        
        db.session.commit()
        print("Done fixing products!")

if __name__ == '__main__':
    fix_all_products()
