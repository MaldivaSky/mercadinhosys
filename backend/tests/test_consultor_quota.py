import pytest
from unittest.mock import patch, MagicMock
from app.services.consultor.quota import verificar_quota_consultor, verificar_quota_insight, CONSULTOR_LIMITE_DIA, INSIGHT_LIMITE_DIA

@patch("app.services.consultor.quota._contar_interacoes_hoje")
def test_quota_consultor(mock_contar):
    # Simula consumo dentro do limite
    mock_contar.return_value = CONSULTOR_LIMITE_DIA - 1
    assert verificar_quota_consultor(1) is True
    
    # Simula consumo atingindo limite
    mock_contar.return_value = CONSULTOR_LIMITE_DIA
    assert verificar_quota_consultor(1) is False

@patch("app.services.consultor.quota._contar_insights_hoje")
def test_quota_insight(mock_contar):
    # Simula consumo dentro do limite
    mock_contar.return_value = INSIGHT_LIMITE_DIA - 1
    assert verificar_quota_insight(1) is True
    
    # Simula consumo atingindo limite
    mock_contar.return_value = INSIGHT_LIMITE_DIA
    assert verificar_quota_insight(1) is False

def test_sem_estabelecimento():
    assert verificar_quota_consultor(None) is False
    assert verificar_quota_insight(None) is False
