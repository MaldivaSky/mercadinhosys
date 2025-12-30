import os
import sys
from datetime import datetime, date

# Adiciona o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import (
    Fornecedor, Produto, Funcionario, Cliente,
    Venda, VendaItem, Pagamento, Compra, CompraItem,
    MovimentacaoEstoque, Auditoria, Configuracao
)
from werkzeug.security import generate_password_hash

def criar_banco_do_zero():
    """Script para criar banco de dados do zero com dados de teste"""
    
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("🔧 INICIANDO CRIAÇÃO DO BANCO DE DADOS")
        print("=" * 60)
        
        # 1. Apagar banco existente
        print("🗑️  1. Removendo banco antigo...")
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        
        # Para Windows, ajustar caminho
        if db_path.startswith('/'):
            db_path = db_path[1:]
        
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"   ✓ Banco antigo removido: {db_path}")
        else:
            print(f"   ✓ Nenhum banco antigo encontrado")
        
        # 2. Criar todas as tabelas
        print("🔄 2. Criando tabelas...")
        db.create_all()
        print("   ✓ Tabelas criadas com sucesso!")
        
        # 3. CRIAR VOCÊ COMO ADMIN
        print("👑 3. Criando administrador do sistema...")
        
        admin = Funcionario(
            nome="Rafael Paiva Dias da Silva",
            cpf="343.721.318-01",
            rg="MG-12.345.678",
            data_nascimento=date(1990, 5, 15),
            telefone="(31) 98765-4321",
            celular="(31) 98765-4321",
            email="rafaelmaldivas@gmail.com",
            endereco="Rua Exemplo, 123 - Centro, Belo Horizonte - MG",
            cargo="Administrador",
            salario=8500.00,
            data_admissao=date(2024, 1, 1),
            usuario="admin",
            nivel_acesso="admin",
            ativo=True
        )
        admin.set_senha("admin123")  # Senha inicial
        admin.set_pin("1234")        # PIN para PDV
        
        db.session.add(admin)
        db.session.commit()
        print(f"   ✓ Admin criado: {admin.nome}")
        print(f"   ✓ Usuário: admin | Senha: admin123 | PIN: 1234")
        
        # 4. CRIAR FORNECEDORES DE EXEMPLO
        print("🏭 4. Criando fornecedores de exemplo...")
        
        fornecedores = [
            Fornecedor(
                nome="Distribuidora Alimentos Ltda",
                razao_social="Distribuidora Alimentos Ltda",
                cnpj="12.345.678/0001-90",
                telefone="(11) 3333-4444",
                email="vendas@alimentos.com.br",
                cidade="São Paulo",
                estado="SP",
                contato_nome="Carlos Silva",
                prazo_entrega=7
            ),
            Fornecedor(
                nome="Bebidas Brasil",
                razao_social="Bebidas Brasil S.A.",
                cnpj="98.765.432/0001-10",
                telefone="(21) 2222-3333",
                email="contato@bebidasbrasil.com",
                cidade="Rio de Janeiro",
                estado="RJ",
                contato_nome="Ana Paula",
                prazo_entrega=5
            ),
            Fornecedor(
                nome="Limpeza Express",
                razao_social="Limpeza Express Comércio",
                cnpj="55.666.777/0001-88",
                telefone="(31) 4444-5555",
                email="sac@limpezaexpress.com",
                cidade="Belo Horizonte",
                estado="MG",
                contato_nome="Roberto Costa",
                prazo_entrega=3
            )
        ]
        
        for f in fornecedores:
            db.session.add(f)
        db.session.commit()
        print(f"   ✓ {len(fornecedores)} fornecedores criados")
        
        # 5. CRIAR PRODUTOS DE EXEMPLO
        print("📦 5. Criando produtos de exemplo...")
        
        produtos = [
            Produto(
                codigo_barras="7891000315507",
                nome="Arroz Branco 5kg",
                descricao="Arroz tipo 1, grãos longos",
                fornecedor_id=1,
                preco_custo=15.00,
                preco_venda=24.90,
                margem_lucro=66.0,
                quantidade=150,
                quantidade_minima=30,
                categoria="Alimentos",
                marca="Tio João",
                tipo="unidade",
                unidade_medida="un"
            ),
            Produto(
                codigo_barras="7891000055502",
                nome="Feijão Carioca 1kg",
                descricao="Feijão tipo carioca",
                fornecedor_id=1,
                preco_custo=4.50,
                preco_venda=8.90,
                margem_lucro=97.8,
                quantidade=200,
                quantidade_minima=40,
                categoria="Alimentos",
                marca="Camil",
                tipo="unidade",
                unidade_medida="un"
            ),
            Produto(
                codigo_barras="7894900010015",
                nome="Coca-Cola 2L",
                descricao="Refrigerante Coca-Cola",
                fornecedor_id=2,
                preco_custo=4.00,
                preco_venda=9.90,
                margem_lucro=147.5,
                quantidade=120,
                quantidade_minima=25,
                categoria="Bebidas",
                marca="Coca-Cola",
                tipo="unidade",
                unidade_medida="un"
            ),
        ]
        
        for p in produtos:
            db.session.add(p)
        db.session.commit()
        print(f"   ✓ {len(produtos)} produtos criados")
        
        # 6. CRIAR CLIENTES DE EXEMPLO
        print("👥 6. Criando clientes de exemplo...")
        
        clientes = [
            Cliente(
                nome="Maria Silva Santos",
                cpf="111.222.333-44",
                telefone="(31) 3333-4444",
                email="maria@gmail.com",
                limite_credito=1000.00
            ),
            Cliente(
                nome="João Pereira Oliveira",
                cpf="222.333.444-55",
                telefone="(31) 4444-5555",
                email="joao@hotmail.com",
                limite_credito=500.00
            ),
        ]
        
        for c in clientes:
            db.session.add(c)
        db.session.commit()
        print(f"   ✓ {len(clientes)} clientes criados")
        
        # 7. CRIAR FUNCIONÁRIOS ADICIONAIS
        print("👔 7. Criando funcionários adicionais...")
        
        funcionarios = [
            Funcionario(
                nome="Carlos Eduardo Mendes",
                cpf="333.444.555-66",
                cargo="Gerente",
                salario=4500.00,
                data_admissao=date(2024, 2, 1),
                usuario="gerente",
                nivel_acesso="gerente"
            ),
            Funcionario(
                nome="Ana Claudia Souza",
                cpf="444.555.666-77",
                cargo="Atendente",
                salario=2200.00,
                data_admissao=date(2024, 3, 15),
                usuario="atendente1",
                nivel_acesso="atendente"
            ),
        ]
        
        for f in funcionarios:
            f.set_senha("123456")
            f.set_pin("1111")
            db.session.add(f)
        db.session.commit()
        print(f"   ✓ {len(funcionarios)} funcionários criados")
        
        print("\n" + "=" * 60)
        print("✅ BANCO DE DADOS CRIADO COM SUCESSO!")
        print("=" * 60)
        print("\n📊 RESUMO DO QUE FOI CRIADO:")
        print(f"   • 1 Administrador (Você)")
        print(f"   • {len(fornecedores)} Fornecedores")
        print(f"   • {len(produtos)} Produtos")
        print(f"   • {len(clientes)} Clientes")
        print(f"   • {len(funcionarios)} Funcionários")
        print(f"\n🔑 ACESSO:")
        print(f"   Usuário: admin")
        print(f"   Senha: admin123")
        print(f"   PIN PDV: 1234")
        print("\n🚀 Para iniciar o sistema, execute:")
        print("   flask run")
        print("=" * 60)

if __name__ == "__main__":
    criar_banco_do_zero()