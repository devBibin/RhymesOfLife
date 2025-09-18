document.addEventListener('DOMContentLoaded', () => {
  const _ = (window.gettext) ? window.gettext : (s) => s;

  const container = document.getElementById('posts-container');
  if (!container) return;

  const tabs               = document.querySelectorAll('.nav-tabs .nav-link');
  const searchForm         = document.getElementById('search-form');
  const searchInput        = document.getElementById('search-input');
  const currentFilterInput = document.getElementById('current-filter');

  function buildUrl({ filter, query, page }) {
    const params = new URLSearchParams();
    if (filter) params.set('filter', filter);
    if (query)  params.set('q', query);
    if (page)   params.set('page', page);
    const qs = params.toString();
    return `${location.pathname}${qs ? `?${qs}` : ''}`;
  }

  async function loadFragment(url) {
    try {
      const resp = await fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
      if (!resp.ok) return;
      const data = await resp.json();
      container.innerHTML = data.html;
      history.pushState(null, '', url);
    } catch {
      // optionally show a toast/alert here
    }
  }

  tabs.forEach((tab) => {
    tab.addEventListener('click', (e) => {
      e.preventDefault();
      const filter = tab.dataset.filter;
      const query  = searchInput.value.trim();
      if (currentFilterInput) currentFilterInput.value = filter;
      tabs.forEach((t) => t.classList.toggle('active', t === tab));
      loadFragment(buildUrl({ filter, query }));
    });
  });

  if (searchForm) {
    searchForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const filter = currentFilterInput?.value;
      const query  = searchInput.value.trim();
      loadFragment(buildUrl({ filter, query }));
    });
  }

  let debounce;
  if (searchInput) {
    searchInput.addEventListener('input', () => {
      clearTimeout(debounce);
      debounce = setTimeout(() => {
        const filter = currentFilterInput?.value;
        const query  = searchInput.value.trim();
        loadFragment(buildUrl({ filter, query }));
      }, 300);
    });
  }

  // Card click-through (ignore interactive elements)
  container.addEventListener('click', (e) => {
    const card = e.target.closest('.js-clickable-card');
    if (!card) return;
    if (e.target.closest('a, button, input, textarea, select, label')) return;
    const href = card.dataset.href;
    if (href) window.location.href = href;
  });

  // AJAX pagination
  container.addEventListener('click', (e) => {
    const link = e.target.closest('.pagination .page-link');
    if (!link) return;
    e.preventDefault();
    const url    = new URL(link.href, window.location.origin);
    const filter = url.searchParams.get('filter') || currentFilterInput?.value || '';
    const query  = url.searchParams.get('q') || searchInput?.value?.trim() || '';
    const page   = url.searchParams.get('page') || '';

    if (currentFilterInput) currentFilterInput.value = filter;
    if (searchInput) searchInput.value = query;
    tabs.forEach((t) => t.classList.toggle('active', t.dataset.filter === filter));

    loadFragment(buildUrl({ filter, query, page }));
  });

  // Handle back/forward navigation
  window.addEventListener('popstate', () => {
    loadFragment(location.href);
  });
});
