from app import db
from app.dashboard_cientifico.data_layer import DataLayer


def test_get_inventory_summary_uses_wac_query(monkeypatch):
    captured = {}

    def fake_execute(query, params):
        captured["sql"] = str(query)
        captured["params"] = params

        class Row:
            total_produtos = 2
            total_unidades = 10
            valor_total = 100.0
            custo_total = 60.0
            estoque_medio = 5.0
            baixo_estoque = 0
            sem_estoque = 0
            produtos_com_wac = 1

        class Result:
            def first(self):
                return Row()

        return Result()

    monkeypatch.setattr(db.session, "execute", fake_execute)

    result = DataLayer.get_inventory_summary(estabelecimento_id=1)

    assert "WITH wac AS" in captured["sql"]
    assert "data_inicio" in captured["params"]
    assert result["lucro_potencial"] == 40.0
    assert result["produtos_com_wac"] == 1
    assert result["wac_days"] == 365
