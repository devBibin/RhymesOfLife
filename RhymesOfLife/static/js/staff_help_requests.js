(function(){
  function getCookie(name){
    const cookies=document.cookie?document.cookie.split('; '):[];
    for(let i=0;i<cookies.length;i++){
      const p=cookies[i], eq=p.indexOf('='), k=eq>-1?p.slice(0,eq):p;
      if(k===name) return decodeURIComponent(eq>-1?p.slice(eq+1):'');
    }
    return '';
  }

  const root=document.getElementById('hr-root');
  if(!root) return;

  const dataUrl=root.dataset.urlData;
  const apiUrl=root.dataset.urlApi;
  const listEl=document.getElementById('hr-list');
  const pagerEl=document.getElementById('hr-pager');
  const counterEl=document.getElementById('hr-counter');
  const filterForm=document.getElementById('hr-filter');
  const statusEl=document.getElementById('hr-status');
  const qEl=document.getElementById('hr-q');

  let currentPage=1;

  async function load(page){
    currentPage=page||1;
    const u=new URL(dataUrl, window.location.origin);
    u.searchParams.set('status', statusEl.value);
    u.searchParams.set('q', qEl.value || '');
    u.searchParams.set('page', currentPage);
    const resp=await fetch(u.toString(), {headers:{'X-Requested-With':'XMLHttpRequest'}});
    if(!resp.ok) return;
    const data=await resp.json();
    if(!data.ok) return;
    listEl.innerHTML=data.rows;
    pagerEl.innerHTML=data.pager;
    const tmp=document.createElement('tbody'); tmp.innerHTML=data.rows;
    const rows=tmp.querySelectorAll('tr.hr-row').length;
    counterEl.textContent=rows ? String(rows) : '';
  }

  filterForm.addEventListener('submit', function(e){ e.preventDefault(); load(1); });
  statusEl.addEventListener('change', function(){ load(1); });

  document.addEventListener('click', async function(e){
    const pageBtn=e.target.closest('.hr-page-btn');
    if(pageBtn){ e.preventDefault(); const p=parseInt(pageBtn.dataset.page||'1',10); load(p); return; }

    const toggle=e.target.closest('.hr-toggle-btn');
    if(toggle){
      const fd=new FormData();
      fd.append('id', toggle.dataset.id);
      fd.append('action', toggle.dataset.action);
      const resp=await fetch(apiUrl, {method:'POST', headers:{'X-CSRFToken':getCookie('csrftoken')}, body:fd});
      if(!resp.ok) return;
      const data=await resp.json();
      if(!data.ok) return;
      load(currentPage);
      return;
    }

    const tr=e.target.closest('tr.hr-row');
    if(tr && !e.target.closest('a,button')){
      openModalFromRow(tr);
    }
  });

  function openModalFromRow(tr){
    const d={
      id: tr.dataset.id,
      created: tr.dataset.created || '',
      username: tr.dataset.username || '',
      telegram: tr.dataset.telegram || '',
      email: tr.dataset.email || '',
      status: tr.dataset.status || 'open',
      message: tr.dataset.message || ''
    };

    const modalEl=document.getElementById('hr-modal');
    const m=new bootstrap.Modal(modalEl);

    setText('hm-id', d.id);
    setText('hm-created', d.created);
    setText('hm-username', d.username || '—');

    const tgEl=document.getElementById('hm-telegram');
    tgEl.innerHTML='';
    if(d.telegram){
      const handle=d.telegram.startsWith('@')?d.telegram:('@'+d.telegram);
      const a=document.createElement('a');
      a.href='https://t.me/'+handle.replace(/^@/,'');
      a.target='_blank'; a.rel='noopener';
      a.className='text-decoration-none';
      a.textContent=handle;
      tgEl.appendChild(a);
    }else{
      tgEl.textContent='—';
    }

    const mailEl=document.getElementById('hm-email');
    mailEl.innerHTML='';
    if(d.email){
      const a=document.createElement('a');
      a.href='mailto:'+d.email;
      a.className='text-decoration-none';
      a.textContent=d.email;
      mailEl.appendChild(a);
    }else{
      mailEl.textContent='—';
    }

    const sEl=document.getElementById('hm-status');
    sEl.innerHTML='';
    const span=document.createElement('span');
    span.className='badge rounded-pill ' + (d.status==='processed'?'bg-success':'bg-secondary');
    span.textContent=(d.status==='processed'?'Processed':'Open');
    sEl.appendChild(span);

    const msgEl=document.getElementById('hm-message');
    msgEl.textContent=d.message;

    const btnProcess=document.getElementById('hm-process');
    const btnUndo=document.getElementById('hm-undo');
    btnProcess.classList.toggle('d-none', d.status==='processed');
    btnUndo.classList.toggle('d-none', d.status!=='processed');

    btnProcess.onclick=()=>updateStatus(d.id,'process',m);
    btnUndo.onclick=()=>updateStatus(d.id,'undo',m);

    m.show();
  }

  function setText(id, value){
    const el=document.getElementById(id);
    if(el) el.textContent=value;
  }

  async function updateStatus(id, action, modalInstance){
    const fd=new FormData();
    fd.append('id', id);
    fd.append('action', action);
    const resp=await fetch(root.dataset.urlApi, {method:'POST', headers:{'X-CSRFToken':getCookie('csrftoken')}, body:fd});
    if(!resp.ok) return;
    const data=await resp.json();
    if(!data.ok) return;
    modalInstance.hide();
    load(currentPage);
  }

  document.addEventListener('DOMContentLoaded', function(){ load(1); });
})();
