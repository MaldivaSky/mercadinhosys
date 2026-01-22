from app import create_app
from app.models import Produto, CategoriaProduto, db

app = create_app()

with app.app_context():
    try:
        estabelecimento_id = 1
        busca = "coc"
        
        query = Produto.query.filter_by(estabelecimento_id=estabelecimento_id)
        
        busca_termo = f"%{busca}%"
        query = query.filter(
            db.or_(
                Produto.nome.ilike(busca_termo),
                Produto.codigo_barras.ilike(busca_termo),
                Produto.codigo_interno.ilike(busca_termo),
                Produto.descricao.ilike(busca_termo),
                Produto.marca.ilike(busca_termo),
            )
        )
        
        paginacao = query.paginate(page=1, per_page=50, error_out=False)
        
        print(f"✅ Busca por '{busca}': {paginacao.total} produtos encontrados")
        
        for produto in paginacao.items[:5]:
            print(f"  - {produto.nome}")
            print(f"    Categoria: {produto.categoria.nome if produto.categoria else 'None'}")
            print(f"    Preco: {float(produto.preco_venda)}")
            
    except Exception as e:
        print(f"❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
