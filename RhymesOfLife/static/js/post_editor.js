(function () {
  const dz = document.getElementById('dropzone');
  const input = document.getElementById('images-input');
  const pick = document.getElementById('pick-files');
  const preview = document.getElementById('new-files');
  const existingWrap = document.getElementById('existing-images');

  if (!dz || !input || !pick) return;

  let dt = new DataTransfer();

  function renderPreview() {
    preview.innerHTML = '';
    Array.from(dt.files).forEach(file => {
      const col = document.createElement('div');
      col.className = 'col-6 col-md-4';
      const card = document.createElement('div');
      card.className = 'border rounded p-1';
      const img = document.createElement('img');
      img.className = 'img-fluid rounded';
      img.alt = file.name;
      card.appendChild(img);
      col.appendChild(card);
      preview.appendChild(col);

      const reader = new FileReader();
      reader.onload = e => { img.src = e.target.result; };
      reader.readAsDataURL(file);
    });
  }

  function addFiles(files) {
    Array.from(files).forEach(f => dt.items.add(f));
    input.files = dt.files;
    renderPreview();
  }

  pick.addEventListener('click', () => input.click());
  input.addEventListener('change', e => addFiles(e.target.files));

  ['dragenter','dragover'].forEach(ev =>
    dz.addEventListener(ev, e => { e.preventDefault(); dz.classList.add('dragover'); })
  );
  ['dragleave','drop'].forEach(ev =>
    dz.addEventListener(ev, e => { e.preventDefault(); dz.classList.remove('dragover'); })
  );
  dz.addEventListener('drop', e => {
    const files = e.dataTransfer.files;
    if (files && files.length) addFiles(files);
  });

  if (existingWrap) {
    existingWrap.addEventListener('click', e => {
      const btn = e.target.closest('[data-remove-image]');
      if (!btn) return;
      const id = btn.getAttribute('data-remove-image');
      const checkbox = document.getElementById(`rm-${id}`);
      if (!checkbox) return;
      const active = btn.classList.toggle('btn-danger');
      btn.classList.toggle('btn-light', !active);
      checkbox.checked = active;
    });
  }
})();
