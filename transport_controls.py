"""SLA operacional: cálculos sem integrações externas ou efeitos financeiros."""
from datetime import datetime,timezone,timedelta
TZ=timezone(timedelta(hours=-3))
PLANNED=['sla_coleta_inicio','sla_coleta_fim','sla_destino_inicio','sla_destino_fim','sla_cpt','sla_tolerancia_early','sla_tolerancia_atraso','sla_alerta_cpt']
REPORTED=['sla_previsao_coleta','sla_previsao_destino','sla_previsao_saida','sla_chegada_coleta','sla_fim_carregamento','sla_inicio_descarga','sla_motivo','sla_responsavel','sla_observacao']
def parse(value):
    if not value:return None
    result=datetime.fromisoformat(str(value).replace('Z','+00:00'))
    return result.replace(tzinfo=TZ) if result.tzinfo is None else result.astimezone(TZ)
def validate_sla(p,o=None):
    for field in ['sla_tolerancia_early','sla_tolerancia_atraso','sla_alerta_cpt']:
        value=p.get(field)
        if value not in [None,'']:
            n=float(value)
            if not n.is_integer() or not 0<=n<=1440:raise ValueError('Tolerância SLA deve ser um número inteiro entre 0 e 1440 minutos.')
    for prefix in ['coleta','destino']:
        start=parse(p.get('sla_'+prefix+'_inicio'));end=parse(p.get('sla_'+prefix+'_fim'))
        if start and not end:raise ValueError('Informe o fim da janela de '+prefix+'.')
        if start and end and end<start:raise ValueError('Fim da janela de '+prefix+' anterior ao início.')
    if o:
        sequence=['sla_chegada_coleta','carregamento_real','sla_fim_carregamento','saida_real','chegada_real','sla_inicio_descarga','descarga_real']
        previous=None
        for field in sequence:
            value=parse(o.get(field))
            if value and previous and value<previous:raise ValueError('Revise a sequência dos horários reais da viagem: '+field+'.')
            if value:previous=value
        if o.get('sla_responsavel')=='Agregado' and not str(o.get('sla_observacao','')).strip():raise ValueError('Justifique a atribuição do atraso ao agregado.')
def stage(label,start,end,forecast,actual,early,late,current,closed=False):
    lower=parse(start);upper=parse(end);pred=parse(forecast);real=parse(actual)
    def classify(value):
        if not value:return 'Sem informação',0
        if lower and value<lower-timedelta(minutes=early):return 'Early',round((lower-value).total_seconds()/60,1)
        if upper and value>upper+timedelta(minutes=late):return 'Atraso',round((value-upper).total_seconds()/60,1)
        if lower or upper:return 'No prazo',0
        return 'Sem janela',0
    real_state,real_delta=classify(real);pred_state,pred_delta=classify(pred)
    overdue=bool(not real and upper and current>upper+timedelta(minutes=late) and not closed)
    if real:status=real_state+' real' if real_state in ['Early','Atraso'] else real_state
    elif closed:status='Sem confirmação' if upper else 'Sem janela'
    elif overdue:status='Prazo vencido sem confirmação'
    else:status=pred_state+' previsto' if pred_state in ['Early','Atraso'] else pred_state
    minutes=real_delta if real else round((current-upper).total_seconds()/60,1) if overdue else pred_delta
    return dict(etapa=label,status=status,minutos=minutes,inicio=start or '',limite=end or '',previsao=forecast or '',real=actual or '',early_previsto=pred_state=='Early' and not real and not closed,atraso_previsto=pred_state=='Atraso' and not real and not closed,early_real=real_state=='Early',atraso_real=real_state=='Atraso',prazo_vencido=overdue,no_prazo_real=real_state=='No prazo',avaliavel=bool(real and upper))
def calculate_sla(p,o=None,current=None):
    o=o or {};current=current or datetime.now(TZ);current=current.replace(tzinfo=TZ) if current.tzinfo is None else current
    early=int(p.get('sla_tolerancia_early') or 0);late=int(p.get('sla_tolerancia_atraso') or 0)
    closed=p.get('status') in ['Finalizada','Cancelada'] or o.get('status') in ['Finalizada','Cancelada']
    stages=[stage('Coleta / carregamento',p.get('sla_coleta_inicio'),p.get('sla_coleta_fim') or p.get('carregamento'),o.get('sla_previsao_coleta'),o.get('sla_chegada_coleta') or o.get('carregamento_real'),early,late,current,closed),stage('Chegada no destino',p.get('sla_destino_inicio'),p.get('sla_destino_fim') or p.get('eta_destino'),o.get('sla_previsao_destino'),o.get('chegada_real'),early,late,current,closed)]
    if p.get('sla_cpt'):stages.append(stage('Saída / CPT',None,p['sla_cpt'],o.get('sla_previsao_saida'),o.get('saida_real'),0,late,current,closed))
    for item in stages:item['risco_cpt']=False
    if p.get('sla_cpt'):
        remaining=(parse(p['sla_cpt'])-current).total_seconds()/60;threshold=int(p.get('sla_alerta_cpt') if p.get('sla_alerta_cpt') not in [None,''] else 30)
        last=stages[-1];last['risco_cpt']=bool(not closed and not o.get('saida_real') and 0<=remaining<=threshold)
        if last['risco_cpt'] and not last['atraso_previsto']:last['status']='CPT próximo: confirmar saída'
    def duration(a,b):
        start=parse(o.get(a));end=parse(o.get(b));return round((end-start).total_seconds()/60,1) if start and end else None
    return {'programacao':p.get('id'),'oc':o.get('id'),'lh_trip':p.get('lh_trip',''),'cliente':p.get('cliente'),'origem':p.get('origem'),'destino':p.get('destino'),'motorista':p.get('motorista'),'status_viagem':o.get('status') or p.get('status'),'cancelada':p.get('status')=='Cancelada' or o.get('status')=='Cancelada','etapas':stages,'reportado_em':o.get('sla_reportado_em',''),'motivo':o.get('sla_motivo',''),'responsavel':o.get('sla_responsavel') or 'A apurar','observacao':o.get('sla_observacao',''),'duracoes':{'espera_coleta':duration('sla_chegada_coleta','carregamento_real'),'carregamento':duration('carregamento_real','sla_fim_carregamento'),'espera_destino':duration('chegada_real','sla_inicio_descarga'),'descarga':duration('sla_inicio_descarga','descarga_real')}}
def punctuality(sla):
    if sla.get('cancelada'):return None
    stages=[s for s in sla['etapas'] if s['avaliavel']]
    if not stages:return None
    if any(s['atraso_real'] for s in stages):
        if sla['responsavel']!='Agregado':return None
        delay=max(s['minutos'] for s in stages if s['atraso_real'])
        return 4 if delay<=30 else 3 if delay<=60 else 2 if delay<=120 else 1
    if any(s['early_real'] for s in stages):return None
    return 5
