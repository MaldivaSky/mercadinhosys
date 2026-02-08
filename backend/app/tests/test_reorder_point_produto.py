from app.models import Produto


def test_ponto_ressuprimento_returns_zero_without_lead_time(monkeypatch):
    p = Produto()
    assert p.ponto_ressuprimento(lead_time_dias=0) == 0.0
    assert p.ponto_ressuprimento(lead_time_dias=None) == 0.0


def test_ponto_ressuprimento_uses_demanda_media(monkeypatch):
    p = Produto()

    monkeypatch.setattr(p, "demanda_media_diaria", lambda days=30: 4.0)

    assert p.ponto_ressuprimento(lead_time_dias=10, days=30, fator_seguranca=1.5) == 60.0
