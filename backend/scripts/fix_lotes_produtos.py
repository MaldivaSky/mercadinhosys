import os
import sys

# Corrige imports do backend
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import Produto, ProdutoLote

app = create_app()

def fix_produtos_lotes():
    with app.app_context():
        produtos = Produto.query.all()
        atualizados = 0
        
        for prod in produtos:
            # Buscar o lote mais proximo do vencimento
            lote_principal = ProdutoLote.query.filter_by(produto_id=prod.id, ativo=True).order_by(ProdutoLote.data_validade.asc()).first()
            if lote_principal and not prod.lote:
                prod.lote = lote_principal.numero_lote
                prod.data_validade = lote_principal.data_validade
                prod.data_fabricacao = lote_principal.data_fabricacao
                prod.controlar_validade = True
                atualizados += 1
                
        db.session.commit()
        print(f"✅ CONSERTADO! {atualizados} produtos locais tiveram seus lotes e validades corrigidos.")

if __name__ == '__main__':
    fix_produtos_lotes()
