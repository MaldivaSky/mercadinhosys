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
    assert _get_nivel(_FakeUser("ADMIN")) == 1
    assert _get_nivel(_FakeUser("CAIXA")) == 3
    assert _get_nivel(_FakeUser("ESTOQUE")) == 4
    assert _get_nivel(_FakeUser("RH")) == 5
    assert _get_nivel(_FakeUser("VENDEDOR")) == 7
    # Super admin tem bypass total (nível 0)
    assert _get_nivel(_FakeUser("ADMIN", is_super_admin=True)) == 0


def test_admin_acessa_tudo_da_loja():
    admin = _FakeUser("ADMIN")
    for recurso in ["pdv", "estoque", "financeiro", "rh", "configuracoes", "fiscal", "relatorios"]:
        assert _check_resource(admin, recurso), f"admin deveria acessar {recurso}"


def test_caixa_opera_pdv_mas_nao_financeiro_nem_rh():
    caixa = _FakeUser("CAIXA")
    assert _check_resource(caixa, "pdv")
    assert _check_resource(caixa, "vendas")
    assert _check_resource(caixa, "ponto")
    assert not _check_resource(caixa, "financeiro")
    assert not _check_resource(caixa, "rh")
    assert not _check_resource(caixa, "configuracoes")


def test_estoque_gerencia_produtos_mas_nao_caixa_nem_financeiro():
    estoque = _FakeUser("ESTOQUE")
    assert _check_resource(estoque, "estoque")
    assert _check_resource(estoque, "produtos")
    assert _check_resource(estoque, "entrada_xml")
    assert _check_resource(estoque, "fornecedores")
    assert not _check_resource(estoque, "pdv")
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
