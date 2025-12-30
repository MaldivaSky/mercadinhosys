# recreate_db.py
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import (
    Produto,
    Funcionario,
    Cliente,
    Venda,
    VendaItem,
    Categoria,
    MovimentacaoEstoque,
)

print("🔄 Recriando banco de dados do zero...")

app = create_app()

with app.app_context():
    # 1. DROP todas as tabelas (cuidado!)
    print("🗑️  Removendo tabelas antigas...")
    db.drop_all()

    # 2. CREATE todas as tabelas novas
    print("🏗️  Criando novas tabelas...")
    db.create_all()

    # 3. Criar funcionário admin
    print("👤 Criando funcionário admin...")
    admin = Funcionario(
        nome="Administrador",
        cpf="000.000.000-00",
        usuario="admin",
        cargo="Gerente",
        nivel_acesso="admin",
        ativo=True,
    )
    admin.set_senha("admin123")
    admin.set_pin("1234")
    db.session.add(admin)

    # 4. Criar algumas categorias básicas
    print("🏷️  Criando categorias...")
    categorias = [
        Categoria(nome="Alimentos", descricao="Produtos alimentícios", cor="#2ecc71"),
        Categoria(nome="Bebidas", descricao="Bebidas em geral", cor="#3498db"),
        Categoria(nome="Limpeza", descricao="Produtos de limpeza", cor="#9b59b6"),
        Categoria(nome="Padaria", descricao="Pães e bolos", cor="#e67e22"),
        Categoria(nome="Hortifruti", descricao="Frutas e verduras", cor="#27ae60"),
        Categoria(nome="Carnes", descricao="Açougue", cor="#e74c3c"),
        Categoria(nome="Laticínios", descricao="Leite, queijo, iogurte", cor="#f1c40f"),
    ]

    for cat in categorias:
        db.session.add(cat)
    
    db.session.flush()  # Precisamos fazer flush para gerar os IDs das categorias

    # 5. Criar alguns produtos de exemplo
    print("📦 Criando produtos de exemplo...")
    
    # Obter as categorias por nome
    cat_alimentos = Categoria.query.filter_by(nome="Alimentos").first()
    cat_bebidas = Categoria.query.filter_by(nome="Bebidas").first()
    cat_hortifruti = Categoria.query.filter_by(nome="Hortifruti").first()
    cat_laticinios = Categoria.query.filter_by(nome="Laticínios").first()
    
    produtos = [
        Produto(
            nome="Arroz Branco 5kg",
            codigo_barras="7891000315507",
            descricao="Arroz tipo 1",
            preco_custo=15.00,
            preco_venda=24.90,
            margem_lucro=66.0,
            quantidade=50,
            quantidade_minima=10,
            categoria_id=cat_alimentos.id,
            marca="Tio João",
            tipo="unidade",
            unidade_medida="un",
            ativo=True,
        ),
        Produto(
            nome="Feijão Carioca 1kg",
            codigo_barras="7891000055502",
            descricao="Feijão tipo carioca",
            preco_custo=4.50,
            preco_venda=8.90,
            margem_lucro=97.8,
            quantidade=100,
            quantidade_minima=20,
            categoria_id=cat_alimentos.id,
            marca="Camil",
            tipo="unidade",
            unidade_medida="un",
            ativo=True,
        ),
        Produto(
            nome="Coca-Cola 2L",
            codigo_barras="7894900010015",
            descricao="Refrigerante Coca-Cola",
            preco_custo=4.00,
            preco_venda=9.90,
            margem_lucro=147.5,
            quantidade=75,
            quantidade_minima=15,
            categoria_id=cat_bebidas.id,
            marca="Coca-Cola",
            tipo="unidade",
            unidade_medida="un",
            ativo=True,
        ),
        Produto(
            nome="Banana",
            descricao="Banana nanica",
            preco_custo=1.50,
            preco_venda=3.90,
            margem_lucro=160.0,
            quantidade=150,
            quantidade_minima=30,
            categoria_id=cat_hortifruti.id,
            marca="",
            tipo="granel",
            unidade_medida="kg",
            ativo=True,
        ),
        Produto(
            nome="Queijo Mussarela",
            codigo_barras="7891000255555",
            descricao="Queijo mussarela fatiado",
            preco_custo=25.00,
            preco_venda=42.90,
            margem_lucro=71.6,
            quantidade=25,
            quantidade_minima=5,
            categoria_id=cat_laticinios.id,
            marca="Itambé",
            tipo="granel",
            unidade_medida="kg",
            ativo=True,
        ),
    ]

    for prod in produtos:
        db.session.add(prod)

    # 6. Salvar tudo
    db.session.commit()

    print("✅ Banco de dados recriado com sucesso!")
    print("")
    print("📋 RESUMO:")
    print(f"   👤 Funcionários: 1 (admin:admin123)")
    print(f"   🏷️  Categorias: {len(categorias)}")
    print(f"   📦 Produtos: {len(produtos)}")
    print("")
    print("🔑 Credenciais para login:")
    print("   Usuário: admin")
    print("   Senha: admin123")
    print("   PIN PDV: 1234")
