"""
app/middleware/rate_limit.py
Configuração de Rate Limiting
"""

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask import request


def get_identifier():
    """Identifica o usuário para rate limiting"""
    # Tenta pegar o token JWT se existir
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header.split(" ")[1][:20]  # Usa parte do token
    # Senão usa o IP
    return get_remote_address()


limiter = Limiter(
    key_func=get_identifier,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",  # Para produção use Redis: "redis://localhost:6379"
)

# Configurações específicas por tipo de endpoint
RATE_LIMITS = {
    "auth": "5 per minute",  # Login limitado
    "create": "30 per minute",  # Criação de recursos
    "read": "100 per minute",  # Leitura
    "update": "30 per minute",  # Atualização
    "delete": "20 per minute",  # Deleção
}

