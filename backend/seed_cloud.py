"""
Seed Script Inteligente - Funciona em Local e Nuvem
Detecta automaticamente o ambiente e popula o banco de dados
"""
import os
import sys
from datetime import datetime, timedelta
from decimal import Decimal

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import (
    Estabelecimento,
    Funcionario,
    Cliente,
    Fornecedor,
    Categoria,
    Produto,
    Venda,
    VendaItem,
)
from werkzeug.security import generate_password_hash


def detect_environment():
    """Detecta se está rodando em local ou nuvem"""
    if os.environ.get("RENDER"):
        return "RENDER"
    elif os.environ.get("RAILWAY"):
        return "RAILWAY"
    elif os.environ.get("HEROKU"):
        return "HEROKU"
    elif os.environ.get("DATABASE_URL") and "neon" in os.environ.get("DATABASE_URL", ""):
        return "NEON"
    else:
        return "LOCAL"


def seed_database():
    """Popula o banco de dados com dados de teste"""
    
    env = detect_environment()
    print(f"\n{'='*60}")
    print(f"🌱 SEED DATABASE - Ambiente: {env}")
    print(f"{'='*60}\n")
    
    app = create_app()
    
    with app.app_context():
        # Verificar conexão com o banco
        try:
            db.engine.connect()
            print("✅ Conexão com banco de dados OK")
            print(f"📊 Database: {db.engine.url.database}")
            print(f"🔗 Host: {db.engine.url.host or 'local'}\n")
        except Exception as e:
            print(f"❌ Erro ao conectar no banco: {e}")
            return False
        
        # Criar todas as tabelas
        print("📋 Criando tabelas...")
        db.create_all()
        print("✅ Tabelas criadas\n")
        
        # Verificar se já existe dados
        if Estabelecimento.query.first():
            print("⚠️  Banco já possui dados!")
            resposta = input("Deseja limpar e recriar? (s/N): ").lower()
            if resposta != 's':
                print("❌ Seed cancelado")
                return False
            
            print("🗑️  Limpando dados existentes...")
            db.drop_all()
            db.create_all()
            print("✅ Dados limpos\n")
        
        # 1. ESTABELECIMENTO
        print("🏢 Criando estabelecimento...")
        estabelecimento = Estabelecimento(
            nome="Mercado Souza Center",
            cnpj="12.345.678/0001-90",
            telefone="(84) 3234-5678",
            email="contato@mercadosouza.com.br",
            endereco="Rua Principal, 123",
            cidade="Natal",
            estado="RN",
            cep="59000-000",
        )
        db.session.add(estabelecimento)
        db.session.flush()
        print(f"✅ Estabelecimento criado: {estabelecimento.nome}\n")
        
        # 2. FUNCIONÁRIOS
        print("👥 Criando funcionários...")
        funcionarios = [
            {
                "nome": "Administrador Sistema",
                "username": "admin",
                "password": "admin123",
                "email": "admin@empresa.com",
                "cpf": "156.987.243-00",
                "telefone": "84 1791-7604",
                "cargo": "Gerente",
                "role": "ADMIN",
                "status": "ativo",
                "permissoes": {
                    "pdv": True,
                    "estoque": True,
                    "compras": True,
                    "financeiro": True,
                    "relatorios": True,
                    "configuracoes": True,
                },
            },
            {
                "nome": "João Silva",
                "username": "joao",
                "password": "joao123",
                "email": "joao@empresa.com",
                "cpf": "123.456.789-00",
                "telefone": "(84) 98765-4321",
                "cargo": "Vendedor",
                "role": "VENDEDOR",
                "status": "ativo",
                "permissoes": {"pdv": True, "estoque": False},
            },
        ]
        
        for func_data in funcionarios:
            func = Funcionario(
                estabelecimento_id=estabelecimento.id,
                nome=func_data["nome"],
                username=func_data["username"],
                senha_hash=generate_password_hash(func_data["password"]),
                email=func_data["email"],
                cpf=func_data["cpf"],
                telefone=func_data["telefone"],
                cargo=func_data["cargo"],
                role=func_data["role"],
                status=func_data["status"],
                data_admissao=datetime.now().date(),
                permissoes=func_data["permissoes"],
            )
            db.session.add(func)
            print(f"  ✅ {func.nome} ({func.role})")
        
        db.session.flush()
        print()
        
        # 3. CLIENTES
        print("🛒 Criando clientes...")
        clientes_data = [
            {"nome": "Maria Santos", "cpf": "111.222.333-44", "telefone": "(84) 91234-5678"},
            {"nome": "Pedro Oliveira", "cpf": "222.333.444-55", "telefone": "(84) 92345-6789"},
            {"nome": "Ana Costa", "cpf": "333.444.555-66", "telefone": "(84) 93456-7890"},
        ]
        
        for cliente_data in clientes_data:
            cliente = Cliente(
                estabelecimento_id=estabelecimento.id,
                nome=cliente_data["nome"],
                cpf=cliente_data["cpf"],
                telefone=cliente_data["telefone"],
                email=f"{cliente_data['nome'].split()[0].lower()}@email.com",
            )
            db.session.add(cliente)
            print(f"  ✅ {cliente.nome}")
        
        db.session.flush()
        print()
        
        # 4. FORNECEDORES
        print("🚚 Criando fornecedores...")
        fornecedores_data = [
            {
                "nome_fantasia": "Distribuidora ABC",
                "razao_social": "ABC Distribuidora LTDA",
                "cnpj": "11.222.333/0001-44",
                "telefone": "(84) 3111-2222",
                "email": "contato@abc.com",
                "cidade": "Natal",
                "estado": "RN",
            },
            {
                "nome_fantasia": "Atacado XYZ",
                "razao_social": "XYZ Atacado LTDA",
                "cnpj": "22.333.444/0001-55",
                "telefone": "(84) 3222-3333",
                "email": "vendas@xyz.com",
                "cidade": "Parnamirim",
                "estado": "RN",
            },
        ]
        
        fornecedores = []
        for forn_data in fornecedores_data:
            fornecedor = Fornecedor(
                estabelecimento_id=estabelecimento.id,
                nome_fantasia=forn_data["nome_fantasia"],
                razao_social=forn_data["razao_social"],
                cnpj=forn_data["cnpj"],
                telefone=forn_data["telefone"],
                email=forn_data["email"],
                cidade=forn_data["cidade"],
                estado=forn_data["estado"],
                cep="59000-000",
                logradouro="Rua Comercial",
                numero="100",
                bairro="Centro",
                ativo=True,
            )
            db.session.add(fornecedor)
            fornecedores.append(fornecedor)
            print(f"  ✅ {fornecedor.nome_fantasia}")
        
        db.session.flush()
        print()
        
        # 5. CATEGORIAS
        print("📁 Criando categorias...")
        categorias_data = [
            "Alimentos",
            "Bebidas",
            "Limpeza",
            "Higiene",
            "Padaria",
        ]
        
        categorias = []
        for cat_nome in categorias_data:
            categoria = Categoria(
                estabelecimento_id=estabelecimento.id,
                nome=cat_nome,
                descricao=f"Produtos de {cat_nome.lower()}",
            )
            db.session.add(categoria)
            categorias.append(categoria)
            print(f"  ✅ {categoria.nome}")
        
        db.session.flush()
        print()
        
        # 6. PRODUTOS
        print("📦 Criando produtos...")
        produtos_data = [
            {"nome": "Arroz Tipo 1 5kg", "categoria": 0, "fornecedor": 0, "preco_custo": 15.00, "preco_venda": 22.90, "quantidade": 50, "codigo": "7891234567890"},
            {"nome": "Feijão Preto 1kg", "categoria": 0, "fornecedor": 0, "preco_custo": 5.50, "preco_venda": 8.90, "quantidade": 80, "codigo": "7891234567891"},
            {"nome": "Açúcar Cristal 1kg", "categoria": 0, "fornecedor": 0, "preco_custo": 3.20, "preco_venda": 4.99, "quantidade": 100, "codigo": "7891234567892"},
            {"nome": "Refrigerante Cola 2L", "categoria": 1, "fornecedor": 1, "preco_custo": 4.50, "preco_venda": 7.99, "quantidade": 60, "codigo": "7891234567893"},
            {"nome": "Água Mineral 1.5L", "categoria": 1, "fornecedor": 1, "preco_custo": 1.20, "preco_venda": 2.50, "quantidade": 120, "codigo": "7891234567894"},
            {"nome": "Detergente Líquido", "categoria": 2, "fornecedor": 0, "preco_custo": 1.80, "preco_venda": 2.99, "quantidade": 90, "codigo": "7891234567895"},
            {"nome": "Sabão em Pó 1kg", "categoria": 2, "fornecedor": 0, "preco_custo": 8.50, "preco_venda": 12.90, "quantidade": 40, "codigo": "7891234567896"},
            {"nome": "Shampoo 400ml", "categoria": 3, "fornecedor": 1, "preco_custo": 6.00, "preco_venda": 9.99, "quantidade": 35, "codigo": "7891234567897"},
            {"nome": "Sabonete 90g", "categoria": 3, "fornecedor": 1, "preco_custo": 1.50, "preco_venda": 2.49, "quantidade": 150, "codigo": "7891234567898"},
            {"nome": "Pão Francês kg", "categoria": 4, "fornecedor": 0, "preco_custo": 8.00, "preco_venda": 12.00, "quantidade": 20, "codigo": "7891234567899"},
        ]
        
        produtos = []
        for prod_data in produtos_data:
            produto = Produto(
                estabelecimento_id=estabelecimento.id,
                nome=prod_data["nome"],
                codigo_barras=prod_data["codigo"],
                categoria_id=categorias[prod_data["categoria"]].id,
                fornecedor_id=fornecedores[prod_data["fornecedor"]].id,
                preco_custo=Decimal(str(prod_data["preco_custo"])),
                preco_venda=Decimal(str(prod_data["preco_venda"])),
                quantidade=prod_data["quantidade"],
                unidade_medida="UN",
                ativo=True,
            )
            db.session.add(produto)
            produtos.append(produto)
            print(f"  ✅ {produto.nome} - R$ {produto.preco_venda}")
        
        db.session.flush()
        print()
        
        # 7. VENDAS (apenas em ambiente de teste)
        if env == "LOCAL":
            print("💰 Criando vendas de exemplo...")
            admin = Funcionario.query.filter_by(username="admin").first()
            cliente = Cliente.query.first()
            
            for i in range(5):
                venda = Venda(
                    estabelecimento_id=estabelecimento.id,
                    funcionario_id=admin.id,
                    cliente_id=cliente.id if i % 2 == 0 else None,
                    codigo=f"V-{datetime.now().strftime('%Y%m%d')}-{1000+i}",
                    subtotal=Decimal("50.00"),
                    desconto=Decimal("5.00"),
                    total=Decimal("45.00"),
                    forma_pagamento="dinheiro",
                    status="finalizada",
                    data_venda=datetime.now() - timedelta(days=i),
                )
                db.session.add(venda)
                
                # Adicionar itens
                item = VendaItem(
                    venda=venda,
                    produto_id=produtos[i % len(produtos)].id,
                    quantidade=2,
                    preco_unitario=produtos[i % len(produtos)].preco_venda,
                    subtotal=produtos[i % len(produtos)].preco_venda * 2,
                )
                db.session.add(item)
                print(f"  ✅ Venda {venda.codigo}")
            print()
        
        # COMMIT FINAL
        print("💾 Salvando no banco de dados...")
        db.session.commit()
        print("✅ Dados salvos com sucesso!\n")
        
        # RESUMO
        print(f"{'='*60}")
        print("📊 RESUMO DO SEED")
        print(f"{'='*60}")
        print(f"  Estabelecimentos: {Estabelecimento.query.count()}")
        print(f"  Funcionários:     {Funcionario.query.count()}")
        print(f"  Clientes:         {Cliente.query.count()}")
        print(f"  Fornecedores:     {Fornecedor.query.count()}")
        print(f"  Categorias:       {Categoria.query.count()}")
        print(f"  Produtos:         {Produto.query.count()}")
        print(f"  Vendas:           {Venda.query.count()}")
        print(f"{'='*60}\n")
        
        print("🎉 SEED COMPLETO!")
        print(f"\n📝 Credenciais de acesso:")
        print(f"  Username: admin")
        print(f"  Password: admin123")
        print(f"\n🌐 Ambiente: {env}")
        print(f"{'='*60}\n")
        
        return True


if __name__ == "__main__":
    try:
        success = seed_database()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
