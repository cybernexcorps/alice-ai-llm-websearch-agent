/**
 * api.js — Fetch wrappers for all /api/* endpoints
 */

const API_BASE = '';

async function _post(path, body) {
  const resp = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!resp.ok) {
    let detail = `HTTP ${resp.status}`;
    try { const err = await resp.json(); detail = err.detail || detail; } catch {}
    throw new Error(detail);
  }
  return resp.json();
}

async function _get(path) {
  const resp = await fetch(`${API_BASE}${path}`);
  if (!resp.ok) {
    let detail = `HTTP ${resp.status}`;
    try { const err = await resp.json(); detail = err.detail || detail; } catch {}
    throw new Error(detail);
  }
  return resp.json();
}

const AliceAPI = {
  /** POST /api/search — {query} → {answer, response_id} */
  search(query) {
    return _post('/api/search', { query });
  },

  /** POST /api/chat — {message, conversation_id?} → {answer, conversation_id} */
  chat(message, conversationId = null) {
    return _post('/api/chat', { message, conversation_id: conversationId });
  },

  /** POST /api/chat/reset — {conversation_id} → {status} */
  chatReset(conversationId) {
    return _post('/api/chat/reset', { conversation_id: conversationId });
  },

  /** POST /api/fetch — {url} → {content} */
  fetchUrl(url) {
    return _post('/api/fetch', { url });
  },

  /**
   * POST /api/export — triggers file download.
   * Returns a Blob, so we handle it separately (not JSON).
   */
  async export(query, answer, format) {
    const resp = await fetch(`${API_BASE}/api/export`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, answer, format }),
    });
    if (!resp.ok) {
      let detail = `HTTP ${resp.status}`;
      try { const err = await resp.json(); detail = err.detail || detail; } catch {}
      throw new Error(detail);
    }
    const blob = await resp.blob();
    const disposition = resp.headers.get('Content-Disposition') || '';
    const match = disposition.match(/filename="([^"]+)"/);
    const filename = match ? match[1] : `alice-result.${format}`;
    return { blob, filename };
  },

  /** GET /api/config → ConfigResponse */
  config() {
    return _get('/api/config');
  },
};

window.AliceAPI = AliceAPI;
