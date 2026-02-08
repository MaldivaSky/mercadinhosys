from app.models import Cliente


def test_segmentar_rfm_campeao():
    assert Cliente.segmentar_rfm(5, 5, 5) == "Campeão"


def test_segmentar_rfm_fiel():
    assert Cliente.segmentar_rfm(5, 3, 1) == "Fiel"


def test_segmentar_rfm_risco():
    assert Cliente.segmentar_rfm(1, 4, 4) == "Risco"


def test_segmentar_rfm_perdido():
    assert Cliente.segmentar_rfm(1, 1, 1) == "Perdido"
