document.addEventListener('DOMContentLoaded', () => {
  const _ = window.gettext ? window.gettext : (s) => s;
  const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;

  const commentsDiv = document.getElementById('comments');
  const commentForm = document.getElementById('comment-form');

  function jsonHeaders(extra = {}) {
    return {
      'X-Requested-With': 'XMLHttpRequest',
      'Accept': 'application/json',
      ...extra,
    };
  }

  const escapeHtml = (s) =>
    String(s)
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;')
      .replaceAll("'", '&#039;');

  function setLikeState(btn, liked, likeCount) {
    const icon = btn?.querySelector('.bi');
    if (icon) {
      icon.classList.toggle('bi-heart-fill', liked);
      icon.classList.toggle('bi-heart', !liked);
    }
    btn?.classList.toggle('is-active', liked);
    btn?.setAttribute('aria-pressed', liked ? 'true' : 'false');
    btn?.setAttribute('data-liked', liked ? 'true' : 'false');

    const scope = btn.closest('.rl-chipbar') || document;
    const countEl = scope.querySelector('.js-like-count') || document.getElementById('like-count');
    if (countEl && typeof likeCount === 'number') countEl.textContent = String(likeCount);
  }

  document.querySelectorAll('.js-like-toggle').forEach((btn) => {
    const initiallyLiked = btn.getAttribute('data-liked') === 'true';
    setLikeState(btn, initiallyLiked);

    btn.addEventListener('click', async (e) => {
      e.preventDefault();

      const url = btn.getAttribute('data-like-url');
      if (!url) return;

      if (!csrftoken) {
        const loginLink = document.getElementById('like-login-link');
        if (loginLink) window.location.href = loginLink.href;
        return;
      }

      btn.disabled = true;
      try {
        const r = await fetch(url, {
          method: 'POST',
          headers: jsonHeaders({ 'X-CSRFToken': csrftoken }),
          credentials: 'same-origin',
        });
        if (!r.ok) return;
        const data = await r.json();
        setLikeState(btn, !!data.liked, data.like_count);
      } catch {
      } finally {
        btn.disabled = false;
      }
    });
  });

  function removePlaceholder() {
    document.getElementById('no-comments-placeholder')?.remove();
  }

  function showPlaceholder() {
    if (!commentsDiv) return;
    if (!commentsDiv.querySelector('.rl-comment')) {
      const p = document.createElement('p');
      p.id = 'no-comments-placeholder';
      p.className = 'rl-empty';
      p.textContent = _('No comments yet.');
      commentsDiv.appendChild(p);
    }
  }

  function updateCommentCount(v) {
    const cc = document.getElementById('comment-count');
    if (cc && typeof v === 'number') cc.textContent = String(v);
  }

  function attachCommentHandlers() {
    if (!commentsDiv || !csrftoken) return;

    commentsDiv.querySelectorAll('.delete-comment-btn').forEach((btn) => {
      btn.onclick = async () => {
        const el = btn.closest('[data-comment-id]');
        const id = el?.dataset?.commentId;
        if (!id) return;
        if (!confirm(_('Delete?'))) return;

        btn.disabled = true;
        try {
          const r = await fetch(`/articles/comment/${id}/delete/`, {
            method: 'POST',
            headers: jsonHeaders({ 'X-CSRFToken': csrftoken }),
            credentials: 'same-origin',
          });
          if (!r.ok) return;
          const d = await r.json();
          if (d.deleted) {
            el.remove();
            updateCommentCount(d.comment_count);
            showPlaceholder();
          }
        } catch {
        } finally {
          btn.disabled = false;
        }
      };
    });

    commentsDiv.querySelectorAll('.edit-comment-btn').forEach((btn) => {
      btn.onclick = () => {
        const el = btn.closest('[data-comment-id]');
        const id = el?.dataset?.commentId;
        if (!id) return;

        const textP = el.querySelector('.comment-text');
        const old = (textP?.textContent || '').trim();

        const ta = document.createElement('textarea');
        ta.className = 'form-control rl-comment__edit';
        ta.value = old;

        const actions = el.querySelector('.rl-comment__actions');
        if (!actions) return;

        const saveBtn = document.createElement('button');
        saveBtn.className = 'btn btn-sm btn-success';
        saveBtn.type = 'button';
        saveBtn.innerHTML = `<i class="bi bi-check2" aria-hidden="true"></i><span class="visually-hidden">${escapeHtml(_('Save'))}</span>`;

        const cancelBtn = document.createElement('button');
        cancelBtn.className = 'btn btn-sm btn-outline-secondary';
        cancelBtn.type = 'button';
        cancelBtn.innerHTML = `<i class="bi bi-x" aria-hidden="true"></i><span class="visually-hidden">${escapeHtml(_('Cancel'))}</span>`;

        if (textP) textP.replaceWith(ta);

        const oldButtons = Array.from(actions.querySelectorAll('button'));
        oldButtons.forEach((b) => (b.style.display = 'none'));

        actions.appendChild(saveBtn);
        actions.appendChild(cancelBtn);

        cancelBtn.onclick = () => {
          const np = document.createElement('p');
          np.className = 'rl-comment__text comment-text text-break';
          np.innerHTML = escapeHtml(old).replaceAll('\n', '<br>');
          ta.replaceWith(np);

          saveBtn.remove();
          cancelBtn.remove();
          oldButtons.forEach((b) => (b.style.display = ''));
        };

        saveBtn.onclick = async () => {
          saveBtn.disabled = true;
          try {
            const r = await fetch(`/articles/comment/${id}/edit/`, {
              method: 'POST',
              headers: jsonHeaders({
                'X-CSRFToken': csrftoken,
                'Content-Type': 'application/x-www-form-urlencoded',
              }),
              credentials: 'same-origin',
              body: `text=${encodeURIComponent(ta.value)}`,
            });
            if (!r.ok) return;
            const d = await r.json();

            const np = document.createElement('p');
            np.className = 'rl-comment__text comment-text text-break';
            np.innerHTML = escapeHtml(d.text || '').replaceAll('\n', '<br>');
            ta.replaceWith(np);

            saveBtn.remove();
            cancelBtn.remove();
            oldButtons.forEach((b) => (b.style.display = ''));
          } catch {
          } finally {
            saveBtn.disabled = false;
          }
        };
      };
    });
  }

  if (csrftoken && commentsDiv && commentForm) {
    commentForm.addEventListener('submit', async (e) => {
      e.preventDefault();

      const pageId = document.getElementById('page-id')?.value;
      if (!pageId) return;

      const fd = new FormData(commentForm);
      const submitBtn = commentForm.querySelector('button[type="submit"]');

      if (submitBtn) submitBtn.disabled = true;
      try {
        const r = await fetch(`/articles/${pageId}/comment/`, {
          method: 'POST',
          headers: jsonHeaders({ 'X-CSRFToken': csrftoken }),
          credentials: 'same-origin',
          body: fd,
        });
        if (!r.ok) return;
        const d = await r.json();

        if (d.error) {
          alert(d.error);
          return;
        }

        removePlaceholder();

        const html = `
          <div class="rl-comment" data-comment-id="${escapeHtml(d.id)}">
            <div class="rl-comment__head">
              ${d.avatar ? `<img src="${escapeHtml(d.avatar)}" class="rl-comment__avatar" width="34" height="34" alt="">` : ''}
              <div class="d-flex flex-column">
                <span class="rl-comment__name">${escapeHtml(d.username || '')}</span>
                <span class="rl-comment__time">${escapeHtml(_('Just now'))}</span>
              </div>
              <div class="rl-comment__actions">
                <button class="btn btn-sm btn-outline-secondary edit-comment-btn" type="button" aria-label="${escapeHtml(_('Edit'))}">
                  <i class="bi bi-pencil" aria-hidden="true"></i>
                </button>
                <button class="btn btn-sm btn-outline-danger delete-comment-btn" type="button" aria-label="${escapeHtml(_('Delete'))}">
                  <i class="bi bi-trash" aria-hidden="true"></i>
                </button>
              </div>
            </div>
            <p class="rl-comment__text comment-text text-break">${escapeHtml(d.text || '').replaceAll('\n', '<br>')}</p>
          </div>
        `.trim();

        commentsDiv.insertAdjacentHTML('afterbegin', html);
        updateCommentCount(d.comment_count);
        commentForm.reset();
        attachCommentHandlers();
      } catch {
      } finally {
        if (submitBtn) submitBtn.disabled = false;
      }
    });
  }

  attachCommentHandlers();
  showPlaceholder();
});
