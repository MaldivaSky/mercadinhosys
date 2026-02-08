from app.dashboard_cientifico.models_layer import PracticalModels


def test_analyze_inventory_abc_truncates_payload_but_keeps_full_summary():
    products = [
        {"id": i, "nome": f"P{i}", "valor_total": 1.0, "quantidade": 1, "preco_custo": 0.5}
        for i in range(100)
    ]

    result = PracticalModels.analyze_inventory_abc(products, top_n=10)

    assert result["total_products"] == 100
    assert result["total_products_considered"] == 100
    assert result["returned_products"] == 10
    assert result["is_truncated"] is True

    assert result["resumo"]["A"]["quantidade"] == 80
    assert len(result["produtos"]) == 10


def test_analyze_inventory_abc_return_all_products_overrides_top_n():
    products = [
        {"id": i, "nome": f"P{i}", "valor_total": 1.0, "quantidade": 1, "preco_custo": 0.5}
        for i in range(100)
    ]

    result = PracticalModels.analyze_inventory_abc(products, top_n=10, return_all_products=True)

    assert result["returned_products"] == 100
    assert result["is_truncated"] is False
    assert len(result["produtos"]) == 100
