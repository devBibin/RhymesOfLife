function getCookie(name) {
  const parts = (document.cookie || '').split('; ');
  for (const p of parts) {
    const [k, v] = p.split('=');
    if (k === name) return decodeURIComponent(v || '');
  }
  return '';
}

function getCSRF(scopeEl) {
  const local = scopeEl && scopeEl.querySelector
    ? scopeEl.querySelector('[name=csrfmiddlewaretoken]')
    : null;
  return (local && local.value) || getCookie('csrftoken') || '';
}

function setLikeState(btn, liked, likeCount) {
  const icon = btn?.querySelector('.bi');
  if (icon) {
    icon.classList.toggle('bi-heart-fill', liked);
    icon.classList.toggle('bi-heart', !liked);
    icon.classList.toggle('text-danger', liked);
  }
  btn?.classList.toggle('active', liked);
  btn?.setAttribute('aria-pressed', liked ? 'true' : 'false');
  btn?.setAttribute('data-liked', liked ? 'true' : 'false');

  const scope = btn.closest('.post-actions') || document;
  const countEl = scope.querySelector('.js-like-count');
  if (countEl && typeof likeCount === 'number') countEl.textContent = likeCount;
}

// ------- likes (delegated) -------
(function initLikesDelegated() {
  document.addEventListener('click', async (e) => {
    const btn = e.target.closest('.js-like-toggle');
    if (!btn) return;
    e.preventDefault();

    const url = btn.getAttribute('data-like-url');
    if (!url) return;

    const csrftoken = getCSRF(document);
    if (!csrftoken) {
      const loginLink = document.getElementById('like-login-link');
      if (loginLink) window.location.href = loginLink.href;
      return;
    }

    if (btn.disabled) return;
    btn.disabled = true;

    try {
      const r = await fetch(url, {
        method: 'POST',
        headers: {
          'X-CSRFToken': csrftoken,
          'X-Requested-With': 'XMLHttpRequest'
        }
      });

      if (r.status === 401) {
        const login = document.getElementById('like-login-link');
        if (login) window.location.href = login.href;
        return;
      }
      if (!r.ok) return;

      const data = await r.json();
      setLikeState(btn, !!data.liked, data.like_count);
    } catch (_) {
    } finally {
      btn.disabled = false;
    }
  });
})();

// ------- comments: add -------
function initCommentForms() {
  document.querySelectorAll('form[data-comment-form]').forEach((form) => {
    if (form.dataset.commentBound === '1') return;
    form.dataset.commentBound = '1';

    form.addEventListener('submit', async (e) => {
      e.preventDefault();

      const csrftoken = getCSRF(form);
      const r = await fetch(form.action, {
        method: 'POST',
        body: new FormData(form),
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
          'X-CSRFToken': csrftoken
        }
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

// ------- comments: more (delegated) -------
(function initCommentsMoreDelegated() {
  if (document.body.dataset.commentsMoreBound === '1') return;
  document.body.dataset.commentsMoreBound = '1';

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
})();

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
  dz.addEventListener('drop', (e) => {
    e.preventDefault();
    dz.classList.remove('bg-light');
    fi.files = e.dataTransfer.files;
    renderPreview();
  });
  fi.addEventListener('change', renderPreview);
}

// ------- boot -------
document.addEventListener('DOMContentLoaded', () => {
  initCommentForms();
  initDropzone();
});