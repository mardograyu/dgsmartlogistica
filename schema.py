"""Campos e opções do sistema. O mesmo esquema alimenta servidor e formulários."""
def fields(spec):
    result=[]
    for row in spec.split('\n'):
        if not row.strip(): continue
        parts=row.strip().split('|')
        key,label=parts[:2]; kind=parts[2] if len(parts)>2 else 'text'
        f={'key':key,'label':label,'type':kind}
        if len(parts)>3: f['options']=parts[3].split(';')
        result.append(f)
    return result

SCHEMA={}
def module(key,title,spec): SCHEMA[key]={'title':title,'fields':fields(spec)}
module('pessoas','Pessoas','''tipo|Tipo de pessoa|select|Jurídica;Física
nome|Nome / Razão social
fantasia|Apelido / Nome fantasia
documento|CPF / CNPJ
inscricao|RG / Inscrição estadual
data|Nascimento / Abertura|date
status|Status|select|Ativo;Inativo;Bloqueado
categorias|Categorias|checks|Cliente;Fornecedor;Proprietário;Agenciador
rntrc|RNTRC
tipo_proprietario|Tipo de proprietário|select|;TAC;ETC;CTC
inss|INSS
cep|CEP
logradouro|Logradouro
numero|Número
bairro|Bairro
cidade|Cidade|ref|cidades
uf|UF
pais|País
telefone|Telefone
celular|Celular
email|E-mail|email
contatos|Contatos adicionais (nome, telefone, e-mail)|rows
seguradora|Seguradora
seguradora_cnpj|CNPJ da seguradora
apolice_rctrc|Apólice RCTR-C
apolice_rcdc|Apólice RC-DC
observacoes|Observações|textarea''')
module('motoristas','Motoristas','''nome|Nome
apelido|Apelido
cpf|CPF
rg|RG
rg_orgao|Órgão emissor
rg_uf|UF do RG
pis|PIS
estado_civil|Estado civil|select|;Solteiro;Casado;Divorciado;Viúvo;União estável
nascimento|Nascimento|date
naturalidade|Naturalidade
pai|Nome do pai
mae|Nome da mãe
telefone|Telefone
celular|Celular
email|E-mail|email
cep|CEP
logradouro|Logradouro
numero|Número
bairro|Bairro
cidade|Cidade|ref|cidades
uf|UF
pais|País
cnh|Número da CNH
cnh_categoria|Categoria da CNH|select|;A;B;C;D;E;AB;AC;AD;AE
cnh_validade|Validade da CNH|date
cnh_primeira|Primeira habilitação|date
status|Status|select|Ativo;Inativo;Bloqueado
motivo|Motivo do status
tracao|Veículo de tração|ref|veiculos
carreta|Carreta 1|ref|veiculos
carreta2|Carreta 2|ref|veiculos
captacao|Captação|ref|captacao
observacoes|Observações|textarea''')
module('veiculos','Veículos','''placa|Placa
tipo|Tipo|select|Cavalo;Truck;Toco;Carreta;Bitrem;Rodotrem;VUC;Utilitário;Outro
carroceria|Carroceria|select|Baú;Sider;Graneleiro;Prancha;Tanque;Frigorífico;Aberta;Outra
eixos|Eixos|number
status|Status|select|Ativo;Inativo;Bloqueado
motivo|Motivo do status
marca|Marca
modelo|Modelo
cor|Cor
ano_fabricacao|Ano fabricação|number
ano_modelo|Ano modelo|number
tara|Tara (kg)|number
capacidade|Capacidade (kg)|number
renavam|RENAVAM
chassi|Chassi
proprietario|Proprietário|ref|pessoas
rntrc|RNTRC
rastreador|Empresa de rastreamento|select|;OnixSat;Omnilink;Sascar;Outra
rastreador_outro|Outra empresa
dispositivo|Identificador do rastreador
cidade|Cidade|ref|cidades
uf|UF
latitude|Latitude|number
longitude|Longitude|number
posicao_em|Data da posição|datetime-local
observacoes|Observações|textarea''')
module('cidades','Cidades','''nome|Cidade
uf|UF
ibge|Código IBGE
pais|País
status|Status|select|Ativo;Inativo''')
module('captacao','Captação','''data|Data|date
status|Status|select|Novo;Em contato;Aprovado;Reprovado
ultimo_contato|Último contato|datetime-local
nome|Nome do motorista
telefone|Telefone
implemento|Implemento
regioes|Regiões de interesse
rotas|Rotas de interesse
responsavel|Captador responsável|ref|usuarios
meio|Meio de captação|select|Indicação;Fretebras;Entrou em contato;Outro
meio_outro|Outro meio
agenciador|Agenciador|ref|pessoas
motorista|Motorista cadastrado|ref|motoristas
observacoes|Observações internas|textarea''')
module('programacao','Programação','''lh_trip|LH TRIP
cliente|Cliente / Tomador|ref|pessoas
valor_cliente|Frete recebido do cliente|money
status|Status|select|Captada;Sem motorista;Pronta para OC;OC criada;Aberta;Embarque Autorizado;Em Carregamento;Em Viagem;Chegada no Cliente;Finalizada;Cancelada
carregamento|Data e hora do carregamento|datetime-local
eta_destino|ETA destino / Descarga|datetime-local
origem|Remetente / Origem|ref|pessoas
destino|Destinatário / Destino|ref|pessoas
motorista|Motorista|ref|motoristas
tracao|Tração|ref|veiculos
carreta|Carreta 1|ref|veiculos
carreta2|Carreta 2|ref|veiculos
frete_agregado|Frete fixo ofertado ao agregado|offer
pedagio|Pedágio repassado ao agregado|money
produto|Produto predominante
quantidade|Quantidade|number
peso|Peso (kg)|number
volume|Volume
captador|Captador da viagem|ref|usuarios
observacoes|Observações|textarea''')
module('oc','Ordens de carregamento','''programacao|Programação|ref|programacao
status|Status|select|Aberta;Embarque Autorizado;Em Carregamento;Em Viagem;Chegada no Cliente;Finalizada
autorizacao|Autorização de embarque|datetime-local
saida_real|Saída real|datetime-local
descarga_real|Descarga real|datetime-local
observacoes|Observações|textarea''')
module('cte','CT-e','''oc|Ordem de carregamento|ref|oc
emissao|Data de emissão|datetime-local
ambiente|Ambiente|select|Homologação;Produção
serie|Série
numero|Número
tipo|Tipo CT-e|select|Normal;Complementar;Substituição
servico|Tipo de serviço|select|Normal;Subcontratação;Redespacho;Redespacho intermediário;Vinculado a multimodal
chave_referenciada|Chave CT-e referenciado
cfop|CFOP
remetente|Remetente|ref|pessoas
destinatario|Destinatário|ref|pessoas
expedidor|Expedidor|ref|pessoas
recebedor|Recebedor|ref|pessoas
pagador|Pagador|ref|pessoas
tomador|Tomador|ref|pessoas
origem_cidade|Município origem|ref|cidades
destino_cidade|Município destino|ref|cidades
documentos|Documentos transportados (chave NF-e, número, série, valor)|rows
produto|Produto predominante
quantidade|Quantidade|number
peso|Peso (kg)|number
valor_carga|Valor da mercadoria|money
seguro_responsavel|Responsável pelo seguro
seguradora|Seguradora
seguradora_cnpj|CNPJ da seguradora
apolice|Apólice
averbacao|Averbação
valor_segurado|Valor segurado|money
aliquota_seguro|Alíquota seguro (%)|number
frete_agregado|Frete agregado|money
frete|Frete|money
outros|Outros componentes|money
seguro|Seguro|money
pedagio|Pedágio|money
valor_total|Valor total da prestação|money
icms_cst|CST ICMS
icms_base|Base ICMS|money
icms_reducao|Redução base (%)|number
icms_aliquota|Alíquota ICMS (%)|number
icms_valor|Valor ICMS|money
ibs_cbs_cst|CST IBS / CBS
classe_tributaria|cClassTrib
ibs_cbs_base|Base IBS / CBS|money
ibs_uf_aliquota|Alíquota IBS UF (%)|number
ibs_mun_aliquota|Alíquota IBS Município (%)|number
cbs_aliquota|Alíquota CBS (%)|number
motorista|Motorista|ref|motoristas
tracao|Tração|ref|veiculos
carreta|Carreta 1|ref|veiculos
carreta2|Carreta 2|ref|veiculos
observacoes_fiscais|Observações fiscais|textarea
observacoes|Observações internas|textarea''')
module('mdfe','MDF-e','''oc|Ordem de carregamento|ref|oc
numero|Número
serie|Série
ambiente|Ambiente|select|Homologação;Produção
emissao|Data de emissão|datetime-local
contratante|Contratante|ref|pessoas
motorista|Motorista|ref|motoristas
tracao|Tração|ref|veiculos
carreta|Carreta 1|ref|veiculos
carreta2|Carreta 2|ref|veiculos
origem_cep|CEP carregamento
origem_cidade|Município carregamento|ref|cidades
destino_cep|CEP descarga
destino_cidade|Município descarga|ref|cidades
uf_inicio|UF início
uf_fim|UF fim
rota|Rota MDF-e|ref|rotas
documentos|CT-e / NF-e vinculados (chave, município, valor carga, peso)|rows
tipo_carga|Tipo de carga
produto|Produto predominante
ncm|NCM
peso|Peso (kg)|number
valor_carga|Valor total da carga|money
seguro_responsavel|Responsável pelo seguro
seguradora|Seguradora
seguradora_cnpj|CNPJ seguradora
apolice|Apólice
averbacao|Averbação
pedagio_pagador|Responsável pelo vale-pedágio|ref|pessoas
pedagio_operadora|Operadora vale-pedágio
pedagio_documento|Documento vale-pedágio
pedagio_valor|Valor vale-pedágio|money
ciot|Número CIOT
ciot_responsavel|Responsável pelo CIOT
ciot_cnpj|CNPJ responsável CIOT
contrato|Número contrato
contrato_valor|Valor contrato|money
indicador_pagamento|Indicador de pagamento|select|À vista;A prazo
adiantamento|Adiantamento|money
banco|Banco
agencia|Agência
conta|Conta
pix|Chave PIX
parcelas|Parcelas (data, valor)|rows
encerramento|Data encerramento|datetime-local
cancelamento_motivo|Justificativa cancelamento|textarea
observacoes|Observações|textarea''')
module('vale_pedagio','Vale-pedágio','''oc|Ordem de carregamento|ref|oc
pagador|Pagador|ref|pessoas
beneficiario|Beneficiário|ref|pessoas
operadora|Operadora|select|Repom
documento|Documento
valor|Valor|money
rota|Rota
observacoes|Observações|textarea''')
module('ciot','CIOT','''oc|Ordem de carregamento|ref|oc
operadora|Operadora|select|Repom
responsavel|Responsável|ref|pessoas
cnpj|CNPJ responsável
numero|Número CIOT
contrato|Contrato
valor|Valor contrato|money
observacoes|Observações|textarea''')
module('rotas','Rotas MDF-e','''nome|Nome da rota
origem|Origem|ref|cidades
destino|Destino|ref|cidades
ufs|UFs do percurso em ordem (separadas por vírgula)
observacoes|Observações|textarea''')
module('ocorrencias','Ocorrências de veículos','''veiculo|Veículo|ref|veiculos
oc|Ordem de carregamento|ref|oc
data|Data e hora|datetime-local
tipo|Tipo de ocorrência
descricao|Descrição|textarea
status|Status|select|Aberta;Em tratamento;Resolvida''')
module('financeiro','Financeiro','''oc|Ordem de carregamento|ref|oc
tipo|Tipo|select|Recebimento cliente;Despesa;Bônus;Desconto
descricao|Descrição
valor|Valor|money
vencimento|Vencimento|date
pago_em|Pago / Recebido em|date
beneficiario|Beneficiário|ref|pessoas
observacoes|Observações|textarea''')
module('usuarios','Usuários','''nome|Nome
email|E-mail|email
senha|Nova senha (deixe vazio para manter)|password
perfis|Perfis|checks|Administrador;Operação;Cadastro;Captação;Torre de Controle;Financeiro
abas|Abas adicionais|checks|
ocultar|Abas bloqueadas|checks|
status|Status|select|Ativo;Inativo''')
COMMON=['dashboard','tracking','painel']
PROFILES={'Administrador':list(SCHEMA)+COMMON+['configuracoes','auditoria'],
 'Operação':[k for k in SCHEMA if k not in ['usuarios','financeiro','vale_pedagio']]+COMMON,
 'Cadastro':['pessoas','motoristas','veiculos','cidades']+COMMON,
 'Captação':['captacao','programacao']+COMMON,
 'Torre de Controle':['oc']+COMMON,'Financeiro':['financeiro','vale_pedagio','ciot']+COMMON}
for f in SCHEMA['usuarios']['fields']:
    if f['key'] in ['abas','ocultar']: f['options']=list(SCHEMA)+COMMON+['configuracoes','auditoria']
FINANCIAL_KEYS={f['key'] for m in SCHEMA.values() for f in m['fields'] if f['type']=='money'}|{'lucro','comissao','percentual_comissao','adiantamento_valor','saldo_valor'}
OC_REQUIRED=['lh_trip','cliente','carregamento','eta_destino','origem','destino','motorista','tracao','produto','quantidade','peso','volume','captador','valor_cliente','frete_agregado','pedagio']
# Campos adicionais confirmados nos formulários CT-e / MDF-e enviados.
SCHEMA['cte']['fields']+=fields('''pagador_frete|Pagador do frete|select|;Remetente;Destinatário;Recebedor;Outro
+tipo_frete|Tipo de frete|select|;Carga;Unitário
+seguro_efeito|Efeito do seguro
+aliquota_rctrc|Alíquota RCTR-C (%)|number
+aliquota_rcfdc|Alíquota RCFDC (%)|number
+apolice_2|Apólice 2
+tipo_base_icms|Tipo de base de cálculo ICMS|select|;Frete;Frete + Pedágio;Frete + Pedágio + Seguro;Frete + Pedágio + Outras Despesas;Frete + Pedágio + Seguro + Outras Despesas
+ibs_uf_valor|Valor IBS estadual|money
+ibs_mun_valor|Valor IBS municipal|money
+cbs_valor|Valor CBS|money'''.replace('\n+','\n'))
SCHEMA['mdfe']['fields']+=fields('''pedagio_responsavel|Responsável pelo pedágio|select|;Transportador;Contratante;Sem Pedágio
+pedagio_tipo|Tipo de vale-pedágio|select|;TAG;Leitura de placa
+pedagio_operadora_cnpj|CNPJ da operadora de vale-pedágio'''.replace('\n+','\n'))
for f in SCHEMA['cte']['fields']:
    if f['key']=='seguro_responsavel':f.update(type='select',options=['','Transportador','Remetente','Destinatário','Tomador Serviço','Sem Seguro'])
    if f['key']=='icms_cst':f.update(type='select',options=['','00 - Tributação Normal','40 - Isenção de ICMS','60 - ICMS ST','90 - ICMS Outros'])
for f in SCHEMA['mdfe']['fields']:
    if f['key']=='seguro_responsavel':f.update(type='select',options=['','Transportador','Contratante'])
    if f['key']=='ciot_responsavel':f.update(type='select',options=['','Transportador','Contratante'])
    if f['key']=='tipo_carga':f.update(type='select',options=['','01 - Granel sólido','02 - Granel líquido','03 - Frigorificada','04 - Conteinerizada','05 - Carga geral','06 - Neogranel','07 - Perigosa (granel sólido)','08 - Perigosa (granel líquido)','09 - Perigosa (carga frigorificada)','10 - Perigosa (conteinerizada)','11 - Perigosa (carga geral)','12 - Granel pressurizada'])
FINANCIAL_KEYS.update(f['key'] for m in SCHEMA.values() for f in m['fields'] if f['type']=='money')

for m in ['cte','mdfe','ciot','vale_pedagio']:
    SCHEMA[m]['fields'].append({'key':'situacao_emissao','label':'Situação da emissão','type':'readonly'})

SCHEMA['oc']['title']='OC'
# V3 — campos conferidos nos novos prints.
SCHEMA['programacao']['fields']+=fields('''telefone_motorista|Telefone|readonly
+tipo_veiculo|Tipo de veículo|select|;Cavalo;Truck;Toco;Carreta;Bitrem;Rodotrem;VUC;Utilitário;Outro
+carroceria|Carroceria|select|;Não aplicável;Baú;Sider;Graneleiro;Prancha;Tanque;Frigorífico;Aberta;Outra
+observacoes_associacao|Observações da associação|textarea'''.replace('\n+','\n'))
SCHEMA['oc']['fields']+=fields('''data_oc|Data da OC|date
+tomador|Tomador do serviço|ref|pessoas
+remetente|Remetente|ref|pessoas
+destinatario|Destinatário|ref|pessoas
+origem|Origem (Razão Social)|ref|pessoas
+destino|Destino (Razão Social)|ref|pessoas
+quantidade|Quantidade|number
+volume|Volume
+produto|Mercadoria / Produto
+ncm|NCM
+peso|Peso (kg)|number
+motorista|Motorista|ref|motoristas
+tracao|Cavalo / Truck / Van / Utilitário|ref|veiculos
+carreta|Carreta 1|ref|veiculos
+carreta2|Carreta 2|ref|veiculos
+beneficiario_tipo|Beneficiário do frete|select|Proprietário do Veículo;Motorista;Outra Pessoa
+beneficiario|Pessoa beneficiária|ref|pessoas
+beneficiario_rntrc|ANTT / RNTRC do beneficiário
+frete_agregado|Valor do frete a pagar|money
+adiantamento_calculado|Adiantamento (70%)|readonly
+pedagio|Pedágio|money
+inss_desconto|INSS|money
+sest_desconto|SEST|money
+senat_desconto|SENAT|money
+saldo_calculado|Saldo (30%)|readonly
+previsao_adiantamento|Previsão do pagamento de adiantamento|readonly
+previsao_saldo|Previsão do pagamento do saldo|readonly
+valor_cliente|Valor do frete a receber|money'''.replace('\n+','\n'))
for m in ['motoristas','veiculos']:
    SCHEMA[m]['fields'].append({'key':'drive_pasta','label':'Link da pasta Google Drive (opcional)','type':'text'})
for m in ['pessoas','motoristas','veiculos']:
    SCHEMA[m]['fields'].insert(0,{'key':'cadastro_id','label':{'pessoas':'ID da pessoa','motoristas':'ID do motorista','veiculos':'ID do veículo'}[m],'type':'readonly'})
for f in SCHEMA['veiculos']['fields']:
    if f['key']=='carroceria' and 'Não aplicável' not in f['options']:f['options'].insert(0,'Não aplicável')
FINANCIAL_KEYS.update(['adiantamento_calculado','saldo_calculado','previsao_adiantamento','previsao_saldo','inss_desconto','sest_desconto','senat_desconto'])
OC_PROGRAM_MAP={'tomador':'cliente','origem':'origem','destino':'destino','quantidade':'quantidade','volume':'volume','produto':'produto','peso':'peso','motorista':'motorista','tracao':'tracao','carreta':'carreta','carreta2':'carreta2','frete_agregado':'frete_agregado','pedagio':'pedagio','valor_cliente':'valor_cliente'}
PROGRAM_INITIAL=['lh_trip','cliente','valor_cliente','status','carregamento','eta_destino','origem','destino','observacoes']

FINANCIAL_KEYS.update(['beneficiario_tipo','beneficiario','beneficiario_rntrc'])

# V4 — informações necessárias aos filtros e listagens enviados.
SCHEMA['vale_pedagio']['fields']+=fields('''data|Data da operação|date
tracao|Veículo / Placa|ref|veiculos
meio_pagamento|Meio de pagamento|select|Repom
situacao_operacao|Situação da operação|readonly''')
SCHEMA['rotas']['fields']+=fields('status|Status|select|Ativo;Inativo')

SCHEMA['vale_pedagio']['fields'].append({'key':'lh_trip','label':'LH Trip da programação','type':'readonly'})

# V5 — fluxo de status e formulários das fontes fornecidas.
SCHEMA['oc']['fields']+=fields("""abertura_em|Abertura da OC|datetime-local
carregamento_real|Início do carregamento|datetime-local
chegada_real|Chegada no cliente|datetime-local
cancelamento_em|Data do cancelamento|datetime-local
cancelamento_motivo|Motivo do cancelamento|textarea""")
# Cancelamento continua pela Programação, com motivo e sincronização.
SCHEMA['programacao']['fields'].append({'key':'cancelamento_motivo','label':'Motivo do cancelamento','type':'readonly'})
SCHEMA['ciot']['fields']+=fields("""ambiente|Ambiente|select|Homologação;Produção
cte|CT-e vinculado|ref|cte
mdfe|MDF-e vinculado|ref|mdfe
motorista|Motorista|ref|motoristas
tracao|Tração|ref|veiculos
carreta|Carreta 1|ref|veiculos
carreta2|Carreta 2|ref|veiculos
carreta3|Carreta 3|ref|veiculos
carreta4|Carreta 4|ref|veiculos
inicio_viagem|Início da viagem|datetime-local
fim_viagem|Fim previsto da viagem|datetime-local
documento_viagem|Documento da viagem
distancia|Distância (km)|number
cep_origem|CEP de origem
cep_destino|CEP de destino
latitude_origem|Latitude de origem|number
longitude_origem|Longitude de origem|number
latitude_destino|Latitude de destino|number
longitude_destino|Longitude de destino|number
ncm|NCM
produto|Descrição da carga
peso_kg|Peso da carga (kg)|number
valor_carga|Valor da carga|money
embalagem|Embalagem
tipo_carga|Tipo da carga
retorno_vazio|Retorno vazio|select|Não;Sim
alto_desempenho|Alto desempenho|select|Não;Sim
documentos|Documentos da carga|rows
total_operacao|Total da operação|money
total_viagem|Total da viagem|money
total_adiantamento|Total do adiantamento|money
total_quitacao|Total de quitação|money
combustivel|Combustível|money
pedagio|Pedágio|money
seguro|Seguro|money
outros_creditos|Outros créditos|money
outros_debitos|Outros débitos|money
justificativa_valores|Justificativa dos valores|textarea
irrf|IRRF|money
sest|SEST|money
senat|SENAT|money
inss|INSS|money
iss|ISS|money
outros_tributos|Outros tributos|money
pagamentos|Parcelas de pagamento|rows
cancelamento_motivo|Motivo do cancelamento|textarea
peso_encerramento|Peso no encerramento (kg)|number""")
SCHEMA['vale_pedagio']['fields']+=fields("""carreta|Carreta|ref|veiculos
cpf_cnpj_subcontratado|CPF/CNPJ do subcontratado
placa_visual|Placa da tração|readonly
eixos_tracao_visual|Eixos da tração|readonly
eixos_carreta_visual|Eixos da carreta|readonly
numero_eixos|Total de eixos|number
ajustar_eixos|Ajustar eixos manualmente|select|Não;Sim
eixos_ajuste_motivo|Motivo do ajuste de eixos|textarea
inicio_vigencia|Início da vigência|datetime-local
fim_vigencia|Fim da vigência|datetime-local
rodagem|Rodagem|select|Simples;Dupla
eixo_suspenso|Eixo suspenso|select|Não;Sim
origem_uf|UF origem
origem_cidade|Cidade origem
origem_codigo_ibge|Código IBGE origem
origem_cep|CEP origem
destino_uf|UF destino
destino_cidade|Cidade destino
destino_codigo_ibge|Código IBGE destino
destino_cep|CEP destino
item_financeiro1|Item financeiro 1
item_financeiro2|Item financeiro 2
item_financeiro3|Item financeiro 3""")
FINANCIAL_KEYS.update(f['key'] for m in SCHEMA.values() for f in m['fields'] if f['type']=='money')
FINANCIAL_KEYS.add('pagamentos')

# Dados essenciais para impedir cadastros sem identificação e viagens sem rota.
REQUIRED_FIELDS = {
 'pessoas':['nome','documento'], 'motoristas':['nome','cpf'],
 'veiculos':['placa','tipo'], 'cidades':['nome','uf'],
 'captacao':['nome','telefone','responsavel'],
 'programacao':['lh_trip','cliente','origem','destino','carregamento','eta_destino'],
 'rotas':['nome','origem','destino'], 'ocorrencias':['veiculo','descricao'],
 'financeiro':['oc','descricao','valor','vencimento'], 'cte':['oc'], 'mdfe':['oc'], 'ciot':['oc'], 'vale_pedagio':['oc'],
}
for _module, _keys in REQUIRED_FIELDS.items():
 for _field in SCHEMA[_module]['fields']:
  _field['required'] = _field['key'] in _keys
