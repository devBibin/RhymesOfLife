document.addEventListener('DOMContentLoaded', function () {
  document.addEventListener('click', function (e) {
    const card = e.target.closest('.js-clickable-card');
    if (!card) return;
    if (e.target.closest('a, button, input, textarea, select, label')) return;
    const href = card.dataset.href;
    if (href) window.location.href = href;
  });
});
