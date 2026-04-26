from datetime import timezone
import time
import threading
import requests
import os
import json
from datetime import datetime
from sqlalchemy import create_engine
from app.models import db, AuditoriaSincronia, Estabelecimento
from flask import current_app

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
        self.cloud_api_url = os.getenv("CLOUD_API_URL") # URL da API na nuvem para receber os deltas
        
    def check_internet(self):
        """Verifica conectividade com a nuvem"""
        try:
            # Tenta pingar a API da nuvem ou o Google como fallback
            target = self.cloud_api_url if self.cloud_api_url else "https://www.google.com"
            requests.get(target, timeout=5)
            return True
        except:
            return False

    def sync_deltas(self):
        """Processa a fila de sincronização"""
        with self.app.app_context():
            pendentes = AuditoriaSincronia.query.filter_by(status="pendente").order_by(SyncQueue.created_at.asc()).limit(50).all()
            
            if not pendentes:
                return

            print(f"🔄 Sincronizador: Processando {len(pendentes)} mutações...")
            
            for sync_item in pendentes:
                try:
                    res = self.envio_para_nuvem(sync_item)
                    print(f"📡 Item {sync_item.id} -> {sync_item.tabela}: Envio {'SUCESSO' if res else 'FALHA'}")
                    if res:
                        sync_item.status = "sincronizado"
                        sync_item.data_sincronia = datetime.now(timezone.utc)
                    else:
                        sync_item.tentativas += 1
                        if sync_item.tentativas > 5:
                            sync_item.status = "erro"
                            sync_item.msg_erro = "Máximo de tentativas atingido"
                except Exception as e:
                    print(f"❌ Erro individual no item {sync_item.id}: {e}")
                    sync_item.tentativas += 1
                    sync_item.msg_erro = str(e)
            
            try:
                db.session.commit()
                print("💾 Sincronizador: Commit realizado na fila local.")
            except Exception as e:
                db.session.rollback()
                print(f"💥 Erro no commit da fila: {e}")

    def envio_para_nuvem(self, sync_item):
        """Simula ou executa o envio do delta para o banco central"""
        # Se CLOUD_API_URL estiver configurado, faz o POST real
        if self.cloud_api_url:
            try:
                # Sincronização de Guerrilha: Handshake Industrial
                sync_token = os.getenv("CLOUD_SYNC_TOKEN", "")
                resp = requests.post(
                    f"{self.cloud_api_url}/api/sync/receive",
                    json=sync_item.to_dict(),
                    timeout=15,
                    headers={
                        "Authorization": f"Bearer {sync_token}",
                        "Content-Type": "application/json"
                    }
                )
                return resp.status_code == 200
            except:
                return False
        
        # Fallback para simulação (Validação de infraestrutura local)
        return True

    def run(self):
        """Loop principal do worker"""
        print(f"📡 Worker de Sincronia de Guerrilha iniciado (Frequência: {self.intervalo_check}s)")
        
        while True:
            if self.check_internet():
                try:
                    self.sync_deltas()
                except Exception as e:
                    print(f"❌ Erro durante sincronização: {str(e)}")
            else:
                print("📶 Sem internet. Aguardando sinal para sincronizar...")
                
            time.sleep(self.intervalo_check)

def start_sync_worker(app):
    """Entry point para iniciar o worker sem travar o Flask"""
    worker = GuerrillaSyncWorker(app)
    worker.start()
    return worker
