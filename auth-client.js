// Keep the short-lived Clerk session cookie refreshed while the static lab is open.
window.addEventListener('load', async () => {
  try {
    await window.Clerk.load({ ui: { ClerkUI: window.__internal_ClerkUICtor } });
    if (!window.Clerk.session) {
      location.replace('/sign-in?return_to=' + encodeURIComponent(location.pathname + location.search));
      return;
    }
    const account = document.createElement('div');
    account.setAttribute('aria-label', 'AI Simple account');
    Object.assign(account.style, { position: 'fixed', top: '18px', right: '24px', zIndex: '100' });
    document.body.append(account);
    window.Clerk.mountUserButton(account, { afterSignOutUrl: '/sign-in' });
  } catch {
    const notice = document.createElement('p');
    notice.textContent = 'Your sign-in could not be refreshed. Reload the page before continuing.';
    Object.assign(notice.style, { position: 'fixed', bottom: '16px', right: '16px', padding: '12px', background: '#18181b', color: '#fca5a5', zIndex: '100' });
    document.body.append(notice);
  }
});
