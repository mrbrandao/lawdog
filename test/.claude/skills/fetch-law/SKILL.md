---
name: fetch-law
description: >-
  Busca texto atualizado de artigos jurídicos em fontes oficiais
  (planalto.gov.br, TJ do estado). Usada internamente por outras skills
  quando knowledge/ não tem o artigo ou pode estar desatualizado.
  Ativar em: /lawdog:fetch-law, buscar artigo, verificar lei atualizada,
  texto oficial da lei.
compatibility: >-
  Requer conexão com internet. Fontes federais: planalto.gov.br.
  Fontes estaduais: TJ do estado identificado no caso.
allowed-tools: WebFetch
metadata:
  author: mrbrandao
  version: "1.0"
---

## Protocolo importado

- `protocols/knowledge-sources.md`

## Trigger

Acionada por `/lawdog:caso` ou outra skill quando precisam de texto atualizado.
Usuário pode invocar diretamente: `/lawdog:fetch-law <norma> <artigo>`

Exemplos:
- `/lawdog:fetch-law Lei 9.099/95 Art. 3`
- `/lawdog:fetch-law CDC Art. 42`
- `/lawdog:fetch-law Código Civil Art. 927`

## Fluxo

1. Identifique a norma e o artigo solicitado
2. Selecione a URL na tabela de fontes abaixo
3. Faça WebFetch na URL
4. Extraia o texto do artigo específico (número exato, com parágrafos e incisos)
5. Retorne no formato de output abaixo

Se o artigo não for encontrado na URL principal:
- Tente https://www.planalto.gov.br/legislacao buscando pela lei
- Se ainda não encontrar: informe o usuário e sugira busca manual
- Nunca invente o conteúdo do artigo

## Fontes por norma

| Norma | URL |
|---|---|
| Código Civil (Lei 10.406/2002) | https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm |
| CDC (Lei 8.078/1990) | https://www.planalto.gov.br/ccivil_03/leis/l8078compilado.htm |
| Lei 9.099/1995 (JEC) | https://www.planalto.gov.br/ccivil_03/leis/l9099.htm |
| Legislação federal geral | https://www.planalto.gov.br/legislacao |

## Output

```
**Art. [N] — [Nome da Lei]**

[texto completo do artigo, incluindo parágrafos e incisos]

Fonte: [URL]
Verificado em: [YYYY-MM-DD]
```
