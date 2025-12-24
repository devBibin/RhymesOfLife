document.addEventListener('click', (e) => {
  const el = e.target.closest('.js-clickable-card');
  if (!el) return;

  const a = e.target.closest('a, button, input, textarea, select, label');
  if (a) return;

  const href = el.getAttribute('data-href');
  if (href) window.location.href = href;
});
