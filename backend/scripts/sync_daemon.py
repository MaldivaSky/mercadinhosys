"""
Sync Daemon — replicação local → Aiven em processo DEDICADO e ISOLADO.

Por que existe: rodar o sync dentro do worker do gunicorn é frágil (morre no
--reload, corre entre múltiplos workers, trava em transferências longas). Este
daemon roda em um container próprio, com um único runner, sobrevivendo a reloads
do servidor web.

Uso: python -m scripts.sync_daemon
Env:
  DATABASE_URL, AIVEN_DATABASE_URL  → conexões (já no ambiente do backend)
  SYNC_PUSH_INTERVAL_SEC            → intervalo entre ciclos (default 300s)
  SYNC_AUTO_PUSH                    → "false" desliga o daemon
"""
import os
import sys
import time
from datetime import datetime

# Garante que o pacote 'scripts' seja importável quando rodado como módulo
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.robust_sync import robust_sync as force_sync  # noqa: E402

INTERVAL = int(os.getenv("SYNC_PUSH_INTERVAL_SEC", "300"))


def _ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _heartbeat(status, total, dur, erro=None):
    """Grava o batimento do sync no Postgres local (lido por /api/sync/health)."""
    try:
        import psycopg2
        from scripts.force_sync_to_aiven import _parse_url
        conn = psycopg2.connect(**_parse_url(os.environ["DATABASE_URL"], force_no_ssl=True))
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO sync_heartbeat (id, last_run_at, status, total_registros, duracao_segundos, erro, updated_at)
               VALUES (1, (now() at time zone 'utc'), %s, %s, %s, %s, (now() at time zone 'utc'))
               ON CONFLICT (id) DO UPDATE SET last_run_at=EXCLUDED.last_run_at, status=EXCLUDED.status,
                   total_registros=EXCLUDED.total_registros, duracao_segundos=EXCLUDED.duracao_segundos,
                   erro=EXCLUDED.erro, updated_at=EXCLUDED.updated_at""",
            (status, total, round(float(dur), 2), (str(erro)[:2000] if erro else None)),
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[{_ts()}] [SYNC DAEMON] heartbeat falhou: {e}", flush=True)


def main() -> int:
    if os.getenv("SYNC_AUTO_PUSH", "true").lower() == "false":
        print(f"[{_ts()}] [SYNC DAEMON] desabilitado (SYNC_AUTO_PUSH=false). Encerrando.", flush=True)
        return 0
    if not os.getenv("DATABASE_URL") or not os.getenv("AIVEN_DATABASE_URL"):
        print(f"[{_ts()}] [SYNC DAEMON] DATABASE_URL/AIVEN_DATABASE_URL ausentes. Encerrando.", flush=True)
        return 0

    print(f"[{_ts()}] [SYNC DAEMON] iniciado — intervalo {INTERVAL}s (local → Aiven).", flush=True)
    # Pequena espera inicial para o Postgres/serviços subirem
    time.sleep(min(15, INTERVAL))

    while True:
        inicio = time.time()
        try:
            res = force_sync(silent=True)
            dur = time.time() - inicio
            if res.get("success"):
                total = res.get("total_registros", 0)
                print(f"[{_ts()}] [SYNC DAEMON] OK: {total} registros em {dur:.1f}s.", flush=True)
                _heartbeat("ok", total, dur)
            else:
                print(f"[{_ts()}] [SYNC DAEMON] FALHA: {res.get('erro')}", flush=True)
                _heartbeat("erro", 0, dur, res.get("erro"))
        except Exception as e:  # nunca deixa o loop morrer
            print(f"[{_ts()}] [SYNC DAEMON] ERRO no ciclo: {e}", flush=True)
            _heartbeat("erro", 0, time.time() - inicio, e)
        time.sleep(INTERVAL)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"[{_ts()}] [SYNC DAEMON] encerrado.", flush=True)
