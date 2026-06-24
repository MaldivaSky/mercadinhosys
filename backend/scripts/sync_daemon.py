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
            if res.get("success"):
                print(f"[{_ts()}] [SYNC DAEMON] OK: {res.get('total_registros', 0)} registros "
                      f"em {time.time() - inicio:.1f}s.", flush=True)
            else:
                print(f"[{_ts()}] [SYNC DAEMON] FALHA: {res.get('erro')}", flush=True)
        except Exception as e:  # nunca deixa o loop morrer
            print(f"[{_ts()}] [SYNC DAEMON] ERRO no ciclo: {e}", flush=True)
        time.sleep(INTERVAL)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"[{_ts()}] [SYNC DAEMON] encerrado.", flush=True)
