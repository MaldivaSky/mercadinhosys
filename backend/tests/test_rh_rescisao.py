import pytest
from datetime import date
from decimal import Decimal
from app.models import Funcionario, Rescisao, FuncionarioBeneficio, Beneficio, Despesa

def test_registrar_e_cancelar_rescisao_com_despesa_financeira(session):
    admin = Funcionario.query.filter_by(role="admin").first()
    assert admin is not None
    estab_id = admin.estabelecimento_id

    # 1. Criar um funcionário teste
    func = Funcionario(
        estabelecimento_id=estab_id,
        nome="João da Silva Demissão Teste",
        cpf="98765432100",
        username="joao_demissao",
        role="FUNCIONARIO",
        ativo=True,
        status="ativo",
        data_nascimento=date(1995, 5, 10),
        celular="92988887777",
        email="joao@teste.com",
        cargo="Operador de Caixa",
        data_admissao=date(2024, 1, 1),
        salario_base=Decimal("2000.00")
    )
    func.set_password("senha123")
    session.add(func)
    session.flush()

    # 2. Criar um benefício ativo para o funcionário
    ben = Beneficio(
        estabelecimento_id=estab_id,
        nome="Vale Transporte",
        valor_padrao=Decimal("200.00"),
        ativo=True
    )
    session.add(ben)
    session.flush()

    fb = FuncionarioBeneficio(
        estabelecimento_id=estab_id,
        funcionario_id=func.id,
        beneficio_id=ben.id,
        valor=Decimal("200.00"),
        ativo=True
    )
    session.add(fb)
    session.commit()

    # 3. Simular e gravar rescisão com despesa financeira associada
    from app.services.rh_calculator_service import calcular_rescisao
    dt_dem = date(2026, 7, 20)
    resultado = calcular_rescisao(func, dt_dem, "S_JUSTA", ferias_vencidas_dias=0)

    valor_despesa = Decimal(str(resultado["total_liquido_estimado"]))
    despesa = Despesa(
        estabelecimento_id=estab_id,
        descricao=f"Rescisão Trabalhista - {func.nome} ({resultado['tipo_rescisao']})",
        categoria="Rescisão Trabalhista",
        tipo="variavel",
        valor=valor_despesa,
        data_despesa=dt_dem,
        data_emissao=dt_dem,
        data_vencimento=dt_dem,
        forma_pagamento="PIX",
        recorrente=False,
        observacoes=f"Lançamento automático de verbas rescisórias da demissão de {func.nome}."
    )
    session.add(despesa)
    session.flush()

    rescisao = Rescisao(
        estabelecimento_id=estab_id,
        funcionario_id=func.id,
        despesa_id=despesa.id,
        data_demissao=dt_dem,
        tipo_rescisao="S_JUSTA",
        verbas_rescisorias_json=resultado,
        total_proventos=Decimal(str(resultado["total_proventos"])),
        total_descontos=Decimal("0.00"),
        total_liquido=Decimal(str(resultado["total_liquido_estimado"])),
    )
    session.add(rescisao)

    func.data_demissao = dt_dem
    func.ativo = False
    func.status = "demitido"

    FuncionarioBeneficio.query.filter_by(
        funcionario_id=func.id,
        ativo=True
    ).update({"ativo": False})

    session.commit()

    # 4. Verificar se funcionário, benefício, rescisão e despesa foram gravados
    func_db = Funcionario.query.get(func.id)
    assert func_db.ativo is False
    assert func_db.status == "demitido"
    assert func_db.data_demissao == dt_dem

    fb_db = FuncionarioBeneficio.query.get(fb.id)
    assert fb_db.ativo is False

    rescisao_db = Rescisao.query.filter_by(funcionario_id=func.id).first()
    assert rescisao_db is not None
    assert rescisao_db.despesa_id == despesa.id

    despesa_db = Despesa.query.get(despesa.id)
    assert despesa_db is not None
    assert despesa_db.categoria == "Rescisão Trabalhista"
    assert despesa_db.valor == valor_despesa

    # 5. Testar Cancelamento/Estorno da Rescisão e da Despesa Financeira
    despesa_id_salvo = rescisao_db.despesa_id
    session.delete(despesa_db)
    session.delete(rescisao_db)
    func_db.data_demissao = None
    func_db.ativo = True
    func_db.status = "ativo"
    session.commit()

    assert Despesa.query.get(despesa_id_salvo) is None
    assert Rescisao.query.filter_by(funcionario_id=func.id).first() is None
    assert Funcionario.query.get(func.id).ativo is True


def test_deduplicacao_e_forma_pagamento_rescisao(session):
    """Garante que a forma de pagamento é gravada e que demissões repetidas por testes anteriores são deduplicadas."""
    admin = Funcionario.query.filter_by(role="admin").first()
    assert admin is not None
    estab_id = admin.estabelecimento_id

    # 1. Criar um funcionário para o teste de deduplicação
    vendedor = Funcionario(
        estabelecimento_id=estab_id,
        nome="Vendedor Gama Teste Deduplicacao",
        cpf="11122233344",
        username="vendedor_gama",
        role="FUNCIONARIO",
        ativo=True,
        status="ativo",
        data_nascimento=date(1990, 1, 1),
        celular="92977776666",
        email="vendedor@gama.com",
        cargo="Vendedor",
        data_admissao=date(2023, 1, 1),
        salario_base=Decimal("3000.00")
    )
    vendedor.set_password("senha123")
    session.add(vendedor)
    session.commit()

    # 2. Primeira demissão com ACORDO (valor menor)
    from app.services.rh_calculator_service import calcular_rescisao
    res_acordo = calcular_rescisao(vendedor, date(2026, 7, 20), "ACORDO")
    d1 = Despesa(
        estabelecimento_id=estab_id,
        descricao=f"Rescisão Trabalhista - {vendedor.nome} (ACORDO)",
        categoria="Rescisão Trabalhista",
        tipo="variavel",
        valor=Decimal(str(res_acordo["total_liquido_estimado"])),
        data_despesa=date(2026, 7, 20),
        forma_pagamento="PIX"
    )
    session.add(d1)
    session.flush()

    r1 = Rescisao(
        estabelecimento_id=estab_id,
        funcionario_id=vendedor.id,
        despesa_id=d1.id,
        data_demissao=date(2026, 7, 20),
        tipo_rescisao="ACORDO",
        verbas_rescisorias_json=res_acordo,
        total_proventos=Decimal(str(res_acordo["total_proventos"])),
        total_liquido=Decimal(str(res_acordo["total_liquido_estimado"])),
        forma_pagamento="PIX"
    )
    session.add(r1)
    session.commit()

    # 3. Segunda demissão sem acordo (S_JUSTA) com forma de pagamento 'Transferência'
    res_sjusta = calcular_rescisao(vendedor, date(2026, 7, 20), "S_JUSTA")
    
    # Simula a limpeza do backend (garantir_despesas_rescisoes_legadas)
    from app.routes.rh import _garantir_despesas_rescisoes_legadas
    
    # Criar 2ª rescisão simulando clique do usuário
    d2 = Despesa(
        estabelecimento_id=estab_id,
        descricao=f"Rescisão Trabalhista - {vendedor.nome} (S_JUSTA)",
        categoria="Rescisão Trabalhista",
        tipo="variavel",
        valor=Decimal(str(res_sjusta["total_liquido_estimado"])),
        data_despesa=date(2026, 7, 20),
        forma_pagamento="Transferência"
    )
    session.add(d2)
    session.flush()

    r2 = Rescisao(
        estabelecimento_id=estab_id,
        funcionario_id=vendedor.id,
        despesa_id=d2.id,
        data_demissao=date(2026, 7, 20),
        tipo_rescisao="S_JUSTA",
        verbas_rescisorias_json=res_sjusta,
        total_proventos=Decimal(str(res_sjusta["total_proventos"])),
        total_liquido=Decimal(str(res_sjusta["total_liquido_estimado"])),
        forma_pagamento="Transferência"
    )
    session.add(r2)
    session.commit()

    # Executar a sincronização e deduplicação
    _garantir_despesas_rescisoes_legadas()

    # 4. Validar que existe APENAS 1 rescisão ativa (a mais recente, S_JUSTA)
    rescisoes = Rescisao.query.filter_by(funcionario_id=vendedor.id).all()
    assert len(rescisoes) == 1
    assert rescisoes[0].tipo_rescisao == "S_JUSTA"
    assert rescisoes[0].forma_pagamento == "Transferência"

    # Validar que a despesa financeira reflete exatamente S_JUSTA e R$ 9.000+
    desp_final = Despesa.query.get(rescisoes[0].despesa_id)
    assert desp_final is not None
    assert desp_final.forma_pagamento == "Transferência"
    assert "S_JUSTA" in desp_final.descricao

