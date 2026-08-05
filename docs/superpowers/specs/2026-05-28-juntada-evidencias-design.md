# Juntada de Evidências — Design Spec

**Date:** 2026-05-28
**Status:** approved
**Scope:** gestão de evidências e produção documental — skills de organização de
juntada, conversão de arquivos, qualidade tipográfica e integração com o fluxo
do `/lawdog:caso`

---

## 1. Contexto

O lawdog abre um caso e orienta o usuário a reunir evidências, mas não tem
mecanismo para receber, analisar, converter e organizar esses arquivos no padrão
exigido pelo PROJUDI/JEC. Esta spec define a stack de skills que preenche essa
lacuna — do staging em `anexos/` até a `juntada/` numerada e pronta para upload.

O caso real (processo 0014101-52.2026.8.16.0182, TJPR) valida o design: 57
arquivos numa juntada única, misturando PDFs e WebMs, com PDFs grandes divididos
em partes (`parte1`, `parte2`), agrupamento temático com prefixo numérico.

---

## 2. Atualização à estrutura de diretórios

Adicionar `docs/` a cada petição em `plugin/protocols/file-structure.md`:

```
$LAWDOG_CASES_DIR/
└── <case-slug>/
    ├── caso.md
    └── <peticao>/
        ├── docs/           # NOVO — originais editáveis criados/gerados pelo lawdog
        │   ├── peticao-inicial.md
        │   └── peticao-inicial.docx   # gerado por doc2docx sob demanda
        ├── anexos/         # EXISTENTE — staging: ponto de entrada unificado
        └── juntada/        # EXISTENTE — destino organizado, JEC-ready
            ├── 01-peticao-inicial.pdf
            ├── 02-documentos-pessoais.pdf
            ├── 03.1-devassa-visual.webm
            └── 04.1-foto-dano.pdf
```

**`anexos/`** é o **ponto de entrada unificado**. Todo arquivo — colocado pelo
usuário diretamente ou referenciado por path externo — passa por `anexos/` antes
de ser processado. Isso garante rastreabilidade completa.

**`docs/`** — arquivos de texto editáveis produzidos pelo lawdog. Nunca removidos.

---

## 3. Stack de skills modulares

Cada skill é autônoma — invocável diretamente pelo usuário ou como sub-agente.

| Skill | Ferramenta | Responsabilidade |
|---|---|---|
| `/lawdog:juntada` | Bash | Orquestrador: staging → análise → nomenclatura em lote → conversão → juntada |
| `/lawdog:img2pdf` | ImageMagick `convert` | `.jpg`, `.jpeg`, `.png`, `.heic` → `.pdf` |
| `/lawdog:doc2pdf` | Pandoc + pdflatex | `.md`, `.txt`, `.doc`, `.docx` → `.pdf` formatado |
| `/lawdog:pdf-split` | ghostscript ou pdftk | Divide qualquer `.pdf` > 4MB em partes (`-1`, `-2`, ...) |
| `/lawdog:doc2docx` | Pandoc | `.md`, `.txt` → `.docx` editável bem formatado |
| `/lawdog:video2forum` | ffmpeg | Vídeos → `.webm` (já existe — sem alteração) |

---

## 4. Lógica de movimentação (regra central)

**Arquivos em `anexos/` NUNCA são removidos.**
Após processados, o original recebe sufixo `.converted`:
`foto.jpg` → `foto.jpg.converted`

O script detecta `.converted` e pula em re-execuções — idempotência garantida.

**Arquivos externos (fora de `$LAWDOG_CASES_DIR`):**
Quando o usuário informa um path externo, o lawdog **copia o arquivo para
`anexos/` primeiro**, e só então processa a partir de lá. O original externo
nunca é tocado.

**Conflito de nomes:** se já existir um arquivo com o mesmo nome no destino
(em `anexos/`, `docs/` ou `juntada/`), o novo arquivo recebe sufixo numérico
incremental com hífen: `arquivo.pdf` → `arquivo-1.pdf` → `arquivo-2.pdf`.
Sem espaços — consistente com a convenção kebab-case do projeto.

| Tipo em `anexos/` | Ação | Destino em `juntada/` | Tag em `anexos/` |
|---|---|---|---|
| `.jpg`, `.jpeg`, `.png`, `.heic` | img2pdf → PDF | `NN(.N)-nome.pdf` | `arquivo.jpg.converted` |
| `.mp4`, `.mov`, `.avi`, `.mkv` | video2forum → WebM | `NN(.N)-nome.webm` | `arquivo.mp4.converted` |
| `.pdf` | Copia | `NN(.N)-nome.pdf` | `arquivo.pdf.converted` |
| `.webm` | Copia | `NN(.N)-nome.webm` | `arquivo.webm.converted` |
| `.md`, `.txt`, `.doc`, `.docx` | Move para `docs/` | — não vai para `juntada/` | Sem tag — não persiste em `anexos/` após o move; conflito em `docs/` → sufixo `-N` |

---

## 5. Fluxo do `/lawdog:juntada`

### Etapa 1 — Coleta e staging

**1a. Verificação de `anexos/`**
Lista arquivos sem sufixo `.converted` (pendentes de processo).

**1b. Paths externos fornecidos pelo usuário**
Se o usuário informar caminhos fora de `$LAWDOG_CASES_DIR`:
- O lawdog copia cada arquivo para `anexos/` antes de processar
- Informa o usuário: *"Copiei `foto.jpg` para `anexos/` — processando a partir daqui."*
- O original externo permanece intocado

Se `anexos/` estiver vazio E não houver paths informados:
> "Nenhum arquivo pendente. Coloque seus arquivos em:
> `<path>/anexos/`
> Ou me informe os caminhos completos dos arquivos diretamente."

### Etapa 2 — Análise de conteúdo em lote

O lawdog **lê ou visualiza todos os arquivos** antes de fazer qualquer pergunta.
Para cada um:
- **Fotos** → visualiza e extrai: o que mostra, relevância para o caso
- **PDFs** → lê e extrai: tipo de documento, valor, data, partes, cláusulas
- **Vídeos** → analisa pelo nome e contexto disponível

Ao final desta etapa, o lawdog tem uma leitura completa do lote inteiro e
avalia a força probatória de cada evidência.

### Etapa 3 — Proposta de nomenclatura em tabela (interação única)

O lawdog apresenta **uma tabela com todos os arquivos de uma vez**, com nomes
sugeridos baseados no conteúdo lido/visualizado:

```
Analisei os arquivos em anexos/. Aqui está minha proposta de nomenclatura:

| # | Arquivo original     | Nome sugerido para juntada/   | Grupo         |
|---|----------------------|-------------------------------|---------------|
| 1 | IMG_4821.HEIC        | 04.1-rachadura-muro.pdf       | Danos         |
| 2 | IMG_4822.HEIC        | 04.2-rachadura-muro.pdf       | Danos         |
| 3 | contrato.pdf         | 02-contrato-servico.pdf       | Documentos    |
| 4 | video_20240115.mp4   | 03.1-video-devassa-visual.webm| Vídeos        |
| 5 | nota_fiscal.pdf      | 02-nota-fiscal.pdf            | Documentos    |

Pode ajustar nomes ou grupos. Se estiver ok, confirme e processo tudo de uma vez.
```

O usuário responde com ajustes ou confirma. Uma única interação para N arquivos.
Após confirmação: o lawdog procede com as conversões.

### Etapa 4 — Conversão (sub-agentes em background)

Cada conversão é despachada como sub-agente paralelo. O lawdog permanece
disponível para conversar enquanto as conversões ocorrem em background.

| Extensão | Sub-skill | Output |
|---|---|---|
| `.jpg`, `.jpeg`, `.png`, `.heic` | `/lawdog:img2pdf` | `.pdf` |
| `.md`, `.txt`, `.doc`, `.docx` | `/lawdog:doc2pdf` | `.pdf` |
| `.mp4`, `.mov`, `.avi`, `.mkv` | `/lawdog:video2forum` | `.webm` |
| `.pdf`, `.webm` | — sem conversão — | arquivo original |

### Etapa 5 — Validação do limite de 4MB (JEC)

Após conversão, `/lawdog:juntada` verifica o tamanho de cada arquivo:

- **PDF de documento** (gerado por `doc2pdf` ou colocado pelo usuário) > 4MB
  → aciona `/lawdog:pdf-split`: `02-contrato.pdf` → `02.1-contrato.pdf` +
  `02.2-contrato.pdf`. Aplicável a qualquer PDF de texto multi-página.

- **PDF de imagem** (gerado por `img2pdf`) > 4MB → o `img2pdf` reduz qualidade
  internamente via `convert -quality <N>` até abaixo de 4MB. Split não faz
  sentido para imagem — você não divide uma foto ao meio. Na prática esse caso
  é raro: fotos convertidas para PDF raramente ultrapassam 4MB.

- **Vídeo WebM** → sem verificação de tamanho (PROJUDI aceita mídia sem
  limite de 4MB documentado — confirmado pelo caso real com múltiplos `.webm`).

### Etapa 6 — Organização final e tagging

Para cada arquivo convertido e validado:
1. Copia para `juntada/<NN(.N)>-<label>.<ext>` com a numeração confirmada
2. Renomeia original em `anexos/`: `arquivo.ext` → `arquivo.ext.converted`

### Etapa 7 — Relatório final

1. Lista numerada de todos os arquivos em `juntada/` com paths completos
2. Avaliação jurídica: evidências fortes / fracas / ausentes para o caso
3. Tamanho de cada arquivo — confirmação dentro do limite JEC (PDFs ≤4MB)
4. O que ainda falta para o caso estar bem documentado

---

## 6. Template tipográfico (`plugin/templates/base-legal.latex`)

Motor de layout único reutilizável por `doc2pdf`. Não é ABNT — é tipografia
profissional para documentos judiciais.

| Problema a resolver | Implementação LaTeX |
|---|---|
| Linhas órfãs/viúvas (linha solta no topo/fim de página) | `\widowpenalty=10000`, `\clubpenalty=10000`, `\displaywidowpenalty=10000` |
| Bloco de assinatura isolado em nova página | `\begin{samepage}` em cidade + data + nome |
| Parágrafo quebrado com linha única no topo | Penalidades de quebra + `\looseness=-1` |
| Páginas em branco extras | `\raggedbottom` |
| Justificação forçada com espaços feios | `\usepackage{microtype}` |
| Fonte ilegível ou muito acadêmica | `\usepackage{lmodern}` |
| Margens inadequadas para A4 judicial | 3cm esq, 2cm dir, 2.5cm topo, 2cm rodapé |
| Espaçamento | `\usepackage{setspace}` + `\onehalfspacing` |
| Elementos decorativos | Proibidos — zero `\hrule`, `---`, boxes, bordas |

---

## 7. Protocolo de qualidade documental (`protocols/document-standards.md`)

Novo protocolo importado por `doc2pdf`, `doc2docx` e pela futura skill de
redação de petições.

Conteúdo:
- **Estrutura obrigatória**: Fatos → Fundamento Legal → Pedidos — em linha reta
- **Parágrafos**: uma ideia por parágrafo; nunca linha solta no topo de página
- **Bloco de assinatura**: sempre na mesma página que a frase final do corpo
- **Proibições**: páginas em branco, `---` decorativos, repetições, AI slop,
  títulos desnecessários, frases de preenchimento
- **O que um juiz aprecia**: direto, claro, pedidos numerados, linguagem de
  advogado experiente — não de chatbot

---

## 8. Atualização ao `AGENTS.md` — seção "Qualidade Documental"

Nova seção a inserir após "Raciocínio Adversarial":

> **Qualidade Documental**
>
> O lawdog confecciona documentos que um juiz leia com facilidade e apreciação:
> diretos, claros, sem excesso. Fatos → fundamento → pedido em linha reta.
> Parágrafos curtos, cada um com uma ideia. Nunca produz páginas em branco,
> linhas decorativas (`---`), repetições ou frases de preenchimento.
>
> O bloco de data, cidade e assinatura nunca é separado do corpo do documento.
> Nenhuma linha fica isolada no topo de uma página nova.
>
> Usa `base-legal.latex` via `doc2pdf` para toda produção documental. A qualidade
> tipográfica é parte da representação do cliente — não é opcional.

---

## 9. Integração com `/lawdog:caso`

Ao criar cada petição, `/lawdog:caso`:
1. Cria `docs/`, `anexos/`, `juntada/` dentro do diretório da petição
2. Informa path do `anexos/` ao usuário:
   > "Pode colocar seus arquivos de evidência em:
   > `~/lawdog-cases/obra-irregular/peticao-inicial/anexos/`
   > Ou me informe os caminhos. Quando quiser organizar, chame
   > `/lawdog:juntada obra-irregular`."
3. Não bloqueia — juntada é invocada quando o usuário estiver pronto

---

## 10. Decisões registradas

| Decisão | Escolha | Motivo |
|---|---|---|
| Ponto de entrada unificado | `anexos/` para tudo | Rastreabilidade; paths externos são copiados para lá antes de processar |
| Arquivos processados | Tag `.converted`, nunca remover | Sem perda acidental; usuário controla cleanup |
| Idempotência | Detectar `.converted`, pular | Re-execuções seguras |
| Nomenclatura | Tabela em lote, uma interação | Evita interrogatório arquivo por arquivo |
| Análise de conteúdo | Lawdog visualiza/lê antes de sugerir nomes | Nomes baseados em conteúdo, não em adivinhação |
| Template LaTeX | `base-legal.latex` único | Um motor, múltiplos documentos |
| Não ABNT | Intencional | Documento processual ≠ trabalho acadêmico |
| Vídeos em `juntada/` | Junto com PDFs | PROJUDI aceita; caso real confirma |
| Sub-skills paralelas | Sub-agentes em background | Lawdog livre para conversar durante conversões |
| Documentos de texto em `anexos/` | Move para `docs/`, avisa usuário | Editáveis precisam de revisão antes de ir para juntada |
