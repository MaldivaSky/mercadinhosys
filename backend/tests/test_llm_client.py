import pytest
from unittest.mock import patch, MagicMock
import os
from app.utils.llm_client import gerar_resposta, llm_disponivel, PROVIDERS

def test_llm_indisponivel(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    
    assert not llm_disponivel()
    assert gerar_resposta([{"role": "user", "content": "teste"}]) is None

@patch("app.utils.llm_client.requests.post")
def test_gerar_resposta_sucesso(mock_post, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake_gemini_key")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-2.5-flash")
    
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "Resposta do Gemini"}}]
    }
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response
    
    resultado = gerar_resposta([{"role": "user", "content": "Oi"}], provider="gemini")
    assert resultado == "Resposta do Gemini"
    mock_post.assert_called_once()
    assert "fake_gemini_key" in mock_post.call_args[1]["headers"]["Authorization"]

@patch("app.utils.llm_client.requests.post")
def test_fallback_automatico(mock_post, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake_gemini_key")
    monkeypatch.setenv("GROQ_API_KEY", "fake_groq_key")
    
    # Simula erro no provedor primário (Gemini)
    mock_post.side_effect = [Exception("Erro Gemini"), MagicMock(
        json=lambda: {"choices": [{"message": {"content": "Resposta do Groq"}}]},
        raise_for_status=lambda: None
    )]
    
    resultado = gerar_resposta([{"role": "user", "content": "Oi"}], provider="gemini")
    
    # Verifica se caiu no fallback (Groq)
    assert resultado == "Resposta do Groq"
    assert mock_post.call_count == 2
