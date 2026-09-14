import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createHandler, SEARCH, DETAILS } from './supabase/functions/cults-search/core.mjs';
const token = 'a'.repeat(64);
const config = { CONNECTOR_API_TOKEN: token, CULTS_USERNAME: 'fixture-user', CULTS_API_KEY: 'fixture-key' };
const fixture = { name: 'Test model', url: 'https://cults3d.com/en/3d-model/art/test-model', creator: { nick: 'Author' }, price: { cents: 0 }, tags: ['fdm'], license: null };
function setup(fetcher, overrides = {}, extra = {}) {
  return createHandler({ env: k => ({ ...config, ...overrides })[k], fetcher, ...extra });
}
const req = (path = '/search?q=dragon', auth = `Bearer ${token}`, method = 'GET') => new Request(`https://example.com/functions/v1/cults-search${path}`, { method, headers: auth ? { Authorization: auth } : {} });
const response = data => Response.json({ data });
test('missing/wrong token never contacts Cults; missing config fails closed', async () => {
  const noFetch = () => { throw new Error('must not call'); };
  for (const auth of ['', 'Bearer wrong']) assert.equal((await setup(noFetch)(req(undefined, auth))).status, 401);
  assert.equal((await setup(noFetch, { CONNECTOR_API_TOKEN: '' })(req())).status, 503);
  assert.equal((await setup(noFetch, { CULTS_API_KEY: '' })(req())).status, 503);
});
test('invalid parameters, extra GraphQL, duplicate parameters and writes are rejected', async () => {
  const handler = setup(() => { throw new Error('must not call'); });
  for (const path of ['/search?q=x', '/search?q=dragon&limit=21', '/search?q=dragon&offset=-1', '/search?q=dragon&query=mutation', '/search?q=dragon&q=cat', '/details?slug=https://evil.com']) assert.equal((await handler(req(path))).status, 400);
  assert.equal((await handler(req(undefined, undefined, 'POST'))).status, 405);
  assert.equal((await handler(req('/sales'))).status, 404);
});
test('search uses fixed query, keeps input in variables, normalizes zero price and unknown license', async () => {
  const injection = 'dragon" } mutation { deleteCreation }';
  const handler = setup(async (url, init) => {
    assert.equal(url, 'https://cults3d.com/graphql'); assert.equal(init.redirect, 'error');
    assert.equal(init.method, 'POST'); assert.match(init.headers.Authorization, /^Basic /);
    const body = JSON.parse(init.body); assert.equal(body.query, SEARCH); assert.equal(body.variables.query, injection);
    return response({ creationsSearchBatch: { total: 3, results: [fixture] } });
  });
  const result = await handler(req('/search?q=' + encodeURIComponent(injection) + '&limit=1'));
  assert.equal(result.status, 200); const data = await result.json();
  assert.equal(data.models[0].price.cents, 0); assert.equal(data.models[0].license, null);
  assert.equal(data.next_offset, 1); assert.equal(data.models[0].slug, 'test-model');
  assert.equal(result.headers.get('access-control-allow-origin'), null);
});
test('details and model not found', async () => {
  const handler = setup(async (_, init) => { const b = JSON.parse(init.body); assert.equal(b.query, DETAILS); assert.equal(b.variables.slug, 'test-model'); return response({ creation: fixture }); });
  assert.equal((await handler(req('/details?slug=test-model'))).status, 200);
  assert.equal((await setup(async () => response({ creation: null }))(req('/details?slug=missing'))).status, 404);
});
test('upstream failures and GraphQL errors never expose raw error or secrets', async () => {
  for (const reply of [() => new Response('fixture-key', { status: 401 }), () => Response.json({ errors: [{ message: 'fixture-key' }] }), () => new Response('not JSON')]) {
    const r = await setup(async () => reply())(req()); assert.equal(r.status, 502); assert.doesNotMatch(await r.text(), /fixture-key/);
  }
  assert.equal((await setup(async () => new Response('', { status: 429 }))(req())).status, 429);
});
test('timeout and oversized upstream body', async () => {
  const slow = setup((_, init) => new Promise((_, reject) => init.signal.addEventListener('abort', () => reject(new Error('aborted')))), {}, { timeoutMs: 5 });
  assert.equal((await slow(req())).status, 504);
  assert.equal((await setup(async () => new Response('x'.repeat(2_000_001)))(req())).status, 502);
});
test('per-instance throttle resets', async () => {
  let time = 100000; const handler = setup(async () => response({ creationsSearchBatch: { total: 0, results: [] } }), {}, { now: () => time });
  for (let i = 0; i < 30; i++) assert.equal((await handler(req())).status, 200);
  assert.equal((await handler(req())).status, 429); time += 60001;
  assert.equal((await handler(req())).status, 200);
});
