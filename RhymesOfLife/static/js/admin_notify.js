function getCookie(name){
  const parts=(document.cookie||'').split('; ');
  for(const p of parts){const [k,v]=p.split('='); if(k===name) return decodeURIComponent(v||'');}
  return '';
}

(function(){
  const cfg = window.ADMIN_NOTIFY_CFG || {};
  const API_URL = cfg.apiUrl;
  const SUGGEST_URL = cfg.suggestUrl;

  const $ = (id) => document.getElementById(id);
  const scopeEl = $('scope');
  const recipientWrap = $('recipient-wrap');
  const unameEl = $('recipient_username');
  const idManualEl = $('recipient_id');
  const idAutoEl = $('recipient_id_auto');
  const suggestList = $('user_suggest');
  const sendBtn = $('send');
  const result = $('result');

  function toggleRecipient(){
    recipientWrap.style.display = scopeEl.value === 'personal' ? '' : 'none';
  }

  function prefillFromQuery(){
    const q = new URLSearchParams(location.search);
    if(q.has('scope')) scopeEl.value = q.get('scope');
    if(q.has('recipient')) idManualEl.value = q.get('recipient');
    if(q.has('username')) unameEl.value = q.get('username');
    if(q.has('type')) $('type').value = q.get('type');
    if(q.has('title')) $('title').value = q.get('title');
    if(q.has('message')) $('message').value = q.get('message');
    if(q.has('url')) $('url').value = q.get('url');
  }

  let suggestAbort;
  async function loadSuggest(query){
    if(suggestAbort) suggestAbort.abort();
    suggestAbort = new AbortController();
    const r = await fetch(`${SUGGEST_URL}?q=${encodeURIComponent(query)}`, { signal: suggestAbort.signal });
    if(!r.ok) return;
    const {items=[]} = await r.json();
    suggestList.innerHTML = '';
    for(const it of items){
      const opt = document.createElement('option');
      opt.value = it.username;
      opt.dataset.id = it.id;
      opt.label = it.email || it.username;
      suggestList.appendChild(opt);
    }
  }

  function syncPickedUser(){
    idAutoEl.value = '';
    const v = unameEl.value.trim();
    if(!v) return;
    const match = [...suggestList.children].find(o => o.value.toLowerCase() === v.toLowerCase());
    if(match && match.dataset.id) idAutoEl.value = match.dataset.id;
  }

  async function send(){
    result.textContent = '';
    const body = {
      scope: scopeEl.value,
      recipient_id: idManualEl.value ? Number(idManualEl.value) : (idAutoEl.value ? Number(idAutoEl.value) : null),
      recipient_username: unameEl.value.trim() || null,
      notification_type: $('type').value,
      title: $('title').value,
      message: $('message').value,
      url: $('url').value
    };
    const r = await fetch(API_URL, {
      method: 'POST',
      headers: {'Content-Type': 'application/json','X-CSRFToken': getCookie('csrftoken')},
      body: JSON.stringify(body)
    });
    if(!r.ok){
      const t = await r.text();
      result.innerHTML = '<div class="alert alert-danger" role="alert">'+ t +'</div>';
      return;
    }
    const j = await r.json();
    let text = '';
    if(j.id) text = (typeof gettext==='function'? gettext('Notification sent. ID: ') : 'Notification sent. ID: ') + j.id;
    else if(j.sent != null) {
      const p1 = (typeof gettext==='function'? gettext('Broadcast sent to ') : 'Broadcast sent to ');
      const p2 = (typeof gettext==='function'? gettext(' users') : ' users');
      text = p1 + j.sent + p2;
    } else {
      text = (typeof gettext==='function'? gettext('Done') : 'Done');
    }
    result.innerHTML = '<div class="alert alert-success" role="alert">'+ text +'</div>';
  }

  function onUnameInput(){
    const v = unameEl.value.trim();
    syncPickedUser();
    if(v.length >= 2) loadSuggest(v);
    else suggestList.innerHTML = '';
  }

  prefillFromQuery();
  toggleRecipient();
  scopeEl.addEventListener('change', toggleRecipient);
  unameEl.addEventListener('input', onUnameInput);
  unameEl.addEventListener('change', syncPickedUser);
  sendBtn.addEventListener('click', send);
})();
