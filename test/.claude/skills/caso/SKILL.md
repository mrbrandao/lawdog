---
name: caso
description: >-
  Inicia e gerencia um caso no JEC. Conduz o intake completo do usuário
  (narrativa livre → triagem → lacunas → simulação adversarial → abertura),
  cria a estrutura de diretórios do caso e gera caso.md com o resumo inicial.
  Ativar em: /lawdog:caso, abrir caso, iniciar processo, tenho um problema
  jurídico, quero processar alguém, preciso entrar com uma ação.
compatibility: >-
  Usa LAWDOG_CASES_DIR se definido; fallback: ~/lawdog-cases.
  Configurar com plugin/scripts/setup.sh.
allowed-tools: Bash, Read, Write, WebFetch
metadata:
  author: mrbrandao
  version: "1.0"
---

## Protocolos importados

- `protocols/case-intake.md` — fluxo completo de atendimento
- `protocols/file-structure.md` — convenção de diretórios (fonte única)
- `protocols/knowledge-sources.md` — como acessar artigos jurídicos
- `knowledge/court-portals.md` — TJ/PROJUDI por estado

## Trigger

Usuário descreve um problema jurídico ou invoca `/lawdog:caso`.

## Fluxo

Siga cada etapa de `protocols/case-intake.md` na ordem:

### Etapa 1 — Narrativa livre

Convide o usuário a descrever o problema com suas próprias palavras.
Não interrompa com formulários ou perguntas. Deixe terminar.

### Etapa 2 — Triagem

Identifique: tipo do caso, estado do usuário (consulte `knowledge/court-portals.md`),
se cabe no JEC (consulte `knowledge/codigo-civil-jec.md` → Art. 3° Lei 9.099/95;
nunca hardcode o valor em reais), código aplicável (CC, CDC, ou ambos).

Se o caso não couber no JEC: comunique claramente e oriente alternativas.
Encerre a skill — não abra estrutura de diretórios para casos fora do escopo.

### Etapa 3 — Lacunas

Pergunte o que falta para avaliar o caso: partes, datas, valores, evidências.
UMA pergunta por vez. Aguarde a resposta antes de perguntar a próxima.

### Etapa 4 — Simulação adversarial

Simule internamente a defesa da parte contrária. Apresente os pontos fracos
ao usuário com honestidade. Se o caso for fraco, diga e explique o que mudaria.

### Etapa 5 — Decisão e abertura

Pergunte: "Com base no que analisamos, você deseja prosseguir e abrir o caso?"

**Se sim:**

1. Resolva LAWDOG_CASES_DIR:

```bash
CASES_DIR="${LAWDOG_CASES_DIR:-$HOME/lawdog-cases}"
```

2. Gere o `<case-slug>` em kebab-case a partir do tema (ex: `obra-irregular`).
   Regras completas em `protocols/file-structure.md`: lowercase, sem acentos, max 40 chars.

3. Crie a estrutura de diretórios:

```bash
mkdir -p "$CASES_DIR/<case-slug>/peticao-inicial/anexos"
```

4. Gere `caso.md` usando o template em `protocols/file-structure.md`.
   Preencha: partes, estado/comarca, fundamento jurídico (artigos verificados),
   timeline, evidências disponíveis, pontos fracos da simulação adversarial.

5. Escreva o arquivo em `$CASES_DIR/<case-slug>/caso.md`.

6. Informe o path completo ao usuário e oriente o próximo passo:
   - Consulte `knowledge/court-portals.md` para acesso ao JEC do estado
   - Se tiver vídeos como evidência: use `/lawdog:video2forum` para converter

**Se não:** resuma o que precisaria mudar para o caso se tornar viável.

## Orientação ao portal

Após abrir o caso, consulte `knowledge/court-portals.md` para o estado do usuário
e oriente passo a passo: como acessar o JEC, selecionar comarca e vara, e
distribuir a petição inicial quando chegar esse momento.
