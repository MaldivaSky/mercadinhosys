"""
IA Copiloto — Groq Cloud (api.groq.com, tier gratuito, formato compatível OpenAI).

Uso genérico: qualquer feature do sistema que precise de um texto gerado por
IA (mensagem de cliente, explicação de indicador, resumo diário) passa por
`gerar_texto()`. Sem GROQ_API_KEY configurada, retorna None e quem chamou
decide o fallback (aqui: usar o template fixo) — nunca quebra a tela.
"""
import os
import requests

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
TIMEOUT_SEGUNDOS = 15


def ia_disponivel() -> bool:
    return bool(os.getenv("GROQ_API_KEY"))


def gerar_texto(system_prompt: str, user_prompt: str, max_tokens: int = 300) -> str | None:
    """Chama a Groq Cloud (formato de chat compatível com a API da OpenAI).
    Retorna None em qualquer falha (sem chave, rede, erro da API) — o
    chamador deve ter um fallback pronto (nunca deixar a tela sem resposta)."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None
    try:
        resp = requests.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "max_tokens": max_tokens,
                "temperature": 0.7,
            },
            timeout=TIMEOUT_SEGUNDOS,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception:
        return None
