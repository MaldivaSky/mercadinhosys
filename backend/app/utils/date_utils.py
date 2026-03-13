from datetime import datetime, timedelta, timezone

def get_now_manaus():
    """Retorna o datetime atual no fuso horário de Manaus (Amazônia - UTC-4) como naive para compatibilidade com DB"""
    tz_manaus = timezone(timedelta(hours=-4))
    return datetime.now(tz_manaus).replace(tzinfo=None)
