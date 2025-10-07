document.addEventListener('DOMContentLoaded', () => {
  const _ = (window.gettext) ? window.gettext : (s) => s;

  const container = document.getElementById('posts-container');
  if (!container) return;

  const sortButtons      = document.querySelectorAll('[data-sort]');
  const searchForm       = document.getElementById('search-form');
  const searchInput      = document.getElementById('search-input');
  const currentSortInput = document.getElementById('current-sort');

  const ajaxBase = container.dataset.api;
  const pagePath = location.pathname;

  function buildQuery({ sort, query, page }) {
    const params = new URLSearchParams();
    if (sort)  params.set('sort', sort);
    if (query) params.set('q', query);
    if (page)  params.set('page', page);
    return params.toString();
  }
  function buildApiUrl(opts) {
    const qs = buildQuery(opts);
    return `${ajaxBase}${qs ? `?${qs}` : ''}`;
  }
  function buildDisplayUrl(opts) {
    const qs = buildQuery(opts);
    return `${pagePath}${qs ? `?${qs}` : ''}`;
  }

  function activateSortButton(value) {
    sortButtons.forEach((b) => {
      const isActive = b.getAttribute('data-sort') === value;
      b.classList.toggle('is-active', isActive);
      b.setAttribute('aria-pressed', isActive ? 'true' : 'false');
    });
  }

  function currentOpts(extra = {}) {
    return {
      sort:  currentSortInput?.value || 'date',
      query: searchInput?.value?.trim() || '',
      ...extra,
    };
  }

  async function loadFragment(opts) {
    const apiUrl = buildApiUrl(opts);
    try {
      const resp = await fetch(apiUrl, { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
      if (!resp.ok) return;
      const data = await resp.json();
      if (!data?.html) return;
      container.innerHTML = data.html;
      history.pushState(opts, '', buildDisplayUrl(opts));
      attachPagination();
      activateSortButton(opts.sort || 'date');
    } catch {}
  }

  sortButtons.forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const sort = btn.getAttribute('data-sort') || 'date';
      if (currentSortInput) currentSortInput.value = sort;
      activateSortButton(sort);
      loadFragment(currentOpts({ page: 1, sort }));
    });
  });

  if (searchForm) {
    searchForm.addEventListener('submit', (e) => {
      e.preventDefault();
      loadFragment(currentOpts({ page: 1 }));
    });
  }

  let debounce;
  if (searchInput) {
    searchInput.addEventListener('input', () => {
      clearTimeout(debounce);
      debounce = setTimeout(() => {
        loadFragment(currentOpts({ page: 1 }));
      }, 300);
    });
  }

  function attachPagination() {
    container.querySelectorAll('.pagination a.page-link').forEach((a) => {
      a.addEventListener('click', (e) => {
        e.preventDefault();
        const url = new URL(a.href, window.location.origin);
        const page = url.searchParams.get('page') || '1';
        loadFragment(currentOpts({ page }));
      });
    });
  }

  window.addEventListener('popstate', (e) => {
    const state = e.state;
    const params = new URLSearchParams(location.search);
    const opts = state || {
      sort: params.get('sort') || 'date',
      query: params.get('q') || '',
      page: params.get('page') || '1',
    };
    fetch(buildApiUrl(opts), { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
      .then(r => r.ok ? r.json() : null)
      .then(d => {
        if (d?.html) {
          container.innerHTML = d.html;
          attachPagination();
          activateSortButton(opts.sort || 'date');
        }
      })
      .catch(() => {});
  });

  activateSortButton(currentSortInput?.value || 'date');
  attachPagination();
});
