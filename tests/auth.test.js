import test from 'node:test';
import assert from 'node:assert/strict';
import { createAuthGate, returnPath, CANONICAL_ORIGIN, CLERK_FRONTEND } from '../auth.js';

const env = { CLERK_SECRET_KEY: 'sk_test_private', CLERK_PUBLISHABLE_KEY: 'pk_test_public' };
const user = (email = 'andrew@aisimple.co', verified = true) => ({
  primaryEmailAddressId: 'primary', emailAddresses: [{ id: 'primary', emailAddress: email, verification: { status: verified ? 'verified' : 'unverified' } }],
});
function setup({ authenticated = false, account = user(), state = {}, fail = false, clock = () => 0 } = {}) {
  let lookups = 0; let verifications = 0; let options;
  const client = {
    authenticateRequest: async (_req, opts) => {
      verifications++; options = opts;
      if (fail) throw Error('Clerk unavailable');
      return { isAuthenticated: authenticated, status: authenticated ? 'signed-in' : 'signed-out', toAuth: () => ({ userId: authenticated ? 'user_one' : null }), ...state };
    },
    users: { getUser: async () => { lookups++; return account; } },
  };
  const handler = createAuthGate({ getClient: () => client, env, now: clock, proceed: ({ headers }) => new Response('next', { headers }) });
  return { handler, calls: () => ({ lookups, verifications, options }) };
}
const request = path => new Request(CANONICAL_ORIGIN + path);

test('unauthenticated HTML is redirected to sign-in with its list selection', async () => {
  const { handler } = setup(); const r = await handler(request('/?scope=ai-dtc'));
  assert.equal(r.status, 302);
  assert.equal(new URL(r.headers.get('location')).pathname, '/sign-in');
  assert.equal(new URL(r.headers.get('location')).searchParams.get('return_to'), '/?scope=ai-dtc');
});
test('direct index.html cannot bypass authentication', async () => {
  const { handler } = setup(); assert.equal((await handler(request('/index.html'))).status, 302);
});
test('anonymous media, thumbnails and JSON never return content', async () => {
  const { handler } = setup();
  for (const path of ['/clips/reel.mp4', '/thumbs/reel.jpg', '/data/account_posts.json']) assert.equal((await handler(request(path))).status, 401);
});
test('approved verified primary account can access dashboard and media', async () => {
  const { handler, calls } = setup({ authenticated: true });
  for (const path of ['/', '/index.html', '/clips/reel.mp4', '/thumbs/reel.jpg']) {
    const r = await handler(request(path)); assert.equal(await r.text(), 'next'); assert.equal(r.headers.get('cache-control'), 'private, no-store');
  }
  assert.equal(calls().verifications, 4); assert.equal(calls().lookups, 1);
});
test('JWT options pin trusted origins, issuer and session-only tokens', async () => {
  const { handler, calls } = setup({ authenticated: true }); await handler(request('/'));
  assert.deepEqual(calls().options.authorizedParties, [CANONICAL_ORIGIN, 'https://life.aisimple.co']);
  assert.equal(calls().options.issuer, CLERK_FRONTEND); assert.equal(calls().options.acceptsToken, 'session_token');
});
test('unapproved user gets a 403 with an explicit sign-out option', async () => {
  const { handler } = setup({ authenticated: true, account: user('other@example.com') });
  const r = await handler(request('/')); assert.equal(r.status, 403); assert.match(await r.text(), /Clerk.signOut/);
});
test('missing or unverified primary emails cannot bypass access policy', async () => {
  for (const account of [user('andrew@aisimple.co', false), { primaryEmailAddressId: 'missing', emailAddresses: [] }]) {
    const { handler } = setup({ authenticated: true, account }); assert.equal((await handler(request('/'))).status, 403);
  }
});
test('an allowed secondary email does not authorize an unapproved primary account', async () => {
  const account = user('other@example.com'); account.emailAddresses.push({ id: 'secondary', emailAddress: 'andrew@aisimple.co', verification: { status: 'verified' } });
  const { handler } = setup({ authenticated: true, account }); assert.equal((await handler(request('/'))).status, 403);
});
test('email case is normalized and allowlist lookups expire', async () => {
  let time = 0; const { handler, calls } = setup({ authenticated: true, account: user('Andrew@AISimple.co'), clock: () => time });
  assert.equal((await handler(request('/'))).status, 200); time = 61_000; await handler(request('/')); assert.equal(calls().lookups, 2);
});
test('Clerk handshake forwards cookies and redirect without content', async () => {
  const { handler } = setup({ state: { status: 'handshake', headers: new Headers({ Location: CLERK_FRONTEND + '/v1/client/handshake', 'Set-Cookie': '__session=refresh; Secure' }) } });
  const r = await handler(request('/')); assert.equal(r.status, 307); assert.equal(r.headers.get('set-cookie'), '__session=refresh; Secure'); assert.equal(await r.text(), '');
});
test('a malformed handshake and a Clerk outage both fail closed', async () => {
  for (const options of [{ state: { status: 'handshake', headers: new Headers() } }, { fail: true }]) {
    const { handler } = setup(options); const r = await handler(request('/')); assert.ok([401, 503].includes(r.status)); assert.notEqual(await r.text(), 'next');
  }
});
test('missing production credentials fail closed including sign-in', async () => {
  const handler = createAuthGate({ env: {}, getClient: () => { throw Error('must not initialize'); }, proceed: () => new Response('next') });
  for (const path of ['/', '/sign-in']) assert.equal((await handler(request(path))).status, 503);
});
test('deployment aliases redirect to the custom domain before serving data', async () => {
  const { handler, calls } = setup({ authenticated: true });
  const r = await handler(new Request('https://outlier-lab-eta.vercel.app/index.html?scope=ai'));
  assert.equal(r.status, 308); assert.equal(r.headers.get('location'), CANONICAL_ORIGIN + '/index.html?scope=ai'); assert.equal(calls().verifications, 0);
});
test('sign-in accepts only same-origin return paths and escapes script content', async () => {
  for (const input of ['//evil.example/', '/\\evil.example/', 'https://evil.example/', '/sign-in', '/\r\nLocation:evil']) assert.equal(returnPath(input), '/');
  const { handler } = setup(); const r = await handler(request('/sign-in?return_to=' + encodeURIComponent('/?q=</script>'))); const body = await r.text();
  assert.equal(r.status, 200); assert.ok(body.includes('clerk.life.aisimple.co')); assert.ok(body.includes('pk_test_public')); assert.ok(!body.includes('sk_test_private')); assert.ok(!body.includes('const destination="/?q=</script>"'));
});
