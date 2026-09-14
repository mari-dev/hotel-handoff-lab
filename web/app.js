let rows=[],filter='all',history=false,editing=null;
const $=s=>document.querySelector(s), esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const labels=()=>({requested:t('To prepare'),working:t('In progress'),prepared:t('PDF prepared'),sent:t('Sent'),delivered:t('Handed over')});
const lexware='https://app.lexware.de/';
$('#actor').value='';$('#actor').readOnly=true;
$('#logout').onclick=async()=>{await api('/api/auth/logout',{});location.replace('/login');};
const actor=()=>$('#actor').value.trim();
function toast(t){$('#toast').textContent=systemText(t);$('#toast').hidden=false;setTimeout(()=>$('#toast').hidden=true,6500);}
let apiQueue=Promise.resolve();
function api(url,data){
  const run=async()=>{const res=await fetch(url,data?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)}:{});if(res.status===401){location.replace('/login');throw Error('Sign in required');}const value=await res.json();if(!res.ok)throw Error(t(value.error||'Connection error'));return value;};
  const pending=apiQueue.then(run);apiQueue=pending.catch(()=>{});return pending;
}
async function refresh(){try{rows=await api('/api/requests');$('#error').hidden=true;render();await evidence();}catch(e){$('#error').textContent=t(e.message);$('#error').hidden=false;}}
function render(){const expanded=new Set([...document.querySelectorAll('.card details[open]')].map(e=>e.closest('.card').dataset.id));
for(const state of ['requested','working','prepared'])$('#n-'+state).textContent=rows.filter(r=>r.status===state).length;
const search=$('#search').value.toLocaleLowerCase();
const selected=rows.filter(r=>(['sent','delivered'].includes(r.status)===history)&&(history||filter==='all'||r.status===filter)&&r.guest.toLocaleLowerCase().includes(search));
$('#list').innerHTML=selected.map(r=>{const own=r.owner===actor();let primary='';
if(r.status==='requested')primary=`<button class="primary" data-action="claim"><span data-i18n="Prepare ↗">Prepare ↗</span></button>`;
else if(r.status==='working'&&own)primary=`<button data-action="claim"><span data-i18n="Open Lexware ↗">Open Lexware ↗</span></button>`;
else if(r.status==='working')primary='<span class="owner"><span data-i18n="Already claimed">Already claimed</span></span>';
return `<article class="card" data-id="${r.id}"><div class="card-main"><div class="avatar">${esc(r.guest.split(/\s+/).slice(0,2).map(s=>s[0]).join(''))}</div><div class="person"><h2>${esc(r.guest)}</h2><p>${esc(r.stay||t('Stay not yet identified'))} · ${esc(t(r.source))}</p></div><span class="status ${r.status}">${labels()[r.status]}</span><span class="owner">${esc(r.owner||t('Unassigned'))}</span>${primary}</div><details ${expanded.has(r.id)?'open':''}><summary><span data-i18n="Details and activity">Details and activity</span></summary><div class="details-body"><div class="note">${esc(r.note||t('No notes yet. Collect the details needed for the invoice.'))}</div><div class="actions"><button data-action="copy"><span data-i18n="Copy details">Copy details</span></button>${['requested','working'].includes(r.status)?'<button data-action="edit"><span data-i18n="Add information">Add information</span></button>':''}${r.status==='working'&&own?'<button data-action="release"><span data-i18n="Release request">Release request</span></button>':''}${r.status==='prepared'&&own?'<button data-action="deliver"><span data-i18n="Handed over">Handed over</span></button>':''}</div><ul class="events">${r.events.map(e=>`<li>${esc(new Date(e.at).toLocaleTimeString(language,{hour:'2-digit',minute:'2-digit'}))} · ${esc(['PDF folder','Sent mail archive'].includes(e.actor)?t(e.actor):e.actor)} — ${esc(systemText(e.detail))}</li>`).join('')}</ul>${['requested','working','prepared'].includes(r.status)?'<div class="demo"><p><span data-i18n="DEMO · Create synthetic files in local folders. The monitor reads them; no email is sent.">DEMO · Create synthetic files in local folders. The monitor reads them; no email is sent.</span></p><button data-action="sample_pdf"><span data-i18n="Create sample PDF">Create sample PDF</span></button> <button data-action="sample_eml"><span data-i18n="Create sample email">Create sample email</span></button></div>':''}</div></details></article>`;}).join('')||'<div class="empty"><span data-i18n="No requests here.">No requests here.</span><br><span data-i18n="Use “+ Invoice” when a new request arrives.">Use “+ Invoice” when a new request arrives.</span></div>';
localize();
}
$('#list').onclick=async e=>{const button=e.target.closest('[data-action]');if(!button)return;const row=rows.find(r=>r.id===button.closest('.card').dataset.id),action=button.dataset.action;
if(action==='edit'){openEntry(row);return;}
if(action==='sample_pdf'||action==='sample_eml'){button.disabled=true;try{const result=await api('/api/sample-file',{id:row.id,kind:action==='sample_pdf'?'pdf':'eml'});toast(t('File created: ')+result.filename+t('. Wait for automatic detection.'));}catch(err){toast(err.message);}finally{button.disabled=false;}return;}
if(action==='copy'){try{await navigator.clipboard.writeText(`${row.guest}\n${row.stay}\n${row.note}`);toast(t('Details copied'));}catch{toast(t('Copy unavailable: select the details from the card.'));}return;}
if(!actor()){toast(t('Enter your name at the top.'));return;}
let tab=null;if(action==='claim'){tab=window.open('about:blank','_blank');if(tab)tab.opener=null;}
button.disabled=true;
try{await api('/api/action',{id:row.id,action,actor:actor()});if(tab)tab.location=lexware;if(action==='claim')toast(tab?t('Request claimed. Lexware opened.'):t('Request claimed. Your browser blocked the new tab: allow pop-ups and click Open Lexware.'));await refresh();}
catch(err){if(tab)tab.close();toast(err.message);await refresh();}finally{button.disabled=false;}};
function openEntry(row=null){editing=row?.id||null;$('#form').reset();$('#form-error').textContent='';$('#duplicates').hidden=true;$('#intake-evidence').textContent='';$('#intake-status').textContent='';$('#entry-title').textContent=row?t('Complete the details.'):t('Start with a name.');$('#save-request').textContent=row?t('Save details'):t('Add request');$('#prepare-now').hidden=!!row;$('#guest').readOnly=!!row;$('#intake-box').hidden=!!row;
if(row){$('#guest').value=row.guest;$('#form').elements.stay.value=row.stay;$('#form').elements.note.value=row.note;$('#form').elements.source.value=row.source;$('#form').querySelector('details:not(#intake-box)').open=true;}$('#language-dialog').value=language;localize();$('#entry').showModal();}
$('#new').onclick=()=>openEntry();
$('#close').onclick=()=>$('#entry').close();
$('#guest').oninput=()=>{const name=$('#guest').value.trim().toLocaleLowerCase();const matches=rows.filter(r=>name.length>2&&r.guest.toLocaleLowerCase().includes(name));$('#duplicates').hidden=!matches.length;$('#duplicates').innerHTML=matches.length?`<span data-i18n="Possible existing requests. Check the stay before adding another.">Possible existing requests. Check the stay before adding another.</span><br>${matches.map(r=>`<button type="button" data-existing="${r.id}">${esc(r.guest)} · ${labels()[r.status]}</button>`).join('')}`:'';localize($('#duplicates'));};
$('#duplicates').onclick=e=>{const b=e.target.closest('[data-existing]');if(!b)return;const row=rows.find(r=>r.id===b.dataset.existing);$('#entry').close();history=['sent','delivered'].includes(row.status);filter='all';$('#search').value=row.guest;updateNavigation();render();};
$('#form').onsubmit=async e=>{e.preventDefault();if(!actor()){$('#form-error').textContent=t('Enter the operator name at the top.');return;}const prepare=e.submitter.value==='now';let tab=null;if(prepare){tab=window.open('about:blank','_blank');if(tab)tab.opener=null;}const buttons=[...$('#form').querySelectorAll('button[type=submit]')];buttons.forEach(b=>b.disabled=true);
try{const data=Object.fromEntries(new FormData(e.target));if(editing){await api('/api/details',{id:editing,stay:data.stay,note:data.note,actor:actor()});}else{await api('/api/requests',{...data,actor:actor(),prepare});}if(tab)tab.location=lexware;$('#entry').close();history=false;filter='all';$('#search').value='';updateNavigation();await refresh();toast(prepare?(tab?t('Request added and claimed.'):t('Request claimed; allow pop-ups and click Open Lexware.')):(editing?t('Details updated.'):t('Request added. Everyone can see it now.')));}
catch(err){if(tab)tab.close();$('#form-error').textContent=t(err.message);}finally{buttons.forEach(b=>b.disabled=false);}};
function updateNavigation(){$('#heading').textContent=history?t('Completed invoices'):t('Who is waiting for an invoice?');$('#nav-open').classList.toggle('active',!history);$('#nav-history').classList.toggle('active',history);$('.tabs').style.visibility=history?'hidden':'visible';document.querySelectorAll('[data-filter]').forEach(b=>b.classList.toggle('selected',b.dataset.filter===filter));}
$('#nav-open').onclick=()=>{history=false;updateNavigation();render();};$('#nav-history').onclick=()=>{history=true;updateNavigation();render();};
document.querySelectorAll('[data-filter]').forEach(b=>b.onclick=()=>{filter=b.dataset.filter;updateNavigation();render();});$('#search').oninput=render;
api('/api/auth/session').then(user=>{$('#actor').value=user.display_name;refresh();});setInterval(()=>{if(!$('#entry').open)refresh();},6000);

async function evidence(){const items=await api('/api/evidence');const pending=items.filter(x=>x.state!=='linked');$('#evidence-label').textContent=items.length+t(' documents detected')+(pending.length?' · '+pending.length+t(' need review'):'');$('#evidence-list').innerHTML=items.map(x=>'<p><strong>'+esc(x.filename)+'</strong> · '+(x.state==='linked'?t('Linked'):esc(t(x.reason||'Waiting for a match')))+'</p>').join('')||'<p><span data-i18n="Waiting for PDFs and exported emails. No direct connection to Thunderbird.">Waiting for PDFs and exported emails. No direct connection to Thunderbird.</span></p>';localize($('#evidence-list'));}
localize();
api('/api/health').then(h=>{$('#ai-state').textContent=h.ai_configured?t('Strands configured'):t('Strands: configure AWS access');}).catch(()=>{});
$('#analyze').onclick=async()=>{const button=$('#analyze');button.disabled=true;$('#intake-status').textContent=t('Strands is reading the message and checking existing requests…');$('#intake-evidence').textContent='';
try{const result=await api('/api/intake',{message:$('#intake-message').value});const p=result.proposal;
if(!p.invoice_requested){$('#intake-status').textContent=t('No explicit invoice request found. No request has been created.');return;}
$('#guest').value=p.guest?.value||'';$('#form').elements.stay.value=p.stay?.value||'';$('#form').elements.note.value=$('#intake-message').value;$('#form').elements.source.value='Email';
$('#intake-evidence').innerHTML=['guest','stay','company','address'].filter(k=>p[k]).map(k=>'<blockquote>'+esc(p[k].value)+'<br><small><span data-i18n="Source: ">Source: </span>'+esc(p[k].quote)+'</small></blockquote>').join('');
localize($('#intake-evidence'));$('#intake-status').textContent=t('Proposal ready. Check the name and stay before saving. Nothing has been saved automatically.');$('#guest').dispatchEvent(new Event('input'));$('#form').querySelector('details:not(#intake-box)').open=true;
}catch(err){$('#intake-status').textContent=t(err.message);}finally{button.disabled=false;}};

const SpeechRecognitionCtor=window.SpeechRecognition||window.webkitSpeechRecognition;
if(SpeechRecognitionCtor){
  const dictateButton=$('#dictate');dictateButton.hidden=false;
  const localeFor={en:'en-US',de:'de-DE',it:'it-IT'};
  let recognizer=null,listening=false,baseText='';
  function stopDictation(){listening=false;dictateButton.classList.remove('listening');dictateButton.querySelector('span').textContent=t('Dictate');if(recognizer)recognizer.stop();}
  dictateButton.onclick=()=>{
    if(listening){stopDictation();return;}
    recognizer=new SpeechRecognitionCtor();
    recognizer.lang=localeFor[language]||'en-US';
    recognizer.continuous=true;recognizer.interimResults=true;
    baseText=$('#intake-message').value;
    if(baseText&&!/\s$/.test(baseText))baseText+=' ';
    recognizer.onresult=e=>{let finalText='',interimText='';
      for(let i=0;i<e.results.length;i++){const r=e.results[i];if(r.isFinal)finalText+=r[0].transcript;else interimText+=r[0].transcript;}
      $('#intake-message').value=baseText+finalText+interimText;};
    recognizer.onerror=()=>stopDictation();
    recognizer.onend=()=>{if(listening)stopDictation();};
    recognizer.start();
    listening=true;dictateButton.classList.add('listening');dictateButton.querySelector('span').textContent=t('Listening… tap to stop');
  };
}

$('#language').value=language;
const changeLanguage=async(event)=>{
  language=event.target.value;
  $('#language').value=language;$('#language-dialog').value=language;
  await i18next.changeLanguage(language);
  try{localStorage.setItem('invoice-language',language);}catch{}
  for(const id of ['#error','#form-error','#intake-status','#toast'])$(id).textContent=t($(id).textContent);
  localize();updateNavigation();render();await evidence();
  if(!editing)$('#guest').dispatchEvent(new Event('input'));
  // Preserve unsaved form values when switching languages.
  $('#entry-title').textContent=t(editing?'Complete the details.':'Start with a name.');
  $('#save-request').textContent=t(editing?'Save details':'Add request');
  api('/api/health').then(h=>$('#ai-state').textContent=t(h.ai_configured?'Strands configured':'Strands: configure AWS access')).catch(()=>{});
};

$('#language').onchange=changeLanguage;$('#language-dialog').onchange=changeLanguage;
