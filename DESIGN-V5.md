# Versão 5 — revisão autorizada em 09/10/2026

## Interface

- Menu lateral expandido de 210 para 250 px no desktop, com seta na borda para alternar para 78 px. A escolha fica salva no navegador; telas abaixo de 981 px mantêm o menu responsivo. Os rótulos dos ícones aparecem fora da área de rolagem ao passar o mouse ou usar o teclado.
- Logo DG redesenhada em SVG vetorial com fundo transparente, removendo o recorte da prancha preta. A identidade permanece DG Smart Logística, em prata e dourado; sem LTDA. A imagem da carreta no login foi mantida.
- Usuários: cartões de perfis com descrição e uma matriz por aba com Padrão do perfil / Permitir / Bloquear, pesquisa, contador e prévia do acesso resultante. Restaurar padrão remove as exceções da tela. As permissões são verificadas no servidor.
- Enter avança entre campos do editor. Textareas aceitam quebras de linha; pesquisas, login, botões e seleção de cadastros preservam seus comandos. Uma pesquisa digitada sem selecionar cadastro não é enviada como vínculo.

## Programação e OC

A programação nova continua com a etapa inicial. Depois de salvar, abra pelo olhinho e clique em Editar para associar motorista e veículos. O preenchimento pelo motorista não substitui um veículo já escolhido manualmente.

Pronta para OC exige motorista, tração e frete ofertado positivo. O botão Gerar OC aparece após salvar nesse status, com confirmação. Permanecem os demais dados obrigatórios já combinados para gerar a OC, exceto observações. Cada programação gera somente uma OC; o botão passa a abrir a OC existente.

A OC registra abertura, autorização, início de carregamento, saída, chegada ao cliente, descarga e cancelamento. Datas ficam preservadas por status. A chegada precisa estar salva antes de finalizar. A descarga não pode ser anterior à chegada, e a chegada não pode ser anterior à saída. Status e dados associados da OC continuam sincronizados com a programação.

Cancelamento continua pela ação Cancelar viagem da Programação, agora com motivo obrigatório e confirmação. O motivo, horário e histórico ficam guardados na programação e na OC. Não há exclusão do cadastro ou reabertura de viagem cancelada.

## CIOT e Vale-pedágio

CIOT ganhou ambiente, vínculos CT-e/MDF-e, motorista, tração, quatro campos visíveis de carreta, datas, distância, CEPs, coordenadas, carga/NCM/peso, valores, tributos, documentos e parcelas com campos individuais. Dados da OC preenchem os campos operacionais e totais 70/30; classificação da carga e peso precisam ser conferidos. Coordenadas são manuais nesta versão: busca externa aguarda integração. Tributos são informados pelo Financeiro; nenhuma regra tributária foi adotada automaticamente a partir do SSX.

Vale-pedágio ganhou tração/carreta, eixos do conjunto, ajuste manual com motivo, vigência, rodagem/eixo suspenso, origem/destino/IBGE/CEP, documento do subcontratado e itens financeiros. O servidor soma os eixos e valida o motivo do ajuste. A OC preenche veículos e locais. A solicitação de compra exibe confirmação antes de entrar na fila pendente.

As listagens de CIOT e Vale-pedágio atualizam a cada 10 segundos quando visíveis, sem interromper edição nem links focados. Emissão, compra, consulta e eventos externos continuam dependentes dos fornecedores e credenciais. Sem API não é gerado número de autorização, compra concluída, transferência ou pagamento fictício.

## Tracking

Mapa Leaflet 1.9.4 incluído localmente, com camada OpenStreetMap e atribuição. Apenas veículos de OCs em andamento com coordenadas cadastradas aparecem no mapa. Placas, popups com OCs/motoristas, pesquisa, enquadramento e tela cheia foram mantidos. Cores refletem posição até 10 minutos, entre 10 e 30, ou acima de 30/sem horário. Atualização de dados a cada 5 minutos, botão manual e contador. Indicadores de idade mudam a cada minuto. Painel e dashboard continuam atualizando a cada 10 segundos, e o alerta de No-show se repete a cada 5 minutos após ativar som.

## Limites e pendências

- APIs fiscais, Repom e rastreadores serão configuradas depois. Os arquivos SSX revelam interfaces e chamadas internas, não os contratos completos dos provedores.
- Percentual de comissão, despesas e regras tributárias permanecem a definir.
- Geocodificação automática e eventos de CIOT autorizados dependem de integração; os campos locais estão disponíveis.
- Para migrar dados, copie a pasta `data` do projeto anterior com o servidor desligado e mantenha um backup. Não rode duas versões usando o mesmo arquivo SQLite simultaneamente.
