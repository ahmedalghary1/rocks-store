const { test } = require('node:test');
const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { join } = require('node:path');
const vm = require('node:vm');

const source = readFileSync(join(__dirname, '../static/js/main.js'), 'utf8');
const reply = (status, data) => ({ status, ok: status >= 200 && status < 300, json: async () => data });

function browser(fetch, { cookie = '', blockedCookies = false, controller = AbortController } = {}) {
  const field = { value: 'page-token' };
  const document = {
    documentElement: { lang: 'en', classList: { add() {} } },
    body: { dataset: { sessionUrl: '/cart/session/', csrfToken: 'page-token' }, style: {} },
    querySelector: selector => selector === '[name="csrfmiddlewaretoken"]' ? field : null,
    querySelectorAll: selector => selector === '[name="csrfmiddlewaretoken"]' ? [field] : [],
  };
  Object.defineProperty(document, 'cookie', {
    get() {
      if (blockedCookies) throw new Error('SecurityError: cookie access denied');
      return cookie;
    },
    set(value) { cookie = value; },
  });
  const context = {
    document, window: {}, fetch, FormData, AbortController: controller,
    addEventListener() {}, requestAnimationFrame() {},
    setTimeout() { return 1; }, clearTimeout() {},
  };
  const api = vm.runInNewContext(`${source}\n;({ requestData, csrf });`, context);
  return { ...api, document, field };
}

test('Facebook WebView with blocked JS cookies can use the masked page token', async () => {
  const app = browser(async (url, options) => {
    assert.equal(options.headers['X-CSRFToken'], 'page-token');
    assert.equal(options.credentials, 'same-origin');
    assert.equal(options.mode, 'same-origin');
    assert.equal(options.cache, 'no-store');
    return reply(200, { active: true });
  }, { blockedCookies: true });
  const result = await app.requestData('/wishlist/1/toggle/', { method: 'POST' });
  assert.equal(result.data.active, true);
});

test('cookie parser handles separators without spaces', () => {
  const app = browser(() => {}, { cookie: 'rocks_vid=visitor;csrftoken=current-token' });
  assert.equal(app.csrf(), 'current-token');
});

test('refreshes stale form token as well as header before sending cart request', async () => {
  const body = new FormData();
  body.set('csrfmiddlewaretoken', 'stale-form-token');
  body.set('quantity', '2');
  const app = browser(async (url, options) => {
    assert.equal(options.body.get('csrfmiddlewaretoken'), 'current-token');
    assert.equal(options.headers['X-CSRFToken'], 'current-token');
    assert.equal(options.body.get('quantity'), '2');
    return reply(200, { count: 2 });
  }, { cookie: 'csrftoken=current-token' });
  await app.requestData('/cart/add/1/', { method: 'POST', body });
});

test('explicit CSRF rejection refreshes cookies and retries the mutation once', async () => {
  const calls = [];
  const body = new FormData();
  body.set('variant_id', '3');
  const app = browser(async (url, options) => {
    calls.push({ url, token: options.headers?.['X-CSRFToken'] });
    if (calls.length === 1) return reply(403, { code: 'csrf_failed' });
    if (calls.length === 2) {
      assert.equal(url, '/cart/session/');
      assert.equal(options.cache, 'no-store');
      return reply(200, { csrfToken: 'fresh-token' });
    }
    assert.equal(options.body.get('csrfmiddlewaretoken'), 'fresh-token');
    assert.equal(options.body.get('variant_id'), '3');
    return reply(200, { count: 1 });
  }, { blockedCookies: true });
  const result = await app.requestData('/cart/add/1/', { method: 'POST', body });
  assert.equal(result.data.count, 1);
  assert.deepEqual(calls.map(call => call.url), ['/cart/add/1/', '/cart/session/', '/cart/add/1/']);
  assert.equal(calls[2].token, 'fresh-token');
  assert.equal(app.document.body.dataset.csrfToken, 'fresh-token');
  assert.equal(app.field.value, 'fresh-token');
});

test('a second CSRF rejection stops without looping', async () => {
  let calls = 0;
  const app = browser(async url => {
    calls++;
    return url === '/cart/session/' ? reply(200, { csrfToken: 'fresh' })
      : reply(403, { code: 'csrf_failed' });
  });
  const result = await app.requestData('/cart/add/1/', { method: 'POST' });
  assert.equal(result.response.status, 403);
  assert.equal(calls, 3);
});

test('network errors and unrelated 403 responses never replay a cart mutation', async () => {
  for (const networkError of [false, true]) {
    let calls = 0;
    const app = browser(async () => {
      calls++;
      if (networkError) throw new Error('Network unavailable');
      return reply(403, { message: 'Access denied' });
    });
    const request = app.requestData('/cart/add/1/', { method: 'POST' });
    if (networkError) await assert.rejects(request, /Network unavailable/);
    else assert.equal((await request).response.status, 403);
    assert.equal(calls, 1);
  }
});

test('serializes first cart and wishlist requests before cookies are established', async () => {
  const calls = [];
  let release;
  const app = browser(async url => {
    calls.push(url);
    if (calls.length === 1) await new Promise(resolve => { release = resolve; });
    return reply(200, {});
  });
  const cart = app.requestData('/cart/add/1/', { method: 'POST' });
  const wishlist = app.requestData('/wishlist/1/toggle/', { method: 'POST' });
  await Promise.resolve();
  assert.deepEqual(calls, ['/cart/add/1/']);
  release();
  await Promise.all([cart, wishlist]);
  assert.deepEqual(calls, ['/cart/add/1/', '/wishlist/1/toggle/']);
});

test('failed mutation does not prevent the next request', async () => {
  let calls = 0;
  const app = browser(async () => {
    if (++calls === 1) throw new Error('Offline');
    return reply(200, { count: 1 });
  });
  await assert.rejects(app.requestData('/cart/add/1/', { method: 'POST' }), /Offline/);
  assert.equal((await app.requestData('/cart/add/1/', { method: 'POST' })).data.count, 1);
});

test('works without AbortController', async () => {
  const app = browser(async (url, options) => {
    assert.equal(options.signal, undefined);
    return reply(200, {});
  }, { controller: null });
  await app.requestData('/wishlist/1/toggle/', { method: 'POST' });
});

test('HTML error responses produce a readable message without replaying the request', async () => {
  let calls = 0;
  const app = browser(async () => {
    calls++;
    return { status: 403, ok: false, json: async () => { throw new SyntaxError('Unexpected token <'); } };
  });
  await assert.rejects(app.requestData('/cart/add/1/', { method: 'POST' }), /store could not process/);
  assert.equal(calls, 1);
});
