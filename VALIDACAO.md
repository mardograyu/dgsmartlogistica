# Validação da versão 5

Executados em 09/10/2026:

- `python -m unittest discover -s tests -p 'test_*.py' -q`: 29 testes aprovados (26 testes de sistema com servidor HTTP/SQLite e 3 de extração/importação).
- `node tests/test_ui.cjs`: renderização estrutural dos campos, serialização, formulário inicial/associação, permissões e logo SVG transparente.
- `node tests/test_search.cjs`: filtros por aba, documentos/placas, referências, intervalos de datas, indicadores e paginação.
- `node --check` em app.js, v5.js, map.js e leaflet.js.

Os testes de negócio abrangem permissões e sigilo financeiro, exclusividade da aprovação, uma OC por programação, validação Pronta para OC, sincronização, cronologia e histórico dos status, chegada salva antes de finalizar, parcelas, motivo de cancelamento, soma de eixos e ajuste manual, acesso do Financeiro aos dados vinculados sem liberar cadastro completo, duplicados, concorrência, CSRF e persistência das linhas de CIOT.

Não houve verificação visual em navegador nesta execução: o navegador de teste não estava disponível e seu download falhou no ambiente. Os testes de interface são estruturais, não substituem uma conferência visual e operacional da equipe.

Nenhuma API real ou homologação fiscal foi testada. Solicitações externas ficam aguardando configuração. Não houve envio de dinheiro, compra de vale ou emissão autorizada.
