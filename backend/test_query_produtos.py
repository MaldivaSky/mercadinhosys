from app import create_app
from app.models import Produto, CategoriaProduto, db

app = create_app()

with app.app_context():
    try:
        estabelecimento_id = 1
        pagina = 1
        por_pagina = 10
        
        query = Produto.query.filter_by(estabelecimento_id=estabelecimento_id)
        paginacao = query.paginate(page=pagina, per_page=por_pagina, error_out=False)
        
        print(f"✅ Total de produtos: {paginacao.total}")
        print(f"✅ Produtos na página: {len(paginacao.items)}")
        
        if len(paginacao.items) > 0:
            produto = paginacao.items[0]
            print(f"\n📦 Produto exemplo:")
            print(f"   - ID: {produto.id}")
            print(f"   - Nome: {produto.nome}")
            print(f"   - Categoria ID: {produto.categoria_id}")
            print(f"   - Categoria objeto: {produto.categoria}")
            
            if produto.categoria:
                print(f"   - Categoria nome: {produto.categoria.nome}")
                print(f"   - ✅ Categoria OK!")
            else:
                print(f"   - ⚠️ Categoria é None!")
                
            # Testar conversão para dict
            produto_dict = {
                "id": produto.id,
                "nome": produto.nome,
                "categoria": produto.categoria.nome if produto.categoria else "Sem categoria",
                "preco_custo": float(produto.preco_custo),
                "preco_venda": float(produto.preco_venda),
                "quantidade": produto.quantidade,
            }
            print(f"\n✅ Conversão para dict OK:")
            print(f"   {produto_dict}")
                
    except Exception as e:
        print(f"❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
