"""
Backup lógico do Aiven (pg_dump) com rotação.

Observação: o Aiven é um serviço gerenciado e JÁ faz backups automáticos
(diários + PITR). Este script é uma camada extra (cópia off-site/local),
útil para auditoria e restauração rápida.

Uso:   python -m scripts.backup_aiven
Env:   AIVEN_DATABASE_URL, BACKUP_DIR (default /app/backups), BACKUP_KEEP (default 14)
Agende via cron/Task Scheduler (ex.: diário às 03:00).
"""
import os
import sys
import gzip
import glob
import subprocess
from datetime import datetime

BACKUP_DIR = os.getenv("BACKUP_DIR", "/app/backups")
KEEP = int(os.getenv("BACKUP_KEEP", "14"))


def _ts():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def main() -> int:
    url = os.getenv("AIVEN_DATABASE_URL")
    if not url:
        print(f"[{_ts()}] [BACKUP] AIVEN_DATABASE_URL ausente. Abortando.", flush=True)
        return 1
    url = url.replace("postgres://", "postgresql://", 1)
    os.makedirs(BACKUP_DIR, exist_ok=True)
    destino = os.path.join(BACKUP_DIR, f"aiven_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql.gz")

    print(f"[{_ts()}] [BACKUP] iniciando pg_dump → {destino}", flush=True)
    try:
        proc = subprocess.Popen(
            ["pg_dump", "--no-owner", "--no-acl", "--clean", "--if-exists", url],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        with gzip.open(destino, "wb") as fh:
            for chunk in iter(lambda: proc.stdout.read(65536), b""):
                fh.write(chunk)
        err = proc.stderr.read().decode(errors="replace")
        rc = proc.wait()
        if rc != 0:
            print(f"[{_ts()}] [BACKUP] FALHOU (rc={rc}): {err[:300]}", flush=True)
            try: os.remove(destino)
            except OSError: pass
            return rc
        tam = os.path.getsize(destino) / (1024 * 1024)
        print(f"[{_ts()}] [BACKUP] OK: {destino} ({tam:.2f} MB)", flush=True)
    except FileNotFoundError:
        print(f"[{_ts()}] [BACKUP] pg_dump não encontrado no container.", flush=True)
        return 1
    except Exception as e:
        print(f"[{_ts()}] [BACKUP] erro: {e}", flush=True)
        return 1

    # Rotação: mantém os KEEP mais recentes
    arquivos = sorted(glob.glob(os.path.join(BACKUP_DIR, "aiven_*.sql.gz")))
    for antigo in arquivos[:-KEEP]:
        try:
            os.remove(antigo)
            print(f"[{_ts()}] [BACKUP] rotacionado (removido): {os.path.basename(antigo)}", flush=True)
        except OSError:
            pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
