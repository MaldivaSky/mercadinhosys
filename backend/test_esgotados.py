from app import create_app, db
from app.models import Produto

app = create_app()

with app.app_context():
    # Contar produtos esgotados
    esgotados = Produto.query.filter_by(ativo=True).filter(Produto.quantidade == 0).count()
    print(f"Produtos esgotados (ativo=True, quantidade=0): {esgotados}")
    
    # Contar produtos com quantidade <= 0
    esgotados_ou_negativos = Produto.query.filter_by(ativo=True).filter(Produto.quantidade <= 0).count()
    print(f"Produtos com quantidade <= 0: {esgotados_ou_negativos}")
    
    # Listar alguns produtos esgotados
    produtos_esg = Produto.query.filter_by(ativo=True).filter(Produto.quantidade <= 0).limit(10).all()
    print(f"\nPrimeiros 10 produtos esgotados:")
    for p in produtos_esg:
        print(f"  - {p.nome}: quantidade={p.quantidade}")
    
    # Total de produtos ativos
    total = Produto.query.filter_by(ativo=True).count()
    print(f"\nTotal de produtos ativos: {total}")
