const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),path=require('node:path');
const root=path.resolve(__dirname,'..');
let dialog, focused=0;
const previous={isConnected:true,focus(){focused++}};
const document={activeElement:previous,body:{append(el){dialog=el}},createElement(){
 const children={};return {className:'',setAttribute(){},querySelector(key){return children[key]??={textContent:'',focus(){}}},addEventListener(key,fn){this[key]=fn},showModal(){this.open=true},close(){this.open=false},remove(){this.removed=true}};
}};
const ctx=vm.createContext({document,console});vm.runInContext(fs.readFileSync(path.join(root,'static/v7.js'),'utf8'),ctx);
for(const type of ['Cavalo','Truck','Toco','VUC','Utilitário']){ctx.type=type;assert(vm.runInContext("vehicleMatchesSlot('tracao',{tipo:type})",ctx));assert(!vm.runInContext("vehicleMatchesSlot('carreta',{tipo:type})",ctx));}
for(const type of ['Carreta','Bitrem','Rodotrem'])for(const key of ['carreta','carreta2','carreta3','carreta4']){ctx.type=type;ctx.key=key;assert(vm.runInContext("vehicleMatchesSlot(key,{tipo:type})",ctx));assert(!vm.runInContext("vehicleMatchesSlot('tracao',{tipo:type})",ctx));}
assert(!vm.runInContext("vehicleMatchesSlot('tracao',{tipo:''})",ctx));
(async()=>{
 let pending=vm.runInContext("dgConfirm('Voltar? Alterações serão descartadas.')",ctx);
 assert.equal(dialog.querySelector('[data-stay]').textContent,'Continuar editando');assert.equal(dialog.querySelector('[data-proceed]').textContent,'Descartar alterações');
 assert.equal(await vm.runInContext("dgConfirm('Duplicada')",ctx),false);
 dialog.querySelector('[data-stay]').onclick();assert.equal(await pending,false);assert(dialog.removed);assert.equal(focused,1);
 pending=vm.runInContext("dgConfirm('Sair sem salvar?')",ctx);dialog.querySelector('[data-proceed]').onclick();assert.equal(await pending,true);
 pending=vm.runInContext("dgConfirm('Confirmar?')",ctx);let prevented=false;dialog.cancel({preventDefault(){prevented=true}});assert.equal(await pending,false);assert(prevented);
 const source=fs.readFileSync(path.join(root,'static/app.js'),'utf8');assert(!/\bconfirm\(/.test(source));assert(source.includes('validateRequiredForm(m,data)'));assert(source.includes('vehicleMatchesSlot(key,r,el.dataset.module)'));
 console.log('V7: filtros de tração/carretas e confirmação, cancelamento, Escape, foco e bloqueio de diálogos duplicados verificados.');
})().catch(error=>{console.error(error);process.exitCode=1});
