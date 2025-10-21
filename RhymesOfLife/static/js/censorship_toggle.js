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

document.addEventListener('change', async (e) => {
  const sw = e.target.closest('#censorship-switch');
  if (!sw) return;

  const url = sw.getAttribute('data-url');
  const csrftoken = getCSRF(document);
  if (!url || !csrftoken) {
    sw.checked = !sw.checked;
    alert((typeof gettext === 'function' ? gettext('Failed to update setting') : 'Failed to update setting'));
    return;
  }

  sw.disabled = true;
  try {
    const form = new FormData();
    form.append('enabled', sw.checked ? '1' : '0');

    const r = await fetch(url, {
      method: 'POST',
      headers: {
        'X-CSRFToken': csrftoken,
        'X-Requested-With': 'XMLHttpRequest',
        'Accept': 'application/json'
      },
      body: form
    });

    if (!r.ok) {
      sw.checked = !sw.checked;
      const msg = (typeof gettext === 'function' ? gettext('Failed to update setting') : 'Failed to update setting');
      alert(msg + (r.status ? ` (${r.status})` : ''));
      return;
    }

    const data = await r.json();
    if (!data || !data.ok) {
      sw.checked = !sw.checked;
      alert((typeof gettext === 'function' ? gettext('Failed to update setting') : 'Failed to update setting'));
      return;
    }
  } catch (_) {
    sw.checked = !sw.checked;
    alert((typeof gettext === 'function' ? gettext('Failed to update setting') : 'Failed to update setting'));
  } finally {
    sw.disabled = false;
  }
});