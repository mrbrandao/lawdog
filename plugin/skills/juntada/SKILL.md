---
name: juntada
description: >-
  Organizes case evidence from anexos/ into a numbered, JEC-ready juntada/.
  Analyzes file content, proposes batch naming in one table interaction, dispatches
  all conversions as parallel sub-agents, and enforces LAWDOG_PDF_SIZE limit.
  Central entry point for evidence management throughout the case lifecycle.
  Activate on: /lawdog:juntada, organize evidence, prepare juntada, process
  attachments, organizar evidências, preparar juntada, processar anexos,
  evidências prontas, juntar documentos.
compatibility: >-
  Requires uv in PATH. Sub-skills: img2pdf, doc2pdf, pdf-split, video2forum.
  Reads LAWDOG_PDF_SIZE from environment (setup.sh exports it).
  Check: command -v uv && make test-skills
allowed-tools: Bash Read Write WebFetch WebSearch
metadata:
  author: mrbrandao
  version: "1.0"
---

## Protocolos importados

Read `protocols/file-structure.md` at start for directory conventions.
Read `protocols/document-standards.md` when evaluating document quality.

## Trigger

`/lawdog:juntada <case-slug> [petition]` — petition defaults to `peticao-inicial`.

## Fluxo

### Step 1 — Resolve directories and list pending

```bash
CASES_DIR="${LAWDOG_CASES_DIR:-$HOME/lawdog-cases}"
PETICAO="${2:-peticao-inicial}"
ANEXOS="$CASES_DIR/$1/$PETICAO/anexos"
JUNTADA="$CASES_DIR/$1/$PETICAO/juntada"
DOCS="$CASES_DIR/$1/$PETICAO/docs"

LAWDOG_SKILL="${CLAUDE_SKILL_DIR:-${LAWDOG_PLUGIN_DIR}/skills/juntada}"
uv run "${LAWDOG_SKILL}/scripts/juntada.py" list-pending "$ANEXOS"
```

If user provided external paths: copy each to `$ANEXOS` first:
```bash
DEST=$(uv run "${LAWDOG_SKILL}/scripts/juntada.py" resolve-conflict "$ANEXOS/<filename>")
cp "<external-path>" "$DEST"
```
External originals are never touched.

Text documents (.md, .txt, .doc, .docx) in `$ANEXOS`: move to `$DOCS`, inform user.
If `$ANEXOS` empty and no external paths: inform user and wait.

### Step 2 — Analyze all files in batch

Read or view ALL pending files BEFORE asking any questions.
- Images: view — verify content matches what user described
- PDFs/documents: read — extract type, value, date, parties, relevant clauses
- Videos: assess from name and user context

Record evaluation: strong / weak / contradictory / missing evidence.

### Step 3 — Batch naming table (one interaction for all files)

Present ONE table with all files. Names suggested based on content:

```
| # | Original file       | Suggested name for juntada/   | Group     |
|---|---------------------|-------------------------------|-----------|
| 1 | IMG_4821.HEIC       | 04.1-rachadura-muro.pdf       | Danos     |
| 2 | contrato.pdf        | 02-contrato-servico.pdf       | Documentos|
| 3 | video_devassa.mp4   | 03.1-video-devassa.webm       | Vídeos    |
```

Wait for confirmation. Never ask per-file.

### Step 4 — Parallel conversions (all at once)

Dispatch ALL conversions simultaneously as background sub-agents.
Wait for all to complete before Step 5.

| Extension | Sub-skill | Output |
|---|---|---|
| .jpg .jpeg .png .heic | `/lawdog:img2pdf` | .pdf |
| .mp4 .mov .avi .mkv | `/lawdog:video2forum` | .webm |
| .pdf .webm | — no conversion — | same |

### Step 5 — Size validation and split

After all conversions complete, check each PDF:

```bash
MAX="${LAWDOG_PDF_SIZE:-4194304}"
SIZE=$(stat -c%s "<file>" 2>/dev/null || stat -f%z "<file>")
```

Document PDFs >MAX: invoke `/lawdog:pdf-split -i <file> -o <prefix>`
Image PDFs >MAX: img2pdf already handled quality reduction — no split.

### Step 6 — Copy to juntada/ and tag

```bash
DEST=$(uv run "${LAWDOG_SKILL}/scripts/juntada.py" resolve-conflict "$JUNTADA/<NN-name.ext>")
cp "<converted-file>" "$DEST"
uv run "${LAWDOG_SKILL}/scripts/juntada.py" tag "<original-in-anexos>"
```

External files: only `cp`, no tag on original.

### Step 7 — Final report

1. Numbered list of all files in `juntada/` with full paths and sizes
2. Legal assessment: strong / weak / absent evidence
3. Confirmation all files <= `LAWDOG_PDF_SIZE`
4. What is still missing for a well-documented case

## Gotchas

- **Dispatch conversions in parallel, not sequentially.** All sub-agents
  run simultaneously — sequential dispatch defeats the purpose.
- **Never ask per-file for labels.** One table, one interaction.
- **Tag only AFTER copy succeeds.** If `cp` fails, do not tag the original.
- **LAWDOG_PDF_SIZE must be exported.** Remind users to `source ~/.bashrc`
  after first setup if the variable is not available.
