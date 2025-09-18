function ajaxLoad(params) {
  const url = new URL(window.location.href);
  Object.entries(params).forEach(([k, v]) => {
    if (v === null || v === undefined || v === '') url.searchParams.delete(k);
    else url.searchParams.set(k, v);
  });
  return fetch(url.toString(), { headers: { 'X-Requested-With': 'XMLHttpRequest' }})
    .then(async (r) => {
      const text = await r.text();
      if (!r.ok) throw new Error(text || r.statusText);
      let data;
      try { data = JSON.parse(text); } catch { throw new Error(text); }
      document.getElementById('posts-container').innerHTML = data.html;
      initLikes();
      initCommentForms();
      attachPagination();
    })
    .catch((e) => console.error(e));
}

function attachTabs() {
  document.querySelectorAll('.nav.nav-tabs [data-filter]').forEach(a => {
    a.addEventListener('click', (e) => {
      e.preventDefault();
      const f = a.getAttribute('data-filter');
      document.getElementById('current-filter').value = f;
      document.querySelectorAll('.nav.nav-tabs .nav-link').forEach(l => l.classList.remove('active'));
      a.classList.add('active');
      const q = document.getElementById('search-input')?.value || '';
      ajaxLoad({ filter: f, q, page: 1 });
    });
  });
}

function attachSearch() {
  const form = document.getElementById('feed-search');
  if (!form) return;
  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const f = document.getElementById('current-filter').value;
    const q = document.getElementById('search-input').value;
    ajaxLoad({ filter: f, q, page: 1 });
  });
}

function attachPagination() {
  document.querySelectorAll('#posts-container .pagination a.page-link').forEach(a => {
    a.addEventListener('click', (e) => {
      e.preventDefault();
      const url = new URL(a.getAttribute('href'), window.location.origin);
      const f = url.searchParams.get('filter') || document.getElementById('current-filter').value;
      const p = url.searchParams.get('page') || 1;
      const q = document.getElementById('search-input')?.value || '';
      ajaxLoad({ filter: f, q, page: p });
    });
  });
}

document.addEventListener('DOMContentLoaded', () => {
  attachTabs();
  attachSearch();
  attachPagination();
});
