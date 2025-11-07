(function () {
  function getCookie(name) {
    const v = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return v ? v.pop() : '';
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
    tabs.forEach(t => {
      const isActive = t.getAttribute('data-tab') === target;
      t.classList.toggle('active', isActive);
      t.setAttribute('aria-selected', isActive ? 'true' : 'false');
    });
    forms.forEach(f => {
      const isActive = f.id === `${target}-form`;
      f.classList.toggle('active', isActive);
    });
    messages.innerHTML = '';
  }

  async function submitAjax(url, form) {
    const fd = new FormData(form);
    const resp = await fetch(url, {
      method: 'POST',
      headers: {
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': getCookie('csrftoken')
      },
      body: fd,
      credentials: 'same-origin'
    });
    return resp.json();
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
    const initial = root.getAttribute('data-initial-tab') || 'register';
    switchTab(initial);
  }

  function bindForms() {
    regForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      showMessage(messages, '', 'info');
      const res = await submitAjax(registerUrl, regForm);
      if (res.ok && res.redirect) {
        window.location.href = res.redirect;
        return;
      }
      showMessage(messages, res.error || res.message || 'Error', 'danger');
    });

    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      showMessage(messages, '', 'info');
      const res = await submitAjax(loginUrl, loginForm);
      if (res.ok && res.redirect) {
        window.location.href = res.redirect;
        return;
      }
      showMessage(messages, res.error || res.message || 'Error', 'danger');
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
