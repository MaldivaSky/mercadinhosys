/**
 * offlineCatalog — cache local (IndexedDB) do catálogo de produtos para vender
 * SEM sinal. Guarda só o necessário para montar o carrinho: nome, códigos,
 * preço, estoque atual e unidade. A nuvem continua sendo a fonte da verdade;
 * isto é apenas uma cópia leve para operar offline.
 */

export interface ProdutoCatalogo {
  id: number;
  nome: string;
  codigo_barras: string | null;
  codigo_interno: string | null;
  preco_venda: number;
  quantidade: number;        // estoque/disponibilidade no momento do último sync
  unidade_medida: string;
}

const DB_NAME = 'mercadinhosys_catalog';
const STORE = 'produtos';
const DB_VERSION = 1;
const LS_LAST_SYNC = 'catalogo_offline_last_sync';

function openDB(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, DB_VERSION);
    req.onupgradeneeded = (e) => {
      const db = (e.target as IDBOpenDBRequest).result;
      if (!db.objectStoreNames.contains(STORE)) {
        const os = db.createObjectStore(STORE, { keyPath: 'id' });
        os.createIndex('codigo_barras', 'codigo_barras', { unique: false });
      }
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

/** Substitui todo o catálogo cacheado pelo recebido do servidor. */
export async function salvarCatalogo(produtos: ProdutoCatalogo[]): Promise<void> {
  const db = await openDB();
  await new Promise<void>((resolve, reject) => {
    const tx = db.transaction(STORE, 'readwrite');
    const store = tx.objectStore(STORE);
    store.clear();
    for (const p of produtos) store.put(p);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
  try { localStorage.setItem(LS_LAST_SYNC, new Date().toISOString()); } catch { /* ignore */ }
}

export async function lerCatalogo(): Promise<ProdutoCatalogo[]> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE, 'readonly');
    const req = tx.objectStore(STORE).getAll();
    req.onsuccess = () => resolve((req.result as ProdutoCatalogo[]) || []);
    req.onerror = () => reject(req.error);
  });
}

export async function contarCatalogo(): Promise<number> {
  const db = await openDB();
  return new Promise((resolve) => {
    const tx = db.transaction(STORE, 'readonly');
    const req = tx.objectStore(STORE).count();
    req.onsuccess = () => resolve(req.result || 0);
    req.onerror = () => resolve(0);
  });
}

/** Busca offline por nome, código de barras ou código interno. */
export async function buscarOffline(termo: string, limite = 20): Promise<ProdutoCatalogo[]> {
  const t = (termo || '').trim().toLowerCase();
  if (!t) return [];
  const todos = await lerCatalogo();
  // EAN exato primeiro (scanner), depois "contém" no nome/código
  const exato = todos.filter((p) => (p.codigo_barras || '') === termo.trim());
  if (exato.length) return exato.slice(0, limite);
  return todos
    .filter((p) =>
      p.nome.toLowerCase().includes(t) ||
      (p.codigo_barras || '').toLowerCase().includes(t) ||
      (p.codigo_interno || '').toLowerCase().includes(t),
    )
    .slice(0, limite);
}

export function ultimoSyncCatalogo(): string | null {
  try { return localStorage.getItem(LS_LAST_SYNC); } catch { return null; }
}
