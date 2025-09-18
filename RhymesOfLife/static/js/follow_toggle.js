(function () {
  const _ = window.gettext ? window.gettext : (s) => s;

  function csrf() {
    const m = document.cookie.match(/(?:^|;)\s*csrftoken=([^;]+)/);
    return m ? decodeURIComponent(m[1]) : '';
  }

  function label(btn, following) {
    const follow = btn.getAttribute('data-label-follow');
    const unfollow = btn.getAttribute('data-label-unfollow');
    return following ? (unfollow || _('Unfollow')) : (follow || _('Follow'));
  }

  function setState(btn, following) {
    btn.dataset.following = following ? '1' : '0';
    btn.classList.toggle('btn-primary', !following);
    btn.classList.toggle('btn-outline-secondary', following);
    btn.textContent = label(btn, following);
    btn.setAttribute('aria-pressed', following ? 'true' : 'false');
  }

  function setFollowersCount(authorId, count) {
    if (typeof count !== 'number') return false;
    document.querySelectorAll(`[data-followers-count][data-author-id="${authorId}"]`)
      .forEach((el) => { el.textContent = String(Math.max(0, count)); });
    return true;
  }

  function bumpFollowersCount(authorId, delta) {
    if (!authorId || !delta) return;
    document.querySelectorAll(`[data-followers-count][data-author-id="${authorId}"]`)
      .forEach((el) => {
        const n = parseInt(el.textContent.trim(), 10);
        const v = isNaN(n) ? 0 : n;
        el.textContent = String(Math.max(0, v + delta));
      });
  }

  async function toggle(btn) {
    const following = btn.dataset.following === '1';
    const url = following ? btn.dataset.urlUnfollow : btn.dataset.urlFollow;
    const authorId = btn.getAttribute('data-author-id');
    if (!url) return;

    btn.disabled = true;
    try {
      const resp = await fetch(url, {
        method: 'POST',
        headers: { 'X-CSRFToken': csrf(), 'X-Requested-With': 'XMLHttpRequest' }
      });

      if (resp.status === 401) {
        const login = document.querySelector('#like-login-link,[data-login-url]');
        if (login) window.location.href = login.href || login.dataset.loginUrl;
        return;
      }
      if (!resp.ok) throw new Error('request failed');

      const data = await resp.json().catch(() => ({}));
      setState(btn, !following);

      if (!(setFollowersCount(authorId, Number(data.followers_count)))) {
        bumpFollowersCount(authorId, following ? -1 : 1);
      }

      document.dispatchEvent(new CustomEvent('follow:changed', {
        detail: { following: !following, button: btn, authorId, followers_count: data.followers_count }
      }));
    } catch (_) {
    } finally {
      btn.disabled = false;
    }
  }

  document.addEventListener('click', (e) => {
    const btn = e.target.closest('[data-follow-toggle]');
    if (!btn) return;
    e.preventDefault();
    toggle(btn);
  });
})();
