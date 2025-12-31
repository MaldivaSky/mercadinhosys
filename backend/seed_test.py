# backend/seed_final_correto.py
import sys
import os
from datetime import datetime, timedelta
import random
from sqlalchemy import text, inspect

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import (
    db,
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


# Funções auxiliares simplificadas
def gerar_cpf():
    return f"{random.randint(100, 999)}.{random.randint(100, 999)}.{random.randint(100, 999)}-{random.randint(10, 99)}"


def gerar_cnpj():
    return f"{random.randint(10, 99)}.{random.randint(100, 999)}.{random.randint(100, 999)}/0001-{random.randint(10, 99)}"


def gerar_telefone():
    return f"({random.randint(11, 99)}) 9{random.randint(1000, 9999)}-{random.randint(1000, 9999)}"


def seed_completo():
    print("🚀 INICIANDO SEED COMPLETO DO BANCO DE DADOS")
    print("=" * 60)

    app = create_app()

    with app.app_context():
        # Verificar se já existe algum estabelecimento
        existe_estabelecimento = Estabelecimento.query.first()
        if existe_estabelecimento:
            resposta = input(
                "Já existe um estabelecimento. Deseja limpar e recriar todos os dados? (s/n): "
            ).lower()
            if resposta != "s":
                print("Operação cancelada.")
                return
            else:
                print("Limpando dados existentes...")
                # Desabilitar foreign keys temporariamente (SQLite)
                db.session.execute(text("PRAGMA foreign_keys = OFF"))

                # Obter lista de tabelas na ordem inversa de dependência
                tabelas = [
                    "movimentacoes_estoque",
                    "venda_itens",
                    "vendas",
                    "produtos",
                    "fornecedores",
                    "clientes",
                    "funcionarios",
                    "configuracoes",
                    "dashboard_metricas",
                    "relatorios_agendados",
                    "estabelecimentos",
                ]

                for tabela in tabelas:
                    try:
                        db.session.execute(text(f"DELETE FROM {tabela}"))
                        print(f"  - Limpou {tabela}")
                    except Exception as e:
                        print(f"  - Tabela {tabela} não existe ou erro: {e}")
                        pass

                db.session.execute(text("PRAGMA foreign_keys = ON"))
                db.session.commit()
                print("✓ Dados limpos")

        # 1. ESTABELECIMENTO
        print("\n1. Criando estabelecimento...")
        estabelecimento = Estabelecimento(
            nome="Supermercado Central",
            cnpj=gerar_cnpj(),
            telefone=gerar_telefone(),
            email="contato@supermercado.com.br",
            cep="69083-040",
            endereco="Rua Benjamin Benchimol, 360",
            cidade="Manaus",
            estado="AM",
            data_cadastro=datetime.now() - timedelta(days=365),
            ativo=True,
        )
        db.session.add(estabelecimento)
        db.session.commit()
        estabelecimento_id = estabelecimento.id
        print(f"✓ Estabelecimento ID: {estabelecimento_id}")

        # 2. CONFIGURAÇÃO
        print("\n2. Criando configuração...")
        config = Configuracao(
            estabelecimento_id=estabelecimento_id,
            cor_principal="#4F46E5",
            formas_pagamento={
                "dinheiro": {"ativo": True, "taxa": 0},
                "cartao_credito": {"ativo": True, "taxa": 2.5},
                "cartao_debito": {"ativo": True, "taxa": 1.5},
                "pix": {"ativo": True, "taxa": 0},
            },
        )
        db.session.add(config)
        db.session.commit()

        # 3. FUNCIONÁRIOS
        print("\n3. Criando funcionários...")
        funcionarios = []
        dados_func = [
            ("admin", "Administrador", "dono", "admin123"),
            ("gerente", "Maria Silva", "gerente", "123456"),
            ("caixa1", "João Santos", "caixa", "123456"),
            ("caixa2", "Ana Costa", "caixa", "123456"),
        ]

        for username, nome, cargo, senha in dados_func:
            func = Funcionario(
                estabelecimento_id=estabelecimento_id,
                nome=nome,
                username=username,
                cpf=gerar_cpf(),
                telefone=gerar_telefone(),
                email=f"{username}@supermercado.com",
                cargo=cargo,
                role="admin" if cargo == "dono" else "funcionario",
                status="ativo",
                data_admissao=datetime.now().date() - timedelta(days=365),
                ativo=True,
                permissoes={
                    "acesso_pdv": True,
                    "acesso_estoque": True,
                    "acesso_relatorios": cargo in ["dono", "gerente"],
                    "acesso_configuracoes": cargo == "dono",
                },
            )
            func.set_senha(senha)
            funcionarios.append(func)
            db.session.add(func)
        db.session.commit()
        print(f"✓ {len(funcionarios)} funcionários criados")

        # 4. CLIENTES
        print("\n4. Criando clientes...")
        clientes = []
        for i in range(15):
            cliente = Cliente(
                estabelecimento_id=estabelecimento_id,
                nome=f"Cliente {i+1}",
                cpf_cnpj=gerar_cpf(),
                telefone=gerar_telefone(),
                email=f"cliente{i+1}@email.com",
                endereco=f"Rua Exemplo, {100 + i}",
                data_cadastro=datetime.now() - timedelta(days=random.randint(1, 180)),
                total_compras=round(random.uniform(0, 1000), 2),
            )
            clientes.append(cliente)
            db.session.add(cliente)
        db.session.commit()
        print(f"✓ {len(clientes)} clientes criados")

        # 5. FORNECEDORES
        print("\n5. Criando fornecedores...")
        fornecedores = []
        nomes_forn = [
            "Distribuidora Alimentos",
            "Bebidas LTDA",
            "Limpeza Express",
            "Frios do Norte",
        ]

        for nome in nomes_forn:
            forn = Fornecedor(
                estabelecimento_id=estabelecimento_id,
                nome=nome,
                cnpj=gerar_cnpj(),
                telefone=gerar_telefone(),
                email=f"contato@{nome.lower().replace(' ', '')}.com.br",
                endereco="Av. Industrial, 1000",
                contato_comercial="Fulano",
                celular_comercial=gerar_telefone(),
                prazo_entrega=random.randint(3, 10),
                forma_pagamento="30 dias",
            )
            fornecedores.append(forn)
            db.session.add(forn)
        db.session.commit()
        print(f"✓ {len(fornecedores)} fornecedores criados")

        # 6. PRODUTOS
        print("\n6. Criando produtos...")
        produtos = []
        categorias = ["Alimentos", "Bebidas", "Limpeza", "Higiene", "Padaria"]

        for i in range(50):
            preco_custo = round(random.uniform(1, 30), 2)
            preco_venda = round(preco_custo * random.uniform(1.3, 2.0), 2)

            produto = Produto(
                estabelecimento_id=estabelecimento_id,
                fornecedor_id=random.choice(fornecedores).id,
                codigo_barras=f"789{random.randint(1000000000, 9999999999)}",
                nome=f"Produto {i+1}",
                descricao="Descrição do produto",
                marca=f"Marca {random.randint(1, 5)}",
                categoria=random.choice(categorias),
                unidade_medida=random.choice(["UN", "KG", "LT"]),
                quantidade=random.randint(0, 100),
                quantidade_minima=10,
                localizacao=f"Corredor {random.randint(1, 8)}",
                preco_custo=preco_custo,
                preco_venda=preco_venda,
                margem_lucro=round((preco_venda - preco_custo) / preco_custo * 100, 2),
                data_validade=datetime.now().date()
                + timedelta(days=random.randint(30, 365)),
                ativo=True,
            )
            produtos.append(produto)
            db.session.add(produto)
        db.session.commit()
        print(f"✓ {len(produtos)} produtos criados")

        # 8. VENDAS - CORRIGIDO: garantir que valor_recebido não seja nulo
        print("\n7. Criando vendas...")
        formas_pagamento = ["dinheiro", "cartao_credito", "cartao_debito", "pix"]

        for venda_num in range(20):
            data_venda = datetime.now() - timedelta(days=random.randint(0, 30))
            funcionario = random.choice(funcionarios)
            cliente = random.choice([None] + clientes)

            # Primeiro criar a venda com valores padrão
            venda = Venda(
                estabelecimento_id=estabelecimento_id,
                cliente_id=cliente.id if cliente else None,
                funcionario_id=funcionario.id,
                codigo=f"VENDA{data_venda.strftime('%Y%m%d')}{venda_num:03d}",
                subtotal=0.0,  # Inicializar com 0
                desconto=0.0,
                total=0.0,
                forma_pagamento=random.choice(formas_pagamento),
                valor_recebido=0.0,  # NÃO PODE SER NULL - inicializar com 0
                troco=0.0,
                status="finalizada",
                data_venda=data_venda,
                created_at=data_venda,
                updated_at=data_venda,
            )
            db.session.add(venda)
            db.session.commit()  # Commit para obter venda.id

            # Itens da venda
            total_venda = 0
            itens_venda = []

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
                    created_at=data_venda,
                )
                itens_venda.append(item)
                db.session.add(item)
                total_venda += total_item

                # Atualizar estoque do produto
                produto.quantidade = max(0, produto.quantidade - quantidade)

                # Registrar movimentação de estoque
                mov = MovimentacaoEstoque(
                    estabelecimento_id=estabelecimento_id,
                    produto_id=produto.id,
                    venda_id=venda.id,
                    funcionario_id=funcionario.id,
                    tipo="saida",
                    quantidade=quantidade,
                    quantidade_anterior=produto.quantidade + quantidade,
                    quantidade_atual=produto.quantidade,
                    motivo="Venda",
                    created_at=data_venda,
                )
                db.session.add(mov)

            # Atualizar valores da venda com os totais calculados
            venda.subtotal = total_venda
            venda.total = total_venda
            venda.valor_recebido = total_venda  # Valor recebido igual ao total

            # Se for dinheiro, pode ter troco
            if venda.forma_pagamento == "dinheiro":
                venda.valor_recebido = (
                    round((total_venda + 4.99) / 5) * 5
                )  # Arredonda para múltiplo de 5
                venda.troco = venda.valor_recebido - total_venda

            db.session.commit()

            if (venda_num + 1) % 5 == 0:
                print(f"  ✓ Criadas {venda_num + 1} vendas")

        print(f"✓ Total de 20 vendas criadas")

        
        # 8. MÉTRICAS DASHBOARD
        print("\n8. Criando métricas...")
        for i in range(5):
            metrica = DashboardMetrica(
                estabelecimento_id=estabelecimento_id,
                data_referencia=datetime.now().date() - timedelta(days=i),
                total_vendas_dia=round(random.uniform(500, 2000), 2),
                quantidade_vendas_dia=random.randint(5, 15),
                ticket_medio_dia=round(random.uniform(50, 150), 2),
                total_vendas_mes=round(random.uniform(10000, 30000), 2),
            )
            db.session.add(metrica)
        db.session.commit()

        # 9. RELATÓRIOS AGENDADOS
        print("\n9. Criando relatórios...")
        relatorio = RelatorioAgendado(
            estabelecimento_id=estabelecimento_id,
            nome="Relatório Diário",
            tipo="vendas",
            formato="pdf",
            frequencia="diario",
            horario_envio=datetime.strptime("08:00", "%H:%M").time(),
            ativo=True,
        )
        db.session.add(relatorio)
        db.session.commit()

        # RESUMO FINAL
        print("\n" + "=" * 60)
        print("✅ SEED COMPLETO CONCLUÍDO COM SUCESSO!")
        print("=" * 60)
        print(f"📊 RESUMO:")
        print(f"   Estabelecimento: {estabelecimento.nome}")
        print(f"   Funcionários: {len(funcionarios)}")
        print(f"   Clientes: {len(clientes)}")
        print(f"   Fornecedores: {len(fornecedores)}")
        print(f"   Produtos: {len(produtos)}")
        print(f"   Vendas: 20")
        print("=" * 60)
        print("\n🔑 CREDENCIAIS PARA TESTE:")
        print("-" * 40)
        print("   Usuário: admin | Senha: admin123 (Dono)")
        print("   Usuário: gerente | Senha: 123456 (Gerente)")
        print("   Usuário: caixa1 | Senha: 123456 (Caixa)")
        print("   Usuário: caixa2 | Senha: 123456 (Caixa)")
        print("-" * 40)
        print("\n🌐 Acesse: http://localhost:5000")
        print("=" * 60)


if __name__ == "__main__":
    seed_completo()
