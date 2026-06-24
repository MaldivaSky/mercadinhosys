/**
 * useOfflineQueue — Fila de vendas offline para PDV resiliente
 *
 * Arquitetura:
 * - Armazena vendas em IndexedDB quando sem internet
 * - Processa automaticamente quando conexão é restaurada
 * - Suporta até 24h de operação offline
 * - IDs temporários com UUID no frontend
 */
import { useState, useEffect, useCallback } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { apiClient } from '../api/apiClient';

const DB_NAME = 'mercadinhosys_offline';
const STORE_NAME = 'vendas_pendentes';
const DB_VERSION = 1;

export interface VendaOffline {
  uuid: string;            // ID temporário gerado no frontend
  payload: any;            // Payload completo para POST /pdv/finalizar
  tentativas: number;      // Tentativas de sync
  criadoEm: string;        // ISO datetime
  erroUltimo?: string;     // Último erro de sync
}

// ────────────────────────────────────────────────────────────────────────────
// IndexedDB helpers
// ────────────────────────────────────────────────────────────────────────────

function openDB(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, DB_VERSION);
    req.onupgradeneeded = (e) => {
      const db = (e.target as IDBOpenDBRequest).result;
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME, { keyPath: 'uuid' });
      }
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

async function dbGetAll(): Promise<VendaOffline[]> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readonly');
    const req = tx.objectStore(STORE_NAME).getAll();
    req.onsuccess = () => resolve(req.result as VendaOffline[]);
    req.onerror = () => reject(req.error);
  });
}

async function dbPut(item: VendaOffline): Promise<void> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readwrite');
    const req = tx.objectStore(STORE_NAME).put(item);
    req.onsuccess = () => resolve();
    req.onerror = () => reject(req.error);
  });
}

async function dbDelete(uuid: string): Promise<void> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readwrite');
    const req = tx.objectStore(STORE_NAME).delete(uuid);
    req.onsuccess = () => resolve();
    req.onerror = () => reject(req.error);
  });
}

// ────────────────────────────────────────────────────────────────────────────
// Hook principal
// ────────────────────────────────────────────────────────────────────────────

export function useOfflineQueue() {
  const [pendingCount, setPendingCount] = useState(0);
  const [isSyncing, setIsSyncing] = useState(false);
  const [isOnline, setIsOnline] = useState(navigator.onLine);

  // Atualiza contagem de pendências
  const refreshCount = useCallback(async () => {
    try {
      const items = await dbGetAll();
      setPendingCount(items.length);
    } catch {
      // IndexedDB pode não estar disponível em alguns contextos
    }
  }, []);

  // Enfileira venda offline
  const enqueue = useCallback(async (payload: any): Promise<string> => {
    // Usa o offline_uuid já presente no payload (gerado no pdvService) como chave,
    // garantindo que a venda tenha UM único uuid em toda a cadeia (idempotência).
    const uuid = payload?.offline_uuid || uuidv4();
    const item: VendaOffline = {
      uuid,
      payload,
      tentativas: 0,
      criadoEm: new Date().toISOString(),
    };
    await dbPut(item);
    await refreshCount();
    console.log(`📦 Venda enfileirada offline: ${uuid}`);
    return uuid;
  }, [refreshCount]);

  // Processa fila — tenta enviar cada venda para o backend
  const processQueue = useCallback(async (): Promise<{ synced: number; failed: number }> => {
    if (isSyncing) return { synced: 0, failed: 0 };
    setIsSyncing(true);

    let synced = 0;
    let failed = 0;

    try {
      const items = await dbGetAll();
      if (items.length === 0) return { synced: 0, failed: 0 };

      console.log(`🔄 Processando ${items.length} venda(s) offline...`);

      for (const item of items) {
        try {
          // Tenta enviar para o backend
          const response = await apiClient.post('/pdv/finalizar', {
            ...item.payload,
            offline_uuid: item.uuid,     // Rastreabilidade
            offline_criadoEm: item.criadoEm,
          });

          if (response.data?.venda || response.data?.success) {
            await dbDelete(item.uuid);
            synced++;
            console.log(`✅ Venda offline sincronizada: ${item.uuid}`);
          }
        } catch (err: any) {
          // Erro de rede → deixa na fila para próxima tentativa
          const erroMsg = err?.response?.data?.message || err?.message || 'Erro de rede';
          const isNetworkError = !err?.response;

          if (isNetworkError) {
            // Sem internet ainda — atualiza tentativas e sai do loop
            await dbPut({ ...item, tentativas: item.tentativas + 1, erroUltimo: erroMsg });
            failed++;
            break; // Não adianta tentar as próximas se sem rede
          } else {
            // Erro do servidor (400/500) — pode ser dado inválido; marca como falha permanente
            console.error(`❌ Venda offline rejeitada pelo servidor (${item.uuid}):`, erroMsg);
            await dbPut({ ...item, tentativas: item.tentativas + 1, erroUltimo: erroMsg });
            failed++;
          }
        }
      }
    } finally {
      setIsSyncing(false);
      await refreshCount();
    }

    return { synced, failed };
  }, [isSyncing, refreshCount]);

  // Monitora status de rede
  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      // Tenta processar fila automaticamente quando volta a internet
      processQueue().then(({ synced }) => {
        if (synced > 0) {
          console.log(`✅ ${synced} venda(s) offline sincronizada(s) automaticamente`);
        }
      });
    };

    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // Carrega contagem inicial
    refreshCount();

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [processQueue, refreshCount]);

  return {
    pendingCount,
    isSyncing,
    isOnline,
    enqueue,
    processQueue,
    refreshCount,
  };
}
