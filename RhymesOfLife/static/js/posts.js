function initLikes() {
  document.addEventListener('click', async (e) => {
    const likeBtn = e.target.closest('[data-like]');
    if (!likeBtn) return;
    e.preventDefault();
    const url = likeBtn.getAttribute('href');
    const r = await fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
    if (!r.ok) return;
    const data = await r.json();
    const countEl = likeBtn.querySelector('[data-count]');
    if (countEl) countEl.textContent = data.likes;
    likeBtn.classList.toggle('active', data.active);
  });
}

function initCommentForms() {
  document.querySelectorAll('form[data-comment-form]').forEach((form) => {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const r = await fetch(form.action, {
        method: 'POST',
        body: new FormData(form),
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
      });
      if (!r.ok) return;
      const data = await r.json();
      const ul = document.getElementById('comments-' + data.post);
      if (!ul) return;
      const li = document.createElement('li');
      li.className = 'mb-2';
      li.innerHTML = `<strong>${data.author}</strong>: ${data.text}`;
      ul.prepend(li);
      form.reset();
    });
  });
}

function initDropzone() {
  const dz = document.getElementById('dropzone');
  const fi = document.getElementById('file-input');
  const preview = document.getElementById('preview');
  const opener = document.querySelector('[data-open-file]');
  if (!dz || !fi || !preview) return;

  const renderPreview = () => {
    preview.innerHTML = '';
    Array.from(fi.files).forEach((f) => {
      const url = URL.createObjectURL(f);
      const col = document.createElement('div');
      col.className = 'col-4';
      col.innerHTML = `<img src="${url}" class="img-fluid rounded" alt="">`;
      preview.appendChild(col);
    });
  };

  if (opener) opener.addEventListener('click', () => fi.click());
  dz.addEventListener('click', () => fi.click());
  dz.addEventListener('dragover', (e) => { e.preventDefault(); dz.classList.add('bg-light'); });
  dz.addEventListener('dragleave', () => dz.classList.remove('bg-light'));
  dz.addEventListener('drop', (e) => { e.preventDefault(); dz.classList.remove('bg-light'); fi.files = e.dataTransfer.files; renderPreview(); });
  fi.addEventListener('change', renderPreview);
}

document.addEventListener('DOMContentLoaded', () => {
  initLikes();
  initCommentForms();
  initDropzone();
});
