from datetime import datetime, timedelta


from app.dashboard_cientifico.orchestration import DashboardOrchestrator
from app.dashboard_cientifico import orchestration as orch_module


def test_scientific_dashboard_has_recommendations_and_homologous_growth(monkeypatch):
    calls = {"range": 0}

    def fake_sales_summary_range(est_id, start_date, end_date):
        calls["range"] += 1
        if calls["range"] == 1:
            return {
                "total_vendas": 20,
                "total_faturado": 1000.0,
                "ticket_medio": 50.0,
                "dias_com_venda": 7,
                "periodo_dias": (end_date - start_date).days,
                "maior_venda": 200.0,
                "menor_venda": 10.0,
            }
        return {
            "total_vendas": 30,
            "total_faturado": 2000.0,
            "ticket_medio": 66.0,
            "dias_com_venda": 7,
            "periodo_dias": (end_date - start_date).days,
            "maior_venda": 300.0,
            "menor_venda": 10.0,
        }

    monkeypatch.setattr(orch_module.DataLayer, "get_sales_summary_range", fake_sales_summary_range)
    monkeypatch.setattr(
        orch_module.DataLayer,
        "get_inventory_summary",
        lambda est_id: {"baixo_estoque": 5, "valor_total": 10000.0, "lucro_potencial": 1000.0, "total_produtos": 10},
    )
    monkeypatch.setattr(
        orch_module.DataLayer,
        "get_customer_metrics",
        lambda est_id, days: {"clientes_unicos": 10, "ticket_medio_cliente": 30.0, "maior_compra": 200.0, "frequencia_media": 1.0},
    )
    monkeypatch.setattr(
        orch_module.DataLayer,
        "get_sales_timeseries",
        lambda est_id, days: [
            {"data": (datetime(2026, 1, 1) + timedelta(days=i)).strftime("%Y-%m-%d"), "total": 100.0}
            for i in range(7)
        ],
    )

    monkeypatch.setattr(
        DashboardOrchestrator,
        "get_abc_analysis",
        lambda self, days=30, limit=200: {"resumo": {"A": {"margem_media": 10.0}, "B": {"margem_media": 20.5}}},
    )
    monkeypatch.setattr(
        DashboardOrchestrator,
        "get_rfm_analysis",
        lambda self, window_days=180: {"segments": {"Risco": 15, "Perdido": 0}, "customers": [], "window_days": 180},
    )

    orch = DashboardOrchestrator(1)
    result = orch.get_scientific_dashboard(days=7)

    assert result["success"] is True
    assert "recomendacoes" in result
    assert any(r["tipo"] == "retencao" for r in result["recomendacoes"])
    assert any(r["tipo"] == "estoque" for r in result["recomendacoes"])
    assert any(r["tipo"] == "margem" for r in result["recomendacoes"])
    assert result["summary"]["growth"]["value"] is not None
