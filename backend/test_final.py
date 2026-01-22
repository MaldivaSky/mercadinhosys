from app import create_app
from app.models import Produto

app = create_app()

with app.app_context():
    produto = Produto.query.filter_by(estabelecimento_id=1).first()
    
    print(f"Produto: {produto.nome}")
    print(f"Fornecedor: {produto.fornecedor}")
    
    if produto.fornecedor:
        print(f"Razão Social: {produto.fornecedor.razao_social}")
        print(f"Nome Fantasia: {produto.fornecedor.nome_fantasia}")
        fornecedor_nome = produto.fornecedor.razao_social or produto.fornecedor.nome_fantasia
        print(f"✅ Nome do fornecedor: {fornecedor_nome}")
    else:
        print("⚠️ Produto sem fornecedor")
