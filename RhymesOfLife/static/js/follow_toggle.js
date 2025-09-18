(function () {
  function csrf() {
    const m = document.cookie.match(/(?:^|;)\s*csrftoken=([^;]+)/);
    return m ? decodeURIComponent(m[1]) : '';
  }

  function setState(btn, following) {
    btn.dataset.following = following ? '1' : '0';
    btn.classList.toggle('btn-primary', !following);
    btn.classList.toggle('btn-outline-secondary', following);
    btn.textContent = following ? gettext('Unfollow') : gettext('Follow');
  }

  async function toggle(btn) {
    const following = btn.dataset.following === '1';
    const url = following ? btn.dataset.urlUnfollow : btn.dataset.urlFollow;

    try {
      const resp = await fetch(url, {
        method: 'POST',
        headers: { 'X-CSRFToken': csrf(), 'X-Requested-With': 'XMLHttpRequest' }
      });
      if (!resp.ok) throw new Error('request failed');
      setState(btn, !following);
    } catch (e) {
    }
  }

  document.addEventListener('click', (e) => {
    const btn = e.target.closest('[data-follow-toggle]');
    if (!btn) return;
    e.preventDefault();
    toggle(btn);
  });
})();
