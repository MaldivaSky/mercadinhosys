"""
Backfill único: alimenta o Catálogo Mestre com os produtos que JÁ existem nos
tenants (cadastrados antes da alimentação automática entrar em vigor).

Idempotente — usa a mesma lógica de dedupe por EAN de
catalogo_mestre_service.registrar_produto_se_novo, então rodar de novo não
duplica nada.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import Produto, Estabelecimento, CatalogoMestre
from app.services.catalogo_mestre_service import registrar_produto_se_novo

app = create_app()


def backfill():
    with app.app_context():
        produtos = Produto.query.filter(Produto.codigo_barras.isnot(None)).all()
        estabelecimentos = {e.id: e for e in Estabelecimento.query.all()}
        total_antes = CatalogoMestre.query.count()

        processados = 0
        for prod in produtos:
            est = estabelecimentos.get(prod.estabelecimento_id)
            registrar_produto_se_novo(prod, est, via="backfill")
            processados += 1
        db.session.commit()

        total_depois = CatalogoMestre.query.count()
        print(f"Produtos com EAN avaliados: {processados}")
        print(f"Catálogo Mestre: {total_antes} -> {total_depois} ({total_depois - total_antes} novo(s))")


if __name__ == '__main__':
    backfill()
