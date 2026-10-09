/* Regression tests for resolved names, compound filters, metrics and actual pagination. */
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),path=require('node:path');
const root=path.resolve(__dirname,'..'),schema=JSON.parse(fs.readFileSync(path.join(root,'docs/campos.json')));
const elements=Object.fromEntries(['#list-table','#list-result-count','#list-metrics','#list-pagination'].map(k=>[k,{innerHTML:'',textContent:''}]));
const ctx=vm.createContext({console,setInterval:()=>0,setTimeout:()=>0,clearTimeout:()=>{},document:{querySelector:s=>elements[s]||null,querySelectorAll:()=>[]}});
vm.runInContext(fs.readFileSync(path.join(root,'static/app.js'),'utf8').replace(/^boot\(\);$/m,''),ctx);
ctx.schema=schema;vm.runInContext("state={schema,refs:{pessoas:[{id:1,nome:'Transportes São José',documento:'12345678000190'}],cidades:[{id:2,nome:'Poços de Caldas',uf:'MG'}],motoristas:[{id:3,nome:'João Silva',cpf:'12345678901'}],veiculos:[{id:4,nome:'ABC1D23',placa:'ABC1D23'}],programacao:[{id:5,nome:'LH-TESTE'}]}}",ctx);
function filter(m,data,f){ctx.m=m;ctx.data=data;ctx.f=f;return JSON.parse(JSON.stringify(vm.runInContext('filterList(m,data,f)',ctx)))}
assert.equal(filter('pessoas',[{id:1,nome:'José',documento:'12345678000190',cidade:2,status:'Ativo',categorias:['Cliente','Fornecedor']}],{nome:'jose',documento:'12.345.678',cidade:'pocos',categoria:'Fornecedor',status:'Ativo'}).length,1);
assert.equal(filter('pessoas',[{nome:'José',cidade:2,categorias:['Cliente']}],{cidade:'MG',categoria:'Fornecedor'}).length,0);
assert.equal(filter('motoristas',[{id:3,nome:'João Silva',cpf:'12345678901',cidade:2}],{documento:'123.456.789-01',cidade:'mg'}).length,1);
assert.equal(filter('veiculos',[{placa:'ABC1D23',proprietario:1,tipo:'Cavalo',status:'Ativo'}],{placa:'ABC-1D23',proprietario:'12.345.678/0001',tipo:'Cavalo'}).length,1);
assert.equal(filter('veiculos',[{placa:'ABC1D23',proprietario:1}],{proprietario:'sao jose'}).length,1);
const programs=[{id:2,lh_trip:'ROTA-B',cliente:1,status:'Captada',carregamento:'2026-10-09T10:00'},{id:1,lh_trip:'ROTA-A',cliente:1,status:'Em Viagem',carregamento:'2026-10-08T10:00'}];
assert.deepEqual(filter('programacao',programs,{cliente:'1',de:'2026-10-08',ate:'2026-10-08'}).map(r=>r.id),[1]);
assert.deepEqual(filter('programacao',programs,{}).map(r=>r.id),[1,2]);
assert.equal(filter('oc',[{id:7,data_oc:'2026-10-08',programacao:5,motorista:3,tomador:1}],{q:'joao',de:'2026-10-08',ate:'2026-10-08'}).length,1);
assert.equal(filter('oc',[{programacao:5}],{q:'LH-TESTE'}).length,1);
assert.equal(filter('mdfe',[{numero:'123',ambiente:'Homologação'},{numero:'123',ambiente:'Produção'}],{q:'123',ambiente:'Produção'}).length,1);
assert.equal(filter('vale_pedagio',[{documento:'123456',oc:7,tracao:4,data:'2026-10-08',situacao_operacao:'Rascunho',meio_pagamento:'Repom'}],{documento_operacao:'123.456',placa:'ABC-1D23',oc:'#7',de:'2026-10-08',ate:'2026-10-08',situacao:'Rascunho'}).length,1);
assert.equal(filter('rotas',[{nome:'Sul',origem:2,destino:2,ufs:'MG,SP',status:'Ativo'}],{origem:'2',destino:'2',status:'Ativo',q:'pocos'}).length,1);
ctx.data=[{id:1,categorias:['Cliente','Fornecedor']}];assert.match(vm.runInContext("listMetricsHTML('pessoas',data)",ctx),/Clientes<\/span><strong>1/);
ctx.data=[{cnh_validade:vm.runInContext('localDay(new Date(Date.now()-86400000))',ctx)},{cnh_validade:vm.runInContext('localDay(new Date(Date.now()+86400000))',ctx)}];const metrics=vm.runInContext("listMetricsHTML('motoristas',data)",ctx);assert.match(metrics,/CNH vencidas<\/span><strong>1/);assert.match(metrics,/CNH a vencer<\/span><strong>1/);
ctx.data=Array.from({length:25},(_,i)=>({id:i+1,nome:'Pessoa '+(i+1),status:'Ativo'}));vm.runInContext("rows=data;current='pessoas';listFilters={por_pagina:'10'};listPage=1;tableRows()",ctx);assert.equal(elements['#list-table'].innerHTML.split('data-edit=').length-1,10);assert.match(elements['#list-pagination'].innerHTML,/1–10 de 25/);vm.runInContext('listPage=3;tableRows()',ctx);assert.equal(elements['#list-table'].innerHTML.split('data-edit=').length-1,5);assert.match(elements['#list-pagination'].innerHTML,/21–25 de 25/);
for(const m of ['pessoas','motoristas','veiculos','programacao','oc','mdfe','vale_pedagio','rotas']){ctx.m=m;const html=vm.runInContext('listFilterHTML(m)',ctx);assert.match(html,/por_pagina/);assert(html.includes('name='))}
console.log('Pesquisa: 8 abas, documentos/placas formatados, nomes vinculados, filtros combinados, datas, indicadores e paginação verificados.');
