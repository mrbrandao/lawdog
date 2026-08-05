# Backlog — Lawdog

Melhorias identificadas, decisões pendentes e ideias para sessões futuras.
**Leia este arquivo no início de qualquer nova sessão de desenvolvimento.**

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
