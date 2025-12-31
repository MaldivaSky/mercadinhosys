# backend/seed.py
import sys
import os
from datetime import datetime, timedelta
import random
import math

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import (
    Estabelecimento,
    Configuracao,
    Funcionario,
    Cliente,
    Fornecedor,
    Produto,
    Venda,
    VendaItem,
    MovimentacaoEstoque,
    DashboardMetrica,
    RelatorioAgendado,
)

# Dados fictícios (mantenha igual ao anterior)
MARCAS = [
    "Nestlé",
    "Coca-Cola",
    "P&G",
    "Unilever",
    "Ambev",
    "Heineken",
    "Sadia",
    "Perdigão",
    "Bauducco",
    "Garoto",
]
# ... (mantenha todas as funções auxiliares: gerar_cnpj, gerar_cpf, etc.)


def seed_database():
    """Função principal para popular o banco de dados"""
    print("Iniciando seed do banco de dados...")

    # Criar aplicação Flask
    app = create_app()

    with app.app_context():
        # VERIFICAR se as tabelas existem primeiro
        print("Verificando tabelas...")

        # Lista de tabelas que devem existir
        tabelas = [
            "estabelecimentos",
            "configuracoes",
            "funcionarios",
            "clientes",
            "fornecedores",
            "produtos",
            "vendas",
            "venda_itens",
            "movimentacoes_estoque",
            "dashboard_metricas",
            "relatorios_agendados",
        ]

        # Tentar criar tabelas se não existirem
        try:
            # Verificar se a tabela estabelecimentos existe
            from sqlalchemy import inspect

            inspector = inspect(db.engine)
            tabelas_existentes = inspector.get_table_names()

            print(f"Tabelas existentes: {tabelas_existentes}")

            # Se não existirem tabelas, criar todas
            if not tabelas_existentes:
                print("Criando todas as tabelas...")
                db.create_all()
                print("Tabelas criadas com sucesso!")
            else:
                print("Tabelas já existem, prosseguindo...")

        except Exception as e:
            print(f"Erro ao verificar tabelas: {e}")
            print("Criando tabelas...")
            db.create_all()

        # LIMPAR dados existentes (com cuidado)
        print("\nLimpar dados existentes? (s/n)")
        resposta = input().lower()

        if resposta == "s":
            print("Limpando dados...")
            # Limpar na ordem inversa das dependências
            MovimentacaoEstoque.query.delete()
            VendaItem.query.delete()
            Venda.query.delete()
            Produto.query.delete()
            Fornecedor.query.delete()
            Cliente.query.delete()
            Funcionario.query.delete()
            Configuracao.query.delete()
            DashboardMetrica.query.delete()
            RelatorioAgendado.query.delete()
            Estabelecimento.query.delete()
            db.session.commit()
            print("Dados limpos!")

        # AGORA VAMOS CRIAR OS DADOS PASSO A PASSO

        # 1. CRIAR ESTABELECIMENTO (SEM usar flush ainda)
        print("\n1. Criando estabelecimento...")

        # Gerar dados do estabelecimento
        cep = "01001-000"

        # Função para gerar endereço do estabelecimento
        def gerar_endereco_estabelecimento():
            cidade, estado, logradouro, bairro = random.choice(
                [
                    ("São Paulo", "SP", "Avenida Paulista", "Bela Vista"),
                    ("Rio de Janeiro", "RJ", "Avenida Atlântica", "Copacabana"),
                    ("Belo Horizonte", "MG", "Avenida Afonso Pena", "Centro"),
                    ("Curitiba", "PR", "Rua das Flores", "Centro"),
                ]
            )
            numero = random.randint(100, 5000)
            return {
                "endereco": f"{logradouro}, {numero} - {bairro}",
                "cidade": cidade,
                "estado": estado,
            }

        endereco_info = gerar_endereco_estabelecimento()

        estabelecimento = Estabelecimento(
            nome="Supermercado Central",
            cnpj="12.345.678/0001-99",  # CNPJ fixo para teste
            telefone="(11) 9999-8888",
            email="contato@supermercadocentral.com.br",
            cep=cep,
            endereco=endereco_info["endereco"],
            cidade=endereco_info["cidade"],
            estado=endereco_info["estado"],
            data_cadastro=datetime.now() - timedelta(days=365),
            ativo=True,
        )

        db.session.add(estabelecimento)
        db.session.commit()  # COMMIT primeiro para garantir ID
        print(f"✓ Estabelecimento criado: ID {estabelecimento.id}")

        # 2. CRIAR CONFIGURAÇÃO
        print("\n2. Criando configuração...")

        configuracao = Configuracao(
            estabelecimento_id=estabelecimento.id,
            logo_url="/static/logo.png",
            cor_principal="#4F46E5",
            tema_escuro=False,
            impressao_automatica=True,
            tipo_impressora="termica",
            exibir_preco_tela=True,
            permitir_venda_sem_estoque=False,
            desconto_maximo_percentual=15.0,
            arredondamento_valores=0.05,
            dias_alerta_validade=15,
            estoque_minimo_padrao=10,
            tempo_sessao_minutos=30,
            tentativas_senha_bloqueio=3,
            formas_pagamento={
                "dinheiro": {"ativo": True, "taxa": 0, "exige_troco": True},
                "cartao_credito": {"ativo": True, "taxa": 2.5, "parcelas": 12},
                "cartao_debito": {"ativo": True, "taxa": 1.5},
                "pix": {"ativo": True, "taxa": 0},
            },
            alertas_email=True,
            alertas_whatsapp=False,
        )

        db.session.add(configuracao)
        db.session.commit()
        print(f"✓ Configuração criada para estabelecimento {estabelecimento.id}")

        # 3. CRIAR FUNCIONÁRIOS
        print("\n3. Criando funcionários...")

        funcionarios = []
        funcionarios_data = [
            {
                "nome": "João Silva",
                "username": "joao",
                "cargo": "dono",
                "senha": "123456",
            },
            {
                "nome": "Maria Santos",
                "username": "maria",
                "cargo": "gerente",
                "senha": "123456",
            },
            {
                "nome": "Carlos Oliveira",
                "username": "carlos",
                "cargo": "caixa",
                "senha": "123456",
            },
            {
                "nome": "Ana Costa",
                "username": "ana",
                "cargo": "caixa",
                "senha": "123456",
            },
        ]

        for i, func_data in enumerate(funcionarios_data):
            funcionario = Funcionario(
                estabelecimento_id=estabelecimento.id,
                nome=func_data["nome"],
                username=func_data["username"],
                cpf=f"{i+1:03d}.456.789-{i+1:02d}",
                telefone=f"(11) 9{i:04d}-{i+1:04d}",
                email=f"{func_data['username']}@supermercado.com",
                cargo=func_data["cargo"],
                role="admin" if func_data["cargo"] == "dono" else "funcionario",
                status="ativo",
                comissao_percentual=0.0,
                data_admissao=datetime.now() - timedelta(days=100),
                ativo=True,
                permissoes={
                    "acesso_pdv": True,
                    "acesso_estoque": True,
                    "acesso_relatorios": True,
                    "acesso_configuracoes": func_data["cargo"] in ["dono", "gerente"],
                    "acesso_financeiro": func_data["cargo"] in ["dono", "gerente"],
                    "pode_dar_desconto": True,
                    "limite_desconto": (
                        20.0 if func_data["cargo"] in ["dono", "gerente"] else 5.0
                    ),
                    "pode_cancelar_venda": func_data["cargo"] in ["dono", "gerente"],
                },
            )

            funcionario.set_senha(func_data["senha"])
            funcionarios.append(funcionario)
            db.session.add(funcionario)

        db.session.commit()
        print(f"✓ {len(funcionarios)} funcionários criados")

        # 4. CRIAR CLIENTES (simplificado)
        print("\n4. Criando clientes...")

        clientes = []
        for i in range(10):
            cliente = Cliente(
                estabelecimento_id=estabelecimento.id,
                nome=f"Cliente {i+1}",
                cpf_cnpj=f"{i+1:03d}.456.789-{i:02d}",
                telefone=f"(11) 9{i:04d}-{i:04d}",
                email=f"cliente{i+1}@email.com",
                endereco=f"Rua das Flores, {i+1}00",
                data_cadastro=datetime.now() - timedelta(days=random.randint(1, 100)),
                total_compras=random.uniform(100, 5000),
                ultima_compra=datetime.now() - timedelta(days=random.randint(1, 30)),
                observacoes="",
            )
            clientes.append(cliente)
            db.session.add(cliente)

        db.session.commit()
        print(f"✓ {len(clientes)} clientes criados")

        # 5. CRIAR FORNECEDORES
        print("\n5. Criando fornecedores...")

        fornecedores = []
        nomes_fornecedores = ["Fornecedor A", "Fornecedor B", "Fornecedor C"]

        for i, nome in enumerate(nomes_fornecedores):
            fornecedor = Fornecedor(
                estabelecimento_id=estabelecimento.id,
                nome=nome,
                cnpj=f"{i+1:02d}.123.456/0001-{i+1:02d}",
                telefone=f"(11) 3{i:04d}-{i:04d}",
                email=f"contato@{nome.lower().replace(' ', '')}.com.br",
                endereco=f"Av. Industrial, {i+1}000",
                contato_comercial=f"Sr. {['João', 'Maria', 'Carlos'][i]}",
                celular_comercial=f"(11) 9{i+5:04d}-{i:04d}",
                prazo_entrega=random.randint(2, 7),
                forma_pagamento="30 dias",
            )
            fornecedores.append(fornecedor)
            db.session.add(fornecedor)

        db.session.commit()
        print(f"✓ {len(fornecedores)} fornecedores criados")

        # 6. CRIAR PRODUTOS
        print("\n6. Criando produtos...")

        produtos = []
        categorias = ["Alimentos", "Bebidas", "Limpeza", "Higiene"]

        for i in range(20):  # 20 produtos para teste
            preco_custo = round(random.uniform(1, 20), 2)
            preco_venda = round(preco_custo * random.uniform(1.3, 2.0), 2)

            produto = Produto(
                estabelecimento_id=estabelecimento.id,
                fornecedor_id=random.choice(fornecedores).id,
                codigo_barras=f"78912345{i:06d}",
                nome=f"Produto {i+1}",
                descricao=f"Descrição do produto {i+1}",
                marca=random.choice(MARCAS),
                fabricante=random.choice(MARCAS),
                categoria=random.choice(categorias),
                unidade_medida=random.choice(["UN", "KG", "LT"]),
                quantidade=random.randint(0, 100),
                quantidade_minima=10,
                localizacao=f"Corredor {random.randint(1, 5)}",
                preco_custo=preco_custo,
                preco_venda=preco_venda,
                margem_lucro=round((preco_venda - preco_custo) / preco_custo * 100, 2),
                data_validade=datetime.now() + timedelta(days=random.randint(30, 365)),
                lote=f"L{i+1:04d}/2024",
                imagem_url="",
                ativo=True,
            )
            produtos.append(produto)
            db.session.add(produto)

        db.session.commit()
        print(f"✓ {len(produtos)} produtos criados")

        # 7. CRIAR ALGUMAS VENDAS (opcional - podemos pular se quiser testar rápido)
        print("\n7. Criando vendas de exemplo...")

        criar_vendas = input("Deseja criar vendas de exemplo? (s/n): ").lower()

        if criar_vendas == "s":
            formas_pagamento = ["dinheiro", "cartao_credito", "cartao_debito", "pix"]

            for venda_num in range(10):  # 10 vendas para teste
                data_venda = datetime.now() - timedelta(days=random.randint(0, 30))
                funcionario = random.choice(funcionarios)

                venda = Venda(
                    estabelecimento_id=estabelecimento.id,
                    cliente_id=(
                        random.choice(clientes).id if random.random() > 0.3 else None
                    ),
                    funcionario_id=funcionario.id,
                    codigo=f"V{data_venda.strftime('%Y%m%d')}{venda_num:04d}",
                    subtotal=0,
                    desconto=0,
                    total=0,
                    forma_pagamento=random.choice(formas_pagamento),
                    valor_recebido=0,
                    troco=0,
                    status="finalizada",
                    data_venda=data_venda,
                )

                db.session.add(venda)
                db.session.commit()  # Commit para obter venda.id

                # Adicionar itens à venda
                total_venda = 0
                for _ in range(random.randint(1, 5)):
                    produto = random.choice(produtos)
                    quantidade = random.randint(1, 3)
                    preco_unitario = produto.preco_venda
                    total_item = preco_unitario * quantidade

                    item = VendaItem(
                        venda_id=venda.id,
                        produto_id=produto.id,
                        produto_nome=produto.nome,
                        produto_codigo=produto.codigo_barras,
                        produto_unidade=produto.unidade_medida,
                        quantidade=quantidade,
                        preco_unitario=preco_unitario,
                        total_item=total_item,
                    )

                    db.session.add(item)
                    total_venda += total_item

                    # Atualizar estoque
                    produto.quantidade = max(0, produto.quantidade - quantidade)

                # Atualizar valores da venda
                venda.subtotal = total_venda
                venda.total = total_venda
                venda.valor_recebido = total_venda

                db.session.commit()

            print("✓ 10 vendas criadas")

        # FINALIZAR
        print("\n" + "=" * 50)
        print("SEED CONCLUÍDO COM SUCESSO!")
        print("=" * 50)
        print(f"Estabelecimento: {estabelecimento.nome}")
        print(f"Funcionários: {len(funcionarios)}")
        print(f"Clientes: {len(clientes)}")
        print(f"Fornecedores: {len(fornecedores)}")
        print(f"Produtos: {len(produtos)}")
        print("=" * 50)
        print("\nCredenciais para login:")
        print("Usuário: joao | Senha: 123456 (Dono)")
        print("Usuário: maria | Senha: 123456 (Gerente)")
        print("Usuário: carlos | Senha: 123456 (Caixa)")
        print("=" * 50)


if __name__ == "__main__":
    seed_database()
