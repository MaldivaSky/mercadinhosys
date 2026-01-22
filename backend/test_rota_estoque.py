from app import create_app
from app.models import Produto, db

app = create_app()

with app.app_context():
    total = Produto.query.filter_by(estabelecimento_id=1).count()
    print(f"✅ Total de produtos no banco: {total}")
    
    if total > 0:
        produto = Produto.query.filter_by(estabelecimento_id=1).first()
        print(f"✅ Exemplo de produto: {produto.nome}")
        print(f"   - Categoria: {produto.categoria}")
        print(f"   - Categoria ID: {produto.categoria_id}")
