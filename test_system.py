import unittest,tempfile,threading,sys,os,json,http.client
from pathlib import Path
from datetime import date,datetime,timedelta
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import server

class System(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();server.DB=Path(cls.temp.name)/'test.sqlite';os.environ['DG_ADMIN_PASSWORD']='Test-admin-12345';server.initialize()
        cls.http=server.ThreadingHTTPServer(('127.0.0.1',0),server.API);cls.port=cls.http.server_port;cls.thread=threading.Thread(target=cls.http.serve_forever,daemon=True);cls.thread.start()
    @classmethod
    def tearDownClass(cls):cls.http.shutdown();cls.http.server_close();cls.temp.cleanup()
    def setUp(self):self.cookie='';self.csrf='';self.login('admin@dg.local','Test-admin-12345')
    def request(self,path,data=None):
        c=http.client.HTTPConnection('127.0.0.1',self.port);headers={'Cookie':self.cookie,'X-CSRF-Token':self.csrf}
        if data is not None:headers['Content-Type']='application/json'
        c.request('POST' if data is not None else 'GET','/api/'+path,json.dumps(data).encode() if data is not None else None,headers);r=c.getresponse();raw=r.read()
        cookie=r.getheader('Set-Cookie')
        if cookie:self.cookie=cookie.split(';')[0]
        try:body=json.loads(raw)
        except Exception:body=raw.decode()
        return r.status,body
    def login(self,email,senha):
        status,data=self.request('login',{'email':email,'senha':senha});self.assertEqual(status,200,data)
        status,data=self.request('bootstrap');self.assertEqual(status,200,data);self.csrf=data['csrf'];return data
    def save(self,m,d,id=None,version=None):
        status,r=self.request('records',{'module':m,'data':d,'id':id,'version':version});self.assertEqual(status,200,r);return r['record']
    def user(self,role):
        token=server.secrets.token_hex(4);email=token+'@test.local';r=self.save('usuarios',{'nome':'Teste '+role,'email':email,'senha':'Test-user-12345','perfis':[role],'abas':[],'ocultar':[],'status':'Ativo'});return email
    def trip(self):
        token=server.secrets.token_hex(4);p=self.save('pessoas',{'nome':'Cliente '+token,'documento':token,'tipo':'Jurídica','status':'Ativo'});v=self.save('veiculos',{'placa':token,'tipo':'Cavalo','status':'Ativo'});d=self.save('motoristas',{'nome':'Motorista '+token,'cpf':token,'tracao':v['id'],'status':'Ativo','cnh':'123','cnh_validade':'2030-01-01'});
        return self.save('programacao',{'lh_trip':token,'cliente':p['id'],'origem':p['id'],'destino':p['id'],'motorista':d['id'],'tracao':v['id'],'valor_cliente':10000,'frete_agregado':7000,'pedagio':300,'produto':'Carga','quantidade':1,'peso':100,'volume':'1','captador':1,'carregamento':'2026-10-01T10:00','eta_destino':'2026-10-02T10:00','status':'Pronta para OC'})
    def oc(self,p):
        status,data=self.request('generate-oc',{'id':p['id'],'accept_warnings':True});self.assertEqual(status,200,data)
        status,ocs=self.request('records?module=oc');return next(o for o in ocs if o['id']==data['id'])
    def test_01_password_hashed(self):
        encoded=server.password('a');self.assertEqual(len(encoded.split(':')[0]),32);self.assertEqual(len(encoded.split(':')[1]),64);self.assertTrue(server.verify('a',encoded));self.assertFalse(server.verify('b',encoded))
    def test_02_business_days(self):
        self.assertEqual(server.business_days(date(2026,10,8)),date(2026,10,23));self.assertEqual(server.business_days(date(2026,11,13),5),date(2026,11,23))
    def test_03_duplicate_notify(self):
        token=server.secrets.token_hex(4);self.save('veiculos',{'placa':token,'tipo':'Cavalo','status':'Ativo'});status,data=self.request('records',{'module':'veiculos','data':{'placa':token,'tipo':'Cavalo','status':'Ativo'}});self.assertEqual(status,400);self.assertIn('já cadastrado',data['error'])
    def test_04_one_oc_and_sync(self):
        p=self.trip();o=self.oc(p);status,result=self.request('generate-oc',{'id':p['id']});self.assertTrue(result['existing']);self.assertEqual(result['id'],o['id'])
        self.save('oc',dict(o,status='Em Viagem',autorizacao='2026-10-01T09:00',saida_real='2026-10-01T10:00'),o['id'],o['version']);status,programs=self.request('records?module=programacao');self.assertEqual(next(x for x in programs if x['id']==p['id'])['status'],'Em Viagem')
        status,pay=self.request('payments');advance=next(x for x in pay if x['oc_id']==o['id'] and x['kind']=='Adiantamento');self.assertEqual(advance['amount'],490000);self.assertIn('16:00',advance['due'])
    def test_05_admin_cannot_approve(self):
        p=self.trip();o=self.oc(p);self.save('oc',dict(o,status='Em Viagem',autorizacao='2026-10-01T09:00',saida_real='2026-10-01T10:00'),o['id'],o['version']);status,pay=self.request('payments');parcel=next(x for x in pay if x['oc_id']==o['id']);status,data=self.request('payment-action',{'id':parcel['id'],'action':'approve'});self.assertEqual(status,403)
    def test_06_operation_privacy_backend(self):
        p=self.trip();email=self.user('Operação');data=self.login(email,'Test-user-12345');self.assertNotIn('financeiro',data['tabs']);self.assertNotIn('vale_pedagio',data['tabs']);status,list_=self.request('records?module=programacao');r=next(x for x in list_ if x['id']==p['id']);self.assertNotIn('valor_cliente',r);self.assertNotIn('frete_agregado',r);status,_=self.request('payments');self.assertEqual(status,403);status,_=self.request('records',{'module':'programacao','id':p['id'],'data':{'valor_cliente':1}});self.assertEqual(status,403)
    def test_07_captacao_fixed_offer_only(self):
        p=self.trip();email=self.user('Captação');data=self.login(email,'Test-user-12345');status,list_=self.request('records?module=programacao');r=next(x for x in list_ if x['id']==p['id']);self.assertEqual(r['frete_agregado'],7000);self.assertNotIn('valor_cliente',r);r=self.save('programacao',{'frete_agregado':7100},p['id'],r['version']);self.assertEqual(r['frete_agregado'],7100)
    def test_08_approval_reset_when_changed(self):
        p=self.trip();o=self.oc(p);o=self.save('oc',{'chegada_real':'2026-10-08T14:00'},o['id'],o['version']);o=self.save('oc',dict(o,status='Finalizada',autorizacao='2026-10-01T09:00',saida_real='2026-10-01T10:00',descarga_real='2026-10-08T15:00'),o['id'],o['version']);email=self.user('Financeiro');self.login(email,'Test-user-12345');status,pay=self.request('payments');advance=next(x for x in pay if x['oc_id']==o['id'] and x['kind']=='Adiantamento');status,data=self.request('payment-action',{'id':advance['id'],'action':'approve'});self.assertEqual(status,200,data);status,data=self.request('payment-action',{'id':advance['id'],'action':'send'});self.assertEqual(status,409);self.assertIn('Nenhum dinheiro',data['error']);self.login('admin@dg.local','Test-admin-12345');status,programs=self.request('records?module=programacao');p=next(x for x in programs if x['id']==p['id']);self.save('programacao',{'frete_agregado':7200},p['id'],p['version']);status,pay=self.request('payments');self.assertEqual(next(x for x in pay if x['id']==advance['id'])['status'],'Pendente')
    def test_09_cancel_keeps_and_cannot_reopen(self):
        p=self.trip();o=self.oc(p);status,data=self.request('cancel-trip',{'id':p['id'],'motivo':'Cliente cancelou a carga'});self.assertEqual(status,200,data);status,ocs=self.request('records?module=oc');self.assertEqual(next(x for x in ocs if x['id']==o['id'])['status'],'Cancelada');status,data=self.request('records',{'module':'programacao','id':p['id'],'data':{'status':'Captada'}});self.assertEqual(status,400)
    def test_10_concurrent_editor(self):
        p=self.save('pessoas',{'nome':'Version test','tipo':'Física','documento':'12345678900'});self.save('pessoas',{'nome':'Updated'},p['id'],p['version']);status,data=self.request('records',{'module':'pessoas','id':p['id'],'version':p['version'],'data':{'nome':'Lost update'}});self.assertEqual(status,400);self.assertIn('Outro usuário',data['error'])
    def test_11_partial_import_duplicates(self):
        token=server.secrets.token_hex(4);status,data=self.request('import',{'module':'veiculos','records':[{'placa':token,'tipo':'Cavalo'},{'placa':token,'tipo':'Cavalo'}]});self.assertEqual(status,200);self.assertTrue(data[0]['ok']);self.assertIn('já cadastrado',data[1]['error'])
    def test_12_csrf(self):
        csrf=self.csrf;self.csrf='wrong';status,data=self.request('records',{'module':'pessoas','data':{'nome':'CSRF'}});self.assertEqual(status,403);self.csrf=csrf
    def test_13_required_oc(self):
        p=self.trip();p=self.save('programacao',{'status':'Captada','motorista':'','tracao':''},p['id']);status,data=self.request('generate-oc',{'id':p['id']});self.assertEqual(status,400);self.assertIn('Preencha',data['error'])
    def test_14_multiple_trips_same_driver(self):
        p=self.trip();d=dict(p);d.pop('id');d.pop('version');d['lh_trip']='Outra viagem';q=self.save('programacao',d);self.oc(p);self.oc(q);self.assertNotEqual(p['id'],q['id'])
    def test_15_static_ui(self):
        c=http.client.HTTPConnection('127.0.0.1',self.port);c.request('GET','/');r=c.getresponse();self.assertEqual(r.status,200);self.assertIn('DG Smart',r.read().decode())

    def test_16_oc_fields_and_distinct_participants(self):
        p=self.trip();o=self.oc(p);self.assertEqual(o['motorista'],p['motorista']);self.assertEqual(o['produto'],'Carga')
        other=self.save('pessoas',{'nome':'Remetente independente','tipo':'Jurídica','documento':'12345678000199'})
        o=self.save('oc',{'remetente':other['id'],'produto':'Carga revisada','frete_agregado':8000},o['id'],o['version'])
        status,programs=self.request('records?module=programacao');p=next(x for x in programs if x['id']==p['id'])
        self.assertEqual(p['produto'],'Carga revisada');self.assertEqual(p['frete_agregado'],8000);self.assertEqual(p['origem'],p['cliente']);self.assertEqual(o['remetente'],other['id'])
        status,pay=self.request('payments');self.assertEqual(next(x for x in pay if x['oc_id']==o['id'] and x['kind']=='Adiantamento')['amount'],560000)
    def test_17_oc_privacy_and_financial_discount_permissions(self):
        p=self.trip();o=self.oc(p)
        status,data=self.request('records',{'module':'oc','id':o['id'],'version':o['version'],'data':{'inss_desconto':10}});self.assertEqual(status,403)
        email=self.user('Financeiro');self.login(email,'Test-user-12345')
        status,data=self.request('records',{'module':'oc','id':o['id'],'data':{'inss_desconto':10}});self.assertEqual(status,403) # tab permission remains required
        self.login('admin@dg.local','Test-admin-12345');email=self.user('Operação');bootstrap=self.login(email,'Test-user-12345')
        self.assertFalse(any(f['key'] in ['adiantamento_calculado','beneficiario','saldo_calculado'] for f in bootstrap['schema']['oc']['fields']))
        status,op=self.request('operations?view=tracking');oc=next(x for x in op['oc'] if x['id']==o['id']);self.assertNotIn('frete_agregado',oc);self.assertNotIn('beneficiario_tipo',oc)

    def test_18_new_filter_data_defaults_and_provider_state(self):
        p=self.trip();o=self.oc(p)
        vpo=self.save('vale_pedagio',{'oc':o['id'],'operadora':'Repom','documento':'123456','valor':300})
        self.assertEqual(vpo['tracao'],p['tracao']);self.assertEqual(vpo['lh_trip'],p['lh_trip']);self.assertEqual(vpo['meio_pagamento'],'Repom');self.assertEqual(vpo['situacao_operacao'],'Rascunho');self.assertTrue(vpo['data'])
        status,response=self.request('document-action',{'module':'vale_pedagio','id':vpo['id'],'action':'emit'});self.assertEqual(status,200,response)
        status,records=self.request('records?module=vale_pedagio');vpo=next(r for r in records if r['id']==vpo['id']);self.assertEqual(vpo['situacao_operacao'],'Aguardando configuração')
        city=self.save('cidades',{'nome':'Cidade filtro','uf':'MG'})
        route=self.save('rotas',{'nome':'Rota filtro','origem':city['id'],'destino':city['id']});self.assertEqual(route['status'],'Ativo')
        status,b=self.request('bootstrap');self.assertEqual(next(r for r in b['refs']['cidades'] if r['id']==city['id'])['uf'],'MG')

    def test_19_ready_requires_driver_vehicle_and_positive_offer(self):
        p=self.trip();status,data=self.request('records',{'module':'programacao','id':p['id'],'data':{'status':'Pronta para OC','motorista':'','frete_agregado':100}})
        self.assertEqual(status,400);self.assertIn('motorista',data['error'])
        p=self.trip();p=self.save('programacao',{'status':'Captada'},p['id'],p['version'])
        status,data=self.request('generate-oc',{'id':p['id']});self.assertEqual(status,400);self.assertIn('Pronta para OC',data['error'])

    def test_20_arrival_must_be_saved_before_finalization(self):
        p=self.trip();o=self.oc(p)
        status,data=self.request('records',{'module':'oc','id':o['id'],'data':{'status':'Finalizada','autorizacao':'2026-10-01T09:00','saida_real':'2026-10-01T10:00','chegada_real':'2026-10-02T08:00','descarga_real':'2026-10-02T09:00'}})
        self.assertEqual(status,400);self.assertIn('Salve a chegada',data['error'])
        o=self.save('oc',{'status':'Chegada no Cliente','autorizacao':'2026-10-01T09:00','saida_real':'2026-10-01T10:00','chegada_real':'2026-10-02T08:00'},o['id'],o['version'])
        o=self.save('oc',{'status':'Finalizada','descarga_real':'2026-10-02T09:00'},o['id'],o['version'])
        self.assertEqual(o['status_datas']['Chegada no Cliente'],'2026-10-02T08:00');self.assertEqual(o['status'],'Finalizada')

    def test_21_cancellation_requires_reason_and_keeps_history(self):
        p=self.trip();o=self.oc(p)
        status,data=self.request('cancel-trip',{'id':p['id']});self.assertEqual(status,400)
        status,data=self.request('cancel-trip',{'id':p['id'],'motivo':'Carga indisponível'});self.assertEqual(status,200,data)
        status,ocs=self.request('records?module=oc');o=next(x for x in ocs if x['id']==o['id']);self.assertEqual(o['cancelamento_motivo'],'Carga indisponível');self.assertTrue(o['status_datas']['Cancelada'])

    def test_22_vpo_axles_and_manual_reason(self):
        traction=self.save('veiculos',{'placa':server.secrets.token_hex(4),'tipo':'Cavalo','eixos':3,'status':'Ativo'})
        trailer=self.save('veiculos',{'placa':server.secrets.token_hex(4),'tipo':'Carreta','eixos':3,'status':'Ativo'})
        o=self.oc(self.trip());vpo=self.save('vale_pedagio',{'oc':o['id'],'tracao':traction['id'],'carreta':trailer['id'],'numero_eixos':99})
        self.assertEqual(vpo['numero_eixos'],6)
        status,data=self.request('records',{'module':'vale_pedagio','id':vpo['id'],'data':{'ajustar_eixos':'Sim','numero_eixos':5}});self.assertEqual(status,400)
        vpo=self.save('vale_pedagio',{'ajustar_eixos':'Sim','numero_eixos':5,'eixos_ajuste_motivo':'Eixo suspenso'},vpo['id']);self.assertEqual(vpo['numero_eixos'],5)

    def test_23_permissions_override_and_conflict(self):
        status,data=self.request('records',{'module':'usuarios','data':{'nome':'Conflito','email':'conflict@test.local','senha':'Test-user-12345','perfis':['Cadastro'],'abas':['oc'],'ocultar':['oc'],'status':'Ativo'}})
        self.assertEqual(status,400)
        email='overrides-'+server.secrets.token_hex(4)+'@test.local'
        self.save('usuarios',{'nome':'Overrides','email':email,'senha':'Test-user-12345','perfis':['Cadastro'],'abas':['oc'],'ocultar':['veiculos'],'status':'Ativo'})
        data=self.login(email,'Test-user-12345');self.assertIn('oc',data['tabs']);self.assertNotIn('veiculos',data['tabs']);self.assertFalse(data['approve'])

    def test_24_finance_can_import_oc_and_axles_without_registry_tabs(self):
        p=self.trip();o=self.oc(p);email=self.user('Financeiro');self.login(email,'Test-user-12345')
        status,data=self.request('oc-source?module=ciot&id='+str(o['id']));self.assertEqual(status,200,data);self.assertEqual(data['programacao']['frete_agregado'],7000)
        status,data=self.request('vehicle-axles?tracao='+str(p['tracao']));self.assertEqual(status,200,data);self.assertEqual(data['tracao']['id'],p['tracao'])
        self.login('admin@dg.local','Test-admin-12345');email=self.user('Cadastro');self.login(email,'Test-user-12345')
        status,_=self.request('oc-source?module=ciot&id='+str(o['id']));self.assertEqual(status,403)

    def test_25_loading_timestamp_and_chronology(self):
        p=self.trip();o=self.oc(p)
        status,data=self.request('records',{'module':'oc','id':o['id'],'data':{'status':'Em Carregamento','autorizacao':'2026-10-01T08:00'}});self.assertEqual(status,400)
        o=self.save('oc',{'status':'Em Carregamento','autorizacao':'2026-10-01T08:00','carregamento_real':'2026-10-01T09:00'},o['id'],o['version'])
        status,data=self.request('records',{'module':'oc','id':o['id'],'data':{'status':'Em Viagem','saida_real':'2026-10-01T08:00'}});self.assertEqual(status,400)
        self.assertEqual(o['status_datas']['Em Carregamento'],'2026-10-01T09:00')

    def test_26_ciot_repeatable_data_persists_and_validates(self):
        o=self.oc(self.trip());ciot=self.save('ciot',{'oc':o['id'],'operadora':'Repom','ambiente':'Homologação','documentos':[{'numero':'123','ncm':'1001','quantidade':'10'}],'pagamentos':[{'valor':'70','pix':'chave-teste'}]})
        self.assertEqual(ciot['documentos'][0]['numero'],'123');self.assertEqual(ciot['pagamentos'][0]['valor'],'70')
        status,data=self.request('records',{'module':'ciot','id':ciot['id'],'data':{'latitude_origem':100}});self.assertEqual(status,400)

    def test_27_empty_and_whitespace_records_rejected(self):
        for module in ['programacao','pessoas','motoristas','veiculos','cidades','captacao','rotas','cte','mdfe','ciot','vale_pedagio']:
            status,before=self.request('records?module='+module)
            for payload in [{},{'nome':'   ','placa':'   ','lh_trip':'   ','status':'Ativo'}]:
                status,result=self.request('records',{'module':module,'data':payload})
                self.assertEqual(status,400,(module,result));self.assertIn('obrigatórios',result['error'])
            status,after=self.request('records?module='+module);self.assertEqual(len(before),len(after))

    def test_28_vehicle_slot_validation_and_reference_types(self):
        p=self.trip();trailer=self.save('veiculos',{'placa':'R'+server.secrets.token_hex(3),'tipo':'Carreta'})
        truck=self.save('veiculos',{'placa':'T'+server.secrets.token_hex(3),'tipo':'Truck'})
        for key,vehicle in [('tracao',trailer),('carreta',truck),('carreta2',truck)]:
            status,result=self.request('records',{'module':'programacao','id':p['id'],'data':{key:vehicle['id']}})
            self.assertEqual(status,400,result)
        p=self.save('programacao',{'tracao':truck['id'],'carreta':trailer['id']},p['id']);self.assertEqual(p['tracao'],truck['id'])
        status,data=self.request('bootstrap');self.assertEqual(next(v for v in data['refs']['veiculos'] if v['id']==trailer['id'])['tipo'],'Carreta')

    def test_29_initial_program_requires_route_but_driver_can_wait(self):
        p=self.trip();data={k:v for k,v in p.items() if k not in ['id','version','created','updated','motorista','tracao','carreta','carreta2','oc_id']};data['status']='Captada'
        for key in ['cliente','origem','destino','lh_trip','carregamento','eta_destino']:
            invalid=dict(data);invalid[key]='';status,result=self.request('records',{'module':'programacao','data':invalid});self.assertEqual(status,400,result)
        fresh=self.save('programacao',data);self.assertFalse(fresh.get('motorista'));self.assertEqual(fresh['status'],'Captada')

if __name__=='__main__':unittest.main(verbosity=2)

