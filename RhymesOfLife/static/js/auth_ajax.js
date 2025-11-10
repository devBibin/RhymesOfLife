(function () {
  function getCookie(name) {
    const m = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return m ? decodeURIComponent(m.pop()) : '';
  }

  function t(s) {
    try {
      if (typeof window.gettext === 'function') return window.gettext(s);
    } catch (e) {}
    return s;
  }

  function showMessage(container, text, type) {
    container.innerHTML = '';
    if (!text) return;
    const div = document.createElement('div');
    div.className = `alert alert-${type} mb-3`;
    div.textContent = text;
    container.appendChild(div);
  }

  function switchTab(target) {
    const tabs = root.querySelectorAll('.form-tab');
    const forms = root.querySelectorAll('.form-container');
    tabs.forEach(btn => {
      const active = btn.getAttribute('data-tab') === target;
      btn.classList.toggle('active', active);
      btn.setAttribute('aria-selected', active ? 'true' : 'false');
    });
    forms.forEach(f => f.classList.toggle('active', f.id === `${target}-form`));
    messages.innerHTML = '';
  }

  async function submitAjax(url, form, submitBtn) {
    const fd = new FormData(form);
    const opts = {
      method: 'POST',
      headers: { 'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': getCookie('csrftoken') },
      body: fd,
      credentials: 'same-origin'
    };
    submitBtn.disabled = true;
    submitBtn.setAttribute('aria-busy', 'true');
    try {
      const resp = await fetch(url, opts);
      const data = await resp.json().catch(() => ({}));
      if (!resp.ok) throw data;
      return data;
    } catch (err) {
      const msg = (err && (err.error || err.message)) || t('Network error. Please try again.');
      return { ok: false, error: msg };
    } finally {
      submitBtn.disabled = false;
      submitBtn.removeAttribute('aria-busy');
    }
  }

  function bindTabs() {
    root.querySelectorAll('.form-tab').forEach(btn => {
      btn.type = 'button';
      btn.addEventListener('click', () => switchTab(btn.getAttribute('data-tab')));
    });
    root.querySelectorAll('[data-switch]').forEach(a => {
      a.addEventListener('click', (e) => {
        e.preventDefault();
        switchTab(a.getAttribute('data-switch'));
      });
    });
    switchTab(root.getAttribute('data-initial-tab') || 'register');
  }

  function bindForms() {
    regForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      showMessage(messages, '', 'info');
      const btn = regForm.querySelector('button[type=submit]');
      const res = await submitAjax(registerUrl, regForm, btn);
      if (res.ok && res.redirect) { window.location.href = res.redirect; return; }
      showMessage(messages, res.error || t('Unknown error'), 'danger');
    });

    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      showMessage(messages, '', 'info');
      const btn = loginForm.querySelector('button[type=submit]');
      const res = await submitAjax(loginUrl, loginForm, btn);
      if (res.ok && res.redirect) { window.location.href = res.redirect; return; }
      showMessage(messages, res.error || t('Unknown error'), 'danger');
    });
  }

  const root = document.getElementById('auth-root');
  if (!root) return;
  const messages = document.getElementById('auth-messages');
  const regForm = document.getElementById('register-form');
  const loginForm = document.getElementById('login-form');
  const registerUrl = root.getAttribute('data-register-url');
  const loginUrl = root.getAttribute('data-login-url');

  bindTabs();
  bindForms();
})();
