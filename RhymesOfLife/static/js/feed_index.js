function ajaxLoad(params) {
  const url = new URL(window.location.href);
  Object.entries(params).forEach(([k, v]) => {
    if (v === null || v === undefined || v === '') url.searchParams.delete(k);
    else url.searchParams.set(k, v);
  });

  return fetch(url.toString(), { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
    .then(async (r) => {
      const text = await r.text();
      if (!r.ok) throw new Error(text || r.statusText);
      let data;
      try { data = JSON.parse(text); } catch { throw new Error(text); }
      document.getElementById('posts-container').innerHTML = data.html;
      if (typeof window.initCommentForms === 'function') window.initCommentForms();
      attachPagination();
      if (history && history.replaceState) history.replaceState(null, '', url.toString());
      document.dispatchEvent(new CustomEvent('feed:reloaded'));
    })
    .catch((e) => console.error(e));
}

function attachTabs() {
  document.querySelectorAll('.nav [data-filter]').forEach((a) => {
    a.addEventListener('click', (e) => {
      e.preventDefault();
      const f = a.getAttribute('data-filter');
      document.getElementById('current-filter').value = f;

      const nav = a.closest('.nav');
      if (nav) nav.querySelectorAll('.nav-link').forEach((l) => l.classList.remove('active'));
      a.classList.add('active');

      ajaxLoad({ filter: f, page: 1 });
    });
  });
}

function attachPagination() {
  document.querySelectorAll('#posts-container .pagination a.page-link').forEach((a) => {
    a.addEventListener('click', (e) => {
      e.preventDefault();
      const url = new URL(a.getAttribute('href'), window.location.origin);
      const f = url.searchParams.get('filter') || document.getElementById('current-filter').value;
      const p = url.searchParams.get('page') || 1;
      ajaxLoad({ filter: f, page: p });
    });
  });
}

function getCSRF(scopeEl) {
  const local = scopeEl && scopeEl.querySelector ? scopeEl.querySelector('[name=csrfmiddlewaretoken]') : null;
  if (local && local.value) return local.value;
  const raw = (document.cookie || '').split('; ').find(r => r.startsWith('csrftoken='));
  return raw ? decodeURIComponent(raw.split('=')[1] || '') : '';
}

function bindModerationSwitch() {
  const sw = document.getElementById('mod-switch');
  if (!sw) return;
  sw.addEventListener('change', async () => {
    const mode = sw.checked ? 'uncensored' : 'censored';
    const csrftoken = getCSRF(document);

    const formUser = new FormData();
    formUser.append('mode', mode);
    try {
      await fetch(sw.getAttribute('data-url-user'), {
        method: 'POST',
        headers: {'X-Requested-With':'XMLHttpRequest','X-CSRFToken':csrftoken,'Accept':'application/json'},
        body: formUser
      });
    } catch (_) {}

    const globalUrl = sw.getAttribute('data-url-global');
    if (globalUrl) {
      const formGlobal = new FormData();
      formGlobal.append('mode', mode);
      formGlobal.append('threshold', '');
      try {
        await fetch(globalUrl, {
          method: 'POST',
          headers: {'X-Requested-With':'XMLHttpRequest','X-CSRFToken':csrftoken,'Accept':'application/json'},
          body: formGlobal
        });
      } catch (_) {}
    }

    ajaxLoad({ filter: document.getElementById('current-filter').value, page: 1 });
  });
}

function toast(msg, type='info') {
  let box = document.getElementById('toast-box');
  if (!box) {
    box = document.createElement('div');
    box.id = 'toast-box';
    box.style.position = 'fixed';
    box.style.right = '16px';
    box.style.bottom = '16px';
    box.style.zIndex = '2000';
    document.body.appendChild(box);
  }
  const el = document.createElement('div');
  el.className = `alert alert-${type} shadow-sm mt-2`;
  el.role = 'alert';
  el.textContent = msg;
  box.appendChild(el);
  setTimeout(() => el.remove(), 4000);
}

document.addEventListener('DOMContentLoaded', () => {
  attachTabs();
  attachPagination();
  if (typeof window.initCommentForms === 'function') window.initCommentForms();
  bindModerationSwitch();

  document.addEventListener('follow:changed', () => {
    const f = document.getElementById('current-filter').value;
    if (f === 'subscriptions') ajaxLoad({ filter: f, page: 1 });
  });

  document.addEventListener('post:updated', (e) => {
    const f = document.getElementById('current-filter').value;
    if (['mine','latest','pending','subscriptions'].includes(f)) {
      ajaxLoad({ filter: f, page: 1 });
    }
    if (e.detail && e.detail.message) toast(e.detail.message, 'success');
  });

  document.addEventListener('post:created', (e) => {
    const f = document.getElementById('current-filter').value;
    if (f === 'mine' || f === 'latest') {
      ajaxLoad({ filter: f, page: 1 });
    }
    if (e.detail && e.detail.message) toast(e.detail.message, e.detail.approved ? 'success' : 'warning');
  });
});
