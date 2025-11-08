function getCookie(name) {
  const parts = (document.cookie || '').split('; ');
  for (const p of parts) {
    const [k, v] = p.split('=');
    if (k === name) return decodeURIComponent(v || '');
  }
  return '';
}

function getCSRF(scopeEl) {
  const local = scopeEl && scopeEl.querySelector ? scopeEl.querySelector('[name=csrfmiddlewaretoken]') : null;
  return (local && local.value) || getCookie('csrftoken') || '';
}

function t(s) {
  if (typeof window.gettext === 'function') return window.gettext(s);
  return s;
}

function formatDateISOToLocal(iso) {
  try {
    const d = new Date(iso);
    return new Intl.DateTimeFormat(undefined, {
      year: 'numeric', month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit'
    }).format(d);
  } catch (_) {
    return iso || '';
  }
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

  const scope = btn.closest('.post-card') || document;
  const countEl = scope.querySelector('.js-like-count');
  if (countEl && typeof likeCount === 'number') countEl.textContent = likeCount;
}

function renderCommentItem(item) {
  const li = document.createElement('li');
  li.className = 'mb-2 d-flex align-items-start';
  li.id = `c-${item.id}`;

  const img = document.createElement('img');
  img.src = item.author.avatar;
  img.width = 32;
  img.height = 32;
  img.className = 'rounded-circle me-2';
  img.alt = 'Avatar';

  const wrapper = document.createElement('div');
  wrapper.className = 'flex-grow-1';

  const header = document.createElement('div');
  header.className = 'd-flex align-items-center gap-2';

  const strong = document.createElement('strong');
  strong.textContent = item.author.username;

  const small = document.createElement('small');
  small.className = 'text-muted';
  small.textContent = formatDateISOToLocal(item.created_at);

  header.appendChild(strong);
  header.appendChild(small);

  if (item.can_delete) {
    const delBtn = document.createElement('button');
    delBtn.type = 'button';
    delBtn.className = 'btn btn-sm btn-outline-danger ms-auto';
    delBtn.setAttribute('data-comment-delete', '');
    delBtn.setAttribute('data-post', String(item.post));
    delBtn.setAttribute('data-comment', String(item.id));
    delBtn.setAttribute('aria-label', t('Delete'));
    delBtn.textContent = '🗑';
    header.appendChild(delBtn);
  }

  const textDiv = document.createElement('div');
  textDiv.className = 'text-break';
  textDiv.textContent = item.text;

  wrapper.appendChild(header);
  wrapper.appendChild(textDiv);

  li.appendChild(img);
  li.appendChild(wrapper);
  return li;
}

function updatePostCommentsCount(scopeEl, count) {
  const actions = scopeEl.querySelector('.post-actions');
  if (!actions) return;
  const wrap = actions.querySelector('.bi-chat-left-text')?.parentElement;
  if (!wrap) return;

  let numEl = wrap.querySelector('.js-comments-count');
  if (!numEl) {
    numEl = document.createElement('span');
    numEl.className = 'js-comments-count';
    wrap.appendChild(numEl);
  }
  numEl.textContent = String(count);
}

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
          'X-Requested-With': 'XMLHttpRequest',
          'Accept': 'application/json'
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
          'X-CSRFToken': csrftoken,
          'Accept': 'application/json'
        }
      });
      if (!r.ok) return;

      const data = await r.json();
      const ul = document.getElementById('comments-' + data.post);
      if (!ul) return;

      if (data.item) {
        const el = renderCommentItem({ ...data.item, post: data.post });
        ul.prepend(el);
      }
      const postCard = form.closest('.post-card') || document;
      if (typeof data.count === 'number') updatePostCommentsCount(postCard, data.count);

      form.reset();
    });
  });
}
window.initCommentForms = initCommentForms;

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
    const r = await fetch(`${url}?${qs.toString()}`, {
      headers: { 'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json' }
    });
    if (!r.ok) return;

    const data = await r.json();
    const ul = document.getElementById(`comments-${postId}`);
    if (!ul) return;

    if (Array.isArray(data.items)) {
      const frag = document.createDocumentFragment();
      data.items.forEach((item) => frag.appendChild(renderCommentItem({ ...item, post: Number(postId) })));
      ul.appendChild(frag);
    }

    if (data.has_more) {
      btn.dataset.offset = String(data.next_offset || offset + limit);
    } else {
      btn.remove();
    }
  });
})();

(function initCommentDeleteDelegated() {
  document.addEventListener('click', async (e) => {
    const btn = e.target.closest('[data-comment-delete]');
    if (!btn) return;
    e.preventDefault();

    const postId = btn.getAttribute('data-post');
    const commentId = btn.getAttribute('data-comment');
    const url = btn.getAttribute('data-url') || `/posts/${postId}/comments/${commentId}/delete/`;
    const csrftoken = getCSRF(document);

    const r = await fetch(url, {
      method: 'POST',
      headers: {
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': csrftoken,
        'Accept': 'application/json'
      }
    });
    if (!r.ok) return;

    const data = await r.json();
    if (!data.ok) return;

    const postCard = btn.closest('.post-card') || document;
    const li = document.getElementById(`c-${commentId}`);
    if (li) li.remove();

    if (typeof data.count === 'number') {
      updatePostCommentsCount(postCard, data.count);
    } else {
      const numEl = postCard.querySelector('.js-comments-count');
      const prev = parseInt((numEl && numEl.textContent) || '0', 10);
      updatePostCommentsCount(postCard, Math.max(0, prev - 1));
    }
  });
})();

(function initReportDelegated() {
  document.addEventListener('click', async (e) => {
    const a = e.target.closest('[data-report]');
    if (!a) return;
    e.preventDefault();

    const url = a.getAttribute('data-url');
    const csrftoken = getCSRF(document);
    if (!url || !csrftoken) return;

    const r = await fetch(url, {
      method: 'POST',
      headers: {'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': csrftoken, 'Accept': 'application/json'}
    });
    if (!r.ok) return;

    const data = await r.json();
    const card = a.closest('.post-card');

    if (data.hidden && card) {
      card.remove();
      return;
    }
    alert(t('Report submitted'));
  });
})();

function initDropzone() {
  const dz = document.getElementById('dropzone');
  const fi = document.getElementById('file-input') || document.getElementById('images-input');
  const preview = document.getElementById('preview') || document.getElementById('new-files');
  const opener = document.querySelector('[data-open-file]') || document.getElementById('pick-files');
  if (!dz || !fi || !preview) return;

  if (dz.dataset.bound === '1') return;
  dz.dataset.bound = '1';

  const max = parseInt(dz.getAttribute('data-max') || '10', 10);
  const existing = parseInt(dz.getAttribute('data-existing') || '0', 10);
  let removedExisting = 0;

  const counter = document.querySelector('[data-files-count]');
  const maxEl = document.querySelector('[data-files-max]');
  if (maxEl) maxEl.textContent = String(max);

  let store = [];
  let uid = 0;
  let lastOpenAt = 0;

  const updateCounter = () => {
    const total = existing - removedExisting + store.length;
    if (counter) counter.textContent = String(Math.max(0, total));
  };

  const rebuildFileList = () => {
    const dt = new DataTransfer();
    store.forEach(it => dt.items.add(it.file));
    fi.files = dt.files;
    updateCounter();
  };

  const renderPreview = () => {
    preview.innerHTML = '';
    store.forEach(it => {
      const col = document.createElement('div');
      col.className = 'col-6 col-md-4 col-lg-3';
      const wrap = document.createElement('div');
      wrap.className = 'thumb';
      const img = document.createElement('img');
      img.alt = it.file.name;
      wrap.appendChild(img);
      const rm = document.createElement('button');
      rm.type = 'button';
      rm.className = 'remove';
      rm.setAttribute('data-remove-id', String(it.id));
      rm.setAttribute('aria-label', t('Remove'));
      rm.textContent = '×';
      wrap.appendChild(rm);
      col.appendChild(wrap);
      preview.appendChild(col);

      const reader = new FileReader();
      reader.onload = e => { img.src = e.target.result; };
      reader.readAsDataURL(it.file);
    });
  };

  const addFiles = (files) => {
    const remaining = Math.max(0, max - (existing - removedExisting + store.length));
    if (remaining <= 0) return;
    const list = Array.from(files || []).slice(0, remaining);
    for (const f of list) {
      store.push({ id: ++uid, file: f });
    }
    rebuildFileList();
    renderPreview();
  };

  if (opener) {
    opener.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      const now = Date.now();
      if (now - lastOpenAt < 300) return;
      lastOpenAt = now;
      fi.click();
    });
  }

  dz.addEventListener('click', (e) => {
    if (e.target.closest('[data-open-file],input[type="file"],#pick-files,button,a')) return;
    const now = Date.now();
    if (now - lastOpenAt < 300) return;
    lastOpenAt = now;
    fi.click();
  });

  dz.addEventListener('dragover', (e) => { e.preventDefault(); dz.classList.add('drag'); });
  dz.addEventListener('dragleave', () => dz.classList.remove('drag'));
  dz.addEventListener('drop', (e) => {
    e.preventDefault();
    dz.classList.remove('drag');
    addFiles(e.dataTransfer.files);
  });

  fi.addEventListener('change', () => addFiles(fi.files));

  preview.addEventListener('click', (e) => {
    const btn = e.target.closest('[data-remove-id]');
    if (!btn) return;
    const id = parseInt(btn.getAttribute('data-remove-id') || '0', 10);
    store = store.filter(it => it.id !== id);
    rebuildFileList();
    renderPreview();
  });

  document.addEventListener('existing:toggle', (e) => {
    const active = !!(e && e.detail && e.detail.active);
    removedExisting += active ? 1 : -1;
    if (removedExisting < 0) removedExisting = 0;
    updateCounter();
  });

  updateCounter();
  rebuildFileList();
  renderPreview();
}

async function ajaxSubmitForm(form, onSuccess) {
  const csrftoken = getCSRF(form);
  const r = await fetch(form.action, {
    method: 'POST',
    body: new FormData(form),
    headers: { 'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': csrftoken, 'Accept': 'application/json' }
  });
  const text = await r.text();
  let data = {};
  try { data = JSON.parse(text); } catch { }
  if (!r.ok) throw { status: r.status, data, text };
  if (onSuccess) onSuccess(data);
  return data;
}

function bindCreateFormAjax() {
  const form = document.getElementById('post-create-form');
  if (!form) return;
  if (form.dataset.bound === '1') return;
  form.dataset.bound = '1';

  const alertBox = document.getElementById('post-create-alert');

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    try {
      const data = await ajaxSubmitForm(form, (d) => d);
      document.dispatchEvent(new CustomEvent('post:created', {
        detail: { approved: !!data.approved, message: data.message || t('Post created') }
      }));
      if (alertBox) {
        alertBox.className = 'alert alert-success';
        alertBox.textContent = data.message || t('Post created');
        alertBox.classList.remove('d-none');
      }
      form.reset();
      const preview = document.getElementById('preview');
      if (preview) preview.innerHTML = '';
      const counter = document.querySelector('[data-files-count]');
      if (counter) counter.textContent = '0';
    } catch (err) {
      const errors = (err && err.data && err.data.errors) || [];
      if (alertBox) {
        alertBox.className = 'alert alert-danger';
        alertBox.innerHTML = errors.length ? `<ul class="mb-0">${errors.map(e => `<li>${e}</li>`).join('')}</ul>` : (err.text || t('Error'));
        alertBox.classList.remove('d-none');
      }
    }
  });
}

function bindEditFormAjax() {
  const form = document.getElementById('post-edit-form');
  if (!form) return;
  if (form.dataset.bound === '1') return;
  form.dataset.bound = '1';

  const alertBox = document.getElementById('post-edit-alert');

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    try {
      const data = await ajaxSubmitForm(form, (d) => d);
      if (alertBox) {
        alertBox.className = 'alert alert-success';
        alertBox.textContent = data.message || t('Post updated.');
        alertBox.classList.remove('d-none');
      }
      document.dispatchEvent(new CustomEvent('post:updated', {
        detail: { post_id: data.post_id, message: data.message || t('Post updated.') }
      }));
    } catch (err) {
      const errors = (err && err.data && err.data.errors) || [];
      if (alertBox) {
        alertBox.className = 'alert alert-danger';
        alertBox.innerHTML = errors.length ? `<ul class="mb-0">${errors.map(e => `<li>${e}</li>`).join('')}</ul>` : (err.text || t('Error'));
        alertBox.classList.remove('d-none');
      }
    }
  });
}

(function bindCardActionsDelegated() {
  document.addEventListener('click', async (e) => {
    const a = e.target.closest('[data-action]');
    if (!a) return;
    const action = a.getAttribute('data-action');
    const url = a.getAttribute('data-url');
    if (!url) return;
    e.preventDefault();

    const csrftoken = getCSRF(document);
    const r = await fetch(url, {
      method: 'POST',
      headers: { 'X-Requested-With':'XMLHttpRequest','X-CSRFToken':csrftoken,'Accept':'application/json' }
    });
    if (!r.ok) return;

    const data = await r.json();
    const card = a.closest('.post-card');

    if (action === 'hide' && card) {
      card.remove();
    }
    if (action === 'unhide') {
      if (data.html) {
        if (card) card.outerHTML = data.html;
        else {
          const container = document.querySelector('#posts-container .row.gy-4') || document.getElementById('posts-container');
          if (container) container.insertAdjacentHTML('afterbegin', data.html);
        }
      }
    }
    if (action === 'approve' && card) {
      document.dispatchEvent(new CustomEvent('post:updated', { detail: { message: t('Post approved') } }));
    }
    if (action === 'reject' && card) {
      card.remove();
    }
  });
})();

document.addEventListener('DOMContentLoaded', () => {
  initCommentForms();
  initDropzone();
  bindCreateFormAjax();
  bindEditFormAjax();
});
