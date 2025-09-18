document.addEventListener('DOMContentLoaded', () => {
  const _ = window.gettext ? window.gettext : (s) => s;
  const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;

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
    const countEl = scope.querySelector('.js-like-count') || document.getElementById('like-count');
    if (countEl && typeof likeCount === 'number') countEl.textContent = likeCount;
  }

  document.querySelectorAll('.js-like-toggle').forEach((btn) => {
    const initiallyLiked = btn.getAttribute('data-liked') === 'true';
    setLikeState(btn, initiallyLiked);

    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const url = btn.getAttribute('data-like-url');
      if (!url) return;
      if (!csrftoken) {
        const loginLink = document.getElementById('like-login-link');
        if (loginLink) window.location.href = loginLink.href;
        return;
      }
      fetch(url, { method: 'POST', headers: { 'X-CSRFToken': csrftoken } })
        .then((r) => r.json())
        .then((data) => setLikeState(btn, !!data.liked, data.like_count))
        .catch(() => {});
    });
  });

  const commentsDiv = document.getElementById('comments');
  const commentForm = document.getElementById('comment-form');

  function removePlaceholder() {
    document.getElementById('no-comments-placeholder')?.remove();
  }

  function showPlaceholder() {
    if (!commentsDiv) return;
    if (!commentsDiv.querySelector('.comment')) {
      const p = document.createElement('p');
      p.id = 'no-comments-placeholder';
      p.className = 'text-muted';
      p.textContent = _('No comments yet.');
      commentsDiv.appendChild(p);
    }
  }

  function attachCommentHandlers() {
    if (!commentsDiv || !csrftoken) return;

    commentsDiv.querySelectorAll('.delete-comment-btn').forEach((btn) => {
      btn.onclick = () => {
        const el = btn.closest('.comment');
        const id = el?.dataset?.commentId;
        if (!id) return;
        if (!confirm(_('Delete?'))) return;

        fetch(`/articles/comment/${id}/delete/`, { method: 'POST', headers: { 'X-CSRFToken': csrftoken } })
          .then((r) => r.json())
          .then((d) => {
            if (d.deleted) {
              el.remove();
              const cc = document.getElementById('comment-count');
              if (cc) cc.textContent = d.comment_count;
              showPlaceholder();
            }
          })
          .catch(() => {});
      };
    });

    commentsDiv.querySelectorAll('.edit-comment-btn').forEach((btn) => {
      btn.onclick = () => {
        const el = btn.closest('.comment');
        const id = el?.dataset?.commentId;
        if (!id) return;

        const textP = el.querySelector('.comment-text');
        const old = (textP?.textContent || '').trim();

        const ta = document.createElement('textarea');
        ta.className = 'form-control mb-2';
        ta.value = old;

        const saveBtn = document.createElement('button');
        saveBtn.className = 'btn btn-sm btn-success';
        saveBtn.type = 'button';
        saveBtn.textContent = `💾 ${_('Save')}`;

        if (textP) textP.replaceWith(ta);
        btn.replaceWith(saveBtn);

        saveBtn.onclick = () => {
          fetch(`/articles/comment/${id}/edit/`, {
            method: 'POST',
            headers: { 'X-CSRFToken': csrftoken, 'Content-Type': 'application/x-www-form-urlencoded' },
            body: `text=${encodeURIComponent(ta.value)}`
          })
            .then((r) => r.json())
            .then((d) => {
              const np = document.createElement('p');
              np.className = 'comment-text text-break';
              np.innerHTML = (d.text || '').replace(/\n/g, '<br>');
              ta.replaceWith(np);
              saveBtn.replaceWith(btn);
            })
            .catch(() => {});
        };
      };
    });
  }

  if (csrftoken && commentsDiv && commentForm) {
    commentForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const fd = new FormData(commentForm);

      const pageId = document.getElementById('page-id')?.value;
      fetch(`/articles/${pageId}/comment/`, { method: 'POST', headers: { 'X-CSRFToken': csrftoken }, body: fd })
        .then((r) => r.json())
        .then((d) => {
          if (d.error) {
            alert(d.error);
            return;
          }
          removePlaceholder();
          const html = `
            <div class="comment mb-3" data-comment-id="${d.id}">
              <div class="d-flex align-items-center mb-1">
                ${d.avatar ? `<img src="${d.avatar}" class="comment-avatar rounded-circle me-2" width="32" alt="">` : ''}
                <strong>${d.username}</strong>
                <small class="text-muted ms-2">${_('Just now')}</small>
                <div class="ms-auto">
                  <button class="btn btn-sm btn-outline-secondary edit-comment-btn" type="button" aria-label="${_('Edit')}">✏️</button>
                  <button class="btn btn-sm btn-outline-danger delete-comment-btn" type="button" aria-label="${_('Delete')}">🗑</button>
                </div>
              </div>
              <p class="comment-text text-break">${(d.text || '').replace(/\n/g, '<br>')}</p>
            </div>`.trim();
          commentsDiv.insertAdjacentHTML('afterbegin', html);
          const cc = document.getElementById('comment-count');
          if (cc) cc.textContent = d.comment_count;
          commentForm.reset();
          attachCommentHandlers();
        })
        .catch(() => {});
    });
  }

  attachCommentHandlers();
  showPlaceholder();
});
