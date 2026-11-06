const sourceLabels = {blablalink:'BlaBlaLink', file:'JSONファイル', session:'保存ファイル'};

export function formatHistoryLabel(entry) {
  return `${new Date(entry.imported_at).toLocaleString('ja-JP')} / ${sourceLabels[entry.source] || entry.source} / 所持人数：${entry.owned_count}人`;
}

export function makeHistoryEntry({snapshot, source, now = new Date()}) {
  const imported_at = new Date(now).toISOString();
  const entry = {id:globalThis.crypto?.randomUUID?.() || `${imported_at}-${Math.random().toString(36).slice(2)}`, imported_at, source, is_demo:!!snapshot.is_demo, owned_count:Object.keys(snapshot.profile?.chars || {}).length, snapshot:structuredClone(snapshot)};
  entry.label = formatHistoryLabel(entry);
  return entry;
}

export function pushHistory(list, entry, limit = 20) {
  const rows = Array.isArray(list) ? list : [];
  const duplicate = rows.length > 0 && JSON.stringify(rows[0].snapshot.profile) === JSON.stringify(entry.snapshot.profile);
  return [duplicate ? {...entry, id:rows[0].id} : entry, ...rows.slice(duplicate ? 1 : 0)].slice(0, Math.max(0, limit));
}

export function openStore() {
  return new Promise(resolve => {
    try {
      if (!globalThis.indexedDB) return resolve(null);
      const request = globalThis.indexedDB.open('nikke-tools', 1);
      let finished = false;
      const finish = value => { if (!finished) { finished = true; resolve(value); } else value?.close(); };
      request.onupgradeneeded = () => { try { if (!request.result.objectStoreNames.contains('kv')) request.result.createObjectStore('kv'); } catch { finish(null); } };
      request.onsuccess = () => finish(request.result);
      request.onerror = request.onblocked = () => finish(null);
    } catch { resolve(null); }
  });
}

async function transact(key, mode, operation) {
  const db = await openStore();
  if (!db) return mode === 'readonly' ? null : false;
  return new Promise(resolve => {
    const fallback = mode === 'readonly' ? null : false;
    const finish = value => { try { db.close(); } catch {} resolve(value); };
    try {
      const transaction = db.transaction('kv', mode);
      const request = operation(transaction.objectStore('kv'), key);
      transaction.oncomplete = () => finish(mode === 'readonly' ? request.result ?? null : true);
      transaction.onerror = transaction.onabort = () => finish(fallback);
      request.onerror = () => finish(fallback);
    } catch { finish(fallback); }
  });
}

export const getItem = key => transact(key, 'readonly', (store, k) => store.get(k));
export const setItem = (key, value) => transact(key, 'readwrite', (store, k) => store.put(value, k));
export const deleteItem = key => transact(key, 'readwrite', (store, k) => store.delete(k));
