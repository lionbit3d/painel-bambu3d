// Only these two fixed read operations can reach Cults. Never accept GraphQL from clients.
const FIELDS = `name(locale: EN) url(locale: EN) illustrationImageUrl
  creator { nick shortUrl } tags(locale: EN)
  price(currency: USD) { cents } license { name(locale: EN) }
  publishedAt viewsCount likesCount downloadsCount`;
export const SEARCH = `query Search($query: String!, $limit: Int!, $offset: Int!) {
  creationsSearchBatch(query: $query, limit: $limit, offset: $offset) {
    total results { ${FIELDS} }
  }
}`;
export const DETAILS = `query Details($slug: String!) { creation(slug: $slug) { ${FIELDS} } }`;
const json = (body, status = 200, extra = {}) => new Response(JSON.stringify(body), {
  status, headers: { 'Content-Type': 'application/json; charset=utf-8',
    'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff', ...extra },
});
const fail = (code, status, extra) => json({ error: code }, status, extra);
const str = v => typeof v === 'string' ? v : null;
function https(v) {
  try { const u = new URL(v); return u.protocol === 'https:' && !u.username && !u.password ? u.href : null; }
  catch { return null; }
}
function model(c) {
  if (!c || typeof c !== 'object' || !str(c.name) || !https(c.url)) throw new Error('invalid model');
  const url = https(c.url);
  return { title: c.name, url, slug: new URL(url).pathname.split('/').filter(Boolean).at(-1),
    author: { name: str(c.creator?.nick), url: https(c.creator?.shortUrl) },
    images: [https(c.illustrationImageUrl)].filter(Boolean),
    price: Number.isSafeInteger(c.price?.cents) ? { cents: c.price.cents, currency: 'USD' } : null,
    tags: Array.isArray(c.tags) ? c.tags.filter(x => typeof x === 'string') : [],
    license: c.license?.name ? { name: str(c.license.name) } : null,
    published_at: str(c.publishedAt),
    views: c.viewsCount ?? null, likes: c.likesCount ?? null, downloads: c.downloadsCount ?? null };
}
async function equal(a, b) {
  const digest = s => crypto.subtle.digest('SHA-256', new TextEncoder().encode(s));
  const [x, y] = await Promise.all([digest(a), digest(b)]);
  const aa = new Uint8Array(x), bb = new Uint8Array(y);
  let diff = 0; for (let i = 0; i < aa.length; i++) diff |= aa[i] ^ bb[i];
  return diff === 0;
}
function integer(params, key, fallback, min, max) {
  const value = params.get(key);
  if (value === null) return fallback;
  if (!/^\d+$/.test(value)) throw new Error('bad parameter');
  const n = Number(value); if (!Number.isSafeInteger(n) || n < min || n > max) throw new Error('bad parameter');
  return n;
}
export function createHandler({ env, fetcher = fetch, now = Date.now, timeoutMs = 12000 }) {
  // Best effort per warm isolate; not a global quota across Supabase instances.
  let windowStart = 0, calls = 0;
  return async req => {
    const token = env('CONNECTOR_API_TOKEN') || '';
    if (!/^[a-fA-F0-9]{64}$/.test(token)) return fail('connector_not_configured', 503);
    const auth = req.headers.get('authorization') || '';
    if (auth.length > 100 || !await equal(auth, `Bearer ${token}`)) return fail('unauthorized', 401);
    if (req.method !== 'GET') return fail('method_not_allowed', 405, { Allow: 'GET' });
    const u = new URL(req.url);
    const route = u.pathname.replace(/^\/functions\/v1/, '').replace(/^\/cults-search/, '');
    if (route !== '/search' && route !== '/details') return fail('not_found', 404);
    let query, variables;
    try {
      const allowed = route === '/search' ? ['q', 'limit', 'offset'] : ['slug'];
      for (const key of u.searchParams.keys()) if (!allowed.includes(key) || u.searchParams.getAll(key).length !== 1) throw new Error('parameter');
      if (u.search.length > 2000) throw new Error('size');
      if (route === '/search') {
        const q = (u.searchParams.get('q') || '').trim();
        if (q.length < 2 || q.length > 160 || /[\x00-\x1f]/.test(q)) throw new Error('query');
        query = SEARCH;
        variables = { query: q, limit: integer(u.searchParams, 'limit', 5, 1, 20), offset: integer(u.searchParams, 'offset', 0, 0, 1000) };
      } else {
        const slug = u.searchParams.get('slug') || '';
        if (!/^[\p{L}\p{N}_-]{1,250}$/u.test(slug)) throw new Error('slug');
        query = DETAILS; variables = { slug };
      }
    } catch { return fail('invalid_parameters', 400); }
    const username = env('CULTS_USERNAME') || '', key = env('CULTS_API_KEY') || '';
    if (!username || username.includes(':') || !key) return fail('cults_not_configured', 503);
    if (now() - windowStart >= 60000) { windowStart = now(); calls = 0; }
    if (++calls > 30) return fail('rate_limited', 429, { 'Retry-After': '60' });
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    try {
      const bytes = new TextEncoder().encode(`${username}:${key}`);
      const basic = btoa(Array.from(bytes, b => String.fromCharCode(b)).join(''));
      const response = await fetcher('https://cults3d.com/graphql', {
        method: 'POST', redirect: 'error', signal: controller.signal,
        headers: { Authorization: `Basic ${basic}`, 'Content-Type': 'application/json', 'User-Agent': 'LionBit-Cults-Research/1.0' },
        body: JSON.stringify({ query, variables }),
      });
      if (response.status === 429) return fail('cults_rate_limited', 429, { 'Retry-After': '60' });
      if (!response.ok) { await response.body?.cancel(); return fail('cults_unavailable', 502); }
      // Limit decompressed response bytes, including chunked responses.
      const reader = response.body?.getReader(); if (!reader) throw new Error('empty');
      const chunks = []; let size = 0;
      while (true) {
        const { value, done } = await reader.read(); if (done) break;
        size += value.byteLength;
        if (size > 2_000_000) { await reader.cancel(); throw new Error('size'); }
        chunks.push(value);
      }
      const dataBytes = new Uint8Array(size); let pos = 0;
      for (const chunk of chunks) { dataBytes.set(chunk, pos); pos += chunk.length; }
      const payload = JSON.parse(new TextDecoder().decode(dataBytes));
      if (payload.errors?.length || !payload.data) return fail('cults_query_failed', 502);
      if (route === '/details') {
        if (payload.data.creation === null) return fail('model_not_found', 404);
        return json({ model: model(payload.data.creation), source: 'Cults3D' });
      }
      const batch = payload.data.creationsSearchBatch;
      if (!Array.isArray(batch?.results) || !Number.isSafeInteger(batch.total) || batch.total < 0) throw new Error('shape');
      const models = batch.results.slice(0, variables.limit).map(model);
      const next = variables.offset + models.length;
      return json({ models, total: batch.total, limit: variables.limit, offset: variables.offset,
        next_offset: models.length && next < batch.total && next <= 1000 ? next : null, source: 'Cults3D' });
    } catch { return fail(controller.signal.aborted ? 'cults_timeout' : 'cults_unavailable', controller.signal.aborted ? 504 : 502); }
    finally { clearTimeout(timer); }
  };
}
