# Correções V7

Confirmações de saída e ações internas usam uma janela com o visual DG. Continuar editando, Escape ou Voltar não descartam dados. Descartar alterações retorna à lista. O foco retorna ao controle original.

Campos essenciais são marcados e verificados no formulário e no servidor, inclusive em importações. Pessoas: nome e documento; motoristas: nome e CPF; veículos: placa e tipo; cidades: nome e UF; captação: nome, telefone e responsável. Programação inicial: LH TRIP, cliente, origem, destino, carregamento e ETA destino. Motorista e conjunto continuam associados na edição posterior. Pronta para OC mantém a exigência de motorista, tração e oferta positiva. Documentos exigem OC vinculada. Observações continuam opcionais.

Tração permite Cavalo, Truck, Toco, VUC e Utilitário. Carretas permitem Carreta, Bitrem e Rodotrem. Outros tipos precisam ser reclassificados no cadastro antes do vínculo. O filtro vale para as buscas e o servidor rejeita vínculos incompatíveis, inclusive em documentos e importações.

Ao atualizar, mantenha seu banco de dados e reinicie o servidor. Cadastros antigos permanecem; ao editar dados incompletos, complete os campos essenciais. Nenhuma API externa foi ativada.

Validação: 32 testes Python e testes JavaScript de formulário, pesquisa e confirmação. A conferência visual pelo navegador remoto não foi possível por bloqueio de acesso ao servidor local.

## Ajuste V7.1
Removida a faixa preta e o nome DG da janela de confirmação. Mantidos o conteúdo branco, a mensagem e os botões.
