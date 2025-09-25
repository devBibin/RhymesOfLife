document.addEventListener('DOMContentLoaded', () => {
  const _ = window.gettext || ((s) => s);
  const statusBox = document.getElementById('status');
  const dialBox = document.getElementById('dial-status');
  const retryBtn = document.getElementById('retry');
  if (!statusBox) return;

  let timer = null;
  let elapsed = 0;
  const intervalMs = 3000;
  const maxWaitMs = (window.PHONE_VERIFY_MAX_WAIT_SEC || 120) * 1000;

  const setStatus = (cls, text) => {
    statusBox.className = cls;
    statusBox.textContent = _(text);
  };

  const stop = () => {
    if (timer) clearInterval(timer);
    timer = null;
  };

  const showRetry = (msgKey) => {
    setStatus('alert alert-warning', msgKey);
    retryBtn.style.display = 'block';
  };

  retryBtn?.addEventListener('click', () => {
    window.location.href = '/auth/phone/enter/';
  });

  const applyResponse = (j) => {
    if (!j || typeof j !== 'object') {
      setStatus('alert alert-warning', 'Network error');
      return;
    }
    if (j.status === 'success' || j.status === 'done') {
      setStatus('alert alert-success', 'Number confirmed. Redirecting…');
      stop();
      setTimeout(() => { window.location.href = j.next || '/consents/'; }, 600);
      return;
    }
    if (j.status === 'pending') {
      setStatus('alert alert-info', 'Waiting for call…');
      if (dialBox) dialBox.textContent = j.dial_status ? `${_('Status')}: ${j.dial_status}` : '';
      return;
    }
    if (j.status === 'timeout') {
      stop();
      if (dialBox) dialBox.textContent = j.dial_status ? `${_('Status')}: ${j.dial_status}` : '';
      showRetry('Verification timed out. Try again.');
      return;
    }
    if (j.status === 'failed') {
      stop();
      if (dialBox) dialBox.textContent = j.dial_status ? `${_('Status')}: ${j.dial_status}` : '';
      showRetry('Call failed. Try again.');
      return;
    }
    setStatus('alert alert-danger', j.message || 'Error');
  };

  const tick = () => {
    fetch('/auth/phone/status/', {
      headers: { 'X-Requested-With': 'XMLHttpRequest', 'Cache-Control': 'no-cache' }
    })
      .then((r) => {
        const ct = r.headers.get('content-type') || '';
        if (!r.ok || !ct.includes('application/json')) throw new Error('bad response');
        return r.json();
      })
      .then(applyResponse)
      .catch(() => setStatus('alert alert-warning', 'Network error'));

    elapsed += intervalMs;
    if (elapsed >= maxWaitMs) {
      stop();
      showRetry('Verification timed out. Try again.');
    }
  };

  tick();
  timer = setInterval(tick, intervalMs);
});
