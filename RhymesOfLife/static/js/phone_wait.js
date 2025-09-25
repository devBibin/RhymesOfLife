document.addEventListener('DOMContentLoaded', () => {
  const _ = window.gettext || ((s) => s);
  const statusBox = document.getElementById('status');
  const dialBox = document.getElementById('dial-status');
  if (!statusBox) return;

  let timer = null;

  const setStatus = (cls, text) => {
    statusBox.className = cls;
    statusBox.textContent = _(text);
  };

  const applyResponse = (j) => {
    if (!j || typeof j !== 'object') {
      setStatus('alert alert-warning', 'Network error');
      return;
    }
    if ('verified' in j) {
      if (j.verified) {
        setStatus('alert alert-success', 'Number confirmed. Redirecting…');
        if (timer) clearInterval(timer);
        setTimeout(() => { window.location.href = j.next || '/consents/'; }, 600);
      } else {
        setStatus('alert alert-info', 'Waiting for call…');
        if (dialBox) dialBox.textContent = j.dial_status ? `${_('Status')}: ${j.dial_status}` : '';
      }
      return;
    }
    if (j.status === 'success' || j.status === 'done') {
      setStatus('alert alert-success', 'Number confirmed. Redirecting…');
      if (timer) clearInterval(timer);
      setTimeout(() => { window.location.href = j.next || '/consents/'; }, 600);
    } else if (j.status === 'pending') {
      setStatus('alert alert-info', 'Waiting for call…');
      if (dialBox) dialBox.textContent = j.dial_status ? `${_('Status')}: ${j.dial_status}` : '';
    } else {
      setStatus('alert alert-danger', j.message || 'Error');
    }
  };

  const tick = () => {
    fetch('/auth/phone/status/', { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
      .then((r) => {
        const ct = r.headers.get('content-type') || '';
        if (!r.ok || !ct.includes('application/json')) throw new Error('bad response');
        return r.json();
      })
      .then(applyResponse)
      .catch(() => setStatus('alert alert-warning', 'Network error'));
  };

  tick();
  timer = setInterval(tick, 3000);
});
