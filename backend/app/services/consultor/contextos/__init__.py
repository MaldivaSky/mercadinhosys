"""Cache in-process para contextos dos especialistas do Consultor IA.

O contexto extraído para a IA usa as mesmas consultas dos dashboards.
Para evitar sobrecarga de agregação repetida e viabilizar a "IA ubíqua",
fazemos cache em memória do resultado.

Regra: TTL 300s (5 min) por (especialista, estabelecimento_id).
"""

import time
import threading

_TTL_SEGUNDOS = 300  # 5 min

_lock = threading.Lock()
# Chave: (especialista: str, estabelecimento_id: int, is_manager: bool)
# Valor: (timestamp_insercao: float, contexto: dict)
_cache: dict[tuple[str, int, bool], tuple[float, dict]] = {}


def obter_contexto(especialista: str, estabelecimento_id: int, is_manager: bool, builder_func) -> dict:
    """Busca o contexto do cache, ou recalcula se expirado."""
    try:
        key = (especialista, int(estabelecimento_id), is_manager)
    except (TypeError, ValueError):
        return {}

    now = time.monotonic()
    
    with _lock:
        hit = _cache.get(key)
        if hit and (now - hit[0]) < _TTL_SEGUNDOS:
            return hit[1]
            
    # Se não tem cache, calcula (fora do lock pra não bloquear requests de outros tenants)
    try:
        novo_contexto = builder_func(estabelecimento_id, is_manager) or {}
    except Exception as e:
        import traceback
        traceback.print_exc()
        novo_contexto = {"aviso": "Alguns dados não puderam ser carregados neste momento. Foque em dicas genéricas de gestão e ignore a ausência de métricas exatas."}
        
    with _lock:
        _cache[key] = (now, novo_contexto)
        
    return novo_contexto


def limpar_cache(estabelecimento_id: int = None):
    """Limpa o cache (usado para forçar refresh manual na API)."""
    with _lock:
        if estabelecimento_id is None:
            _cache.clear()
        else:
            keys_to_delete = [k for k in _cache.keys() if k[1] == int(estabelecimento_id)]
            for k in keys_to_delete:
                del _cache[k]
