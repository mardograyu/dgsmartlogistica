function vehicleMatchesSlot(key, vehicle, module='veiculos') {
  if(module!=='veiculos') return true;
  if(key==='tracao') return ['Cavalo','Truck','Toco','VUC','Utilitário'].includes(vehicle.tipo);
  if(/^carreta[2-4]?$/.test(key)) return ['Carreta','Bitrem','Rodotrem'].includes(vehicle.tipo);
  return true;
}
let slaFilters={};
function wireDriverStatus(readOnly){
  const status=document.getElementById('f-status'),reason=document.getElementById('f-motivo');
  const update=()=>{const required=['Inativo','Bloqueado'].includes(status.value);reason.required=required;reason.setAttribute('aria-required',String(required));const label=reason.closest('.field').querySelector('label');label.querySelector('.status-required')?.remove();if(required){const mark=document.createElement('span');mark.className='required-mark status-required';mark.textContent=' *';label.append(mark)}};
  if(status&&reason){status.addEventListener('change',update);update()}
  const capture=document.querySelector('[data-lookup="captacao"]');
  if(capture){capture.querySelectorAll('input,button').forEach(el=>el.disabled=true);capture.querySelectorAll('button,.input-icon').forEach(el=>el.hidden=true);const text=capture.querySelector('.lookup-text');if(!capture.querySelector('input[type="hidden"]').value)text.value='Cadastro direto';text.readOnly=true;}
  for(const key of ['tracao','carreta','carreta2']){const el=document.getElementById('lookup-'+key);if(el)el.placeholder='DIGITE A PLACA…'}
}
function hasSlaRisk(){return (operations?.sla||[]).some(r=>!r.cancelada&&r.status_viagem!=='Finalizada'&&r.etapas.some(s=>s.atraso_previsto||s.prazo_vencido||s.risco_cpt))}
function slaSummaryHTML(alerts=false){
  const trips=(operations?.sla||[]).filter(r=>!r.cancelada),active=trips.filter(r=>r.status_viagem!=='Finalizada');
  const count=(key,source=active)=>source.filter(r=>r.etapas.some(s=>s[key])).length;
  const cards=[['Early previsto',count('early_previsto')],['Atraso previsto',count('atraso_previsto')],['Prazo sem confirmação',count('prazo_vencido')],['CPT próximo',count('risco_cpt')],['Atraso real',count('atraso_real',trips)]];
  const risks=active.filter(r=>r.etapas.some(s=>s.atraso_previsto||s.prazo_vencido||s.risco_cpt));
  return `<section class="sla-summary"><div class="sla-summary-heading"><h3>Controle de SLA</h3>${state.tabs.includes('sla')?'<button data-sla-open>Ver controle</button>':''}</div><div class="metrics">${cards.map(([name,n])=>`<div class="metric"><small>${name}</small><div class="value">${n}</div></div>`).join('')}</div>${alerts&&risks.length?`<div class="sla-risk-list">${risks.slice(0,5).map(r=>`<div><strong>${esc(r.lh_trip||'#'+r.programacao)}</strong><span>${esc(r.etapas.filter(s=>s.atraso_previsto||s.prazo_vencido||s.risco_cpt).map(s=>s.etapa+': '+s.status+' · '+s.minutos+' min').join(' / '))}</span>${r.oc&&state.tabs.includes('oc')?`<button data-sla-oc="${r.oc}">Abrir OC</button>`:''}</div>`).join('')}</div>`:''}</section>`;
}
function wireSlaActions(){
  document.querySelectorAll('[data-sla-open]').forEach(b=>b.onclick=()=>navigate('sla'));
  document.querySelectorAll('[data-sla-oc]').forEach(b=>b.onclick=async()=>{const id=Number(b.dataset.slaOc);await navigate('oc');const record=rows.find(r=>r.id===id);if(record)await edit(record,'oc')});
}
function slaBreakdownHTML(trips){
 const summary=(kind,label)=>{const groups=new Map();for(const r of trips.filter(x=>!x.cancelada)){const key=kind==='rota'?ref('pessoas',r.origem)+' → '+ref('pessoas',r.destino):kind==='cliente'?ref('pessoas',r.cliente):ref('motoristas',r.motorista);if(!groups.has(key))groups.set(key,{total:0,medidas:0,prazo:0,atraso:0,previsto:0});const g=groups.get(key);g.total++;const stages=r.etapas.filter(s=>s.avaliavel);if(stages.length){g.medidas++;if(stages.every(s=>s.no_prazo_real))g.prazo++}if(r.etapas.some(s=>s.atraso_real))g.atraso++;if(r.etapas.some(s=>s.atraso_previsto))g.previsto++}return `<details class="sla-breakdown"><summary>Resumo por ${label}</summary><div class="tablewrap"><table><thead><tr><th>${label}</th><th>Viagens</th><th>Medidas</th><th>No prazo</th><th>Atraso real</th><th>Atraso previsto</th></tr></thead><tbody>${[...groups].map(([name,g])=>`<tr><td>${esc(name)}</td><td>${g.total}</td><td>${g.medidas}</td><td>${g.medidas?(g.prazo/g.medidas*100).toFixed(1)+'%':'Sem medição'}</td><td>${g.atraso}</td><td>${g.previsto}</td></tr>`).join('')}</tbody></table></div></details>`};
 return `<div class="sla-breakdowns"><p class="muted">Percentuais consideram somente etapas com horário real e limite informado; etapas pendentes ficam sem medição.</p>${summary('cliente','cliente')}${summary('rota','rota')}${summary('motorista','agregado')}</div>`;
}
function slaTripHTML(r){return `<article class="sla-trip"><div class="sla-summary-heading"><h3>${esc(r.lh_trip||'#'+r.programacao)} ${r.oc?'· OC #'+r.oc:''}</h3>${r.oc&&state.tabs.includes('oc')?`<button data-sla-oc="${r.oc}">Abrir OC</button>`:''}</div><p class="muted">${esc(ref('motoristas',r.motorista))} · ${esc(r.status_viagem)} · Responsabilidade: ${esc(r.responsavel)}</p><p class="muted">${esc(ref('pessoas',r.cliente))} · ${esc(ref('pessoas',r.origem))} → ${esc(ref('pessoas',r.destino))}</p><div class="tablewrap"><table><thead><tr><th>Etapa</th><th>Janela / limite</th><th>Previsão atual</th><th>Realizado</th><th>SLA</th></tr></thead><tbody>${r.etapas.map(s=>`<tr><td>${esc(s.etapa)}</td><td>${s.inicio?esc(datefmt(s.inicio))+' → ':''}${esc(datefmt(s.limite))}</td><td>${esc(datefmt(s.previsao))}</td><td>${esc(datefmt(s.real))}</td><td><span class="sla-state ${s.atraso_real||s.prazo_vencido?'late':s.atraso_previsto||s.risco_cpt?'risk':s.early_real||s.early_previsto?'early':'ok'}">${esc(s.status)}</span>${s.minutos?`<small> ${s.minutos} min</small>`:''}</td></tr>`).join('')}</tbody></table></div><div class="sla-durations">${Object.entries(r.duracoes).map(([k,v])=>`<span>${esc({espera_coleta:'Espera na coleta',carregamento:'Carregamento',espera_destino:'Espera no destino',descarga:'Descarga'}[k])}: <b>${v==null?'Sem horários':v+' min'}</b></span>`).join('')}</div>${r.motivo||r.observacao?`<p class="sla-reason">${esc(r.motivo)} · ${esc(r.observacao)}</p>`:''}<small class="muted">Último reporte: ${esc(datefmt(r.reportado_em))}</small></article>`}
function slaView(){
  let trips=(operations.sla||[]).filter(r=>slaFilters.showCancelled||!r.cancelada);
  if(slaFilters.q){const term=normalizeText(slaFilters.q);trips=trips.filter(r=>normalizeText([r.lh_trip,r.oc,ref('motoristas',r.motorista),ref('pessoas',r.cliente),ref('pessoas',r.origem),ref('pessoas',r.destino),r.motivo,r.responsavel].join(' ')).includes(term))}
  if(slaFilters.status)trips=trips.filter(r=>r.etapas.some(s=>s[slaFilters.status]));
  trips.sort((a,b)=>Math.max(...b.etapas.map(s=>s.prazo_vencido||s.atraso_previsto||s.atraso_real?s.minutos:0))-Math.max(...a.etapas.map(s=>s.prazo_vencido||s.atraso_previsto||s.atraso_real?s.minutos:0)));
  const measured=(operations.sla||[]).filter(r=>!r.cancelada&&r.etapas.some(s=>s.avaliavel)),onTime=measured.filter(r=>r.etapas.filter(s=>s.avaliavel).every(s=>s.no_prazo_real));
  $('#view').innerHTML=`<div class="content"><div class="eyebrow">Torre de Controle</div><div class="list-heading"><div><h2>Controle de SLA</h2><p class="muted">Previsões manuais, janelas de atendimento e horários reais. Atualização a cada 10 segundos.</p></div><button id="sla-refresh">Atualizar</button></div>${slaSummaryHTML()}${slaBreakdownHTML(trips)}<p class="sla-explainer">${measured.length?(onTime.length/measured.length*100).toFixed(1)+'% das viagens com horários medidos no prazo':'Ainda não há viagens com horários reais medidos'}. Prazo vencido sem confirmação exige reporte; não confirma um atraso real.</p><form id="sla-filters" class="filter-card"><label class="filter-field"><span>Viagem, OC, cliente, rota ou motorista</span><input name="q" placeholder="Pesquisar…"></label><label class="filter-field"><span>Situação</span><select name="status"><option value="">Todas</option>${[['early_previsto','Early previsto'],['atraso_previsto','Atraso previsto'],['early_real','Early real'],['atraso_real','Atraso real'],['prazo_vencido','Prazo sem confirmação'],['risco_cpt','CPT próximo']].map(([k,v])=>`<option value="${k}">${v}</option>`).join('')}</select></label><label class="sla-checkbox"><input type="checkbox" name="showCancelled"> Incluir canceladas</label><div class="filter-buttons"><button type="button" id="sla-clear">Limpar</button><button class="primary">Pesquisar</button></div></form><p class="muted">${trips.length} viagens encontradas</p>${trips.map(slaTripHTML).join('')||'<div class="empty">Nenhuma viagem encontrada.</div>'}</div>`;
  const form=$('#sla-filters');form.elements.q.value=slaFilters.q||'';form.elements.status.value=slaFilters.status||'';form.elements.showCancelled.checked=!!slaFilters.showCancelled;
  form.onsubmit=e=>{e.preventDefault();slaFilters=Object.fromEntries(new FormData(form));slaView()};$('#sla-clear').onclick=()=>{slaFilters={};slaView()};$('#sla-refresh').onclick=()=>navigate('sla');wireSlaActions();
}
async function loadDriverPerformance(id){
  const panel=document.getElementById('driver-performance');if(!panel)return;
  if(!id){panel.innerHTML='<p class="muted">Selecione um motorista para consultar seu desempenho.</p>';return}
  panel.dataset.driver=String(id);panel.textContent='Carregando desempenho…';
  try{const r=await api('driver-performance?id='+encodeURIComponent(id));if(!panel.isConnected||panel.dataset.driver!==String(id))return;
    panel.innerHTML=`<div class="sla-summary-heading"><h3>Desempenho do agregado</h3><strong>${r.nota_media==null?'Sem avaliações':r.nota_media.toFixed(2)+' / 5'}</strong></div><p>${r.avaliacoes} avaliações · ${r.viagens} viagens · ${r.atrasos_reais} viagens com atraso real · ${r.atrasos_atribuidos} atribuídas ao agregado</p>${r.nota_media!=null&&r.nota_media<=2.5?'<div class="notice">Avaliação baixa: revise o histórico antes de confirmar a viagem. Você pode continuar.</div>':''}<div class="performance-history">${r.historico.map(a=>`<details><summary>OC #${a.oc} · Nota ${a.nota_media??'—'} · ${esc(a.avaliador_nome)}</summary><p>${esc(datefmt(a.avaliado_em))} · ${esc(a.justificativa)}</p>${state.tabs.includes('avaliacoes')?`<button type="button" data-open-evaluation="${a.id}">Abrir avaliação</button>`:''}</details>`).join('')}</div>`;
    panel.querySelectorAll('[data-open-evaluation]').forEach(b=>b.onclick=async()=>{if(formContext&&!await dgConfirm('Sair do cadastro sem salvar?'))return;const eid=Number(b.dataset.openEvaluation);await navigate('avaliacoes');const rating=rows.find(x=>x.id===eid);if(rating)edit(rating,'avaliacoes')});
  }catch(e){if(panel.isConnected)panel.textContent=e.message}
}
function wireTransportForm(m,d,readOnly){
  if(['motoristas','programacao'].includes(m)){
    const panel=document.createElement('section');panel.id='driver-performance';panel.className='form-section performance-panel';document.querySelector('.section-layout').append(panel);
    loadDriverPerformance(m==='motoristas'?d.id:d.motorista);
  }
  if(m==='oc'&&d.id){
    if(state.tabs.includes('avaliacoes')){const button=document.createElement('button');button.type='button';button.textContent='Avaliar agregado';button.onclick=async()=>{if(!readOnly&&!await dgConfirm('Sair do cadastro sem salvar?'))return;const list=await api('records?module=avaliacoes'),existing=list.find(x=>x.oc===d.id);await edit(existing||{oc:d.id},'avaliacoes',!existing)};document.querySelector('.page-heading').append(button)}
  }
  if(m==='avaliacoes'){
    const lookup=document.querySelector('[data-lookup="motorista"]');lookup?.querySelectorAll('input,button').forEach(e=>e.disabled=true);
    const fill=async()=>{const id=$('#f-oc')?.value;if(!id){setField('motorista','');return}const before=id;const op=await api('operations?view='+(['sla','painel','dashboard','tracking'].find(k=>state.tabs.includes(k))||'painel'));if(!formContext||formContext.module!==m||$('#f-oc').value!==before)return;const oc=op.oc.find(x=>String(x.id)===String(id)),p=op.programacao.find(x=>x.id===oc?.programacao);setField('motorista',p?.motorista||'')};
    if(!readOnly)$('#f-oc')?.addEventListener('change',()=>fill().catch(e=>toast(e.message,true)));
    if(d.oc)fill().catch(e=>toast(e.message,true));
  }
}
function markRequiredFields(m) {
  for(const f of state.schema[m].fields.filter(f=>f.required)) {
    const el=document.getElementById('lookup-'+f.key)||document.getElementById('date-'+f.key)||document.getElementById('f-'+f.key);
    const container=document.querySelector('[data-field="'+f.key+'"]');
    if(container&&!container.querySelector('.required-mark')){const label=container.querySelector('label');if(label){const mark=document.createElement('span');mark.className='required-mark';mark.textContent=' *';label.append(mark);}}
    if(el && el.type!=='hidden') el.setAttribute('aria-required','true');
  }
  document.querySelector('.footer-note').textContent='* Campos obrigatórios. Observações são opcionais.';
}
function validateRequiredForm(m,data) {
  const missing=state.schema[m].fields.filter(f=>f.required && (data[f.key]==null||String(data[f.key]).trim()===''));
  document.querySelectorAll('.field-invalid').forEach(el=>el.classList.remove('field-invalid'));
  if(!missing.length) return;
  missing.forEach(f=>document.querySelector('[data-field="'+f.key+'"]')?.classList.add('field-invalid'));
  const f=missing[0];
  (document.getElementById('lookup-'+f.key)||document.getElementById('date-'+f.key)||document.getElementById('f-'+f.key))?.focus();
  throw new Error('Preencha os campos obrigatórios: '+missing.map(f=>f.label).join(', ')+'.');
}
let dgConfirmationOpen=false;
function wireMobileMenu() {
  if(wireMobileMenu.cleanup) wireMobileMenu.cleanup();
  const toggle=document.getElementById('toggle-sidebar'),close=document.getElementById('mobile-menu-close'),backdrop=document.getElementById('mobile-menu-backdrop'),sidebar=document.getElementById('dgSidebar');
  const mobile=window.matchMedia('(max-width:700px)');
  function setOpen(open,restore=true) {
    open=Boolean(open&&mobile.matches);
    document.body.classList.toggle('menu-open',open);
    toggle.setAttribute('aria-expanded',String(open));
    backdrop.hidden=!open;
    sidebar.inert=mobile.matches&&!open;
    document.querySelector('.main').inert=open;
    if(open)close.focus();else if(restore&&mobile.matches)toggle.focus();
  }
  toggle.onclick=()=>setOpen(!document.body.classList.contains('menu-open'));
  close.onclick=backdrop.onclick=()=>setOpen(false);
  const keyboard=event=>{
    if(!mobile.matches||!document.body.classList.contains('menu-open'))return;
    if(event.key==='Escape'){event.preventDefault();setOpen(false);return}
    if(event.key==='Tab'){
      const items=[...sidebar.querySelectorAll('button,a[href],[tabindex="0"]')].filter(el=>!el.disabled&&el.getClientRects().length);
      const first=items[0],last=items[items.length-1];
      if(event.shiftKey&&document.activeElement===first){event.preventDefault();last?.focus()}
      else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first?.focus()}
    }
  };
  const resize=()=>setOpen(false,false);
  document.addEventListener('keydown',keyboard);mobile.addEventListener('change',resize);
  wireMobileMenu.cleanup=()=>{document.removeEventListener('keydown',keyboard);mobile.removeEventListener('change',resize)};
  setOpen(false,false);
}
function dgConfirm(message) {
  if(dgConfirmationOpen) return Promise.resolve(false);
  dgConfirmationOpen=true;
  return new Promise(resolve=>{
    const previous=document.activeElement,discard=/sem salvar|descartad/.test(message);
    const dialog=document.createElement('dialog');dialog.className='dg-confirm';
    dialog.setAttribute('aria-labelledby','dg-confirm-title');dialog.setAttribute('aria-describedby','dg-confirm-message');
    dialog.innerHTML='<div class="dg-confirm-body"><div class="dg-confirm-icon">!</div><h2 id="dg-confirm-title"></h2><p id="dg-confirm-message"></p></div><div class="dg-confirm-actions"><button type="button" data-stay></button><button type="button" class="primary" data-proceed></button></div>';
    dialog.querySelector('h2').textContent=discard?'Descartar alterações?':'Confirmar ação';
    dialog.querySelector('p').textContent=discard?'As alterações que você ainda não salvou serão descartadas. Os dados já salvos permanecem no sistema.':message;
    dialog.querySelector('[data-stay]').textContent=discard?'Continuar editando':'Voltar';
    dialog.querySelector('[data-proceed]').textContent=discard?'Descartar alterações':'Confirmar';
    const finish=value=>{dialog.close();dialog.remove();dgConfirmationOpen=false;if(previous?.isConnected)previous.focus();resolve(value);};
    dialog.querySelector('[data-stay]').onclick=()=>finish(false);
    dialog.querySelector('[data-proceed]').onclick=()=>finish(true);
    dialog.addEventListener('cancel',e=>{e.preventDefault();finish(false)});
    document.body.append(dialog);dialog.showModal();dialog.querySelector('[data-stay]').focus();
  });
}
