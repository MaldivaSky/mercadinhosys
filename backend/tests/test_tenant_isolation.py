"""
Testes de ISOLAMENTO MULTI-TENANT.

Objetivo: provar, de forma automatizada, que um tenant (loja) nunca enxerga
dados de outro através da camada ORM (TenantQuery). Estes testes documentam
o comportamento ESPERADO (seguro). Se algum falhar, há um vazamento real.

Estratégia: criar dois estabelecimentos (A e B), cada um com 1 produto, e
verificar que, com o contexto de tenant fixado em A (g.estabelecimento_id = A),
NENHUM método de consulta retorna o produto de B.
"""
import pytest
from datetime import date
from decimal import Decimal
from flask import g

from app import db
from app.models import Estabelecimento, Produto, CategoriaProduto


import random as _random


def _novo_estab(nome):
    cnpj = f"{_random.randint(10**12, 10**13 - 1)}"
    estab = Estabelecimento(
        nome_fantasia=nome,
        razao_social=f"{nome} LTDA",
        cnpj=cnpj,
        email=f"{nome.lower().replace(' ','')}_{cnpj[-4:]}@iso.test",
        telefone="92999999999",
        data_abertura=date(2024, 1, 1),
        plano="PREMIUM",
        cep="69000-000", logradouro="Rua X", numero="1",
        bairro="Centro", cidade="Manaus", estado="AM", pais="Brasil",
    )
    db.session.add(estab)
    db.session.flush()
    return estab


def _novo_produto(estab_id, nome):
    cat = CategoriaProduto(estabelecimento_id=estab_id, nome=f"Cat {nome}")
    db.session.add(cat)
    db.session.flush()
    p = Produto(
        estabelecimento_id=estab_id,
        categoria_id=cat.id,
        nome=nome,
        preco_venda=Decimal("10.00"),
        preco_custo=Decimal("5.00"),
        quantidade=100,
    )
    db.session.add(p)
    db.session.flush()
    return p


@pytest.fixture
def dois_tenants(session):
    """Cria tenant A e B, cada um com 1 produto de nome distinto."""
    a = _novo_estab("Loja A")
    b = _novo_estab("Loja B")
    _novo_produto(a.id, "Produto Exclusivo A")
    _novo_produto(b.id, "Produto Exclusivo B")
    db.session.commit()
    return a, b


def _fixar_tenant(estab_id):
    """Simula o que o before_request faz: fixa o tenant atual em g."""
    g.estabelecimento_id = estab_id


# ---------------------------------------------------------------------------
# BASELINE — o que já funciona hoje
# ---------------------------------------------------------------------------
def test_all_eh_isolado(dois_tenants):
    """.all() JÁ é filtrado por tenant (baseline verde)."""
    a, b = dois_tenants
    _fixar_tenant(a.id)
    nomes = {p.nome for p in Produto.query.all()}
    assert "Produto Exclusivo A" in nomes
    assert "Produto Exclusivo B" not in nomes, "VAZAMENTO: .all() retornou produto de outro tenant"


# ---------------------------------------------------------------------------
# BURACO #1 — cobertura parcial de métodos (.first / .count / iteração)
# ---------------------------------------------------------------------------
def test_first_eh_isolado(dois_tenants):
    """Buscar por nome do produto de B, no contexto de A, deve retornar None."""
    a, b = dois_tenants
    _fixar_tenant(a.id)
    achado = Produto.query.filter_by(nome="Produto Exclusivo B").first()
    assert achado is None, "VAZAMENTO: .first() retornou produto de outro tenant"


def test_count_eh_isolado(dois_tenants):
    a, b = dois_tenants
    _fixar_tenant(a.id)
    assert Produto.query.count() == 1, "VAZAMENTO: .count() contou produtos de outros tenants"


def test_iteracao_eh_isolada(dois_tenants):
    a, b = dois_tenants
    _fixar_tenant(a.id)
    nomes = {p.nome for p in Produto.query}  # iteração direta
    assert "Produto Exclusivo B" not in nomes, "VAZAMENTO: iterar a query retornou outro tenant"


# ---------------------------------------------------------------------------
# BURACO #2 — fail-open: sem contexto de tenant, não pode despejar tudo
# ---------------------------------------------------------------------------
@pytest.mark.xfail(
    reason="P0 conhecido: fail-open. Sem tenant em 'g', a query nao filtra (legado). "
           "Fechar exige garantir g.estabelecimento_id em TODA rota autenticada sem "
           "quebrar login/rotas publicas/super-admin. Rastreado para a proxima etapa.",
    strict=True,
)
def test_sem_contexto_nao_vaza_tudo(dois_tenants):
    """
    Se g.estabelecimento_id NÃO estiver setado (ex.: before_request falhou),
    a query NÃO pode retornar dados de todos os tenants. Deve falhar fechado.
    """
    a, b = dois_tenants
    if hasattr(g, "estabelecimento_id"):
        delattr(g, "estabelecimento_id")
    resultado = Produto.query.all()
    assert len(resultado) == 0, (
        "FAIL-OPEN: sem contexto de tenant a query retornou "
        f"{len(resultado)} produtos de todos os tenants"
    )
