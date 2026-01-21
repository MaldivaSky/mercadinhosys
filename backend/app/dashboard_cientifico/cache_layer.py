"""
Cache Layer - Cache inteligente com invalidação
Foco: Performance sem dados desatualizados
"""

import time
from typing import Any, Dict, Optional
from datetime import datetime, timedelta
import threading


class SmartCache:
    """
    Cache em memória com TTL (Time To Live) inteligente
    Para produção, usar Redis ou Memcached
    """

    _cache = {}
    _lock = threading.Lock()

    @classmethod
    def get(cls, key: str, max_age_seconds: int = 300) -> Optional[Any]:
        """
        Obtém valor do cache se não estiver expirado
        """
        with cls._lock:
            if key in cls._cache:
                entry = cls._cache[key]
                # Verificar se não expirou
                if time.time() - entry["timestamp"] < max_age_seconds:
                    return entry["data"]
                else:
                    # Remover se expirou
                    del cls._cache[key]
            return None

    @classmethod
    def set(cls, key: str, data: Any, ttl_seconds: int = 300) -> None:
        """
        Armazena valor no cache com TTL
        """
        with cls._lock:
            cls._cache[key] = {
                "data": data,
                "timestamp": time.time(),
                "expires_at": time.time() + ttl_seconds,
            }

            # Limitar tamanho do cache (LRU simples)
            if len(cls._cache) > 1000:
                # Remover o mais antigo
                oldest_key = min(
                    cls._cache.keys(), key=lambda k: cls._cache[k]["timestamp"]
                )
                del cls._cache[oldest_key]

    @classmethod
    def invalidate(cls, key: str) -> None:
        """Remove item do cache"""
        with cls._lock:
            if key in cls._cache:
                del cls._cache[key]

    @classmethod
    def invalidate_pattern(cls, pattern: str) -> None:
        """Remove todos os itens que correspondem ao padrão"""
        with cls._lock:
            keys_to_remove = [k for k in cls._cache.keys() if pattern in k]
            for key in keys_to_remove:
                del cls._cache[key]

    @classmethod
    def get_or_compute(cls, key: str, compute_func, ttl_seconds: int = 300) -> Any:
        """
        Obtém do cache ou calcula e armazena
        Pattern: Cache-Aside
        """
        # Tentar obter do cache
        cached = cls.get(key, ttl_seconds)
        if cached is not None:
            return cached

        # Calcular
        result = compute_func()

        # Armazenar no cache
        cls.set(key, result, ttl_seconds)

        return result


# Decorator para cache automático
def cache_response(ttl_seconds: int = 300):
    """
    Decorator para cache automático de respostas
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            # Criar chave única baseada nos argumentos
            import hashlib
            import pickle

            # Serializar argumentos para criar chave
            try:
                key_data = pickle.dumps((func.__name__, args, kwargs))
                key = hashlib.md5(key_data).hexdigest()
                cache_key = f"{func.__module__}.{func.__name__}:{key}"
            except:
                # Se não puder serializar, não usa cache
                return func(*args, **kwargs)

            # Usar cache inteligente
            return SmartCache.get_or_compute(
                cache_key, lambda: func(*args, **kwargs), ttl_seconds
            )

        return wrapper

    return decorator
