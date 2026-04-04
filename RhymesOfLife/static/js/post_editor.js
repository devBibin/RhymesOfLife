(function () {
  const existingWrap = document.getElementById('existing-images');
  if (!existingWrap) return;

  existingWrap.addEventListener('click', (e) => {
    const btn = e.target.closest('[data-remove-image]');
    if (!btn) return;
    const id = btn.getAttribute('data-remove-image');
    const checkbox = document.getElementById(`rm-${id}`);
    if (!checkbox) return;
    const slot = btn.closest('[data-existing-image-slot]');

    checkbox.checked = true;
    if (slot) {
      slot.classList.add('is-hidden');
    }

    document.dispatchEvent(new CustomEvent('existing:toggle', { detail: { active: true } }));
  });
})();
