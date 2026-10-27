// The same Clerk production instance and approved accounts as life.aisimple.co.
export const CANONICAL_ORIGIN = 'https://outlier.aisimple.co';
export const CLERK_FRONTEND = 'https://clerk.life.aisimple.co';
export const ALLOWED_EMAILS = new Set([
  'andrew@aisimple.co', 'andrew@vibeos.com', 'naegele412@gmail.com',
]);

const privateHeaders = { 'Cache-Control': 'private, no-store', 'Vary': 'Cookie, Authorization' };

export function returnPath(value) {
  if (!value || value.length > 2000 || !value.startsWith('/') || value.startsWith('//') || /[\\\r\n]/.test(value)) return '/';
  const target = new URL(value, CANONICAL_ORIGIN);
  if (target.origin !== CANONICAL_ORIGIN || target.pathname.startsWith('/sign-in')) return '/';
  return target.pathname + target.search + target.hash;
}

export function loginPage(publishableKey, destination = '/', denied = false) {
  const target = JSON.stringify(returnPath(destination)).replaceAll('<', '\\u003c');
  const key = publishableKey.replaceAll('&', '&amp;').replaceAll('"', '&quot;').replaceAll('<', '&lt;');
  return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Sign in · Outlier Lab</title>
  <style>body{margin:0;min-height:100vh;display:grid;place-items:center;background:#0b0b0e;color:#f4f4f6;font:16px system-ui}main{padding:32px;text-align:center}h1{font-size:28px;letter-spacing:-1px;margin:0 0 8px}p{color:#a1a1aa;margin:0 0 28px}#error{max-width:360px;color:#fca5a5}a{color:#f4f4f6}</style>
  <script defer crossorigin="anonymous" src="${CLERK_FRONTEND}/npm/@clerk/ui@1/dist/ui.browser.js"></script>
  <script defer crossorigin="anonymous" data-clerk-publishable-key="${key}" src="${CLERK_FRONTEND}/npm/@clerk/clerk-js@6/dist/clerk.browser.js"></script>
  </head><body><main><h1>Outlier Lab</h1><p>${denied ? 'This account does not have access. Sign out to use an approved AI Simple account.' : 'Sign in with your AI Simple account.'}</p><div id="sign-in"></div><p id="error" role="alert"></p></main>
  <script>window.addEventListener('load',async()=>{try{const destination=${target};await Clerk.load({ui:{ClerkUI:window.__internal_ClerkUICtor},signInFallbackRedirectUrl:destination,signUpFallbackRedirectUrl:destination});if(Clerk.session){if(${denied}){const button=document.createElement('button');button.textContent='Sign out';button.onclick=()=>Clerk.signOut({redirectUrl:'/sign-in'});document.getElementById('sign-in').append(button);}else{location.replace(destination);}return;}Clerk.mountSignIn(document.getElementById('sign-in'),{routing:'hash',forceRedirectUrl:destination,fallbackRedirectUrl:destination});}catch{document.getElementById('error').textContent='Sign-in is temporarily unavailable. Please reload to try again.';}});</script></body></html>`;
}

export function createAuthGate({ getClient, proceed, env = process.env, now = Date.now }) {
  // Coalesce concurrent image/video authorization lookups. JWT verification is
  // still performed for every request; approved primary emails are cached 60s.
  const users = new Map();
  async function approved(client, id) {
    const hit = users.get(id);
    if (hit && hit.expires > now()) return hit.promise;
    const promise = client.users.getUser(id).then(user => {
      const primary = user.emailAddresses.find(email => email.id === user.primaryEmailAddressId);
      return primary?.verification?.status === 'verified' && ALLOWED_EMAILS.has(primary.emailAddress.toLowerCase());
    });
    if (users.size >= 256) users.delete(users.keys().next().value);
    users.set(id, { promise, expires: now() + 60_000 });
    try { return await promise; } catch (error) { users.delete(id); throw error; }
  }

  return async function gate(request) {
    const url = new URL(request.url);
    // Production keys belong on the custom domain. Old deployment aliases must
    // not offer an unprotected copy or attempt sign-in on a different origin.
    if (url.origin !== CANONICAL_ORIGIN) {
      return new Response(null, { status: 308, headers: { ...privateHeaders, Location: CANONICAL_ORIGIN + url.pathname + url.search } });
    }
    if (!env.CLERK_SECRET_KEY || !env.CLERK_PUBLISHABLE_KEY) {
      return new Response('Sign-in is not configured.', { status: 503, headers: privateHeaders });
    }
    if (url.pathname === '/auth-client.js') return proceed({ headers: privateHeaders });
    if (url.pathname === '/sign-in' || url.pathname.startsWith('/sign-in/')) {
      return new Response(loginPage(env.CLERK_PUBLISHABLE_KEY, url.searchParams.get('return_to')), {
        status: 200, headers: { ...privateHeaders, 'Content-Type': 'text/html; charset=utf-8' },
      });
    }
    try {
      const client = getClient();
      const state = await client.authenticateRequest(request, {
        authorizedParties: [CANONICAL_ORIGIN, 'https://life.aisimple.co'],
        issuer: CLERK_FRONTEND,
        acceptsToken: 'session_token',
      });
      // Forward Clerk's handshake cookies/redirect unchanged to refresh an
      // expired browser session. Never serve the data during a handshake.
      if (state.status === 'handshake') {
        const headers = new Headers(state.headers);
        if (!headers.has('Location')) return new Response('Sign-in could not be refreshed.', { status: 401, headers: privateHeaders });
        for (const [name, value] of Object.entries(privateHeaders)) headers.set(name, value);
        return new Response(null, { status: 307, headers });
      }
      const auth = state.toAuth();
      if (!state.isAuthenticated || !auth?.userId) {
        if (/\.(?:mp4|jpe?g|png|webp|json)$/i.test(url.pathname)) return new Response('Sign-in required.', { status: 401, headers: privateHeaders });
        const signIn = new URL('/sign-in', CANONICAL_ORIGIN);
        signIn.searchParams.set('return_to', returnPath(url.pathname + url.search));
        return new Response(null, { status: 302, headers: { ...privateHeaders, Location: signIn.href } });
      }
      if (!await approved(client, auth.userId)) {
        return new Response(loginPage(env.CLERK_PUBLISHABLE_KEY, '/', true), { status: 403, headers: { ...privateHeaders, 'Content-Type': 'text/html; charset=utf-8' } });
      }
      return proceed({ headers: privateHeaders });
    } catch {
      // Includes unavailable Clerk APIs and malformed/invalid authentication.
      // No client-only fallback may expose the static dashboard.
      return new Response('Sign-in could not be verified. Please reload to try again.', { status: 503, headers: privateHeaders });
    }
  };
}
