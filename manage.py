"""Manutenção local. Senhas são recebidas por prompt, nunca pela linha de comando."""
import argparse,sqlite3,getpass,json
from pathlib import Path
import server
p=argparse.ArgumentParser();p.add_argument('action',choices=['backup','reset-admin']);p.add_argument('--output');p.add_argument('--email',default='admin@dg.local');args=p.parse_args()
if args.action=='backup':
    if not server.DB.exists():raise SystemExit('Banco ainda não existe. Inicie o sistema primeiro.')
    target=Path(args.output or 'backups/dg-'+server.now().replace(':','-')+'.sqlite3')
    if target.resolve()==server.DB.resolve() or target.exists():raise SystemExit('Escolha um arquivo novo, diferente do banco atual.')
    target.parent.mkdir(parents=True,exist_ok=True)
    with server.connect() as source,sqlite3.connect(target) as dest:source.backup(dest)
    print('Backup criado:',target)
else:
    if not server.DB.exists():raise SystemExit('Banco ainda não existe.')
    secret=getpass.getpass('Nova senha (mínimo 10 caracteres): ')
    if len(secret)<10:raise SystemExit('Senha muito curta.')
    if secret!=getpass.getpass('Confirme: '):raise SystemExit('Senhas diferentes.')
    with server.connect() as c:
        rows=[r for r in c.execute('SELECT * FROM users') if json.loads(r['data']).get('email')==args.email and 'Administrador' in json.loads(r['data']).get('perfis',[])]
        if len(rows)!=1:raise SystemExit('Administrador não encontrado.')
        c.execute('UPDATE users SET password=? WHERE id=?',(server.password(secret),rows[0]['id']))
    print('Senha redefinida. Reinicie o servidor para invalidar as sessões antigas.')
