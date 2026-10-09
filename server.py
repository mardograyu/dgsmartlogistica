#!/usr/bin/env python3
"""DG Smart Logística — servidor local, SQLite e API sem dependências externas."""
import os,json,sqlite3,secrets,hashlib,hmac,time,re,html,csv,io,zipfile
from pathlib import Path
from datetime import datetime,timedelta,date,timezone
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from urllib.parse import urlparse,parse_qs
from schema import SCHEMA,PROFILES,COMMON,FINANCIAL_KEYS,OC_REQUIRED,OC_PROGRAM_MAP
ROOT=Path(__file__).resolve().parent
DB=Path(os.environ.get('DG_DATABASE',str(ROOT/'data'/'dg.sqlite3')))
TZ=timezone(timedelta(hours=-3)); SESSIONS={}; LIMITS={}
def now(): return datetime.now(TZ).isoformat(timespec='seconds')
def connect():
    DB.parent.mkdir(parents=True,exist_ok=True)
    c=sqlite3.connect(DB,timeout=15); c.row_factory=sqlite3.Row;c.execute('PRAGMA foreign_keys=ON');return c
def password(p,salt=None):
    salt=salt or secrets.token_hex(16)
    return salt+':'+hashlib.pbkdf2_hmac('sha256',p.encode(),salt.encode(),260000).hex()
def verify(p,encoded): return hmac.compare_digest(password(p,encoded.split(':')[0]),encoded)
def initialize():
    with connect() as c:
        c.executescript('''CREATE TABLE IF NOT EXISTS records(id INTEGER PRIMARY KEY AUTOINCREMENT,module TEXT NOT NULL,data TEXT NOT NULL,version INTEGER NOT NULL DEFAULT 1,created TEXT NOT NULL,updated TEXT NOT NULL);
        CREATE INDEX IF NOT EXISTS records_module ON records(module);
        CREATE UNIQUE INDEX IF NOT EXISTS one_oc_per_program ON records(json_extract(data,'$.programacao')) WHERE module='oc';
        CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT,data TEXT NOT NULL,password TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY AUTOINCREMENT,at TEXT,user_id INTEGER,action TEXT,module TEXT,record_id INTEGER,details TEXT);
        CREATE TABLE IF NOT EXISTS payments(id INTEGER PRIMARY KEY AUTOINCREMENT,oc_id INTEGER NOT NULL,kind TEXT NOT NULL,amount INTEGER NOT NULL,due TEXT,beneficiary TEXT,signature TEXT,status TEXT NOT NULL DEFAULT 'Pendente',approved_by INTEGER,approved_at TEXT,provider_ref TEXT,UNIQUE(oc_id,kind));
        CREATE TABLE IF NOT EXISTS jobs(id INTEGER PRIMARY KEY AUTOINCREMENT,provider TEXT,module TEXT,record_id INTEGER,status TEXT,payload TEXT,created TEXT);
        CREATE TABLE IF NOT EXISTS config(key TEXT PRIMARY KEY,value TEXT);''')
        if not c.execute('SELECT 1 FROM users').fetchone():
            secret=os.environ.get('DG_ADMIN_PASSWORD') or secrets.token_urlsafe(14)
            c.execute('INSERT INTO users(data,password) VALUES (?,?)',(json.dumps({'nome':'Administrador DG','email':'admin@dg.local','perfis':['Administrador'],'abas':[],'ocultar':[],'status':'Ativo'}),password(secret)))
            print('\nPRIMEIRO ACESSO — e-mail: admin@dg.local | senha: '+secret+'\nGuarde a senha e altere-a em Usuários.\n',flush=True)
        defaults={'empresa':{'nome':'DG Smart Logística','cnpj':'','ie':'','rntrc':'','endereco':''},'comissao':{'percentual':None,'base':None},'integracoes':{'Repom':'Não configurada','OnixSat':'Não configurada','Omnilink':'Não configurada','Sascar':'Não configurada','Fiscal':'Não configurada'}}
        for k,v in defaults.items(): c.execute('INSERT OR IGNORE INTO config VALUES (?,?)',(k,json.dumps(v)))
def user_obj(row):
    d=json.loads(row['data']);d['id']=row['id'];return d
def allowed(u):
    tabs=set(COMMON)
    for role in u.get('perfis',[]): tabs.update(PROFILES.get(role,[]))
    tabs.update(u.get('abas',[]));tabs.difference_update(u.get('ocultar',[]));return tabs

def is_fin(u): return 'Financeiro' in u.get('perfis',[])
def sees_money(u): return is_fin(u) or 'Administrador' in u.get('perfis',[])
def visible(d,u,module=None):
    out=dict(d)
    if not sees_money(u):
        for k in FINANCIAL_KEYS:
            if k=='frete_agregado' and 'Captação' in u.get('perfis',[]) and module=='programacao': continue
            out.pop(k,None)
        if not ('Captação' in u.get('perfis',[]) and module=='programacao'):out.pop('frete_agregado',None)
    return out
def record(row):
    d=json.loads(row['data']);return dict(d,id=row['id'],version=row['version'],created=row['created'],updated=row['updated'])
def get_rec(c,id,module=None):
    r=c.execute('SELECT * FROM records WHERE id=?',(id,)).fetchone()
    if not r or module and r['module']!=module: raise ValueError('Registro não encontrado.')
    return record(r)
def audit(c,u,action,m,id,details=''):
    c.execute('INSERT INTO audit(at,user_id,action,module,record_id,details) VALUES (?,?,?,?,?,?)',(now(),u['id'],action,m,id,details))
def put(c,m,d,id=None,version=None):
    clean={k:v for k,v in d.items() if k not in ['id','version','created','updated']}
    if id:
        old=get_rec(c,id,m)
        if version is not None and int(version)!=old['version']: raise ValueError('Outro usuário alterou este registro. Atualize a página antes de salvar.')
        c.execute('UPDATE records SET data=?,version=version+1,updated=? WHERE id=?',(json.dumps(clean,ensure_ascii=False),now(),id))
    else:
        id=c.execute('INSERT INTO records(module,data,created,updated) VALUES (?,?,?,?)',(m,json.dumps(clean,ensure_ascii=False),now(),now())).lastrowid
    return get_rec(c,id,m)
def digits(v):return re.sub(r'\D','',str(v or ''))
def cents(v):
    from decimal import Decimal,ROUND_HALF_UP
    try:return int((Decimal(str(v or 0))*100).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
    except Exception:raise ValueError('Valor monetário inválido.')
def easter(y):
    a=y%19;b=y//100;c=y%100;d=b//4;e=b%4;f=(b+8)//25;g=(b-f+1)//3;h=(19*a+b-d-g+15)%30;i=c//4;k=c%4;l=(32+2*e+2*i-h-k)%7;m=(a+11*h+22*l)//451
    return date(y,(h+l-7*m+114)//31,(h+l-7*m+114)%31+1)
def business_days(start,n=10):
    d=start
    while n:
        d+=timedelta(days=1)
        holidays={date(d.year,m,day) for m,day in [(1,1),(4,21),(5,1),(9,7),(10,12),(11,2),(11,15),(11,20),(12,25)]}
        if d.weekday()<5 and d not in holidays:n-=1
    return d
def dt(s):
    v=datetime.fromisoformat(s)
    return v.replace(tzinfo=TZ) if v.tzinfo is None else v.astimezone(TZ)
def sync_payments(c,oc):
    p=get_rec(c,oc['programacao'],'programacao');total=cents(p.get('frete_agregado'));benef=('pessoa:'+str(oc['beneficiario'])) if oc.get('beneficiario') and oc.get('beneficiario_tipo')!='Motorista' else str(p.get('motorista',''))
    terms=[('Adiantamento',(total*70+50)//100,(dt(oc['saida_real'])+timedelta(hours=6)).isoformat() if oc.get('saida_real') else None),('Saldo',total-(total*70+50)//100,datetime.combine(business_days(dt(oc['descarga_real']).date()),datetime.min.time(),TZ).isoformat() if oc.get('descarga_real') else None)]
    for kind,amount,due in terms:
        signature=hashlib.sha256(json.dumps([amount,due,benef]).encode()).hexdigest()
        old=c.execute('SELECT * FROM payments WHERE oc_id=? AND kind=?',(oc['id'],kind)).fetchone()
        if old and old['signature']!=signature:
            if old['status'] in ['Enviado','Pago']: raise ValueError('Há pagamento enviado. Concilie o pagamento antes de alterar valor, beneficiário ou datas.')
            c.execute("UPDATE payments SET amount=?,due=?,beneficiary=?,signature=?,status='Pendente',approved_by=NULL,approved_at=NULL WHERE id=?",(amount,due,benef,signature,old['id']))
        elif not old:c.execute('INSERT INTO payments(oc_id,kind,amount,due,beneficiary,signature) VALUES (?,?,?,?,?,?)',(oc['id'],kind,amount,due,benef,signature))

def validate(c,m,d,id=None):
    missing=[f['label'] for f in SCHEMA[m]['fields'] if f.get('required') and (d.get(f['key']) is None or not str(d.get(f['key'],'')).strip() or (f['type']=='ref' and not d.get(f['key'])))]
    if missing:raise ValueError('Preencha os campos obrigatórios: '+', '.join(missing)+'.')
    for key in ['tracao','carreta','carreta2','carreta3','carreta4']:
        if d.get(key):
            vehicle=get_rec(c,d[key],'veiculos')
            tipo=vehicle.get('tipo','')
            valid=tipo in (['Cavalo','Truck','Toco','VUC','Utilitário'] if key=='tracao' else ['Carreta','Bitrem','Rodotrem'])
            if not valid:raise ValueError(('Tração exige cavalo ou caminhão.' if key=='tracao' else 'Selecione apenas carretas nos campos de carreta.')+' Revise o tipo do veículo '+vehicle.get('placa','')+'.')

    if m in ['pessoas','motoristas','veiculos','cidades']:
        key={'pessoas':'nome','motoristas':'nome','veiculos':'placa','cidades':'nome'}[m]
        if not str(d.get(key,'')).strip():raise ValueError('Preencha '+key+'.')
    keys={'pessoas':'documento','motoristas':'cpf','veiculos':'placa'}
    if m in keys and d.get(keys[m]):
        key=keys[m];v=digits(d[key]) if key!='placa' else re.sub(r'[^A-Z0-9]','',str(d[key]).upper());d[key]=v
        for row in c.execute('SELECT * FROM records WHERE module=?',(m,)):
            r=record(row)
            if r['id']!=id and r.get(key)==v:raise ValueError(f'{key.upper()} já cadastrado no registro #{r["id"]}.')
    if m=='vale_pedagio' and d.get('meio_pagamento') not in [None,'','Repom']:raise ValueError('Meio de pagamento deve ser Repom.')
    if m in ['motoristas','veiculos'] and d.get('status') in ['Inativo','Bloqueado'] and not d.get('motivo'):raise ValueError('Informe o motivo do status.')
    for f in SCHEMA[m]['fields']:
        v=d.get(f['key'])
        if f['type']=='select' and v not in [None,''] and v not in f['options']:raise ValueError('Opção inválida em '+f['label'])
        if f['type']=='ref' and v:
            try:d[f['key']]=int(v)
            except (ValueError,TypeError):raise ValueError('Use o ID do registro em '+f['label'])
            v=d[f['key']]
            if f['options'][0]=='usuarios':
                if not c.execute('SELECT 1 FROM users WHERE id=?',(v,)).fetchone():raise ValueError('Usuário vinculado não existe.')
            else:get_rec(c,v,f['options'][0])
        if f['type'] in ['money','offer'] and v not in [None,''] and cents(v)<0:raise ValueError('Valor não pode ser negativo.')
        if f['type']=='datetime-local' and v:dt(v)
    if m=='programacao' and d.get('status')=='Pronta para OC':
        if not d.get('motorista') or not d.get('tracao') or cents(d.get('frete_agregado'))<=0:
            raise ValueError('Pronta para OC exige motorista, tração e frete do agregado maior que zero.')
    if m=='vale_pedagio':
        if d.get('ajustar_eixos')=='Sim' and not str(d.get('eixos_ajuste_motivo','')).strip():raise ValueError('Informe o motivo do ajuste de eixos.')
        if d.get('inicio_vigencia') and d.get('fim_vigencia') and dt(d['fim_vigencia'])<dt(d['inicio_vigencia']):raise ValueError('A vigência final deve ser posterior à inicial.')
        for key in ['tracao','carreta']:
            if d.get(key) and get_rec(c,d[key],'veiculos').get('status')!='Ativo':raise ValueError('Selecione veículos ativos para o Vale-pedágio.')
    if m=='ciot':
        if d.get('inicio_viagem') and d.get('fim_viagem') and dt(d['fim_viagem'])<dt(d['inicio_viagem']):raise ValueError('Fim da viagem anterior ao início.')
        weight=d.get('peso_encerramento')
        if weight not in [None,'']:
            text=str(weight)
            if not re.fullmatch(r'\d+(?:\.\d{1,3})?',text) or float(weight)<=0:raise ValueError('Peso de encerramento deve ser maior que zero, com até três casas decimais.')
        if d.get('cancelamento_motivo') and len(str(d['cancelamento_motivo']).strip())<10:raise ValueError('Motivo do cancelamento do CIOT exige pelo menos 10 caracteres.')
        for key,limit in [('latitude_origem',90),('latitude_destino',90),('longitude_origem',180),('longitude_destino',180)]:
            if d.get(key) not in [None,''] and not -limit<=float(d[key])<=limit:raise ValueError('Coordenada inválida: '+key)
    if m=='oc':
        if d.get('status') in ['Em Carregamento','Em Viagem','Chegada no Cliente','Finalizada'] and not d.get('autorizacao'):raise ValueError('Informe a autorização de embarque.')
        if d.get('status') in ['Em Viagem','Chegada no Cliente','Finalizada'] and not d.get('saida_real'):raise ValueError('Informe a data e hora de saída real.')
        if d.get('status')=='Chegada no Cliente' and not d.get('chegada_real'):raise ValueError('Informe a data e hora da chegada no cliente.')
        if d.get('status')=='Finalizada' and not d.get('descarga_real'):raise ValueError('Informe a data e hora de descarga real.')
        if d.get('chegada_real') and d.get('saida_real') and dt(d['chegada_real'])<dt(d['saida_real']):raise ValueError('Chegada anterior à saída.')
        if d.get('descarga_real') and d.get('chegada_real') and dt(d['descarga_real'])<dt(d['chegada_real']):raise ValueError('Descarga anterior à chegada.')
        if d.get('carregamento_real') and d.get('saida_real') and dt(d['saida_real'])<dt(d['carregamento_real']):raise ValueError('Saída anterior ao início do carregamento.')
        if d.get('descarga_real') and d.get('saida_real') and dt(d['descarga_real'])<dt(d['saida_real']):raise ValueError('A descarga não pode ser anterior à saída.')

def warnings(c,p):
    alerts=[]
    if p.get('motorista'):
        d=get_rec(c,p['motorista'],'motoristas')
        if d.get('status') in ['Inativo','Bloqueado']:alerts.append('Motorista '+d['status'])
        if d.get('cnh_validade') and d['cnh_validade']<date.today().isoformat():alerts.append('CNH vencida')
        if not d.get('cnh'): alerts.append('Motorista sem CNH informada')
    for key in ['tracao','carreta','carreta2']:
        if p.get(key) and get_rec(c,p[key],'veiculos').get('status') in ['Inativo','Bloqueado']:alerts.append(key+' inativo ou bloqueado')
    for row in c.execute("SELECT * FROM records WHERE module='programacao'"):
        r=record(row)
        if r['id']!=p.get('id') and r.get('status') not in ['Cancelada','Finalizada'] and any(p.get(k) and p[k]==r.get(k) for k in ['motorista','tracao']):alerts.append('Motorista ou veículo também vinculado à programação #'+str(r['id']))
    return alerts

def enrich(c,m,d):
    d=dict(d)
    if m in ['pessoas','motoristas','veiculos']:d['cadastro_id']=str(d['id'])
    if m=='vale_pedagio':
        d.setdefault('data',str(d.get('created') or now())[:10]);d.setdefault('meio_pagamento','Repom');d['situacao_operacao']=d.get('situacao_emissao') or 'Rascunho'
        if d.get('oc'):
            oc=get_rec(c,d['oc'],'oc');p=get_rec(c,oc['programacao'],'programacao');d['lh_trip']=p.get('lh_trip','')
            if not d.get('tracao'):d['tracao']=p.get('tracao','')
    if m=='vale_pedagio':
        traction=get_rec(c,d['tracao'],'veiculos') if d.get('tracao') else {}
        trailer=get_rec(c,d['carreta'],'veiculos') if d.get('carreta') else {}
        d['placa_visual']=traction.get('placa','');d['eixos_tracao_visual']=traction.get('eixos',0);d['eixos_carreta_visual']=trailer.get('eixos',0)
        if d.get('ajustar_eixos')!='Sim':d['numero_eixos']=int(traction.get('eixos') or 0)+int(trailer.get('eixos') or 0)
    if m=='rotas':d.setdefault('status','Ativo')
    if m=='programacao' and d.get('motorista'):
        driver=get_rec(c,d['motorista'],'motoristas');d['telefone_motorista']=driver.get('celular') or driver.get('telefone','')
    if m=='oc' and d.get('programacao'):
        p=get_rec(c,d['programacao'],'programacao')
        for k,pk in OC_PROGRAM_MAP.items():d[k]=p.get(pk,'')
        d.setdefault('remetente',p.get('origem',''));d.setdefault('destinatario',p.get('destino',''))
        d.setdefault('data_oc',d.get('created','')[:10]);d.setdefault('beneficiario_tipo','Proprietário do Veículo')
        if not d.get('beneficiario') and p.get('tracao'):
            owner=get_rec(c,p['tracao'],'veiculos').get('proprietario')
            if owner:d['beneficiario']=owner
        if d.get('beneficiario'):
            d.setdefault('beneficiario_rntrc',get_rec(c,d['beneficiario'],'pessoas').get('rntrc',''))
        total=cents(p.get('frete_agregado'));advance=(total*70+50)//100
        d['adiantamento_calculado']=f'R$ {advance/100:.2f}';d['saldo_calculado']=f'R$ {(total-advance)/100:.2f}'
        for r in c.execute('SELECT * FROM payments WHERE oc_id=?',(d['id'],)):
            d['previsao_adiantamento' if r['kind']=='Adiantamento' else 'previsao_saldo']=r['due'] or 'Aguardando saída / descarga real'
    return d

class API(BaseHTTPRequestHandler):
    server_version='DG/1.0'
    def log_message(self,*args):pass
    def send(self,data,status=200,kind='application/json; charset=utf-8'):
        raw=json.dumps(data,ensure_ascii=False).encode() if 'json' in kind else data if isinstance(data,bytes) else data.encode()
        self.send_response(status);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(raw)));self.send_header('X-Content-Type-Options','nosniff');self.send_header('X-Frame-Options','DENY');self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(raw)
    def body(self):
        size=int(self.headers.get('Content-Length','0'))
        if size>5_000_000:raise ValueError('Limite de 5 MB por importação.')
        return json.loads(self.rfile.read(size) or '{}')
    def auth(self,c):
        cookies=dict(item.strip().split('=',1) for item in self.headers.get('Cookie','').split(';') if '=' in item)
        session=SESSIONS.get(cookies.get('dg_session',''))
        if not session or session['expires']<time.time():raise PermissionError('Entre no sistema para continuar.')
        row=c.execute('SELECT * FROM users WHERE id=?',(session['id'],)).fetchone()
        if not row:raise PermissionError('Conta indisponível.')
        u=user_obj(row)
        if u.get('status')!='Ativo':raise PermissionError('Conta inativa.')
        if self.command=='POST' and self.headers.get('X-CSRF-Token')!=session['csrf']:raise PermissionError('Sessão inválida. Entre novamente.')
        return u,session
    def permission(self,u,m):
        if m not in allowed(u):raise PermissionError('Você não tem acesso a esta aba.')
    def do_GET(self):
        path=urlparse(self.path).path
        if not path.startswith('/api/'):
            p=(ROOT/'static'/('index.html' if path=='/' else path.lstrip('/'))).resolve()
            if not p.is_relative_to(ROOT/'static') or not p.is_file():return self.send('Não encontrado',404,'text/plain')
            kind={'.html':'text/html','.js':'text/javascript','.css':'text/css','.svg':'image/svg+xml','.json':'application/json','.png':'image/png'}.get(p.suffix,'application/octet-stream')
            return self.send(p.read_bytes(),kind=kind)
        self.handle_api(path)
    def do_POST(self):self.handle_api(urlparse(self.path).path)
    def handle_api(self,path):
        try:
            with connect() as c:
                b=self.body() if self.command=='POST' else {};q=parse_qs(urlparse(self.path).query)
                if path=='/api/login' and self.command=='POST':
                    address=self.client_address[0];lim=LIMITS.setdefault(address,[]);lim[:]=[t for t in lim if t>time.time()-300]
                    if len(lim)>=10:return self.send({'error':'Muitas tentativas. Aguarde 5 minutos.'},429)
                    row=next((r for r in c.execute('SELECT * FROM users') if json.loads(r['data']).get('email','').lower()==b.get('email','').lower()),None)
                    if not row or not verify(b.get('senha',''),row['password']) or json.loads(row['data']).get('status')!='Ativo':lim.append(time.time());return self.send({'error':'E-mail ou senha inválidos.'},401)
                    token=secrets.token_urlsafe(32);csrf=secrets.token_urlsafe(24);SESSIONS[token]={'id':row['id'],'csrf':csrf,'expires':time.time()+28800};lim.clear()
                    raw=json.dumps({'ok':True}).encode();self.send_response(200);self.send_header('Set-Cookie','dg_session='+token+'; HttpOnly; SameSite=Strict; Path=/; Max-Age=28800'+('; Secure' if os.environ.get('DG_SECURE_COOKIE')=='1' else ''));self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw);return
                u,s=self.auth(c)
                if path=='/api/bootstrap':
                    schema=json.loads(json.dumps(SCHEMA))
                    for m,sc in schema.items():
                        sc['fields']=[f for f in sc['fields'] if sees_money(u) or (f['key'] not in FINANCIAL_KEYS and f['type']!='money') or (m=='programacao' and f['key']=='frete_agregado' and 'Captação' in u.get('perfis',[]))]
                        if not sees_money(u) and not ('Captação' in u.get('perfis',[]) and m=='programacao'):sc['fields']=[f for f in sc['fields'] if f['type']!='offer']
                    refs={}
                    for m in SCHEMA:
                        if m=='usuarios':refs[m]=[{'id':r['id'],'nome':json.loads(r['data']).get('nome')} for r in c.execute('SELECT * FROM users')]
                        else:refs[m]=[{'id':r['id'],'nome':json.loads(r['data']).get('nome') or json.loads(r['data']).get('placa') or json.loads(r['data']).get('lh_trip') or '#'+str(r['id']), 'cpf':json.loads(r['data']).get('cpf','') if m=='motoristas' else '', 'documento':json.loads(r['data']).get('documento','') if m=='pessoas' else '', 'placa':json.loads(r['data']).get('placa','') if m=='veiculos' else '', 'tipo':json.loads(r['data']).get('tipo','') if m=='veiculos' else '', 'uf':json.loads(r['data']).get('uf','') if m=='cidades' else ''} for r in c.execute('SELECT * FROM records WHERE module=?',(m,))]
                    return self.send({'user':u,'csrf':s['csrf'],'tabs':sorted(allowed(u)),'schema':schema,'refs':refs,'financial':sees_money(u),'approve':is_fin(u),'profiles':PROFILES})
                if path=='/api/logout':
                    for token,item in list(SESSIONS.items()):
                        if item is s:SESSIONS.pop(token,None)
                    return self.send({'ok':True})
                if path=='/api/records':
                    m=b.get('module') or q.get('module',[''])[0];self.permission(u,m)
                    if m not in SCHEMA:raise ValueError('Módulo desconhecido.')
                    if m=='usuarios':return self.users(c,u,b)
                    if self.command=='GET':return self.send([visible(enrich(c,m,record(r)),u,m) for r in c.execute('SELECT * FROM records WHERE module=? ORDER BY id DESC',(m,))])
                    if m=='financeiro' and not is_fin(u):raise PermissionError('Apenas Financeiro edita os lançamentos.')
                    id=b.get('id');old=get_rec(c,id,m) if id else {};d=enrich(c,m,old) if old else {}
                    accepted={f['key'] for f in SCHEMA[m]['fields'] if f['type']!='readonly'}
                    for k,v in b.get('data',{}).items():
                        if k in accepted:
                            if (k in ['inss_desconto','sest_desconto','senat_desconto'] or m=='ciot' and k in ['irrf','sest','senat','inss','iss','outros_tributos']) and not is_fin(u):raise PermissionError('Apenas Financeiro edita descontos.')
                            if m=='programacao' and k=='captador' and old and old.get(k) and v!=old.get(k) and 'Administrador' not in u.get('perfis',[]):raise PermissionError('Apenas Administrador altera o responsável.')
                            if k in FINANCIAL_KEYS and not sees_money(u) and not (k=='frete_agregado' and m=='programacao' and 'Captação' in u.get('perfis',[])):raise PermissionError('Campo financeiro restrito.')
                            if k=='frete_agregado' and not sees_money(u) and 'Captação' not in u.get('perfis',[]):raise PermissionError('Frete restrito.')
                            d[k]=v
                    if m=='oc' and old and d.get('programacao')!=old.get('programacao'):raise ValueError('Não é possível alterar a programação vinculada.')
                    if m=='oc' and old.get('status')=='Cancelada':raise ValueError('OC cancelada não pode ser alterada.')
                    if m=='oc' and d.get('status')=='Finalizada' and not old.get('chegada_real'):raise ValueError('Salve a chegada no cliente antes de finalizar a viagem.')
                    if m=='oc' and not old:raise ValueError('Gere a OC pela programação.')
                    if m=='programacao' and old.get('status')=='Cancelada':raise ValueError('Programação cancelada não pode ser reaberta.')
                    if m=='programacao' and d.get('status')=='Cancelada' and old.get('status')!='Cancelada':raise ValueError('Use Cancelar viagem e informe o motivo.')
                    if m=='programacao' and d.get('status')=='Cancelada' and old.get('oc_id'):raise ValueError('Use a ação Cancelar viagem.')
                    if m=='programacao' and old.get('oc_id') and d.get('status')!=old.get('status'):raise ValueError('Altere o status pelo olhinho da OC.')
                    if m=='oc':
                        dates=dict(old.get('status_datas',{}))
                        mapping={'Aberta':'abertura_em','Embarque Autorizado':'autorizacao','Em Carregamento':'carregamento_real','Em Viagem':'saida_real','Chegada no Cliente':'chegada_real','Finalizada':'descarga_real'}
                        key=mapping.get(d.get('status'))
                        if key and not d.get(key):
                            if d.get('status')=='Aberta':d[key]=old.get('created') or now()
                            elif d.get('status')=='Em Carregamento':raise ValueError('Informe a data e hora do início do carregamento.')
                        for stage,field in mapping.items():
                            if d.get(field):dates[stage]=d[field]
                        d['status_datas']=dates
                    if m=='vale_pedagio':d=enrich(c,m,d)
                    validate(c,m,d,id);r=put(c,m,d,id,b.get('version'));audit(c,u,'Editar' if id else 'Criar',m,r['id'])
                    if m=='oc':
                        p=get_rec(c,r['programacao'],'programacao')
                        if p.get('status')=='Cancelada':raise ValueError('Esta viagem foi cancelada.')
                        p['status']=r['status']
                        for key,pk in OC_PROGRAM_MAP.items():
                            if key in b.get('data',{}):p[pk]=d[key]
                        validate(c,'programacao',p,p['id']);put(c,'programacao',p,p['id']);sync_payments(c,r)
                    if m=='programacao' and r.get('oc_id'):sync_payments(c,get_rec(c,r['oc_id'],'oc'))
                    warn=warnings(c,r) if m=='programacao' else []
                    if m=='programacao' and old.get('oc_id') and any(d.get(k)!=old.get(k) for k in ['motorista','tracao','carreta','carreta2','origem','destino']):warn.append('Revise CT-e, MDF-e, CIOT e vale-pedágio já vinculados à viagem.')
                    return self.send({'record':visible(enrich(c,m,r),u,m),'warnings':warn})
                if path=='/api/generate-oc':
                    self.permission(u,'programacao');p=get_rec(c,b['id'],'programacao')
                    if p.get('oc_id'):return self.send({'id':p['oc_id'],'existing':True})
                    if p.get('status')!='Pronta para OC':raise ValueError('Preencha os dados e salve a programação como Pronta para OC antes de gerar.')
                    missing=[k for k in OC_REQUIRED if p.get(k) in [None,'',[]]]
                    if missing:raise ValueError('Preencha para gerar OC: '+', '.join(missing))
                    warn=warnings(c,p)
                    if warn and not b.get('accept_warnings'):return self.send({'warnings':warn,'needs_confirmation':True})
                    payload={'programacao':p['id'],'status':'Aberta','abertura_em':now(),'status_datas':{'Aberta':now()},'data_oc':datetime.now(TZ).date().isoformat(),'observacoes':p.get('observacoes',''),'beneficiario_tipo':'Proprietário do Veículo'}
                    if p.get('tracao'):payload['beneficiario']=get_rec(c,p['tracao'],'veiculos').get('proprietario','')
                    r=put(c,'oc',payload);p.update(oc_id=r['id'],status='OC criada');put(c,'programacao',p,p['id']);sync_payments(c,r);audit(c,u,'Gerar OC','oc',r['id']);return self.send({'id':r['id'],'warnings':warn})
                if path=='/api/cancel-trip':
                    self.permission(u,'programacao');p=get_rec(c,b['id'],'programacao')
                    if p.get('status') in ['Cancelada','Finalizada']:raise ValueError('Viagem já encerrada.')
                    reason=str(b.get('motivo','')).strip()
                    if not reason:raise ValueError('Informe o motivo do cancelamento.')
                    if p.get('oc_id'):
                        if c.execute("SELECT 1 FROM payments WHERE oc_id=? AND status IN ('Enviado','Pago')",(p['oc_id'],)).fetchone():raise ValueError('Concilie os pagamentos enviados antes de cancelar.')
                        oc=get_rec(c,p['oc_id'],'oc');oc.update(status='Cancelada',cancelamento_motivo=reason,cancelamento_em=now());oc.setdefault('status_datas',{})['Cancelada']=oc['cancelamento_em'];put(c,'oc',oc,oc['id']);c.execute("UPDATE payments SET status='Cancelado',approved_by=NULL,approved_at=NULL WHERE oc_id=?",(oc['id'],))
                    p.update(status='Cancelada',cancelamento_motivo=reason,cancelamento_em=now());put(c,'programacao',p,p['id']);audit(c,u,'Cancelar viagem','programacao',p['id'],reason);return self.send({'ok':True})
                if path=='/api/oc-source':
                    m=q.get('module',[''])[0]
                    if m not in ['ciot','vale_pedagio','cte','mdfe']:raise ValueError('Módulo inválido.')
                    self.permission(u,m)
                    oc=enrich(c,'oc',get_rec(c,int(q.get('id',['0'])[0]),'oc'));p=get_rec(c,oc['programacao'],'programacao')
                    locations={}
                    for side in ['origem','destino']:
                        person=get_rec(c,p[side],'pessoas') if p.get(side) else {}
                        city=get_rec(c,person['cidade'],'cidades') if person.get('cidade') else {}
                        locations[side]={'cep':person.get('cep',''),'uf':person.get('uf') or city.get('uf',''),'cidade':city.get('nome',''),'ibge':city.get('ibge','')}
                    traction=get_rec(c,p['tracao'],'veiculos') if p.get('tracao') else {};owner=get_rec(c,traction['proprietario'],'pessoas') if traction.get('proprietario') else {}
                    return self.send({'oc':visible(oc,u,m),'programacao':visible(p,u,m),'locais':locations,'documento_subcontratado':owner.get('documento','')})
                if path=='/api/vehicle-axles':
                    self.permission(u,'vale_pedagio')
                    def vehicle_info(key):
                        value=q.get(key,[''])[0]
                        if not value:return {}
                        v=get_rec(c,int(value),'veiculos')
                        return {k:v.get(k,'') for k in ['id','placa','eixos','status','tipo']}
                    return self.send({'tracao':vehicle_info('tracao'),'carreta':vehicle_info('carreta')})
                if path=='/api/operations':
                    m=q.get('view',['dashboard'])[0];self.permission(u,m)
                    programs=[visible(record(r),u,'programacao') for r in c.execute("SELECT * FROM records WHERE module='programacao'")]
                    ocs=[visible(record(r),u,'oc') for r in c.execute("SELECT * FROM records WHERE module='oc'")]
                    drivers=[visible(record(r),u,'motoristas') for r in c.execute("SELECT * FROM records WHERE module='motoristas'")]
                    vehicles=[visible(record(r),u,'veiculos') for r in c.execute("SELECT * FROM records WHERE module='veiculos'")]
                    return self.send({'programacao':programs,'oc':ocs,'motoristas':drivers,'veiculos':vehicles,'at':now()})
                if path=='/api/payments':
                    self.permission(u,'financeiro')
                    if not sees_money(u):raise PermissionError('Valores financeiros restritos.')
                    return self.send([dict(r,beneficiary_name=(get_rec(c,int(r['beneficiary'].split(':')[1]),'pessoas').get('nome') if r['beneficiary'].startswith('pessoa:') else get_rec(c,int(r['beneficiary']),'motoristas').get('nome') if r['beneficiary'] else '')) for r in c.execute('SELECT * FROM payments ORDER BY id DESC')])
                if path=='/api/payment-action':
                    if not is_fin(u):raise PermissionError('Aprovação e envio exclusivos do perfil Financeiro.')
                    self.permission(u,'financeiro');p=c.execute('SELECT * FROM payments WHERE id=?',(b['id'],)).fetchone()
                    if not p:raise ValueError('Pagamento inexistente.')
                    oc=get_rec(c,p['oc_id'],'oc')
                    if oc.get('status')=='Cancelada':raise ValueError('Viagem cancelada.')
                    if not p['due']:raise ValueError('Informe saída ou descarga real na OC.')
                    if p['kind']=='Saldo' and oc.get('status')!='Finalizada':raise ValueError('O saldo exige viagem finalizada após a descarga.')
                    if b['action']=='approve':
                        if p['status'] not in ['Pendente','Aprovado']:raise ValueError('Pagamento não pode ser aprovado neste status.')
                        c.execute("UPDATE payments SET status='Aprovado',approved_by=?,approved_at=? WHERE id=?",(u['id'],now(),p['id']));audit(c,u,'Aprovar parcela','financeiro',p['id']);return self.send({'ok':True})
                    if b['action']=='send':
                        if p['status']!='Aprovado':raise ValueError('Aprovação financeira necessária.')
                        if dt(p['due'])>datetime.now(TZ):raise ValueError('O vencimento ainda não chegou.')
                        return self.send({'error':'Repom não contratada/configurada. Nenhum dinheiro foi enviado.'},409)
                    raise ValueError('Ação desconhecida.')
                if path=='/api/document-action':
                    m=b['module'];self.permission(u,m)
                    if m not in ['cte','mdfe','ciot','vale_pedagio']:raise ValueError('Documento inválido.')
                    r=get_rec(c,b['id'],m)
                    if b.get('action') not in ['emit','cancel','close']:raise ValueError('Ação inválida.')
                    if b.get('action') in ['cancel','close']:return self.send({'error':'Ação depende de documento autorizado pelo provedor.'},409)
                    provider='Fiscal' if m in ['cte','mdfe'] else 'Repom'
                    c.execute('INSERT INTO jobs(provider,module,record_id,status,payload,created) VALUES (?,?,?,?,?,?)',(provider,m,r['id'],'Aguardando configuração',json.dumps(r),now()));r['situacao_emissao']='Aguardando configuração';put(c,m,r,r['id']);audit(c,u,'Solicitar emissão',m,r['id'])
                    return self.send({'ok':True,'message':'Solicitação registrada. Provedor não configurado; documento ainda não autorizado.'})
                if path=='/api/config':
                    self.permission(u,'configuracoes')
                    if self.command=='GET':return self.send({r['key']:json.loads(r['value']) for r in c.execute('SELECT * FROM config')})
                    for k,v in b.items():
                        if k in ['empresa','comissao']:c.execute('UPDATE config SET value=? WHERE key=?',(json.dumps(v),k))
                    audit(c,u,'Alterar configurações','configuracoes',0);return self.send({'ok':True})
                if path=='/api/audit':
                    self.permission(u,'auditoria');return self.send([dict(r) for r in c.execute('SELECT * FROM audit ORDER BY id DESC LIMIT 500')])
                if path=='/api/export':
                    m=q.get('module',[''])[0];self.permission(u,m)
                    if m not in SCHEMA or m=='usuarios':raise ValueError('Exportação não disponível.')
                    rows=[visible(record(r),u,m) for r in c.execute('SELECT * FROM records WHERE module=?',(m,))]
                    return self.send({'module':m,'records':rows})
                if path=='/api/import-document':
                    m=b.get('module');self.permission(u,m)
                    if m not in ['cte','mdfe']:raise ValueError('Importação disponível em CT-e e MDF-e.')
                    from imports import extract_document
                    return self.send(extract_document(b.get('filename',''),b.get('content','')))
                if path=='/api/import':
                    m=b['module'];self.permission(u,m)
                    if m not in ['pessoas','motoristas','veiculos','cidades']:raise ValueError('Importe apenas cadastros.')
                    rows=b.get('records',[])
                    if len(rows)>1000:raise ValueError('Máximo de 1.000 registros por lote.')
                    result=[]
                    for i,d in enumerate(rows):
                        c.execute('SAVEPOINT importrow')
                        try:
                            d={k:v for k,v in d.items() if k in {f['key'] for f in SCHEMA[m]['fields']}}
                            validate(c,m,d);r=put(c,m,d);audit(c,u,'Importar',m,r['id']);result.append({'row':i+1,'id':r['id'],'ok':True});c.execute('RELEASE importrow')
                        except (ValueError,KeyError) as e:c.execute('ROLLBACK TO importrow');c.execute('RELEASE importrow');result.append({'row':i+1,'error':str(e)})
                    return self.send(result)
                if path=='/api/print':
                    self.permission(u,'oc');oc=get_rec(c,int(q['id'][0]),'oc');p=get_rec(c,oc['programacao'],'programacao');p=visible(p,u,'programacao')
                    def label(m,id):
                        if not id:return ''
                        d=get_rec(c,id,m);return str(d.get('nome') or d.get('placa') or id)
                    empresa=json.loads(c.execute("SELECT value FROM config WHERE key='empresa'").fetchone()[0]);vals=[('Status',oc.get('status')),('LH TRIP',p.get('lh_trip')),('Cliente',label('pessoas',p.get('cliente'))),('Remetente',label('pessoas',p.get('origem'))),('Destinatário',label('pessoas',p.get('destino'))),('Carregamento',p.get('carregamento')),('ETA destino',p.get('eta_destino')),('Motorista',label('motoristas',p.get('motorista'))),('Tração',label('veiculos',p.get('tracao'))),('Carreta 1',label('veiculos',p.get('carreta'))),('Carreta 2',label('veiculos',p.get('carreta2'))),('Produto',p.get('produto')),('Quantidade',p.get('quantidade')),('Peso',p.get('peso')),('Volume',p.get('volume')),('Observações',p.get('observacoes'))]
                    for k,m in [('motorista','motoristas'),('tracao','veiculos'),('carreta','veiculos'),('carreta2','veiculos')]:
                        if p.get(k):
                            detail=get_rec(c,p[k],m)
                            for field in (['cpf','celular','cnh'] if m=='motoristas' else ['modelo','cidade','proprietario','renavam']):vals.append((k+' / '+field,detail.get(field)))
                    page='<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>OC '+str(oc['id'])+'</title><style>body{font:14px Arial;margin:40px;color:#222}h1{border-bottom:3px solid #b79742;padding-bottom:20px}table{border-collapse:collapse;width:100%}td{padding:9px;border:1px solid #ddd}footer{margin-top:65px;display:flex;justify-content:space-around}@media print{button{display:none}}</style><button onclick="print()">Imprimir / Salvar PDF</button><h1>'+html.escape(empresa['nome'])+'</h1><h2>ORDEM DE CARREGAMENTO #'+str(oc['id'])+'</h2><p>'+html.escape(now())+'</p><table>'+''.join('<tr><td>'+html.escape(k)+'</td><td>'+html.escape(str(v or ''))+'</td></tr>' for k,v in vals)+'</table><footer><span>____________________<br>Responsável</span><span>____________________<br>Motorista</span></footer></html>'
                    return self.send(page,kind='text/html; charset=utf-8')
                return self.send({'error':'Endpoint não encontrado.'},404)
        except PermissionError as e:self.send({'error':str(e)},403)
        except (ValueError,KeyError,TypeError,sqlite3.IntegrityError) as e:self.send({'error':str(e)},400)
        except Exception as e:
            print('Erro interno:',type(e).__name__,str(e),flush=True);self.send({'error':'Erro interno. Consulte o terminal do servidor.'},500)
    def users(self,c,u,b):
        if 'Administrador' not in u.get('perfis',[]):raise PermissionError('Gerenciamento exclusivo do Administrador.')
        if self.command=='GET':return self.send([user_obj(r) for r in c.execute('SELECT * FROM users')])
        id=b.get('id');d=b['data'];secret=d.pop('senha','');d={k:v for k,v in d.items() if k in ['nome','email','perfis','abas','ocultar','status']}
        if not d.get('nome') or not d.get('email'):raise ValueError('Informe nome e e-mail.')
        if not d.get('perfis'):raise ValueError('Selecione pelo menos um perfil.')
        valid_tabs=set(SCHEMA)|set(COMMON)|{'configuracoes','auditoria'}
        if any(tab not in valid_tabs for key in ['abas','ocultar'] for tab in d.get(key,[])):raise ValueError('Aba desconhecida.')
        if set(d.get('abas',[]))&set(d.get('ocultar',[])):raise ValueError('Uma aba não pode ser permitida e bloqueada ao mesmo tempo.')
        if any(role not in PROFILES for role in d.get('perfis',[])):raise ValueError('Perfil desconhecido.')
        if any(r['id']!=id and json.loads(r['data']).get('email','').lower()==d['email'].lower() for r in c.execute('SELECT * FROM users')):raise ValueError('E-mail já cadastrado.')
        if id==u['id'] and ('Administrador' not in d.get('perfis',[]) or d.get('status')!='Ativo'):raise ValueError('Não remova seu próprio acesso de administrador.')
        if secret and len(secret)<10:raise ValueError('Senha deve ter pelo menos 10 caracteres.')
        if id:
            row=c.execute('SELECT * FROM users WHERE id=?',(id,)).fetchone()
            if not row:raise ValueError('Usuário inexistente.')
            c.execute('UPDATE users SET data=?,password=? WHERE id=?',(json.dumps(d),password(secret) if secret else row['password'],id))
        else:
            if not secret:raise ValueError('Informe uma senha de pelo menos 10 caracteres.')
            id=c.execute('INSERT INTO users(data,password) VALUES (?,?)',(json.dumps(d),password(secret))).lastrowid
        audit(c,u,'Salvar usuário','usuarios',id)
        return self.send({'record':dict(d,id=id)})

if __name__=='__main__':
    initialize();host=os.environ.get('DG_HOST','127.0.0.1');port=int(os.environ.get('DG_PORT','8080'));print(f'DG Smart Logística disponível em http://{host}:{port}',flush=True)
    try:ThreadingHTTPServer((host,port),API).serve_forever()
    except KeyboardInterrupt:print('\nServidor encerrado.')
