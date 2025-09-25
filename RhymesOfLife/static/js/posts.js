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
      if (data.html) {
        const t = document.createElement('template');
        t.innerHTML = data.html.trim();
        ul.prepend(t.content);
      }
      form.reset();
    });
  });
}

function initCommentsMore() {
  document.addEventListener('click', async (e) => {
    const btn = e.target.closest('[data-comments-more]');
    if (!btn) return;
    e.preventDefault();

    const postId = btn.dataset.postId;
    const url = btn.dataset.url || `/posts/${postId}/comments/`;
    const offset = parseInt(btn.dataset.offset || '0', 10);
    const limit = parseInt(btn.dataset.limit || '10', 10);

    const qs = new URLSearchParams({ offset: String(offset), limit: String(limit) });
    const r = await fetch(`${url}?${qs.toString()}`, { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
    if (!r.ok) return;

    const data = await r.json();
    const ul = document.getElementById(`comments-${postId}`);
    if (!ul) return;

    if (data.html) {
      const t = document.createElement('template');
      t.innerHTML = data.html.trim();
      ul.append(t.content);
    }

    if (data.has_more) {
      btn.dataset.offset = String(data.next_offset || offset + limit);
    } else {
      btn.remove();
    }
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
  initCommentsMore();
  initDropzone();
});
