"""
Utilitário de timezone para EXIBIÇÃO.

O banco grava tudo em UTC "naive" (datetime.utcnow). Para o usuário, datas e
horas precisam aparecer no fuso local da loja. O Brasil (São Paulo) é UTC-3
fixo desde 2019 (fim do horário de verão), então usamos um offset fixo — sem
depender de `tzdata`/`zoneinfo` (que falta no Windows) e sem lógica de DST.

Configurável por env APP_UTC_OFFSET_HOURS (ex.: -4 para Manaus).
"""
import os
from datetime import datetime, timezone, timedelta

_OFFSET_HORAS = int(os.getenv("APP_UTC_OFFSET_HOURS", "-3"))
LOCAL_TZ = timezone(timedelta(hours=_OFFSET_HORAS))


def to_local(dt):
    """Converte um datetime UTC (naive ou aware) para o fuso local (aware)."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(LOCAL_TZ)


def fmt_local(dt, fmt="%d/%m/%Y %H:%M"):
    """Formata um datetime UTC no fuso local. Retorna '' se None."""
    loc = to_local(dt)
    return loc.strftime(fmt) if loc else ""


def iso_local(dt):
    """ISO 8601 já no fuso local, COM offset (ex.: 2026-07-03T14:30:00-03:00).
    Assim o navegador (new Date(...)) exibe a hora local correta."""
    loc = to_local(dt)
    return loc.isoformat() if loc else None
