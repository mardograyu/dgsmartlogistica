/* Verificação de renderização HTML e serialização; não usa navegador. */
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),path=require('node:path');
const root=path.resolve(__dirname,'..');
const schema=JSON.parse(fs.readFileSync(path.join(root,'docs/campos.json'),'utf8'));
const ctx=vm.createContext({window:{addEventListener:()=>{}},console,setInterval:()=>0,setTimeout:()=>0,clearTimeout:()=>{},document:{querySelector:()=>null,querySelectorAll:()=>[],addEventListener:()=>{}},Event:class{constructor(type){this.type=type}}});
const source=fs.readFileSync(path.join(root,'static/app.js'),'utf8').replace(/^boot\(\);$/m,'');
vm.runInContext(source,ctx);vm.runInContext(fs.readFileSync(path.join(root,'static/v5.js'),'utf8').replace(/^boot\(\);$/m,''),ctx);ctx.fixture=schema;
vm.runInContext("state={schema:fixture,financial:true,approve:true,user:{id:1,perfis:['Administrador']},refs:{pessoas:[{id:4,nome:'Cliente & Cia'}],motoristas:[{id:9,nome:'Motorista Teste'}],veiculos:[],usuarios:[]}}",ctx);
for(const [module,sc] of Object.entries(schema)){
 ctx.module=module;
 const output=vm.runInContext("current=module;formContext={module,data:{id:1}};formSections(module,{id:1})",ctx);
 for(const f of sc.fields){const pattern=f.type==='ref'?`data-lookup="${f.key}"`:`data-field="${f.key}"`;assert.equal(output.split(pattern).length-1,1,`${module}.${f.key} renderizado exatamente uma vez`)}
 assert.match(output,/form-section/);
}
ctx.data={id:1,cliente:4,carregamento:'2026-10-08T15:30'};
const html=vm.runInContext("current='programacao';formContext={module:'programacao'};formSections('programacao',data)",ctx);
assert.match(html,/Cliente &amp; Cia/);assert.match(html,/value="2026-10-08"/);assert.match(html,/value="15:30"/);assert.match(html,/Dados da programação/);assert.match(html,/Associar motorista/);assert.match(html,/Dados da carga/);assert.match(html,/Valores/);
const initial=vm.runInContext("formContext={module:'programacao'};formSections('programacao',{})",ctx);assert.doesNotMatch(initial,/id="f-motorista"/);assert.match(initial,/Dados da programação/);
const moneyKeys=new Set();for(const sc of Object.values(schema))for(const f of sc.fields)if(f.type==='money')moneyKeys.add(f.key);
ctx.filtered={};for(const[m,sc]of Object.entries(schema))ctx.filtered[m]={...sc,fields:sc.fields.filter(f=>f.type!=='money'&&f.type!=='offer')};
const restricted=vm.runInContext("state.schema=filtered;state.financial=false;formSections('programacao',{})",ctx);assert.doesNotMatch(restricted,/id="f-valor_cliente"|id="f-frete_agregado"|id="f-pedagio"|id="margin-value"/);
// Uma busca não selecionada não pode ser enviada como ID, e as datas guardam o formato persistido.
ctx.inputs={'#f-lh_trip':{value:'TESTE'},'#f-cliente':{value:'4'},'#f-motorista':{value:''},'#f-carregamento':{value:'2026-10-08T15:30'},'#f-eta_destino':{value:'2026-10-09T12:00'}};
ctx.document.querySelector=selector=>ctx.inputs[selector]||{value:''};
const result=vm.runInContext("formContext={module:'programacao'};readForm()",ctx);assert.equal(result.cliente,4);assert.equal(result.motorista,'');assert.equal(result.carregamento,'2026-10-08T15:30');
assert.equal(vm.runInContext("titles.oc",ctx),'OC');assert(!source.includes('Ir para…'));assert(!source.includes('.showModal()'));assert(source.includes('/logo-original.png'));
const logo=fs.readFileSync(path.join(root,'static/logo.svg'),'utf8');assert(logo.includes('data:image/png;base64,'));assert(logo.includes('preserveAspectRatio="xMidYMid meet"'));assert(!logo.includes('<rect'));
console.log('UI: campos dos 16 módulos, cadastro em duas etapas da programação, datas separadas, referências, restrições financeiras, OC e logo verificados.');
