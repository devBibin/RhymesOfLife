(function () {
  function onCopyClick(e) {
    const trigger = e.target.closest('[data-copy-link]');
    if (!trigger) return;
    e.preventDefault();
    const anchor = trigger.getAttribute('data-url') || '';
    const url = `${location.origin}${location.pathname}${location.search}${anchor}`;
    const ok = (msg) => alert((typeof gettext === 'function' ? gettext('Link copied') : 'Link copied') + '\n' + url);
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(url).then(ok).catch(() => ok());
    } else {
      ok();
    }
  }

  document.addEventListener('click', onCopyClick);
})();
