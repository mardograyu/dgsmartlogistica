# DG Smart Logística

Sistema web local para uma transportadora, com servidor Python, banco SQLite e interface própria. Versão 4: visual aprovado com menu lateral escuro por grupos, logo original da DG, conteúdo branco/cinza e dourado restrito à marca. Os cadastros abrem em páginas amplas por seções, com busca de referências e datas/horas separadas. Login dividido em foto da carreta com a marca DG à esquerda e cartão de acesso à direita. Painel em tabela com relógio, seis indicadores e paginação; Tracking com lista lateral e mapa de todas as posições reais. Os campos foram organizados a partir dos cadastros, screenshots e formulários SSX enviados.

## Atualizar da versão anterior

Se já cadastrou dados, mantenha o banco. Pare o servidor antigo e faça um backup (`python manage.py backup`). Extraia o novo ZIP em uma pasta nova e copie a pasta `data` da instalação anterior para dentro da nova pasta `dg-smart-logistica`. Inicie a nova versão; os mesmos usuários, senhas e registros serão usados. Nunca substitua seu banco por um banco vazio. O ZIP não contém banco de dados nem credenciais reais.

## Começar no Windows

1. Extraia **toda** a pasta `dg-smart-logistica` do ZIP.
2. Tenha **Python 3.10 ou superior** instalado. Na instalação, marque “Add Python to PATH”. Download oficial: https://www.python.org/downloads/
3. Dê dois cliques em **INICIAR-WINDOWS.bat**.
4. O navegador abrirá em **http://127.0.0.1:8080**. Mantenha o terminal aberto.
5. No primeiro início, o terminal mostra o e-mail **admin@dg.local** e uma **senha aleatória**. Guarde essa senha. Ela só é mostrada na criação do banco.
6. Em **Gestão → Usuários**, altere sua senha e crie os demais usuários. A senha deve ter pelo menos 10 caracteres.

O administrador inicial **não aprova pagamentos**. Para isso, crie um usuário com perfil **Financeiro**, ou atribua esse perfil explicitamente a uma conta autorizada.

**Não abra `static/index.html` diretamente**: os dados e o login dependem do servidor. O arquivo `index.html` da raiz contém a orientação de início; ele não substitui o servidor.

O núcleo do sistema **não precisa de Node, npm ou Docker** e não exige instalação de pacotes Python. A fonte web e o mapa usam a internet; se a fonte não carregar, a interface usa Arial. O mapa depende de OpenStreetMap.

## Mac / Linux

```sh
cd dg-smart-logistica
python3 iniciar.py
```

Para usar outra porta: defina `DG_PORT`. Para não abrir o navegador automaticamente: defina `DG_NO_BROWSER=1`. Para escolher outro banco: defina `DG_DATABASE` com o caminho absoluto.

## O que funciona nesta entrega

- Login, senha com PBKDF2, sessões, proteção CSRF e limite de tentativas de login.
- Perfis múltiplos, abas adicionais e abas bloqueadas por usuário. Menus ocultos e bloqueio de acesso na API.
- Pessoas físicas/jurídicas, categorias múltiplas, contatos adicionais, motoristas, veículos, cidades e captação.
- Consulta e edição pelo olhinho em páginas por seções, preservando o ID. Avisos de CPF/CNPJ/placa duplicados; registros inativos ficam no histórico.
- Programação salva incompleta. Geração de OC exige os dados operacionais/financeiros listados em `schema.py`, exceto observações e campos condicionais como segunda carreta.
- Uma OC por programação, garantida também por índice único no banco.
- Status da OC atualiza a Programação. Saída e descarga reais são informadas manualmente. Recuo de status é permitido. Cancelamento parte da Programação; uma viagem cancelada não é reaberta.
- Avisos sobre motorista/veículo bloqueado, CNH vencida/ausente e motorista/veículo em outra viagem. É possível confirmar e continuar a geração da OC.
- Motorista e veículos podem ter viagens simultâneas. Cada programação mantém seu próprio status.
- Painel: motorista vinculado confirma a viagem; sem motorista depois do horário de carregamento gera no-show. Faixas de 6–4 horas e menos de 4 horas. Som repete a cada 5 minutos, com a página aberta e som ativado pelo usuário.
- Tracking lista OCs em carregamento, em viagem ou com chegada no cliente. Um veículo aparece uma vez, com suas viagens vinculadas. Sai da lista ao finalizar/cancelar todas essas viagens. Pode mostrar posição manual real salva no veículo.
- Parcelas de 70%/30% do frete agregado, em centavos. Adiantamento vence 6 horas após a saída real; saldo vence 10 dias úteis após a descarga real e exige viagem finalizada. Exclui sábado, domingo e os feriados nacionais fixos, inclusive 20/11. Não inclui feriados estaduais/municipais ou pontos facultativos.
- Aprovação individual de parcela exclusivamente pelo Financeiro, com usuário/data. Mudança de valor, beneficiário ou datas exige nova aprovação.
- Financeiro registra recebimentos, despesas, bônus e descontos, além de mostrar diferença de fretes e resultado parcial. Apenas Financeiro edita os lançamentos.
- Rascunhos de CT-e, MDF-e, CIOT e vale-pedágio. Preenchimento a partir da OC e importação com revisão.
- Ordem de carregamento para impressão e “Salvar como PDF” pelo navegador, com campos do modelo enviado. Ela **não é documento fiscal**.
- Exportação JSON; importação JSON/CSV de cadastros com resultado individual; importação XML em documentos; extração parcial de PDF/XLSX/CSV.
- Auditoria de ações, controle de versão para evitar sobrescrever edição concorrente e backup consistente do SQLite.

## O que ainda depende de definição/contratação

Esta entrega **não deve ser chamada de 100% pronta para produção fiscal/financeira**. As seguintes partes não podem ser concluídas sem dados externos:

| Parte | Estado real |
| --- | --- |
| Repom — pagamentos, CIOT e vale-pedágio | Sem contrato/documentação/credenciais. Nenhum pagamento é enviado. Solicitação de documento fica aguardando configuração. |
| CT-e / MDF-e autorizados | Falta escolher provedor, configurar certificado/emitente, homologar e implementar o contrato da API. O sistema guarda rascunhos; não inventa protocolo ou chave autorizada. |
| OnixSat / Omnilink / Sascar | Adaptadores ainda precisam dos contratos e APIs oficiais. Não há rastreamento automático conectado. |
| Comissão | Percentual e composição da base de lucro pendentes. O sistema não paga nem inventa comissão. |
| Despesas e valores finais | Lançamentos manuais disponíveis. Regras e valores específicos ainda precisam ser informados. |
| Contas a receber do cliente | Vencimento/recebimento manual. Prazos por cliente ainda não definidos. |
| Drive | Documentos ficam fora dos cadastros conforme solicitado. Não há autenticação ou upload automático no Google Drive. |
| Importação do banco SSX | Disponível por campos JSON/CSV; o mapeamento do arquivo real depende da exportação que ainda será enviada. |
| OCR | PDF digitalizado não é lido automaticamente. PDFs com texto têm extração parcial, nunca garantia de todos os campos. |
| Produção hospedada | Entrega local em ZIP. Não houve publicação, configuração de domínio, HTTPS ou operação em servidor público. |

Valores/tributos não recebem alíquotas fixas presumidas. Os formulários precisam ser revisados pelo responsável e pelo provedor fiscal antes de qualquer autorização. Modelo DACTE fiscal autorizado e DAMDFE devem vir do provedor contratado; esta versão não gera substitutos fiscais locais.

## Permissões

| Perfil | Acesso padrão |
| --- | --- |
| Administrador | Todas as abas e visualização, usuários/configurações; aprovação exige perfil Financeiro. |
| Operação | Abas operacionais e documentos; sem Vale-pedágio, gestão de usuários ou valores financeiros. |
| Cadastro | Pessoas, Motoristas, Veículos e Cidades. |
| Captação | Captação e Programação; vê/edita somente o frete fixo ofertado ao agregado na Programação, sem ver receita do cliente, pedágio financeiro, margem ou pagamentos. |
| Torre de Controle | OC. |
| Financeiro | Financeiro, Vale-pedágio e CIOT; aprova parcelas. |

Tracking, Painel e Dashboard são comuns por padrão. O administrador pode acrescentar/bloquear abas. Acesso a uma aba financeira sozinho não dá acesso aos valores nem aprovação: o perfil Financeiro é necessário para aprovar; Administrador pode visualizar valores.

## Fluxo recomendado

1. Configure a empresa e usuários.
2. Cadastre cidades e pessoas (cliente, remetente, destinatário, proprietário, agenciador).
3. Cadastre veículos e motorista; vincule tração/carretas.
4. Registre a captação e atribua o captador à programação.
5. Salve a programação inicial. Abra pelo olhinho, clique em Editar, associe o motorista e complete os dados da carga. Um usuário autorizado informa os valores restritos.
6. Clique **OC →** na programação. Confirme os avisos existentes.
7. Abra a OC pelo olhinho, atualize status e datas reais.
8. Financeiro revisa e aprova cada parcela. O envio Repom ficará bloqueado até integração real.
9. Crie e revise rascunhos de documentos a partir da OC.
10. Finalize ou cancele a viagem. Os registros permanecem no histórico.

## Importações

Em Cadastros, clique “Importar”. JSON aceita um array de objetos ou o formato de exportação `{ "module": "veiculos", "records": [...] }`. CSV deve ter cabeçalhos usando as chaves em `docs/campos.json`. Referências entre cadastros usam **IDs do sistema**, não nomes. Campos de lista usam JSON; para contatos/categorias prefira JSON. Duplicados não são criados e o relatório de erros é baixado.

Nos rascunhos CT-e/MDF-e:

- **XML:** lê campos reconhecidos e chaves de 44 dígitos; mostra confirmação antes de aplicar. Revise valores/peso/documentos e preenchimento restante.
- **PDF:** extrai chaves e identificadores reconhecidos. Para habilitar em uma máquina sem Poppler: `python -m pip install -r requirements-optional.txt`. PDF digitalizado exige uma futura integração OCR. Não extrai todos os dados de qualquer contrato Repom.
- **XLSX / CSV:** cabeçalhos em chaves do sistema; a primeira linha de dados preenche campos do manifesto. Chaves presentes nas linhas são propostas como documentos. Usa a primeira aba do XLSX; formatos e fórmulas do Excel não são recalculados.

## Backup e recuperação

```sh
python manage.py backup
python manage.py backup --output backups/meu-backup.sqlite3
python manage.py reset-admin --email admin@dg.local
```

O banco é `data/dg.sqlite3`. Para restaurar um backup, pare o servidor, preserve uma cópia do banco atual e coloque a cópia de backup nesse caminho. Faça backups fora do computador também. Não envie o banco a terceiros: contém dados pessoais e financeiros.

## Testes

```sh
python -m unittest discover -s tests -v
```

Os testes usam banco temporário e credenciais fictícias. Cobrem permissões, aprovação exclusiva, uma OC por programação, status sincronizado, datas/parcelas, duplicados, importação parcial, cancelamento, edição concorrente e CSRF. A renderização estrutural da interface é verificada por `node tests/test_ui.cjs`, incluindo todos os campos dos 16 módulos, referências, datas e restrições financeiras. O JavaScript passa em `node --check static/app.js` (Node é apenas ferramenta opcional de verificação).

## Hospedar depois

O servidor está restrito a `127.0.0.1` por padrão. Para uma operação em equipe, implante atrás de HTTPS com proxy, defina `DG_SECURE_COOKIE=1`, use cópias de segurança e supervisão do processo. Expor este servidor diretamente à internet não equivale a uma implantação pronta. Integrações e homologação devem ser finalizadas antes do uso fiscal/financeiro real.

Código fonte: `server.py` (API/regras), `schema.py` (campos/perfis), `imports.py` (extração), `static/` (interface). Veja `docs/INTEGRACOES.md` para o contrato esperado dos fornecedores.

## Alterações da versão 3

Menu na ordem da referência: Visão geral (Dashboard, Painel, Tracking), Cadastros, Comercial, Transporte, CRM e Gestão. Pessoas, motoristas, veículos e OC têm seções correspondentes aos novos prints. Contatos adicionais usam entradas separadas de nome, telefone e e-mail. O olhinho abre consulta; o botão Editar habilita alterações. Motoristas e veículos permitem registrar o link opcional de uma pasta do Drive.

Na OC, participantes, carga, motorista, veículos, beneficiário e valores são preenchidos a partir da programação. Alterações em carga, motorista, veículos, rota e fretes atualizam a programação vinculada. Remetente/destinatário podem ser pessoas diferentes dos locais de origem/destino. Dados financeiros permanecem ocultos na API e interface para perfis sem autorização. INSS/SEST/SENAT são apenas valores informados pelo Financeiro com acesso à OC: **não há cálculo tributário automático nem dedução automática das parcelas**, pois as regras ainda não foram definidas.

O mapa usa imagens públicas do OpenStreetMap, atribuição visível e cache normal do navegador, carregando apenas os quadrantes visíveis. Precisa de acesso à internet e segue https://operations.osmfoundation.org/policies/tiles/. Para volume elevado, configure outro serviço de mapas em `static/map.js`. O contador de posições antigas inclui posições com coordenadas cuja data esteja ausente. Sem coordenadas reais, nenhum marcador é inventado.

## Pesquisas e indicadores — versão 4

| Aba | Filtros |
| --- | --- |
| Pessoas | Nome, CPF/CNPJ, cidade ou UF, categoria, status e quantidade por página |
| Motoristas | Nome, CPF, cidade ou UF, status e quantidade por página |
| Veículos | Placa, tipo, nome/documento do proprietário, status e quantidade por página |
| Programação | Período, cliente, LH Trip, status, ordenação, intervalo de coleta e quantidade por página |
| OC | Pesquisa por nomes vinculados, status, intervalo de data da OC e quantidade por página |
| MDF-e / CT-e | Ambiente, pesquisa geral e quantidade por página |
| Vale-pedágio | Datas, situação, documento, placa, meio de pagamento, OC, pesquisa geral e quantidade por página |
| Rotas MDF-e | Pesquisa, origem, destino, status e quantidade por página |

Outras listagens também têm pesquisa geral e paginação. Clique em Pesquisar/Filtrar ou pressione Enter; Limpar restaura todos os critérios. Os filtros são combinados. Buscas desconsideram maiúsculas/acentos; CPF/CNPJ e placas aceitam pontuação ou apenas os caracteres. Referências são pesquisadas pelo nome do cadastro, não somente pelo número do ID.

Os indicadores usam registros reais: categorias em Pessoas (uma pessoa pode contar em mais de uma categoria), status em Veículos e vencimento de CNH em Motoristas. **CNH a vencer** significa da data de hoje até 30 dias, incluindo os limites; sem data de validade, não entra nas contagens. Programação considera a semana de segunda a domingo pela data da coleta; OCs criadas conta o status atual OC criada. Os indicadores de OC acompanham o resultado dos filtros; os demais resumem a base total da aba.

Vale-pedágio continua exclusivamente Repom. Situação de compra é somente informativa e depende do provedor real; solicitações locais sem integração aparecem como Aguardando configuração, nunca como compra concluída. Registros antigos de Rotas sem status são exibidos como Ativo.

Teste das pesquisas: `node tests/test_search.cjs`.

## Atualização da versão 5

Veja `docs/DESIGN-V5.md` para a revisão completa: seta de recolhimento do menu, logo SVG transparente, nova seleção de perfis/permissões, fluxo Pronta para OC, datas e histórico dos status, cancelamento com motivo, CIOT e Vale-pedágio ampliados e mapa Leaflet. APIs serão configuradas posteriormente.

Para iniciar no Windows, extraia todo o ZIP e execute **INICIAR-WINDOWS.bat**. Não abra somente o `index.html`. O endereço e as credenciais do primeiro acesso aparecem no terminal. A senha é gerada no seu primeiro início; esta distribuição não inclui contas, registros ou banco de dados de teste.

Validação atual: 29 testes Python e duas verificações estruturais JavaScript aprovados. Detalhes e limitações em `docs/VALIDACAO.md`.
