(function () {
  const existingWrap = document.getElementById('existing-images');
  if (!existingWrap) return;

  existingWrap.addEventListener('click', (e) => {
    const btn = e.target.closest('[data-remove-image]');
    if (!btn) return;
    const id = btn.getAttribute('data-remove-image');
    const checkbox = document.getElementById(`rm-${id}`);
    if (!checkbox) return;

    const active = btn.classList.toggle('btn-danger');
    btn.classList.toggle('btn-light', !active);
    checkbox.checked = active;

    document.dispatchEvent(new CustomEvent('existing:toggle', { detail: { active } }));
  });
})();
