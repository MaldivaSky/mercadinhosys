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
