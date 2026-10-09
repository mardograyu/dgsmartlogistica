# Design V2

Implementação do visual aprovado em 08/10/2026:

- Logo da identidade visual DG reutilizada em SVG autocontido, com a imagem original embutida e enquadramento da marca. Não depende de serviço externo.
- Menu lateral com texto, ícones e grupos; sem o seletor “Ir para”.
- OC é o nome exibido no menu e nas telas.
- Cores neutras: fundo claro, cartões brancos, menu carvão, foco azul acinzentado e status semântico. O dourado fica na marca.
- Cadastros em páginas amplas, divididos em seções. Todos os campos persistidos continuam disponíveis.
- Referências com busca por nome, ID e CPF/CNPJ/placa quando aplicável. A seleção guarda o ID do cadastro.
- Data e hora separadas na interface e combinadas no mesmo campo de dados já utilizado pelo servidor.
- Barra inferior de ações e indicação da margem bruta na programação apenas para perfis autorizados.
- Menu móvel e reorganização dos campos em telas pequenas.

O mockup foi uma referência de composição. Não houve validação visual em navegador nesta execução; o projeto inclui verificação estrutural HTML e testes de API. Integrações externas continuam com as mesmas pendências descritas no README.
