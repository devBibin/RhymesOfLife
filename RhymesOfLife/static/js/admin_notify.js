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

  const typeEl = $('type');
  const titleEl = $('title');
  const messageEl = $('message');
  const urlEl = $('url');
  const buttonTextEl = $('button_text'); // new

  function toggleRecipient(){
    recipientWrap.style.display = scopeEl.value === 'personal' ? '' : 'none';
  }

  function prefillFromQuery(){
    const q = new URLSearchParams(location.search);
    if(q.has('scope')) scopeEl.value = q.get('scope');
    if(q.has('recipient')) idManualEl.value = q.get('recipient');
    if(q.has('username')) unameEl.value = q.get('username');
    if(q.has('type')) typeEl.value = q.get('type');
    if(q.has('title')) titleEl.value = q.get('title');
    if(q.has('message')) messageEl.value = q.get('message');
    if(q.has('url')) urlEl.value = q.get('url');
    if(q.has('button_text') && buttonTextEl) buttonTextEl.value = q.get('button_text');
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
    sendBtn.disabled = true;

    const body = {
      scope: scopeEl.value,
      recipient_id: idManualEl.value ? Number(idManualEl.value) : (idAutoEl.value ? Number(idAutoEl.value) : null),
      recipient_username: unameEl.value.trim() || null,
      notification_type: typeEl.value,
      title: titleEl.value,
      message: messageEl.value,
      url: urlEl.value,
      button_text: buttonTextEl ? buttonTextEl.value : ''
    };

    try{
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
    } catch(e){
      result.innerHTML = '<div class="alert alert-danger" role="alert">'+ (typeof gettext==='function'? gettext('Network error') : 'Network error') +'</div>';
    } finally{
      sendBtn.disabled = false;
    }
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
