import pytest
from datetime import date
from decimal import Decimal
from app.models import Funcionario, Rescisao, FuncionarioBeneficio, Beneficio

def test_registrar_e_cancelar_rescisao(session):
    admin = Funcionario.query.filter_by(role="admin").first()
    assert admin is not None
    estab_id = admin.estabelecimento_id

    # Criar um funcionário teste
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

    # Criar um benefício ativo para o funcionário
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

    # Importar motor de rescisão e testar simulação e gravação
    from app.services.rh_calculator_service import calcular_rescisao
    dt_dem = date(2026, 7, 20)
    resultado = calcular_rescisao(func, dt_dem, "S_JUSTA", ferias_vencidas_dias=0)

    assert resultado["tipo_rescisao"] == "S_JUSTA"
    assert resultado["total_proventos"] > 0

    # Gravar rescisão e desativar funcionário
    rescisao = Rescisao(
        estabelecimento_id=estab_id,
        funcionario_id=func.id,
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

    # Verificar se funcionário está demitido e inativo
    func_db = Funcionario.query.get(func.id)
    assert func_db.ativo is False
    assert func_db.status == "demitido"
    assert func_db.data_demissao == dt_dem

    fb_db = FuncionarioBeneficio.query.get(fb.id)
    assert fb_db.ativo is False

    rescisao_db = Rescisao.query.filter_by(funcionario_id=func.id).first()
    assert rescisao_db is not None
    assert rescisao_db.tipo_rescisao == "S_JUSTA"

    # Testar Cancelamento/Reversão
    func_db.data_demissao = None
    func_db.ativo = True
    func_db.status = "ativo"
    session.delete(rescisao_db)
    session.commit()

    func_reativado = Funcionario.query.get(func.id)
    assert func_reativado.ativo is True
    assert func_reativado.status == "ativo"
    assert func_reativado.data_demissao is None

    rescisao_deletada = Rescisao.query.filter_by(funcionario_id=func.id).first()
    assert rescisao_deletada is None
