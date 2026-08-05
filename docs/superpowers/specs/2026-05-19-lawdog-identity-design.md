# Lawdog Identity Design

**Date:** 2026-05-19
**Status:** approved
**Scope:** identidade inicial do lawdog — persona, camada de protocolos, base de conhecimento jurídico, gestão de casos e bootstrap

---

## 1. Contexto

O lawdog é um plugin de IA para assistentes como Claude Code, Gemini e Cursor, voltado a brasileiros que precisam ingressar com processos no JEC (Juizado Especial de Pequenas Causas / Cíveis) sem advogado. A versão atual possui uma skill funcional (`video2forum`) mas nenhuma identidade ou persona definida. Este spec estabelece a camada de identidade inicial que fundamenta todas as skills futuras.

O JEC permite causas até um valor-limite definido em lei (a ser verificado via `fetch-law` — nunca hardcoded), sem obrigatoriedade de advogado para causas menores. Cada estado tem seu próprio TJ, portal de acompanhamento e regras de juizado. O lawdog deve conhecer essa topografia e orientar o usuário conforme o estado onde reside.

---

## 2. Arquitetura geral

Abordagem: camadas modulares (mix approaches 2+3). A persona é persistente e consistente; os protocolos e skills são consumidos seletivamente conforme o contexto. Cada skill é autônoma e declara explicitamente quais protocolos importa — projetada para mapear 1:1 a um sub-agente autônomo quando o framework de agentes for escolhido.

```
plugin/
├── AGENTS.md                         # persona core (~80 linhas)
├── .claude-plugin/
│   └── plugin.json
├── protocols/                        # contratos comportamentais compartilhados
│   ├── case-intake.md                # fluxo: narrativa → triagem → análise
│   ├── file-structure.md             # convenção de diretórios (fonte única)
│   └── knowledge-sources.md          # como usar knowledge/ e quando fazer fetch
├── knowledge/                        # base jurídica embarcada
│   ├── index.md                      # índice por tema
│   ├── codigo-civil-jec.md           # artigos críticos para JEC
│   └── court-portals.md             # TJ/PROJUDI por estado + navegação
├── skills/
│   ├── video2forum/                  # existente — sem alteração
│   │   ├── SKILL.md
│   │   └── scripts/
│   ├── caso/                         # NOVO — intake + abertura de caso
│   │   └── SKILL.md
│   └── fetch-law/                    # NOVO — busca artigo atualizado
│       └── SKILL.md
└── scripts/
    └── setup.sh                      # bootstrap: LAWDOG_CASES_DIR + deps
```

**Princípio:** nenhuma skill lê o AGENTS.md diretamente. O AGENTS.md define o caráter; os `protocols/` definem o comportamento. Skills importam apenas o que precisam.

---

## 3. Persona (AGENTS.md)

O AGENTS.md é reescrito como contrato mínimo e preciso. Cobre:

- **Identidade**: advogado especializado no Código Civil brasileiro com experiência como juiz. Conhece como o magistrado pensa, avalia provas e decide.
- **Postura**: educado, direto, realista. Nunca alucina — quando não tem certeza de um artigo ou precedente, busca antes de citar. Quando o caso não tem fundamento, diz claramente.
- **Raciocínio adversarial**: antes de declarar um caso viável, simula internamente a defesa da parte contrária. Apresenta ao usuário os pontos fracos que um juiz provavelmente notará.
- **Honestidade sobre limites**: não dá garantias de resultado. Não substitui advogado em casos que excedem o JEC ou que envolvem complexidade fora do seu escopo. Diz isso sem hesitar.
- **Idioma**: responde em português por padrão; segue o idioma do usuário se diferente.
- **Conhecimento**: Código Civil, CPC (no que tange ao JEC), CDC quando relevante. Para artigos: `knowledge/` primeiro, `fetch-law` se precisar de texto atualizado. Nunca cita de memória sem verificar.
- **Referência aos protocolos**: o AGENTS.md aponta para `protocols/` para comportamentos específicos — não os duplica.

---

## 4. Camada de protocolos

### `protocols/case-intake.md`

Fluxo em 5 etapas:

1. **Narrativa livre** — usuário descreve o problema com suas palavras, sem formulário.
2. **Triagem** — lawdog identifica:
   - Tipo de caso (relação de consumo, vizinhança, contrato, dano material/moral, etc.)
   - Estado do usuário (pergunta se não souber) → determina TJ, portal e regras locais
   - Se o caso cabe no JEC (consulta `knowledge/` ou `fetch-law` para valor-limite atual)
   - Código aplicável (CC, CDC, etc.)
   - Se o caso não couber no JEC: comunica imediatamente e orienta alternativas
3. **Lacunas** — identifica o que falta (provas, datas, valores, partes) e pergunta uma coisa por vez
4. **Simulação adversarial** — simula defesa da parte contrária; apresenta pontos fracos ao usuário antes de recomendar avançar
5. **Decisão** — usuário decide se quer abrir o caso; se sim, aciona criação da estrutura de diretórios e geração de `caso.md`

### `protocols/file-structure.md`

Fonte única da verdade para nomes de diretórios e arquivos. Toda skill que cria ou lê arquivos importa este protocolo — nunca hardcoda paths.

```
$LAWDOG_CASES_DIR/
└── <case-slug>/
    ├── caso.md               # resumo: partes, estado/comarca, timeline, código aplicável
    ├── peticao-inicial/
    │   ├── peticao-inicial.pdf
    │   └── anexos/
    ├── peticao-02/
    │   ├── peticao-02.pdf
    │   └── anexos/
    └── peticao-N/
        ├── peticao-N.pdf
        └── anexos/
```

- `<case-slug>`: gerado a partir do tema do caso em kebab-case (ex: `obra-irregular`, `atraso-entrega-produto`)
- `peticao-N`: numeração sequencial; cada interação com o juízo que exige nova juntada gera um novo diretório
- `caso.md`: atualizado pelo lawdog a cada nova etapa do processo

### `protocols/knowledge-sources.md`

Ordem de consulta obrigatória:

1. Consulta `knowledge/index.md` pelo tema
2. Lê o artigo em `knowledge/codigo-civil-jec.md` se presente
3. Se precisar de texto atualizado ou artigo não embarcado: aciona `/lawdog:fetch-law`
4. Nunca cita artigo de memória sem verificar. Se não encontrar: declara que precisa verificar.

---

## 5. Base de conhecimento (`knowledge/`)

### `knowledge/index.md`
Índice por tema: responsabilidade civil, relações de consumo, direito de vizinhança, obrigações, dano moral, etc. Aponta para o arquivo e número do artigo.

### `knowledge/codigo-civil-jec.md`
Artigos críticos para causas JEC: responsabilidade civil (CC), relações de consumo (CDC), obrigações, dano moral. Texto verificado com nota de data de verificação — substituído por `fetch-law` quando houver dúvida de atualização.

### `knowledge/court-portals.md`
Mapeamento estado → TJ URL → portal de acompanhamento → dinâmica de acesso. Paraná como referência inicial:

- TJ: https://www.tjpr.jus.br/
- Acompanhamento (PROJUDI): https://projudi.tjpr.jus.br/projudi/
- Formulário JEC: https://www.tjpr.jus.br/formulario-virtual-juizados-especiais
- Navegação: comarca → vara/juizado (lawdog orienta o usuário passo a passo)

Estrutura pronta para adicionar outros estados. O lawdog lê este arquivo para orientar o usuário conforme o estado identificado na triagem.

---

## 6. Skills

### `/lawdog:caso`
**Importa:** `protocols/case-intake.md`, `protocols/file-structure.md`, `protocols/knowledge-sources.md`, `knowledge/court-portals.md`

Fluxo completo de intake conforme `case-intake.md`. Ao final, se o usuário decidir abrir o caso:
- Cria estrutura de diretórios conforme `file-structure.md` em `$LAWDOG_CASES_DIR`
- Gera `caso.md` com: resumo do problema, partes, estado/comarca, código aplicável, timeline inicial, pontos fracos identificados na simulação adversarial

### `/lawdog:fetch-law`
**Importa:** `protocols/knowledge-sources.md`

Faz WebFetch em fonte oficial (planalto.gov.br, TJ relevante) para buscar texto atualizado de artigo ou regra específica. Retorna texto e URL fonte. Usada internamente por outras skills; raramente invocada diretamente pelo usuário.

### `/lawdog:video2forum` (existente)
Sem alteração de contrato. Continua funcionando de forma independente.

---

## 7. Bootstrap (`scripts/setup.sh`)

Script executado na instalação do plugin:

1. Pergunta ao usuário onde salvar os casos (`LAWDOG_CASES_DIR`)
   - Default (se não informado): `~/lawdog-cases`
   - Usuário pode informar qualquer caminho absoluto ou relativo ao home
2. Exporta `LAWDOG_CASES_DIR` no perfil do shell (`~/.bashrc` ou `~/.zshrc`)
3. Valida dependências: `ffmpeg` (avisa se ausente, não bloqueia)
4. Cria `$LAWDOG_CASES_DIR` se não existir
5. Confirma configuração com resumo ao usuário

---

## 8. Arquitetura futura (não implementado agora)

Quando o framework de agentes for escolhido (CrewAI, LangGraph, Claude Code agents nativos, ou outro), cada skill mapeia diretamente a um agente autônomo:

| Skill atual | Agente futuro |
|---|---|
| `/lawdog:caso` | Agente de intake e triagem |
| `/lawdog:fetch-law` | Agente de pesquisa jurídica |
| `/lawdog:video2forum` | Agente de preparação de evidências |
| (futuro) `/lawdog:peticao` | Agente redator de petições |
| (futuro) `/lawdog:fetch-court-info` | Agente de scraping de portais TJ |

Os `protocols/` viram os contratos de comunicação entre agentes. O `AGENTS.md` vira o agente orquestrador (o lawdog principal que coordena os especializados).

A skill `fetch-court-info` (futura) fará scraping dos portais TJ/PROJUDI com base no estado e comarca do caso, extraindo regras do juizado específico, taxas de distribuição e prazos atualizados.

---

## 9. Decisões registradas

| Decisão | Escolha | Motivo |
|---|---|---|
| Arquitetura | Camadas modulares (mix 2+3) | Modular, consistente, token-eficiente, agent-ready |
| Conhecimento jurídico | Embarcado + fetch sob demanda | Offline-first com atualização quando necessário |
| Fluxo de intake | Narrativa livre → triagem | Natural para leigo, token-eficiente |
| Localização dos casos | `LAWDOG_CASES_DIR` configurável | Convenção sensata com override fácil |
| Sub-agentes agora | Não implementado | Framework não escolhido; skills já são agent-ready |
| Valores-limite JEC | Nunca hardcoded | Verificado via knowledge/ ou fetch-law |
