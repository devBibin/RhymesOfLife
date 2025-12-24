function getCSRF(scopeEl){
  const local = scopeEl && scopeEl.querySelector ? scopeEl.querySelector('[name=csrfmiddlewaretoken]') : null;
  if (local && local.value) return local.value;
  const raw = (document.cookie || '').split('; ').find(r => r.startsWith('csrftoken='));
  return raw ? decodeURIComponent(raw.split('=')[1] || '') : '';
}

let profileReqSeq = 0;
let profileReqAbort = null;

function ajaxLoadProfile(params){
  const url = new URL(window.location.href);
  Object.entries(params || {}).forEach(([k,v])=>{
    if (v===null || v===undefined || v==='') url.searchParams.delete(k);
    else url.searchParams.set(k, v);
  });
  if (profileReqAbort) profileReqAbort.abort();
  profileReqAbort = new AbortController();
  const seq = ++profileReqSeq;
  return fetch(url.toString(), {
    headers: {'X-Requested-With':'XMLHttpRequest','Accept':'application/json'},
    credentials: 'same-origin',
    signal: profileReqAbort.signal
  })
    .then(async(r)=>{
      const text = await r.text();
      if(!r.ok) throw new Error(text||r.statusText);
      if (seq !== profileReqSeq) return;
      let data; try{ data = JSON.parse(text); }catch{ throw new Error(text); }
      const box = document.getElementById('profile-content');
      if (box) box.innerHTML = data.html;
      // re-bind after replace
      attachProfileTabs();
      attachProfilePagination();
      if (typeof window.initCommentForms === 'function') window.initCommentForms();
      if (history && history.replaceState) history.replaceState(null, '', url.toString());
    })
    .catch((e)=>{
      if (e?.name === 'AbortError') return;
      console.error(e);
    });
}

function attachProfileTabs(){
  document.querySelectorAll('#profile-content .nav.nav-pills [data-tab]').forEach((a)=>{
    a.addEventListener('click', (e)=>{
      e.preventDefault();
      const tab = a.getAttribute('data-tab');
      const inp = document.getElementById('current-tab');
      if (inp) inp.value = tab;
      document.querySelectorAll('#profile-content .nav.nav-pills .nav-link').forEach((l)=>l.classList.remove('active'));
      a.classList.add('active');
      const params = tab === 'articles' ? { tab, apage: 1, ppage: null } : { tab, ppage: 1, apage: null };
      ajaxLoadProfile(params);
    });
  });
}

function attachProfilePagination(){
  document.querySelectorAll('#profile-content .pagination a.page-link').forEach((a)=>{
    a.addEventListener('click', (e)=>{
      e.preventDefault();
      const url = new URL(a.getAttribute('href'), window.location.origin);
      const tab = url.searchParams.get('tab') || (document.getElementById('current-tab')?.value || 'posts');
      const apage = url.searchParams.get('apage') || null;
      const ppage = url.searchParams.get('ppage') || null;
      ajaxLoadProfile({ tab, apage, ppage });
    });
  });
}

function bindProfileModeSwitch(){
  const sw = document.getElementById('mod-switch');
  if (!sw) return;
  sw.addEventListener('change', async ()=>{
    const mode = sw.checked ? 'uncensored' : 'censored';
    const csrftoken = getCSRF(document);
    const formUser = new FormData(); formUser.append('mode', mode);
    try {
      await fetch(sw.getAttribute('data-url-user'), {
        method: 'POST',
        headers: {'X-Requested-With':'XMLHttpRequest','X-CSRFToken':csrftoken,'Accept':'application/json'},
        body: formUser
      });
    } catch(_){}
    const globalUrl = sw.getAttribute('data-url-global');
    if (globalUrl) {
      const formGlobal = new FormData();
      formGlobal.append('mode', mode);
      formGlobal.append('threshold', '');
      try {
        await fetch(globalUrl, {
          method: 'POST',
          headers: {'X-Requested-With':'XMLHttpRequest','X-CSRFToken':csrftoken,'Accept':'application/json'},
          body: formGlobal
        });
      } catch(_){}
    }
    const tab = document.getElementById('current-tab')?.value || 'posts';
    const params = tab === 'articles' ? { tab, apage: 1, ppage: null } : { tab, ppage: 1, apage: null };
    ajaxLoadProfile(params);
  });
}

document.addEventListener('DOMContentLoaded', ()=>{
  attachProfileTabs();
  attachProfilePagination();
  if (typeof window.initCommentForms === 'function') window.initCommentForms();
  bindProfileModeSwitch();
});
