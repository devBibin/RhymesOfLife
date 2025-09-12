document.addEventListener('DOMContentLoaded', () => {
  const _ = (window.gettext) ? window.gettext : (s) => s;
  const ngettext = (window.ngettext) ? window.ngettext : (s /*sing*/, p /*plur*/, n) => (n === 1 ? s : p);
  const interpolate = (window.interpolate) ? window.interpolate : ((fmt, obj) => fmt);

  // Clickable card navigation (ignore interactive elements)
  document.body.addEventListener('click', (e) => {
    const card = e.target.closest('.js-clickable-card');
    if (!card) return;
    if (e.target.closest('a, button, textarea, input, select, label')) return;
    const href = card.dataset.href;
    if (href) window.location.href = href;
  });

  const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
  const pageId    = document.getElementById('page-id')?.value;

  // Like button
  const likeBtn = document.getElementById('like-btn');
  if (csrftoken && pageId && likeBtn) {
    likeBtn.addEventListener('click', () => {
      fetch(`/articles/${pageId}/like/`, {
        method: 'POST',
        headers: { 'X-CSRFToken': csrftoken }
      })
      .then((r) => r.json())
      .then((data) => {
        const likeCountEl = document.getElementById('like-count');
        if (likeCountEl) likeCountEl.textContent = data.like_count;

        likeBtn.textContent = data.liked ? _('Remove like') : _('Like');
        likeBtn.classList.toggle('btn-danger', data.liked);
        likeBtn.classList.toggle('btn-outline-danger', !data.liked);
      })
      .catch(() => {
        // optional: silent fail or toast
      });
    });
  }

  // Comments
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

    // Delete
    commentsDiv.querySelectorAll('.delete-comment-btn').forEach((btn) => {
      btn.onclick = () => {
        const el = btn.closest('.comment');
        const id = el?.dataset?.commentId;
        if (!id) return;
        if (!confirm(_('Delete?'))) return;

        fetch(`/articles/comment/${id}/delete/`, {
          method: 'POST',
          headers: { 'X-CSRFToken': csrftoken }
        })
        .then((r) => r.json())
        .then((d) => {
          if (d.deleted) {
            el.remove();
            const cc = document.getElementById('comment-count');
            if (cc) cc.textContent = d.comment_count;
            showPlaceholder();
          }
        })
        .catch(() => {
          // optional error handling
        });
      };
    });

    // Edit
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
            headers: {
              'X-CSRFToken': csrftoken,
              'Content-Type': 'application/x-www-form-urlencoded'
            },
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
          .catch(() => {
            // optional error handling
          });
        };
      };
    });
  }

  if (csrftoken && pageId && commentForm && commentsDiv) {
    commentForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const fd = new FormData(commentForm);

      fetch(`/articles/${pageId}/comment/`, {
        method: 'POST',
        headers: { 'X-CSRFToken': csrftoken },
        body: fd
      })
      .then((r) => r.json())
      .then((d) => {
        if (d.error) {
          // server-provided message (may already be localized)
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
      .catch(() => {
        // optional error handling
      });
    });
  }

  attachCommentHandlers();
  showPlaceholder();
});
