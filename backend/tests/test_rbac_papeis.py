"""
Regras de negócio de acesso por papel (RBAC) — o que cada usuário da demo pode
ou não pode acessar. Garante que, ao trocar de login (admin/caixa/estoque/rh/
vendedor), o sistema restringe corretamente, sem surpresas na demonstração.

Fonte: app/decorators/rbac.py (ROLE_TO_NIVEL + RBAC_MATRIX).
"""
import pytest

from app.decorators.rbac import _get_nivel, _check_resource, ROLE_TO_NIVEL


class _FakeUser:
    def __init__(self, role, is_super_admin=False):
        self.role = role
        self.is_super_admin = is_super_admin


def test_mapa_role_para_nivel_dos_usuarios_da_demo():
    # Numeração CANÔNICA (migração c7d9e1f2a3b4, 2026-07-03): 1 Admin, 2 Gerente,
    # 3 RH, 4 Estoque/Caixa (papéis fundidos), 5 Vendedor, 6 Entregador.
    assert _get_nivel(_FakeUser("ADMIN")) == 1
    assert _get_nivel(_FakeUser("GERENTE")) == 2
    assert _get_nivel(_FakeUser("RH")) == 3
    assert _get_nivel(_FakeUser("CAIXA")) == 4
    assert _get_nivel(_FakeUser("ESTOQUE")) == 4
    assert _get_nivel(_FakeUser("VENDEDOR")) == 5
    assert _get_nivel(_FakeUser("ENTREGADOR")) == 6
    # Super admin tem bypass total (nível 0)
    assert _get_nivel(_FakeUser("ADMIN", is_super_admin=True)) == 0


def test_admin_acessa_tudo_da_loja():
    admin = _FakeUser("ADMIN")
    for recurso in ["pdv", "estoque", "financeiro", "rh", "configuracoes", "fiscal", "relatorios"]:
        assert _check_resource(admin, recurso), f"admin deveria acessar {recurso}"


def test_caixa_opera_pdv_mas_nao_vendas_financeiro_ou_rh():
    # "vendas" (gestão/relatório de vendas) é diferente de "pdv" (operar o
    # caixa) — nivel 4 (Estoque/Caixa) só tem pdv, "vendas" é 1/2 (Admin/Gerente).
    caixa = _FakeUser("CAIXA")
    assert _check_resource(caixa, "pdv")
    assert _check_resource(caixa, "ponto")
    assert not _check_resource(caixa, "vendas")
    assert not _check_resource(caixa, "financeiro")
    assert not _check_resource(caixa, "rh")
    assert not _check_resource(caixa, "configuracoes")


def test_estoque_gerencia_produtos_e_opera_pdv_mas_nao_financeiro_nem_rh():
    # Numeração canônica funde Estoque e Caixa no mesmo nível (4) — por design,
    # ver migração c7d9e1f2a3b4: quem é "Estoque" também opera o PDV.
    estoque = _FakeUser("ESTOQUE")
    assert _check_resource(estoque, "estoque")
    assert _check_resource(estoque, "produtos")
    assert _check_resource(estoque, "entrada_xml")
    assert _check_resource(estoque, "fornecedores")
    assert _check_resource(estoque, "pdv")
    assert not _check_resource(estoque, "financeiro")
    assert not _check_resource(estoque, "rh")


def test_rh_acessa_folha_mas_nao_pdv_nem_estoque():
    rh = _FakeUser("RH")
    assert _check_resource(rh, "rh")
    assert _check_resource(rh, "folha")
    assert _check_resource(rh, "beneficios")
    assert _check_resource(rh, "ponto")
    assert not _check_resource(rh, "pdv")
    assert not _check_resource(rh, "estoque")
    assert not _check_resource(rh, "financeiro")


def test_vendedor_ve_clientes_e_produtos_mas_nao_caixa():
    vendedor = _FakeUser("VENDEDOR")
    assert _check_resource(vendedor, "clientes")
    assert _check_resource(vendedor, "produtos")
    assert not _check_resource(vendedor, "pdv")
    assert not _check_resource(vendedor, "financeiro")
    assert not _check_resource(vendedor, "configuracoes")


def test_configuracoes_e_exclusiva_do_admin():
    assert _check_resource(_FakeUser("ADMIN"), "configuracoes")
    for role in ["CAIXA", "ESTOQUE", "RH", "VENDEDOR", "GERENTE"]:
        assert not _check_resource(_FakeUser(role), "configuracoes"), (
            f"{role} não deveria acessar configurações"
        )
