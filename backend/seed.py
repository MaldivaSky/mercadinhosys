# seed.py - Dados iniciais para teste
from app import create_app, db
from app.models import Estabelecimento, Configuracao, Funcionario

app = create_app()

with app.app_context():
    # Criar estabelecimento
    estabelecimento = Estabelecimento(
        nome="Mercadinho do Zé",
        cnpj="12.345.678/0001-90",
        telefone="(92) 99999-9999",
        email="contato@mercadinhodoze.com",
        endereco="Rua das Flores, 123 - Centro",
        cidade="Manaus",
        estado="AM",
    )
    db.session.add(estabelecimento)
    db.session.commit()

    # Criar configurações
    config = Configuracao(
        estabelecimento_id=estabelecimento.id,
        cor_principal="#4F46E5",
        formas_pagamento={
            "dinheiro": {"ativo": True, "taxa": 0, "exige_troco": True},
            "cartao_credito": {"ativo": True, "taxa": 2.5, "parcelas": 12},
            "cartao_debito": {"ativo": True, "taxa": 1.5},
            "pix": {"ativo": True, "taxa": 0},
        },
    )
    db.session.add(config)

    # Criar funcionário admin
    admin = Funcionario(
        estabelecimento_id=estabelecimento.id,
        nome="Administrador",
        cpf="343.721.318-01",
        telefone="(92) 98888-8888",
        email="admin@mercadinhosys.com",
        cargo="dono",
        data_admissao="2024-01-01",
        permissoes={
            "acesso_pdv": True,
            "acesso_estoque": True,
            "acesso_relatorios": True,
            "acesso_configuracoes": True,
            "acesso_financeiro": True,
            "pode_dar_desconto": True,
            "limite_desconto": 50.0,
            "pode_cancelar_venda": True,
        },
    )
    admin.set_senha("admin123")
    db.session.add(admin)

    db.session.commit()
    print("✅ Dados iniciais criados com sucesso!")
    print(f"   Estabelecimento ID: {estabelecimento.id}")
    print(f"   Login: admin@mercadinhosys.com / admin123")
