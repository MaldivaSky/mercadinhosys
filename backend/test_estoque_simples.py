from app import create_app
from app.models import Produto, CategoriaProduto, db
from flask_jwt_extended import create_access_token

app = create_app()

with app.app_context():
    # Criar token manualmente
    token = create_access_token(
        identity=1,
        additional_claims={"estabelecimento_id": 1, "role": "ADMIN"}
    )
    
    print(f"✅ Token criado")
    
    # Testar a lógica da rota diretamente
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
            else:
                print(f"   - ⚠️ Categoria é None!")
                
    except Exception as e:
        print(f"❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
