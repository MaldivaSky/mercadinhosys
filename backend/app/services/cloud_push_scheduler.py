"""
Cloud Push Scheduler — Sincronização automática local -> Aiven a cada 30 min.

Local-first: a loja opera no banco local e este agendador empurra os dados
para a nuvem (Aiven) em intervalos regulares usando o motor bulk force_sync.

Só roda quando:
  - DATABASE_URL e AIVEN_DATABASE_URL estão definidos E são diferentes
    (ou seja, estamos numa instância LOCAL, não no próprio cloud), e
  - SYNC_AUTO_PUSH != "false".
"""
import os
import time
import threading

DEFAULT_INTERVAL = int(os.getenv("SYNC_PUSH_INTERVAL_SEC", "1800"))  # 30 min


class CloudPushScheduler(threading.Thread):
    def __init__(self, app, interval_sec: int = DEFAULT_INTERVAL):
        super().__init__()
        self.app = app
        self.daemon = True
        self.interval = interval_sec

    def _deve_rodar(self) -> bool:
        local = os.getenv("DATABASE_URL")
        aiven = os.getenv("AIVEN_DATABASE_URL")
        if os.getenv("SYNC_AUTO_PUSH", "true").lower() == "false":
            return False
        if not local or not aiven:
            return False
        # Mesma URL => estamos no próprio cloud; não faz sentido auto-push
        return local.strip() != aiven.strip()

    def run(self):
        self.app.logger.info(
            f"[CLOUD PUSH] Agendador iniciado (intervalo {self.interval}s, local -> Aiven)."
        )
        # Espera inicial para não competir com o boot
        time.sleep(min(120, self.interval))
        while True:
            try:
                from scripts.force_sync_to_aiven import force_sync
                with self.app.app_context():
                    res = force_sync(app=self.app, silent=True)
                if res.get("success"):
                    self.app.logger.info(
                        f"[CLOUD PUSH] OK: {res.get('total_registros', 0)} registros enviados ao Aiven."
                    )
                else:
                    self.app.logger.warning(f"[CLOUD PUSH] Falha: {res.get('erro')}")
            except Exception as e:
                self.app.logger.error(f"[CLOUD PUSH] Erro no ciclo: {e}")
            time.sleep(self.interval)


def start_cloud_push_scheduler(app):
    """Inicia o agendador se as condições forem atendidas. Retorna a thread ou None."""
    scheduler = CloudPushScheduler(app)
    if not scheduler._deve_rodar():
        app.logger.info("[CLOUD PUSH] Agendador NÃO iniciado (cloud/instância única ou desabilitado).")
        return None
    scheduler.start()
    return scheduler
