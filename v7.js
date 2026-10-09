function vehicleMatchesSlot(key, vehicle, module='veiculos') {
  if(module!=='veiculos') return true;
  if(key==='tracao') return ['Cavalo','Truck','Toco','VUC','Utilitário'].includes(vehicle.tipo);
  if(/^carreta[2-4]?$/.test(key)) return ['Carreta','Bitrem','Rodotrem'].includes(vehicle.tipo);
  return true;
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
