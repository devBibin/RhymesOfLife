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
  let reqSeq = 0;
  let reqAbort = null;

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

  async function loadFragment(opts, { pushState = true } = {}) {
    const apiUrl = buildApiUrl(opts);
    if (reqAbort) reqAbort.abort();
    reqAbort = new AbortController();
    const seq = ++reqSeq;
    try {
      const resp = await fetch(apiUrl, {
        headers: { 'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json' },
        credentials: 'same-origin',
        signal: reqAbort.signal,
      });
      if (!resp.ok) return;
      const ct = resp.headers.get('content-type') || '';
      if (!ct.includes('application/json')) return;
      const data = await resp.json();
      if (seq !== reqSeq) return;
      if (!data?.html) return;
      container.innerHTML = data.html;
      if (currentSortInput && opts.sort) currentSortInput.value = opts.sort;
      if (searchInput && Object.prototype.hasOwnProperty.call(opts, 'query')) {
        searchInput.value = opts.query || '';
      }
      if (pushState) history.pushState(opts, '', buildDisplayUrl(opts));
      attachPagination();
      activateSortButton(opts.sort || 'date');
    } catch (e) {
      if (e?.name === 'AbortError') return;
    }
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
    loadFragment(opts, { pushState: false });
  });

  activateSortButton(currentSortInput?.value || 'date');
  attachPagination();
});
