document.addEventListener('DOMContentLoaded', () => {
  const gettext = window.gettext || ((s) => s);

  const container = document.getElementById('posts-container');
  if (!container) return;

  const sortButtons      = document.querySelectorAll('[data-sort]');
  const filterButtons    = document.querySelectorAll('[data-filter]');
  const searchForm       = document.getElementById('search-form');
  const searchInput      = document.getElementById('search-input');
  const currentSortInput = document.getElementById('current-sort');
  const currentFilterInput = document.getElementById('current-filter');
  const filtersToggle = document.getElementById('articleFiltersToggle');
  const filtersPopover = document.getElementById('articleFiltersPopover');
  const articleSubscriptionToggle = document.getElementById('articleSubscriptionToggle');
  const articleSubscriptionSettingsBtn = document.getElementById('articleSubscriptionSettingsBtn');
  const articleSubscriptionSettingsModal = document.getElementById('articleSubscriptionSettingsModal');
  const articleSubscriptionEnabledInput = document.getElementById('article-subscription-enabled');
  const articleSiteEnabledInput = document.getElementById('article-site-enabled');
  const articleTgEnabledInput = document.getElementById('article-tg-enabled');
  const articleEmailEnabledInput = document.getElementById('article-email-enabled');
  const saveArticleSubscriptionSettingsBtn = document.getElementById('saveArticleSubscriptionSettings');
  const subscriptionSettingsUrl = articleSubscriptionToggle?.dataset.settingsUrl || null;
  const subscriptionModalInstance = articleSubscriptionSettingsModal && window.bootstrap
    ? window.bootstrap.Modal.getOrCreateInstance(articleSubscriptionSettingsModal)
    : null;

  const ajaxBase = container.dataset.api;
  const pagePath = location.pathname;
  let reqSeq = 0;
  let reqAbort = null;
  let subscriptionState = null;

  function getCsrfToken() {
    const cookie = document.cookie
      .split('; ')
      .find((row) => row.startsWith('csrftoken='));
    return cookie ? decodeURIComponent(cookie.split('=').slice(1).join('=')) : '';
  }

  function buildQuery({ sort, query, page, filter }) {
    const params = new URLSearchParams();
    if (sort)  params.set('sort', sort);
    if (query) params.set('q', query);
    if (page)  params.set('page', page);
    if (filter) params.set('filter', filter);
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

  function activateFilterButton(value) {
    filterButtons.forEach((b) => {
      const isActive = (b.getAttribute('data-filter') || '') === (value || '');
      b.classList.toggle('is-active', isActive);
      b.setAttribute('aria-pressed', isActive ? 'true' : 'false');
    });
  }

  function currentOpts(extra = {}) {
    return {
      sort:  currentSortInput?.value || 'date',
      filter: currentFilterInput?.value || '',
      query: searchInput?.value?.trim() || '',
      ...extra,
    };
  }

  function syncControlsFromCurrentState() {
    activateSortButton(currentSortInput?.value || 'date');
    activateFilterButton(currentFilterInput?.value || '');
  }

  function setFiltersPopoverOpen(open) {
    if (!filtersToggle || !filtersPopover) return;
    filtersPopover.hidden = !open;
    filtersPopover.classList.toggle('is-open', open);
    filtersToggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    filtersToggle.classList.toggle('is-active', open);
  }

  function applySubscriptionStateToUi(state) {
    subscriptionState = state ? { ...state } : null;
    if (!articleSubscriptionToggle || !subscriptionState) return;

    const enabled = !!subscriptionState.enabled;
    articleSubscriptionToggle.dataset.enabled = enabled ? 'true' : 'false';
    articleSubscriptionToggle.classList.toggle('rl-primary-btn', !enabled);
    articleSubscriptionToggle.classList.toggle('rl-secondary-btn', enabled);
    const icon = articleSubscriptionToggle.querySelector('i');
    const label = articleSubscriptionToggle.querySelector('.article-subscription-toggle__label');
    if (icon) {
      icon.className = `bi ${enabled ? 'bi-bell-fill' : 'bi-bell'}`;
    }
    if (label) {
      label.textContent = enabled
        ? (articleSubscriptionToggle.dataset.labelEnabled || 'Subscribed')
        : (articleSubscriptionToggle.dataset.labelDisabled || 'Subscribe');
    }

    if (articleSubscriptionEnabledInput) articleSubscriptionEnabledInput.checked = enabled;
    if (articleSiteEnabledInput) articleSiteEnabledInput.checked = !!subscriptionState.site_notifications_enabled;
    if (articleTgEnabledInput) articleTgEnabledInput.checked = !!subscriptionState.tg_notifications_enabled;
    if (articleEmailEnabledInput) articleEmailEnabledInput.checked = !!subscriptionState.email_notifications_enabled;

    const channelsDisabled = !enabled;
    [articleSiteEnabledInput, articleTgEnabledInput, articleEmailEnabledInput].forEach((input) => {
      if (input) input.disabled = channelsDisabled;
    });
  }

  async function fetchSubscriptionSettings() {
    if (!subscriptionSettingsUrl) return null;
    const resp = await fetch(subscriptionSettingsUrl, {
      headers: { 'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json' },
      credentials: 'same-origin',
    });
    if (!resp.ok) return null;
    const data = await resp.json();
    if (data?.status !== 'ok' || !data.settings) return null;
    applySubscriptionStateToUi(data.settings);
    return data.settings;
  }

  async function saveSubscriptionSettings(payload) {
    if (!subscriptionSettingsUrl) return null;
    const body = new URLSearchParams();
    Object.entries(payload || {}).forEach(([key, value]) => {
      body.set(key, value ? '1' : '0');
    });
    const resp = await fetch(subscriptionSettingsUrl, {
      method: 'POST',
      headers: {
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': getCsrfToken(),
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Accept': 'application/json',
      },
      credentials: 'same-origin',
      body: body.toString(),
    });
    if (!resp.ok) return null;
    const data = await resp.json();
    if (data?.status !== 'ok' || !data.settings) return null;
    applySubscriptionStateToUi(data.settings);
    return data.settings;
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
      if (currentFilterInput && Object.prototype.hasOwnProperty.call(opts, 'filter')) {
        currentFilterInput.value = opts.filter || '';
      }
      if (searchInput && Object.prototype.hasOwnProperty.call(opts, 'query')) {
        searchInput.value = opts.query || '';
      }
      if (pushState) history.pushState(opts, '', buildDisplayUrl(opts));
      attachPagination();
      syncControlsFromCurrentState();
      return true;
    } catch (e) {
      if (e?.name === 'AbortError') return;
    }
    return false;
  }

  filterButtons.forEach((btn) => {
    btn.addEventListener('click', async (e) => {
      e.preventDefault();
      const filter = btn.getAttribute('data-filter') || '';
      if (currentFilterInput) currentFilterInput.value = filter;
      activateFilterButton(filter);
      const ok = await loadFragment(currentOpts({ page: 1, filter }));
      if (btn.closest('#articleFiltersPopover')) {
        setFiltersPopoverOpen(false);
      }
      if (!ok && btn.href) {
        window.location.href = btn.href;
      }
    });
  });

  sortButtons.forEach((btn) => {
    btn.addEventListener('click', async (e) => {
      e.preventDefault();
      const sort = btn.getAttribute('data-sort') || 'date';
      if (currentSortInput) currentSortInput.value = sort;
      activateSortButton(sort);
      await loadFragment(currentOpts({ page: 1, sort }));
      if (btn.closest('#articleFiltersPopover')) {
        setFiltersPopoverOpen(false);
      }
    });
  });

  if (filtersToggle && filtersPopover) {
    filtersToggle.addEventListener('click', (e) => {
      e.preventDefault();
      const isOpen = filtersToggle.getAttribute('aria-expanded') === 'true';
      setFiltersPopoverOpen(!isOpen);
    });

    document.addEventListener('click', (e) => {
      if (filtersPopover.hidden) return;
      const target = e.target;
      if (filtersPopover.contains(target) || filtersToggle.contains(target)) return;
      setFiltersPopoverOpen(false);
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        setFiltersPopoverOpen(false);
      }
    });
  }

  if (articleSubscriptionEnabledInput) {
    articleSubscriptionEnabledInput.addEventListener('change', () => {
      const enabled = !!articleSubscriptionEnabledInput.checked;
      [articleSiteEnabledInput, articleTgEnabledInput, articleEmailEnabledInput].forEach((input) => {
        if (!input) return;
        input.disabled = !enabled;
        if (enabled && !articleSiteEnabledInput?.checked && !articleTgEnabledInput?.checked && !articleEmailEnabledInput?.checked) {
          articleSiteEnabledInput.checked = true;
        }
      });
    });
  }

  if (articleSubscriptionToggle) {
    articleSubscriptionToggle.addEventListener('click', async () => {
      const enabled = articleSubscriptionToggle.dataset.enabled === 'true';
      const next = await saveSubscriptionSettings({
        enabled: !enabled,
        site_notifications_enabled: !enabled ? true : false,
        tg_notifications_enabled: !enabled ? (subscriptionState?.tg_notifications_enabled ?? true) : false,
        email_notifications_enabled: !enabled ? (subscriptionState?.email_notifications_enabled ?? true) : false,
      });
      if (!next) return;
      if (!enabled && subscriptionModalInstance) {
        subscriptionModalInstance.show();
      }
    });
  }

  if (articleSubscriptionSettingsBtn && articleSubscriptionSettingsModal) {
    articleSubscriptionSettingsBtn.addEventListener('click', async () => {
      await fetchSubscriptionSettings();
    });
  }

  if (saveArticleSubscriptionSettingsBtn) {
    saveArticleSubscriptionSettingsBtn.addEventListener('click', async () => {
      const next = await saveSubscriptionSettings({
        enabled: !!articleSubscriptionEnabledInput?.checked,
        site_notifications_enabled: !!articleSiteEnabledInput?.checked,
        tg_notifications_enabled: !!articleTgEnabledInput?.checked,
        email_notifications_enabled: !!articleEmailEnabledInput?.checked,
      });
      if (next && subscriptionModalInstance) {
        subscriptionModalInstance.hide();
      }
    });
  }

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
      filter: params.get('filter') || '',
      query: params.get('q') || '',
      page: params.get('page') || '1',
    };
    if (currentSortInput) currentSortInput.value = opts.sort || 'date';
    if (currentFilterInput) currentFilterInput.value = opts.filter || '';
    if (searchInput) searchInput.value = opts.query || '';
    loadFragment(opts, { pushState: false });
  });

  syncControlsFromCurrentState();
  attachPagination();
  if (articleSubscriptionToggle) {
    fetchSubscriptionSettings().catch(() => {});
  }
});
