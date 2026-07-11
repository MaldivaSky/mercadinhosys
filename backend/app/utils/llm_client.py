"""Cliente LLM multi-provedor (formato OpenAI chat completions).

Groq  -> respostas rápidas (roteador, chat curto)
Gemini-> análises com contexto grande (especialistas)
Regra: falhou/sem chave -> tenta o outro provedor -> None. Chamador SEMPRE
tem fallback (padrão do sistema: nunca deixar a tela sem resposta).
"""

import os
import requests
import logging

logger = logging.getLogger(__name__)

PROVIDERS = {
    "groq": {
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "key_env": "GROQ_API_KEY",
        "model_env": "GROQ_MODEL",
        "model_default": "llama-3.3-70b-versatile",
    },
    "gemini": {
        "url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "key_env": "GEMINI_API_KEY",
        "model_env": "GEMINI_MODEL",
        "model_default": "gemini-2.5-flash",
    },
}

TIMEOUT_SEGUNDOS = 30


def llm_disponivel() -> bool:
    """Verifica se pelo menos um provedor está configurado."""
    return bool(os.getenv("GROQ_API_KEY") or os.getenv("GEMINI_API_KEY"))


def _chamar_provedor(messages: list[dict], provider_key: str, max_tokens: int, temperature: float) -> str | None:
    provider = PROVIDERS.get(provider_key)
    if not provider:
        return None
        
    api_key = os.getenv(provider["key_env"])
    if not api_key:
        return None

    try:
        model = os.getenv(provider["model_env"], provider["model_default"])
        
        # O Gemini no endpoint compatível com OpenAI (v1beta/openai/chat/completions)
        # e o Groq ambos aceitam o mesmo formato de headers (Bearer token)
        # exceto que o Gemini pode precisar do cabeçalho x-goog-api-key caso o Bearer falhe,
        # mas na doc da OpenAI compatibility do Gemini o Bearer auth com a key costuma funcionar.
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        # O modelo Gemini requer a key no formato compatível, testar com Bearer.
        resp = requests.post(
            provider["url"],
            headers=headers,
            json={
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
            timeout=TIMEOUT_SEGUNDOS,
        )
        
        resp.raise_for_status()
        data = resp.json()
        if "choices" in data and len(data["choices"]) > 0:
            return data["choices"][0]["message"]["content"].strip()
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro na API {provider_key}: {e}")
    except Exception as e:
        logger.error(f"Erro inesperado no cliente LLM ({provider_key}): {e}")
        
    return None


def gerar_resposta(messages: list[dict], provider: str = "gemini",
                   max_tokens: int = 1024, temperature: float = 0.4) -> str | None:
    """Gera resposta com fallback automático.
    
    1) tenta provider pedido;
    2) se sem chave/erro, tenta o outro;
    3) None.
    """
    if not llm_disponivel():
        return None

    # Tenta o provedor primário
    resposta = _chamar_provedor(messages, provider, max_tokens, temperature)
    if resposta is not None:
        return resposta

    # Tenta o fallback
    fallback_provider = "groq" if provider == "gemini" else "gemini"
    logger.warning(f"Provedor {provider} falhou. Tentando fallback para {fallback_provider}...")
    
    return _chamar_provedor(messages, fallback_provider, max_tokens, temperature)
