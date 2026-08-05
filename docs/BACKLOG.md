# Backlog — Lawdog

Melhorias identificadas, decisões pendentes e ideias para sessões futuras.
**Leia este arquivo no início de qualquer nova sessão de desenvolvimento.**

---

## Problemas identificados em sessão real — 2026-06-08/09

**Contexto:** Sessão de importação do caso `obra-irregular-sobrado04` e redação da
petição de novos fatos com prazo real (protocolar no fórum no dia seguinte).

---

### P1. Template LaTeX — múltiplos problemas de formatação

**Status:** corrigido nesta sessão — `base-legal.latex` atualizado em produção
**Identificado em:** 2026-06-08

**Mudanças aplicadas ao `plugin/templates/base-legal.latex` (diff resumido):**

```diff
- \usepackage{lmodern}                    % fonte Computer Modern ilegível
+ \usepackage{charter}                    % fonte Bitstream Charter (próxima a Cambria)

+ % Cabeçalhos de seção azuis com caixa alta e regra horizontal
+ \usepackage{xcolor}
+ \usepackage{titlesec}
+ \definecolor{lawblue}{HTML}{2E75B6}
+ \titleformat{\section}{\large\bfseries\color{lawblue}}{}{0em}{\MakeUppercase}
+   [\vspace{2pt}{\color{lawblue}\hrule height 0.8pt}\vspace{4pt}]
+ \titleformat{\subsection}{\normalsize\bfseries\color{lawblue}}{}{0em}{\MakeUppercase}
+ \titlespacing{\section}{0pt}{14pt}{6pt}

+ % Figuras: posicionamento forçado no lugar onde são referenciadas
+ \usepackage{graphicx}
+ \usepackage{float}
+ \floatplacement{figure}{H}

+ % Captions: sem "Figure N:", itálico, fonte pequena
+ \usepackage{caption}
+ \captionsetup[figure]{labelformat=empty, font={footnotesize,it}, skip=4pt}

+ % Número de página no canto inferior direito
+ \usepackage{fancyhdr}
+ \pagestyle{fancy}
+ \fancyhf{}
+ \fancyfoot[R]{\small\thepage}
+ \renewcommand{\headrulewidth}{0pt}

- \pagestyle{plain}                       % removido — substituído por fancyhdr
```

**Nota sobre dependência de fonte — crítica:**
`charter` requer `8r.enc` ausente em instalações TeX mínimas.
Erro: `pdfTeX error: cannot open encoding file 8r.enc for reading`.
**Solução:** `sudo dnf install texlive-collection-fontsrecommended` (Fedora).
Sem esse pacote, usar `\usepackage{lmodern}` como fallback.

**Template de referência preservado em:** `plugin/templates/base-legal.latex`
(o arquivo em produção já inclui todas as correções acima)

**Ação pendente:**
- Adicionar ao `plugin/scripts/setup.sh` verificação e instalação de `texlive-collection-fontsrecommended`
- Adicionar nota de pré-requisito no README

---

### P2. Imagens em petições — novo padrão e problema de tamanho

**Status:** parcialmente implementado — padrão estabelecido, controle de tamanho pendente
**Identificado em:** 2026-06-08/09

**Novo padrão estabelecido:** Petições com fotos embutidas no corpo do documento
(via markdown `![caption](path){width=X%}`) são muito mais eficazes — o juiz vê
a prova antes de ler sobre ela. Esse formato deve ser **padrão** em todas as petições
onde há evidência fotográfica relevante.

**Problema pendente:** Imagens com aspect ratio vertical ocupam a página inteira
e causam quebras de página indesejadas, mesmo com `width=78%`. Uma foto vertical
de 3:4 a 78% de largura pode ocupar 100% da altura da página.

**Solução a implementar no template:**
```latex
% Limitar imagens a no máximo 40% da altura da página, mantendo proporção
\usepackage{graphicx}
\setkeys{Gin}{width=\linewidth,height=0.40\textheight,keepaspectratio}
```

Isso garante que nenhuma imagem exceda 40% da altura da página, independente
de quanto `width=X%` o markdown especificar.

**Ação necessária:**
- Adicionar `\setkeys{Gin}{height=0.40\textheight,keepaspectratio}` ao `base-legal.latex`
- Testar com imagens verticais (ex: fotos de celular em portrait)
- Atualizar skill `peticao` para orientar Dr. LawDog a incluir fotos relevantes
  quando houver evidência fotográfica que suporte diretamente o argumento

---

### P3. Dr. LawDog não é a voz ativa — espera o usuário conduzir

**Status:** não implementado
**Identificado em:** 2026-06-08

O agente aguardava perguntas em vez de conduzir proativamente. Em casos com prazo
real, o advogado deve alertar riscos, orientar o próximo passo e sinalizar quando
uma decisão do usuário é estrategicamente arriscada — sem ser perguntado.

**Ação necessária — `plugin/AGENTS.md`:**
*"Ao final de cada interação, oriente o próximo passo. Não espere o usuário perguntar.
Se detectar risco estratégico em decisão do usuário, sinalize antes de executar.
Você é o advogado — conduza."*

---

### P4. Skills com trigger não são chamadas — scripts manuais no lugar

**Status:** não implementado
**Identificado em:** 2026-06-08

Quando o usuário mencionava ações com skills dedicadas (conversão de vídeo, imagem,
juntada, petição), o agente criava scripts bash ad-hoc em vez de invocar a skill.

**Ação necessária — `plugin/AGENTS.md`:**
*"Antes de executar qualquer operação de arquivo, verificar se existe skill disponível.
Se existe, invocar a skill — nunca substituir por script manual."*

---

### P5. Dr. LawDog não lê o caso antes de interagir

**Status:** não implementado
**Identificado em:** 2026-06-08

O agente começou sem ler os documentos existentes do caso. O usuário precisou orientar
manualmente a leitura de CLAUDE.md, caso.md e do PROJUDI.

**Ação necessária — `protocols/case-intake.md` (Step 0):**
*"Se caso.md existe, ler COMPLETAMENTE antes de qualquer interação: caso.md completo,
journal.md (se existir), Estado atual, Movimentações, e ao menos os últimos 3
documentos juntados. Nunca peça ao usuário para resumir o que você pode ler."*

---

### P6. Sem loop de revisão de petição — agente sai antes do usuário aprovar

**Status:** não implementado
**Identificado em:** 2026-06-08

Após gerar o rascunho, o agente saiu do loop de revisão sem aguardar aprovação.

**Protocolo correto a implementar — `plugin/skills/peticao/SKILL.md` (Phase 3):**
1. Gerar rascunho → apresentar ao usuário
2. Permanecer em loop explícito até receber "aprovar" ou instrução de abandono
3. A cada ciclo: editar apenas a seção solicitada → mostrar o trecho editado → aguardar
4. Só regenerar PDF quando o usuário pedir ou aprovar
5. Lembrar ao final de cada resposta: *"Posso ajustar qualquer seção. Quando estiver satisfeito, diga aprovar."*
6. Não mudar de assunto sem aprovação explícita

---

### P7. Ausência de task tracking — sessão sem estrutura de progresso

**Status:** não implementado
**Identificado em:** 2026-06-08

Múltiplas tarefas correram em paralelo sem registro. Modelo correto (seguir superpowers):
1. Criar tasks ANTES de começar qualquer fluxo com 3+ etapas
2. Marcar `in_progress` ao iniciar cada task
3. Permanecer na task até concluída — não avançar antes
4. Marcar `completed` só quando realmente concluída
5. Se usuário mudar de assunto: suspender explicitamente, registrar estado parcial

**Ação necessária — `plugin/AGENTS.md`:**
*"Para qualquer fluxo com 3+ etapas, criar tasks antes de começar. Uma task
incompleta = permaneça nela. Siga o modelo do superpowers."*

---

### P8. Ausência de journal do caso — contexto narrativo não é preservado

**Status:** proposta de arquitetura — não implementado
**Identificado em:** 2026-06-08/09

O `caso.md` registra fatos estruturados, mas não preserva o contexto narrativo que
o usuário revela ao longo das sessões: estratégias discutidas, admissões capturadas,
decisões tomadas, nuances do caso. Esse contexto se perde entre sessões e o usuário
precisa reexplicar.

**Proposta: `journal.md` como arquivo complementar ao `caso.md`**

Localização: `$CASES_DIR/<slug>/journal.md` (raiz do caso, ao lado de caso.md)
Natureza: append-only — entradas antigas nunca são editadas.

Formato de cada entrada:
```markdown
## Sessão YYYY-MM-DD

### Contexto revelado pelo usuário
- [fatos novos, admissões, histórias relevantes contadas pelo usuário]

### Decisões estratégicas tomadas
- [o que foi decidido e por quê — inclui o que foi descartado e a razão]

### Pendências abertas
- [o que ficou por fazer, com contexto suficiente para retomar]

### Avaliação Dr. LawDog
[Notas estratégicas sobre o estado atual do caso]
```

**Como funciona:**
- Dr. LawDog lê `journal.md` ao iniciar qualquer sessão do caso (junto com `caso.md`)
- Ao final de cada sessão substantiva, escreve nova entrada datada
- `caso.md` = arquivo estruturado (partes, timeline, fundamento jurídico)
- `journal.md` = diário narrativo e estratégico (evolução, contexto, decisões)

**Ações necessárias:**
- Adicionar `journal.md` ao template de criação de caso em `protocols/file-structure.md`
- Adicionar instrução no Step 0 de `protocols/case-intake.md` para ler o journal ao iniciar sessão
- Adicionar instrução no `plugin/AGENTS.md` para escrever entrada ao final de sessão
- Atualizar skill `caso` para criar `journal.md` em branco ao abrir novo caso

---

## v0.4.0 — roadmap e ordem de implementação

Quatro sub-projetos independentes, a serem executados nesta ordem:

| # | Sub-projeto | Status | Dependências |
|---|---|---|---|
| A | WebSearch pré-aprovado + lola.yaml hook | ✅ Concluído (2026-06-02) | — |
| B | Ciclo de vida do caso (ping-pong judicial) | ✅ Concluído (2026-06-04) | — |
| C | Notificação extrajudicial | ✅ Concluído (2026-06-04) | — |
| D | Ingestão de casos existentes | ✅ Concluído (2026-06-04) | B ✅ |
| E | Redação de petições — `/lawdog:peticao` | ✅ Concluído (2026-06-08) | B ✅ |

Cada sub-projeto tem seu próprio spec → plano → implementação.
Atualizar esta tabela ao concluir cada um.

---

## skill: peticao — redação de petições

**Status:** implementado — 2026-06-08
**Localização:** `plugin/skills/peticao/SKILL.md`

Suporta o ciclo completo de redação de petições:
1. Rascunho automático — Dr. LawDog aplica Lente Tríplice (fatos, direito, pedidos)
2. Refinamento orientado — usuário pode solicitar melhorias iterativas
3. Aprovação explícita — só gera PDF após aprovação do usuário

A skill:
- Acessa `knowledge/` e `fetch-law/` para verificação de artigos
- Gera `-rascunho.md` como edição segura
- Suporta loops de refinamento sem risco de sobrescrita
- Integra com o ciclo de vida do caso (ping-pong judicial)

**Próximos passos:**
- Implementar `/lawdog:movimentacao-2` para acompanhamento de outros tipos de movimentos processuais
- Expandir `knowledge/` com artigos específicos para defesas de JEC

---

## skill: video2forum — melhorias de performance

**Status:** identificado, não implementado
**Identificado em:** branch `improve-video2forum`

### Problemas

**1. Context window pollution (ffmpeg output spam)**
O ffmpeg emite uma linha de progresso por frame group no contexto do agente via
`TaskOutput`. Num vídeo de 14 min isso gera ~20-30k tokens de ruído inútil.

Correção em `scripts/video2forum.sh`: adicionar `-v quiet -stats` à chamada ffmpeg.
- `-v quiet` suprime output informacional
- `-stats` mantém apenas a linha de sumário final
- Resultado: ~50 tokens por vídeo em vez de 20-30k

**2. Performance de encoding (VP8/libvpx lento por padrão)**
Flags atuais: `-quality good -cpu-used 0 -b:v 500k`
`-cpu-used 0` = máxima qualidade, velocidade mínima (~0.03-0.11x realtime).
Um vídeo de 14 min leva ~2 horas.

Correção: mudar `-cpu-used 0` para `-cpu-used 5` e adicionar `-threads 4`.
- `-cpu-used 5`: 3-5x mais rápido, qualidade aceitável para prova judicial
- `-threads 4`: libvpx usa 1 thread por padrão; encoding paralelo ajuda bastante
- Combinado: vídeo de 14 min vai de ~2h para ~30-40 min

**3. SKILL.md pergunta ao usuário o caminho do ffmpeg desnecessariamente**
O script já faz autodetect via `which ffmpeg` e printa erro claro se não encontrar.
A pergunta cria atrito sem motivo.

Correção em `SKILL.md` Step 1: remover a pergunta interativa.
- Se args contiverem um path terminando em `ffmpeg`, extrair e setar `FFMPEG`
- Caso contrário, não passar override — deixar o script resolver
- Nunca perguntar ao usuário

### Mudanças necessárias
- `plugin/skills/video2forum/scripts/video2forum.sh` — flags ffmpeg
- `plugin/skills/video2forum/SKILL.md` — Step 1 (resolução do ffmpeg), Step 4 (paralelo explícito)

### Não-objetivos
- Não mudar o formato de saída (VP8/Vorbis/WebM) — o PROJUDI exige esse formato
- Não adicionar lógica de renomeação de output na skill

---

## arquitetura: SOUL.md — modularização da persona

**Status:** adiado — aguarda escolha do framework de agentes
**Decisão tomada em:** 2026-05-28

### Contexto
A ideia de separar a constituição do lawdog em um `SOUL.md` — referenciado pelo
`AGENTS.md` com uma instrução como `"Persona: leia SOUL.md"` — é arquiteturalmente
correta mas não é suportada pelo tooling atual.

`AGENTS.md` é carregado como blob estático quando o plugin é ativado. Não existe
mecanismo de `import` ou `include` no formato de plugins Claude/agentskills.io.
Nenhum plugin instalado usa referência a arquivos externos a partir do AGENTS.md.

### Decisão atual
Constituição mantida inline no `AGENTS.md` (92 linhas). Custo de token mínimo.

### Quando revisar
Ao escolher o framework multi-agente (CrewAI, LangGraph, AutoGen, etc.):
- `SOUL.md` → system prompt do agente orquestrador (lawdog principal)
- Agentes especialistas herdam princípios relevantes via seus próprios prompts
- Cada framework tem sua forma de compartilhar contexto entre agentes

---

## arquitetura: stack multi-agente — conversão futura

**Status:** planejado — sem data
**Contexto:** o lawdog foi projetado com essa migração em mente

### Mapeamento atual → agentes futuros

| Skill atual | Agente futuro |
|---|---|
| `/lawdog:caso` | Agente de intake e triagem |
| `/lawdog:fetch-law` | Agente de pesquisa jurídica |
| `/lawdog:video2forum` | Agente de preparação de evidências |
| (futuro) `/lawdog:peticao` | Agente redator de petições |
| (futuro) `/lawdog:fetch-court-info` | Agente de scraping de portais TJ |

Os `protocols/` viram os contratos de comunicação entre agentes.
O `AGENTS.md` / `SOUL.md` vira o system prompt do agente orquestrador.

### Frameworks a estudar antes de decidir
- CrewAI — roles, tasks, crews com memória compartilhada
- LangGraph — grafo de agentes com estado persistente
- Claude Code agents nativos — `agents/` dir dentro do plugin (já suportado)
- AutoGen — conversational multi-agent

---

## knowledge: outros estados brasileiros

**Status:** pendente — PR inicialmente focado no Paraná
**Prioridade:** SP > RJ > MG > RS (por volume de causas JEC)

Cada estado a adicionar em `plugin/knowledge/court-portals.md`:
- SP: e-SAJ / ESAJ (https://esaj.tjsp.jus.br)
- RJ: e-proc TJRJ
- MG: SIMBA TJMG
- RS: Themis / SAJ TJRS

---

## img2pdf: suporte HEIC via pillow-heif (melhoria)

**Status:** identificado durante v0.3.0
**Contexto:** usuário tem `/home/user/not/selfie/heic2img.py` usando pillow_heif

A abordagem atual usa `ImageMagick convert` para pré-converter HEIC → PNG antes do
`img2pdf`. A alternativa é usar `pillow_heif.register_heif_opener()` + `Pillow` para
abrir HEIC nativamente, sem dependência de ferramenta de sistema.

Adicionar ao `requirements.txt`: `pillow-heif>=0.18.0`, `Pillow>=10.0.0`
Atualizar `image_to_pdf.py` para seguir o padrão do `heic2img.py` de referência.

---

## conhecimento: WebSearch pré-aprovado vs base local

**Status:** identificado em teste real — 2026-06-02
**Problema:** sem artigos embarcados suficientes, o lawdog depende muito de WebSearch
para artigos jurídicos, gerando constante pedido de aprovação ao usuário.

**Duas abordagens a avaliar no brainstorm:**

A) **Pré-aprovar WebSearch** no `plugin.json` ou settings — o lawdog pode buscar
   livremente sem interromper o usuário. Mais dinâmico, requer conexão.

B) **Expandir a base embarcada** + skill `update-knowledge` para baixar/atualizar
   artigos offline. Funciona sem internet, mas requer manutenção.

C) **Híbrido** — base local ampliada + WebSearch aprovado como fallback.
   Consultar `knowledge/` primeiro, só acionar WebSearch se necessário.

Decisão: avaliar no próximo brainstorm.

---

## estrutura: suporte ao ping-pong judicial (v0.4.0)

**Status:** planejado — próximo brainstorm
**Identificado em:** teste real — 2026-06-02

O JEC funciona como ping-pong: petição inicial → resposta do juiz → nova juntada →
nova resposta, e assim por diante. A estrutura atual não suporta isso adequadamente.

### Questões a resolver no brainstorm

- Onde salvar respostas do juiz? Dentro de `peticao-inicial/` ou em diretório próprio?
- Como nomear as rodadas (peticao-02 é a resposta à decisão do juiz, ou é nova juntada)?
- Como o lawdog lê o andamento do caso e orienta o próximo passo como um advogado real?
- Estrutura de `peticao-inicial/resposta-1/` vs `respostas/decisao-1/` vs outro formato?

### Conceito de evolução do caso
O lawdog deve saber:
1. Ler a decisão/intimação do juiz (PDF do PROJUDI)
2. Interpretar o que foi pedido (mais documentos, emenda à inicial, etc.)
3. Orientar o usuário sobre o prazo e os próximos passos
4. Criar a estrutura para a próxima juntada/petição
5. Acompanhar todo o histórico do caso de forma organizada

---

## notificação extrajudicial (v0.4.0)

**Status:** planejado — próximo brainstorm
**Identificado em:** teste real — 2026-06-02

Antes de abrir um processo, o lawdog deve saber sugerir (quando fizer sentido juridicamente)
a criação de uma notificação extrajudicial. Ela pode:
- Resolver o problema sem processo
- Demonstrar boa-fé perante o juiz se o processo for necessário
- Servir como prova de tentativa de resolução amigável

O lawdog deve:
- Decidir quando sugerir (só quando fizer sentido — não sempre)
- Elaborar o texto da notificação
- Orientar onde entregar/enviar (Cartório de Títulos e Documentos, AR, email com AR)
- Criar template + estrutura de diretório `notificacao-extrajudicial/`
- Suportar recebimento de contra-notificação e saber como responder

---

## ingestão de casos existentes (v0.4.0)

**Status:** planejado — próximo brainstorm
**Identificado em:** teste real — 2026-06-02

Quando um usuário chega com um caso já em andamento (sem organização lawdog),
o sistema deve saber:
1. Perguntar sobre o estado atual do caso (há quanto tempo, qual fase, o que já foi feito)
2. Receber documentos avulsos e organizá-los corretamente
3. Criar a estrutura `lawdog-cases/<slug>/` retroativamente
4. Entender o histórico e dar orientação sobre os próximos passos
5. Integrar com a juntada e demais skills existentes

---

## knowledge: outros códigos jurídicos

**Status:** pendente — base atual cobre CC + CDC + Lei 9.099

Códigos a embarcar em sessões futuras conforme casos aparecerem:
- ECA (Lei 8.069/90) — direitos da criança
- Lei do Inquilinato (Lei 8.245/91) — locação
- Lei de Defesa Civil (Lei 12.608/12)
- CPC artigos relevantes ao JEC além dos já cobertos
