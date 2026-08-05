---
name: importar-caso
description: >-
  Ingests an existing case (not opened through lawdog) and organizes all
  documents into the lawdog-cases structure with correct NN-tipo/ directories,
  caso.md, and Estado atual. Works iteratively: reads files in batches of 20,
  presents a classification table, user validates, lawdog refines, then applies
  via script — nothing is moved or created before user confirmation.
  TRIGGER when: user has existing JEC case not organized in lawdog, mentions
  documents from PROJUDI, says the case is already in progress, wants to
  organize an ongoing case.
  SKIP: do not trigger for new cases (use /lawdog:caso) or single movements
  (use /lawdog:movimentacao).
compatibility: >-
  Requires uv in PATH. importar_caso.py has no external deps (stdlib only).
  Requires LAWDOG_CASES_DIR set (setup.sh configures it).
  Check: command -v uv && echo $LAWDOG_CASES_DIR
allowed-tools: Bash Read Write
metadata:
  author: mrbrandao
  version: "1.1"
---

## Protocolos importados

- `protocols/file-structure.md` — directory naming and caso.md template
- `protocols/case-lifecycle.md` — movement type reference

## Trigger

User invokes `/lawdog:importar-caso`, or `/lawdog:caso` detects an existing
case scenario and redirects here.

## Fluxo

### Phase 0 — Mode detection (ask first)

Before collecting files, ask in Portuguese:

> "Esse caso já foi protocolado no PROJUDI, ou é um caso novo que ainda vai ser
> distribuído?"

**Mode A — Already in PROJUDI:** The `seq` numbers must match the real PROJUDI
sequence numbers (9, 12, 18...). Ask the user to share the PROJUDI movement
history (table or text), so the correct seq numbers can be mapped.

**Mode B — New case, not yet filed:** Use sequential numbers starting at `01`.
The user will update seq numbers when the case gets distributed and appears in PROJUDI.

### Phase 1 — Collect

Accept any combination:
- A directory path: list ALL files AND subdirectories inside (do not flatten)
- Individual file paths provided in conversation

When subdirectories are found, present them explicitly and ask:

> "Encontrei subdiretórios em `<path>`:
> - `audio-sindico/` — 3 arquivos de áudio
> - `fotos/` — 12 imagens
>
> Onde cada um deve ir? (petição específica, anexos, docs, ou movimento separado?)"

Do NOT flatten subdirectories silently. Each subdirectory may belong to a
different movement or location.

### Phase 2 — Iterative Analysis (max 20 files per batch)

Read up to 20 files per round. For each, extract: date, act type, actors, confidence.
For images and videos, recognize them and note they will be converted.

Present classification table in Portuguese:

```
Analisando seus arquivos (lote 1 de N):

| # | Arquivo                   | Data      | Tipo presumido      | Ação          | Conf. |
|---|---------------------------|-----------|---------------------|---------------|-------|
| 1 | peticao.pdf               | 13/04     | Petição inicial     | seq 01 docs/  | ✅    |
| 2 | foto-rachadura.jpg        | —         | Imagem/evidência    | img2pdf→junt. | ✅    |
| 3 | audio-sindico.m4a         | —         | Áudio               | video2forum   | ⚡    |
| 4 | convenção-condomínio.docx | —         | Doc editável        | docs/         | ✅    |

Algum que classifiquei errado? Posso continuar para o próximo lote.
```

When images or videos are found: note that `/lawdog:img2pdf` and `/lawdog:video2forum`
will be called automatically in Phase 4.

User responds → lawdog refines → repeat until all classified and user confirms.

### Phase 3 — Confirmation

Present the full proposed structure. Use ⚠️ immediately before the question:

```
Proposta completa para <slug>:

| Seq | Diretório           | Arquivos                      |
|-----|---------------------|-------------------------------|
| 01  | 01-peticao-inicial/ | peticao.pdf, foto→PDF, áudio→WebM |
| 09  | 09-decisao-juiz/    | decisao-emenda.pdf            |
| 12  | 12-peticao/         | emenda-a-inicial.pdf          |

⚠️ **Posso criar essa estrutura agora?** Nada será movido ou criado antes de confirmar.
```

Wait for explicit "sim" or equivalent. Do NOT proceed without it.

### Phase 4 — Apply (script + sub-skills)

**Step 4a — Write manifest silently (do NOT show JSON to user)**

Use the Write tool to create the manifest at `$CASES_DIR/<slug>/.lawdog-import.json`.
The user does not need to see JSON — it is an implementation detail.

Manifest `seq` values:
- Mode A (PROJUDI): use real PROJUDI seq numbers (`"09"`, `"24"`)
- Mode B (new case): use sequential (`"01"`, `"02"`, `"03"`)

**Step 4b — Run the import script**

```bash
CASES_DIR="${LAWDOG_CASES_DIR:-$HOME/lawdog-cases}"
uv run "${CLAUDE_SKILL_DIR}/scripts/importar_caso.py" \
    --slug "<case-slug>" \
    --cases-dir "$CASES_DIR" \
    --manifest "$CASES_DIR/<case-slug>/.lawdog-import.json"
```

**Step 4c — Convert media files (sub-skills)**

After the directory structure is created, call the right skill for each media:
- Images (`.jpg`, `.png`, `.heic`) → `/lawdog:img2pdf -i <file> -o <juntada/NN-name.pdf>`
- Videos/audio (`.mp4`, `.mov`, `.m4a`, `.avi`) → `/lawdog:video2forum <file>`
- These go into the `juntada/` of the correct petition directory

**Step 4d — Move editables to docs/**

Text documents (`.md`, `.txt`, `.docx`, `.doc`) found in `anexos/` go to `docs/`
with a clear message to the user.

**Step 4e — Report**

After all steps complete, show:
1. Directories created
2. Files organized (with final paths)
3. Conversions done (img2pdf, video2forum)
4. caso.md generated (if new) or preserved (if exists)
5. What still needs to be done (fill in parties, check deadlines)

## Gotchas

- **DO NOT show the JSON manifest to the user** — create it silently with Write tool.
  The user sees only human-readable tables, never raw JSON.
- **DO NOT read the script source before running it** — run `--help` to see the
  interface. Reading source wastes context and is unnecessary.
- **DO NOT flatten subdirectories** — if source has `audio/`, `fotos/`, etc., present
  them explicitly and ask where each goes. Never silently merge into parent.
- **Call sub-skills for media** — images need `/lawdog:img2pdf`, videos need
  `/lawdog:video2forum`. Do not skip this or leave raw media in juntada/.
- **Never create before Phase 3 confirmation** — all file operations happen after ⚠️.
- **Batch limit: 20 files** — preserves context window.
- **caso.md NOT overwritten** if it already exists.
- **External files COPIED, internal files MOVED** — no duplicates.
- **Directory naming: `{NN}-{tipo}/`** — `NN` = PROJUDI seq (Mode A) or sequential
  (Mode B). `09-decisao-juiz/` is correct. `decisao-emenda-inicial/` is WRONG.
- **One PROJUDI seq = one directory** — seq 9 and seq 12 are TWO directories.
- **Manifest persists in case dir** — `$CASES_DIR/<slug>/.lawdog-import.json`
  survives reboots, stays with the case for re-runs.
