// static/js/header.js
(() => {
  const qs = (sel, root = document) => root.querySelector(sel);
  const qsa = (sel, root = document) => Array.from(root.querySelectorAll(sel));

  const header = qs('.site-header');
  const mobileBtn = qs('#mobileMenuBtn');
  const overlay = qs('#mobileMenuOverlay');
  const nav = qs('#navContainer');

  if (!header) return;

  const isMobile = () => window.matchMedia('(max-width: 768px)').matches;
  let isLocked = false;

  const getScrollbarWidth = () => window.innerWidth - document.documentElement.clientWidth;

  const setBodyLock = (locked) => {
    if (locked === isLocked) return;

    if (locked) {
      const w = getScrollbarWidth();
      document.body.style.overflow = 'hidden';
      document.body.style.paddingRight = w > 0 ? `${w}px` : '';
      isLocked = true;
    } else {
      document.body.style.overflow = '';
      document.body.style.paddingRight = '';
      isLocked = false;
    }
  };

  // --- Bootstrap dropdown killing on mobile (Popper causes side menus)
  const disposeBootstrapDropdowns = (root = document) => {
    if (!window.bootstrap || !bootstrap.Dropdown) return;
    qsa('.dropdown-toggle[data-bs-toggle="dropdown"]', root).forEach((t) => {
      try {
        const inst = bootstrap.Dropdown.getInstance(t);
        if (inst) inst.dispose();
      } catch (_) {}
    });
  };

  const disableBootstrapDropdowns = () => {
    const scope = header;

    qsa('[data-bs-toggle="dropdown"]', scope).forEach((t) => {
      if (!t.hasAttribute('data-orig-bs-toggle')) {
        t.setAttribute('data-orig-bs-toggle', 'dropdown');
      }
      t.removeAttribute('data-bs-toggle');
      t.setAttribute('data-mobile-dropdown', 'true');
      t.setAttribute('role', 'button');
    });

    disposeBootstrapDropdowns(scope);

    // Убрать popper inline стили
    qsa('.dropdown-menu', scope).forEach((m) => {
      m.style.removeProperty('position');
      m.style.removeProperty('inset');
      m.style.removeProperty('top');
      m.style.removeProperty('left');
      m.style.removeProperty('right');
      m.style.removeProperty('bottom');
      m.style.removeProperty('transform');
    });
  };

  const enableBootstrapDropdowns = () => {
    qsa('[data-orig-bs-toggle="dropdown"]').forEach((t) => {
      t.setAttribute('data-bs-toggle', 'dropdown');
      t.removeAttribute('data-orig-bs-toggle');
      t.removeAttribute('data-mobile-dropdown');
    });
  };

  const closeAllMobileDropdowns = () => {
    qsa('.dropdown-menu.show', nav || document).forEach((m) => {
      m.classList.remove('show');
      m.style.removeProperty('transform');
      m.style.removeProperty('top');
      m.style.removeProperty('left');
      m.style.removeProperty('right');
      m.style.removeProperty('bottom');
    });

    qsa('.dropdown-toggle[aria-expanded="true"]', nav || document).forEach((t) => {
      t.setAttribute('aria-expanded', 'false');
    });

    qsa('.dropdown.is-open', nav || document).forEach((d) => {
      d.classList.remove('is-open');
    });
  };

  const setMenuState = (open) => {
    if (!mobileBtn || !overlay || !nav) return;

    mobileBtn.classList.toggle('active', open);
    overlay.classList.toggle('active', open);
    nav.classList.toggle('active', open);

    mobileBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
    setBodyLock(open);

    if (open) {
      nav.setAttribute('tabindex', '-1');
      nav.focus({ preventScroll: true });
      disableBootstrapDropdowns();
    } else {
      closeAllMobileDropdowns();
      mobileBtn.focus({ preventScroll: true });
      if (!isMobile()) enableBootstrapDropdowns();
    }
  };

  const isMenuOpen = () => mobileBtn?.classList.contains('active') || false;

  const getFocusable = (root) =>
    qsa(
      'a[href]:not([disabled]), button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
      root
    ).filter((el) => el.offsetParent !== null && el.style.display !== 'none');

  const trapFocus = (e) => {
    if (!isMobile() || !isMenuOpen() || !nav) return;
    if (e.key !== 'Tab') return;

    const focusables = getFocusable(nav);
    if (!focusables.length) return;

    const first = focusables[0];
    const last = focusables[focusables.length - 1];
    const active = document.activeElement;

    if (e.shiftKey && active === first) {
      e.preventDefault();
      last.focus();
      return;
    }

    if (!e.shiftKey && active === last) {
      e.preventDefault();
      first.focus();
    }
  };

  // Mobile accordion toggle
  const handleMobileDropdown = (toggle) => {
    if (!toggle || !isMobile()) return;

    const parent = toggle.closest('.dropdown');
    if (!parent) return;

    const menu = parent.querySelector(':scope > .dropdown-menu');
    if (!menu) return;

    const isOpen = menu.classList.contains('show');

    if (!isOpen) closeAllMobileDropdowns();

    menu.style.removeProperty('transform');
    menu.style.removeProperty('top');
    menu.style.removeProperty('left');
    menu.style.removeProperty('right');
    menu.style.removeProperty('bottom');

    menu.classList.toggle('show', !isOpen);
    toggle.setAttribute('aria-expanded', !isOpen ? 'true' : 'false');
    parent.classList.toggle('is-open', !isOpen);

    if (!isOpen) {
      setTimeout(() => {
        const rect = menu.getBoundingClientRect();
        if (rect.bottom > window.innerHeight) {
          menu.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
      }, 60);
    }
  };

  const onNavClick = (e) => {
    if (!isMobile()) return;

    const toggle = e.target.closest('.dropdown-toggle');
    if (toggle && toggle.hasAttribute('data-mobile-dropdown')) {
      e.preventDefault();
      e.stopPropagation();
      handleMobileDropdown(toggle);
      return;
    }

    const link = e.target.closest('a[href]:not(.dropdown-toggle)');
    if (link && isMenuOpen()) setMenuState(false);
  };

  const onDocClick = (e) => {
    if (!isMobile() || !isMenuOpen()) return;
    if (!nav.contains(e.target) && !mobileBtn.contains(e.target)) setMenuState(false);
  };

  const onResize = () => {
    if (isMobile()) {
      if (isMenuOpen()) disableBootstrapDropdowns();
    } else {
      setMenuState(false);
      enableBootstrapDropdowns();
    }
  };

  const onScroll = () => {
    header.classList.toggle('scrolled', window.scrollY > 20);
  };

  // Initialize
  if (mobileBtn) {
    mobileBtn.setAttribute('aria-controls', 'navContainer');
    mobileBtn.setAttribute('aria-expanded', 'false');

    mobileBtn.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      setMenuState(!isMenuOpen());
    });
  }

  if (overlay) overlay.addEventListener('click', () => setMenuState(false));
  if (nav) nav.addEventListener('click', onNavClick);

  document.addEventListener('click', onDocClick);
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && isMenuOpen()) {
      setMenuState(false);
      return;
    }
    trapFocus(e);
  });

  window.addEventListener('resize', onResize, { passive: true });
  window.addEventListener('scroll', onScroll, { passive: true });

  onResize();
  onScroll();

  // Russian text optimization
  const lang = document.documentElement.lang || '';
  const isRu = lang === 'ru' || lang.startsWith('ru');

  if (isRu) {
    const ruElements = qsa('.nav-link, .action-btn, .lang-switcher, .dropdown-item, .logo-main, .logo-subtitle');
    ruElements.forEach((el) => el.classList && el.classList.add('ru-text-fix', 'ru-header-text'));
    qsa('.logo-main').forEach((el) => el.classList && el.classList.add('ru-logo-text'));
    qsa('.nav-link span, .action-btn span').forEach((el) => el.classList && el.classList.add('ru-overflow-fix'));
  }

  if (isMobile()) disableBootstrapDropdowns();

  document.addEventListener('click', (e) => {
    if (isMobile() && e.target.closest('.dropdown-menu')) {
      e.stopPropagation();
    }
  });

  if (window.location.hash === '#notifications' && isMobile()) {
    setTimeout(() => {
      const notificationsToggle = qs('#notificationsDropdown');
      if (notificationsToggle && !isMenuOpen()) {
        setMenuState(true);
        setTimeout(() => handleMobileDropdown(notificationsToggle), 120);
      }
    }, 500);
  }
})();
