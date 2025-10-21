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
    })
    .catch((e) => console.error(e));
}

function attachTabs() {
  document.querySelectorAll('.nav.nav-tabs [data-filter]').forEach((a) => {
    a.addEventListener('click', (e) => {
      e.preventDefault();
      const f = a.getAttribute('data-filter');
      document.getElementById('current-filter').value = f;
      document.querySelectorAll('.nav.nav-tabs .nav-link').forEach((l) => l.classList.remove('active'));
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

document.addEventListener('DOMContentLoaded', () => {
  attachTabs();
  attachPagination();
  if (typeof window.initCommentForms === 'function') window.initCommentForms();
  bindModerationSwitch();
});
