from datetime import timezone
import time
import threading
import requests
import os
from datetime import datetime
from app.models import db, SyncQueue, allow_all_tenants

class GuerrillaSyncWorker(threading.Thread):
    """
    Worker de segundo plano para Sincronização de Guerrilha.
    Detecta internet e despeja a fila de AuditoriaSincronia na nuvem.
    """
    
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.daemon = True
        self.intervalo_check = float(os.getenv("SYNC_INTERVAL_SEC", 30))
        self.max_retries = int(os.getenv("SYNC_MAX_RETRIES", 3))
        self.cloud_api_url = os.getenv("CLOUD_API_URL", "").rstrip("/")
        self.sync_token = os.getenv("CLOUD_SYNC_TOKEN", "")
        
    def check_internet(self):
        """Verifica conectividade com a nuvem"""
        if not self.cloud_api_url:
            self.app.logger.warning("CLOUD_API_URL nao configurada. Worker de sync nao pode validar conectividade.")
            return False
        try:
            requests.get(self.cloud_api_url, timeout=5)
            return True
        except:
            return False

    def sync_deltas(self):
        """Processa a fila de sincronização (cross-tenant: a fila abrange todas as
        lojas, então o acesso global é explicitado via allow_all_tenants)."""
        with self.app.app_context(), allow_all_tenants():
            pendentes = SyncQueue.query.filter_by(status="pendente").order_by(SyncQueue.created_at.asc()).limit(50).all()
            
            if not pendentes:
                return

            self.app.logger.info(f"🔄 Sincronizador: Processando {len(pendentes)} mutações...")
            
            for sync_item in pendentes:
                try:
                    res = self.envio_para_nuvem(sync_item)
                    self.app.logger.info(f"📡 Item {sync_item.id} -> {sync_item.tabela}: Envio {'SUCESSO' if res else 'FALHA'}")
                    if res:
                        sync_item.status = "sincronizado"
                        sync_item.synced_at = datetime.now(timezone.utc)
                        sync_item.mensagem_erro = None
                    else:
                        sync_item.tentativas += 1
                        if sync_item.tentativas >= self.max_retries:
                            sync_item.status = "erro"
                            sync_item.mensagem_erro = "Maximo de tentativas atingido"
                except Exception as e:
                    self.app.logger.error(f"❌ Erro individual no item {sync_item.id}: {e}")
                    sync_item.tentativas += 1
                    sync_item.mensagem_erro = str(e)
                    if sync_item.tentativas >= self.max_retries:
                        sync_item.status = "erro"
            
            try:
                db.session.commit()
                self.app.logger.info("💾 Sincronizador: Commit realizado na fila local.")
            except Exception as e:
                db.session.rollback()
                self.app.logger.error(f"💥 Erro no commit da fila: {e}")

    def envio_para_nuvem(self, sync_item):
        """Simula ou executa o envio do delta para o banco central"""
        if not self.cloud_api_url or not self.sync_token:
            self.app.logger.error(
                "Sincronizacao cloud indisponivel: CLOUD_API_URL ou CLOUD_SYNC_TOKEN nao configurados."
            )
            return False

        try:
            resp = requests.post(
                f"{self.cloud_api_url}/api/sync/receive",
                json=sync_item.to_sync_payload(),
                timeout=15,
                headers={
                    "Authorization": f"Bearer {self.sync_token}",
                    "Content-Type": "application/json"
                }
            )
            return resp.status_code == 200
        except Exception as exc:
            self.app.logger.error(f"Falha ao enviar item {sync_item.id} para a nuvem: {exc}")
            return False

    def run(self):
        """Loop principal do worker"""
        self.app.logger.info(f"📡 Worker de Sincronia de Guerrilha iniciado (Frequência: {self.intervalo_check}s)")
        
        while True:
            if self.check_internet():
                try:
                    self.sync_deltas()
                except Exception as e:
                    self.app.logger.error(f"❌ Erro durante sincronização: {str(e)}")
            else:
                self.app.logger.warning("📶 Sem internet. Aguardando sinal para sincronizar...")
                
            time.sleep(self.intervalo_check)

    def process_queue(self):
        """Processa a fila uma vez, usado por CLI e smoke tests."""
        with self.app.app_context():
            self.sync_deltas()

def start_sync_worker(app):
    """Entry point para iniciar o worker sem travar o Flask"""
    worker = GuerrillaSyncWorker(app)
    if not worker.cloud_api_url or not worker.sync_token:
        app.logger.warning("Worker de sync nao iniciado: configuracao cloud incompleta.")
        return None
    worker.start()
    return worker
