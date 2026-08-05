---
name: fetch-law
description: >-
  Busca texto atualizado de artigos jurídicos em fontes oficiais
  (planalto.gov.br, TJ do estado). Usada internamente por outras skills
  quando knowledge/ não tem o artigo ou pode estar desatualizado.
  Ativar em: /lawdog:fetch-law, buscar artigo, verificar lei atualizada,
  texto oficial da lei.
compatibility: >-
  Requer conexão com internet. Tenta WebFetch primeiro; usa WebSearch
  como fallback automático se WebFetch falhar (planalto.gov.br pode
  recusar conexões diretas). Fontes estaduais: TJ do estado do caso.
allowed-tools: WebFetch, WebSearch
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
3. **Tente WebFetch na URL** — se falhar (socket error, connection reset, timeout):
   - Não tente novamente com WebFetch
   - Vá direto ao passo 4 (WebSearch)
4. **Fallback — WebSearch** com query estruturada (veja tabela de queries abaixo)
   - Extraia o texto do artigo a partir dos resultados da busca
   - Prefira resultados de planalto.gov.br, senado.leg.br ou camara.leg.br
   - Evite sites de conteúdo jurídico sem fonte oficial (jusbrasil, etc.) salvo
     se for a única opção disponível — nesse caso, sinalize na resposta
5. Extraia o texto do artigo específico (número exato, com parágrafos e incisos)
6. Retorne no formato de output abaixo

Se nenhuma fonte retornar o texto do artigo:
- Informe o usuário e sugira que consulte diretamente https://www.planalto.gov.br
- Nunca invente o conteúdo do artigo

## Fontes por norma (WebFetch — tente primeiro)

| Norma | URL |
|---|---|
| Código Civil (Lei 10.406/2002) | https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm |
| CDC (Lei 8.078/1990) | https://www.planalto.gov.br/ccivil_03/leis/l8078compilado.htm |
| Lei 9.099/1995 (JEC) | https://www.planalto.gov.br/ccivil_03/leis/l9099.htm |
| Legislação federal geral | https://www.planalto.gov.br/legislacao |

## Queries de fallback (WebSearch — use se WebFetch falhar)

| Norma | Query WebSearch |
|---|---|
| Código Civil art. N | `"Art. N" "Código Civil" "Lei 10.406" texto site:planalto.gov.br` |
| CDC art. N | `"Art. N" "Código de Defesa do Consumidor" "Lei 8.078" texto site:planalto.gov.br` |
| Lei 9.099/95 art. N | `"Art. N" "Lei 9.099" "Juizado Especial" texto site:planalto.gov.br` |
| Qualquer lei federal | `"Art. N" "[nome da lei]" texto official site:planalto.gov.br OR site:senado.leg.br` |

Se a query com `site:planalto.gov.br` não retornar o texto, remova o filtro de site.

## Output

```
**Art. [N] — [Nome da Lei]**

[texto completo do artigo, incluindo parágrafos e incisos]

Fonte: [URL]
Verificado em: [YYYY-MM-DD]
```
