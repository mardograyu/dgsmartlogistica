# Integrações pendentes — contrato de implementação

Nenhuma API proprietária foi inventada nesta entrega. O servidor grava intenções de emissão em `jobs` com estado `Aguardando configuração`. A ação de pagamento retorna erro 409 sem mudar a parcela para Enviado/Pago. A interface nunca exibe uma autorização fictícia.

## Repom

Obter acesso contratual, homologação, especificação da autenticação, cadastro de beneficiários, emissão/cancelamento de CIOT, compra/cancelamento de vale-pedágio, ordem de pagamento, consulta de situação, comprovantes e webhook autenticado. Definir vínculo de CPF/beneficiário e contas de liquidação.

Implementação necessária:

1. Revisar parâmetros reais com o fornecedor e mapear os registros locais.
2. Usar identificador idempotente por parcela e assinatura dos termos aprovados.
3. Enviar somente com aprovação Financeiro válida, valor/beneficiário/data inalterados e vencimento atingido; saldo somente após descarga e Finalizada.
4. Guardar identificador externo e resposta auditável; confirmar pagamento apenas por retorno verificado.
5. Fazer reconciliação antes de liberar reenvio ou alteração de valor de parcela enviada.
6. Ajustar homologação/produção e autenticar webhooks no servidor.

## Provedor fiscal

Escolher fornecedor e obter API oficial; certificado A1 ou modalidade exigida, senha/certificado somente no servidor, CNPJ, IE, RNTRC, regime tributário, séries, numeração e ambientes. Implementar validação vigente, assinatura/transmissão conforme modelo, consulta, eventos, cancelamento e encerramento, guarda de XML/protocolo e DANFE/DACTE/DAMDFE retornados pelo fornecedor.

Não definir alíquotas apenas copiando scripts antigos. O responsável deve validar o regime e a configuração fiscal. Cadastro local não é autorização SEFAZ.

## Rastreamento

Criar adaptadores por empresa (OnixSat, Omnilink, Sascar) após receber autorização e documentação. Mapear `veiculos.dispositivo` ao identificador do fornecedor. Normalizar latitude/longitude, instante da posição, velocidade e outros atributos realmente disponíveis. Filtrar pelas OCs em andamento; mostrar falhas/frescura da posição e não substituir falha por uma posição fictícia. Considerar limites de requisições reais e filas por provedor.

## Drive

Os arquivos são mantidos fora dos cadastros. Uma futura integração só será necessária se o usuário quiser pesquisa/link/upload direto; definir conta/pasta/permissões antes.

## Segurança e operação antes da produção

HTTPS, segredos fora do código, backups testados, ambiente de homologação separado, autenticação dos retornos, logs de integração sem senhas/tokens, monitoramento e testes reais com cada fornecedor. O servidor stdlib fornecido é adequado ao desenvolvimento/uso local; escolher a infraestrutura de produção com base na escala e disponibilidade desejadas.
