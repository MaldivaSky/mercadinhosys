"""
MercadinhoSys - SyncWorker Background Service
Responsável por sincronizar dados locais (SQLite) com a nuvem (PostgreSQL)
Executa apenas no modo local para evitar loops infinitos
"""

import os
import time
import json
import logging
import requests
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import text

from app import create_app, db
from app.models import SyncQueue, SyncLog, Estabelecimento

logger = logging.getLogger(__name__)

class SyncWorker:
    """Worker responsável pela sincronização local -> nuvem"""
    
    def __init__(self):
        self.app = create_app()
        self.cloud_api_url = os.getenv("CLOUD_API_URL", "https://mercadinhosys.onrender.com")
        self.sync_token = os.getenv("CLOUD_SYNC_TOKEN", "")
        self.worker_interval = int(os.getenv("SYNC_WORKER_INTERVAL", "30"))  # segundos
        self.max_retries = int(os.getenv("SYNC_MAX_RETRIES", "3"))
        self.is_running = False
        
    def start(self):
        """Inicia o worker em background"""
        if not self.sync_token:
            logger.error("❌ CLOUD_SYNC_TOKEN não configurado. SyncWorker não iniciado.")
            return False
            
        if self.app.config.get("APP_MODE", "local") != "local":
            logger.info("ℹ️ MODO CLOUD detectado. SyncWorker não será iniciado.")
            return False
            
        self.is_running = True
        logger.info(f"🚀 SyncWorker iniciado. Intervalo: {self.worker_interval}s")
        
        try:
            self._run_loop()
        except KeyboardInterrupt:
            logger.info("⏹️ SyncWorker interrompido pelo usuário")
        except Exception as e:
            logger.error(f"💥 Erro fatal no SyncWorker: {e}")
        finally:
            self.is_running = False
            logger.info("⏹️ SyncWorker finalizado")
            
        return True
    
    def stop(self):
        """Para o worker"""
        self.is_running = False
        logger.info("🛑 Sinal de parada enviado ao SyncWorker")
    
    def _run_loop(self):
        """Loop principal do worker"""
        while self.is_running:
            try:
                with self.app.app_context():
                    self._process_pending_syncs()
                    
                # Aguardar próximo ciclo
                time.sleep(self.worker_interval)
                
            except Exception as e:
                logger.error(f"❌ Erro no ciclo de sync: {e}")
                time.sleep(self.worker_interval)
                
    def _check_connectivity(self) -> bool:
        """Verifica se há conexão com a API na nuvem"""
        try:
            response = requests.get(
                f"{self.cloud_api_url}/api/health",
                timeout=5,
                headers={"User-Agent": "MercadinhoSys-SyncWorker/1.0"}
            )
            return response.status_code == 200
        except (requests.exceptions.ConnectionError,
                requests.exceptions.Timeout):
            return False
    
    def _process_pending_syncs(self):
        """Processa todos os itens pendentes na SyncQueue"""
        if not self._check_connectivity():
            logger.info("Sem conexão com a nuvem. Sync adiado.")
            return
        
        # Buscar itens pendentes (limitado para evitar sobrecarga)
        pending_items = SyncQueue.query.filter_by(status="pendente")\
                                     .filter(SyncQueue.tentativas < self.max_retries)\
                                     .order_by(SyncQueue.created_at)\
                                     .limit(50)\
                                     .all()
        
        if not pending_items:
            return
            
        logger.info(f"📦 Processando {len(pending_items)} itens pendentes")
        
        for item in pending_items:
            try:
                success = self._sync_item(item)
                if success:
                    item.status = "sincronizado"
                    item.tentativas += 1
                    item.synced_at = datetime.utcnow()
                    item.mensagem_erro = None
                    logger.info(f"✅ Item {item.id} sincronizado com sucesso")
                else:
                    item.tentativas += 1
                    if item.tentativas >= self.max_retries:
                        item.status = "erro"
                        item.mensagem_erro = "Máximo de tentativas atingido"
                        logger.error(f"❌ Item {item.id} marcado como erro (máx tentativas)")
                    
            except Exception as e:
                item.tentativas += 1
                item.mensagem_erro = str(e)
                logger.error(f"❌ Erro ao sincronizar item {item.id}: {e}")
                
                if item.tentativas >= self.max_retries:
                    item.status = "erro"
            
            finally:
                db.session.commit()
    
    def _sync_item(self, item: SyncQueue) -> bool:
        """Sincroniza um item individual com a nuvem"""
        
        # Preparar payload para API
        payload = {
            "tabela": item.tabela,
            "registro_id": item.registro_id,
            "operacao": item.operacao,
            "estabelecimento_id": item.estabelecimento_id,
            "payload": json.loads(item.payload_json) if item.payload_json else None,
            "timestamp": item.created_at.isoformat() if item.created_at else None
        }
        
        # Fazer requisição para API na nuvem
        try:
            response = requests.post(
                f"{self.cloud_api_url}/api/sync/receive",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.sync_token}",
                    "Content-Type": "application/json",
                    "User-Agent": "MercadinhoSys-SyncWorker/1.0"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("success", False)
            else:
                logger.error(f"❌ Erro HTTP {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            logger.error(f"⏱️ Timeout na sincronização do item {item.id}")
            return False
        except requests.exceptions.ConnectionError:
            logger.error(f"🔌 Erro de conexão ao sincronizar item {item.id}")
            return False
        except Exception as e:
            logger.error(f"💥 Erro na requisição do item {item.id}: {e}")
            return False
    
    def _create_sync_log(self, operation: str, status: str, payload: Dict[str, Any], 
                        result: Optional[Dict[str, Any]] = None, error: Optional[str] = None):
        """Cria um registro de log da sincronização"""
        try:
            log = SyncLog(
                estabelecimento_id=1,  # Ajustar conforme necessário
                operacao=operation,
                status=status,
                payload_json=json.dumps(payload),
                resultado_json=json.dumps(result) if result else None,
                mensagem_erro=error
            )
            db.session.add(log)
            db.session.commit()
        except Exception as e:
            logger.error(f"❌ Erro ao criar sync log: {e}")

def main():
    """Função principal para executar o SyncWorker"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    worker = SyncWorker()
    worker.start()

if __name__ == "__main__":
    main()
