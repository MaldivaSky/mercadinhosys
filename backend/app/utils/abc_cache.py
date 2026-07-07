"""Cache in-process da classificação ABC por tenant.

A classificação ABC exige agregar venda_itens do período — caro demais para
rodar a cada request de listagem/estatística (era a principal causa de lentidão
da página de Produtos). Aqui o cálculo roda no máximo uma vez a cada TTL por
estabelecimento e todos os consumidores (lista, filtros rápidos, cards) leem o
MESMO resultado, garantindo que card e lista nunca divirjam.

Regra de negócio: ABC por faturamento em janela móvel de 90 dias (padrão de
varejo alimentar — histórico completo distorce: produto que vendeu muito há um
ano continuaria classe A para sempre).

Cache por processo (gunicorn multi-worker terá um cache por worker); TTL curto
mantém a divergência entre workers irrelevante na prática.
"""

import time
import threading

ABC_PERIODO_DIAS = 90
_TTL_SEGUNDOS = 600  # 10 min

_lock = threading.Lock()
_cache: dict[int, tuple[float, dict]] = {}


def get_classificacoes_abc(estabelecimento_id) -> dict:
    """Retorna {produto_id: 'A'|'B'|'C'} do tenant, cacheado por TTL.

    Produtos sem venda no período não aparecem no dict — o chamador decide
    como tratá-los (a convenção do sistema é classe C / "encalhado").
    """
    try:
        key = int(estabelecimento_id)
    except (TypeError, ValueError):
        # 'all' (super admin) não tem classificação dinâmica por tenant
        return {}

    now = time.monotonic()
    hit = _cache.get(key)
    if hit and (now - hit[0]) < _TTL_SEGUNDOS:
        return hit[1]

    from app.models import Produto

    classificacoes = Produto.calcular_classificacao_abc_dinamica(
        key, periodo_dias=ABC_PERIODO_DIAS
    ) or {}
    with _lock:
        _cache[key] = (now, classificacoes)
    return classificacoes


def invalidar(estabelecimento_id=None):
    """Invalida o cache (de um tenant ou todos) — usar após recálculo manual."""
    with _lock:
        if estabelecimento_id is None:
            _cache.clear()
        else:
            _cache.pop(int(estabelecimento_id), None)
