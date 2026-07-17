from app.models import CategoriaProduto, Configuracao, Estabelecimento, Produto
from app.services.view_schema_service import (
    mix_permitido_para_estabelecimento,
    normalizar_familia_produto,
    resolver_view_schema,
)


def test_schema_contextual_respeita_mix_customizado(session):
    estab = session.query(Estabelecimento).first()
    estab.segmento = "mercearia"
    estab.configuracoes = {"mix_produtos": ["bazar", "alimento"]}
    session.commit()

    schema = resolver_view_schema(estab, familia_produto="bazar")

    assert schema["familia_produto"]["chave"] == "bazar"
    assert schema["familia_produto"]["perfil_fiscal_padrao"] == "bazar_padrao"
    assert schema["mix_permitido"] == ["bazar", "alimento"]
    assert schema["flags"]["usa_validade"] is False
    assert schema["flags"]["usa_embalagens"] is True


def test_familia_invalida_faz_fallback_para_primeiro_item_do_mix(session):
    estab = session.query(Estabelecimento).first()
    estab.segmento = "mercearia"
    estab.configuracoes = {"mix_produtos": ["bazar", "alimento"]}
    session.commit()

    familia = normalizar_familia_produto(
        familia_produto="autopecas",
        estabelecimento=estab,
        tipo_item="produto",
    )
    schema = resolver_view_schema(estab, familia_produto="autopecas")

    assert mix_permitido_para_estabelecimento(estab) == ["bazar", "alimento"]
    assert familia == "bazar"
    assert schema["familia_produto"]["chave"] == "bazar"


def test_servico_forca_familia_e_perfil_fiscal_de_servico(session):
    estab = session.query(Estabelecimento).first()
    estab.segmento = "autopecas"
    estab.configuracoes = {"mix_produtos": ["autopecas", "servico"]}
    session.commit()

    schema = resolver_view_schema(estab, familia_produto="autopecas", tipo_item="servico")

    assert schema["familia_produto"]["chave"] == "servico"
    assert schema["familia_produto"]["perfil_fiscal_padrao"] == "servico"
    assert "servico" in schema["tipos_item"]
    assert schema["flags"]["usa_servicos"] is True


def test_configuracao_to_dict_expoe_flag_de_foto_no_pdv(session):
    config = Configuracao(estabelecimento_id=1, mostrar_foto_produto_pdv=True)

    data = config.to_dict()

    assert data["mostrar_foto_produto_pdv"] is True


def test_produto_to_dict_expoe_familia_perfil_e_atributos(session):
    estab = session.query(Estabelecimento).first()
    categoria = CategoriaProduto(nome="Bazar", estabelecimento_id=estab.id)
    session.add(categoria)
    session.flush()
    produto = Produto(
        estabelecimento_id=estab.id,
        nome="Forma Antiaderente",
        categoria_id=categoria.id,
        preco_custo=10,
        preco_venda=19.9,
        quantidade=5,
        quantidade_minima=1,
        unidade_medida="un",
        familia_produto="bazar",
        perfil_fiscal="bazar_padrao",
    )
    produto.atributos = {"embalagem": "Unidade"}
    session.add(produto)
    session.commit()

    data = produto.to_dict()

    assert data["familia_produto"] == "bazar"
    assert data["perfil_fiscal"] == "bazar_padrao"
    assert data["atributos"] == {"embalagem": "Unidade"}
