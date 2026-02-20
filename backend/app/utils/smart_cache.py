# app/utils/smart_cache.py
"""
SmartCache - Cache de Elite para MercadinhoSys
Cache em memória simples e eficiente para reduzir latência em consultas de infraestrutura.
"""

import time
import threading
from flask import current_app

class SmartCache:
    _cache = {}
    _lock = threading.Lock()
    _default_ttl = 300  # 5 minutos

    @classmethod
    def get(cls, key):
        """Busca valor no cache com verificação de expiração"""
        with cls._lock:
            if key in cls._cache:
                entry = cls._cache[key]
                if time.time() < entry['expiry']:
                    return entry['value']
                else:
                    del cls._cache[key]
        return None

    @classmethod
    def set(cls, key, value, ttl=None):
        """Armazena valor no cache com TTL customizado"""
        ttl = ttl if ttl is not None else cls._default_ttl
        with cls._lock:
            cls._cache[key] = {
                'value': value,
                'expiry': time.time() + ttl
            }

    @classmethod
    def delete(cls, key):
        """Remove item específico do cache"""
        with cls._lock:
            if key in cls._cache:
                del cls._cache[key]

    @classmethod
    def clear(cls):
        """Limpa todo o cache"""
        with cls._lock:
            cls._cache.clear()

# Atalhos específicos para Configuração
def get_cached_config(estabelecimento_id):
    return SmartCache.get(f"config_{estabelecimento_id}")

def set_cached_config(estabelecimento_id, config_data):
    SmartCache.set(f"config_{estabelecimento_id}", config_data)

def invalidate_config(estabelecimento_id):
    SmartCache.delete(f"config_{estabelecimento_id}")
