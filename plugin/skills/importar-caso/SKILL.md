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
  version: "1.0"
---

## Protocolos importados

- `protocols/file-structure.md` — directory naming and caso.md template
- `protocols/case-lifecycle.md` — movement type reference

## Trigger

User invokes `/lawdog:importar-caso`, or `/lawdog:caso` detects an existing
case scenario and redirects here.

## Fluxo

### Phase 1 — Collect

Accept directory path or individual file paths. Build the file list.
Do NOT read file contents yet.

### Phase 2 — Iterative Analysis (max 20 files per batch)

Read up to 20 files. For each extract: date, act type, actors, confidence.
Present classification table in Portuguese:

```
Analisando seus arquivos (lote 1 de N):

| # | Arquivo              | Data presumida | Tipo presumido      | Confiança |
|---|----------------------|----------------|---------------------|-----------|
| ? | peticao.pdf          | 13/04/2026     | Petição inicial     | ✅ Alta   |
| ? | IMG_20240901.jpg     | —              | Desconhecido        | ❌ Baixa  |

Algum que classifiquei errado? Posso continuar quando quiser.
```

User responds → lawdog refines → repeat until all classified and confirmed.

### Phase 3 — Confirmation

⚠️ **Posso criar essa estrutura agora?** Nada será movido até sua confirmação.

Wait for explicit confirmation before any file operation.

### Phase 4 — Apply via script

Write the manifest **inside the case directory** (not /tmp — survives reboots):

```bash
CASES_DIR="${LAWDOG_CASES_DIR:-$HOME/lawdog-cases}"
MANIFEST="$CASES_DIR/<case-slug>/.lawdog-import.json"
mkdir -p "$CASES_DIR/<case-slug>"
```

Manifest format — `seq` MUST be the real PROJUDI sequence number:

```json
{
  "slug": "<case-slug>",
  "movements": [
    {"seq": "09", "type": "decisao-juiz", "files": ["/abs/path/decisao.pdf"]},
    {"seq": "12", "type": "peticao", "files": ["/abs/path/emenda.pdf"]}
  ]
}
```

Valid `type` values: `peticao-inicial`, `peticao`, `decisao-juiz`,
`manifestacao-reu`, `intimacao`, `notificacao-extrajudicial`, `contranotificacao-reu`

Run the script (it validates type slugs and rejects unknown ones):

```bash
uv run "${CLAUDE_SKILL_DIR}/scripts/importar_caso.py" \
    --slug "<case-slug>" \
    --cases-dir "$CASES_DIR" \
    --manifest "$MANIFEST"
```

## Gotchas

- **Never create anything before Phase 3 confirmation.**
- **Batch limit is 20 files** — preserves context window.
- **caso.md NOT overwritten** if it already exists.
- **External files COPIED** (originals preserved). **Internal files MOVED** (no duplicates).
- **⚠️ mandatory before confirmation question** — must appear immediately before it.
- **DO NOT read the script source before running it.** Run `--help` first to see the
  interface. Reading the source wastes context window and is unnecessary — the script
  is a black box: give it the correct flags and it works.
- **`seq` in manifest = PROJUDI sequence number**, NOT an internal counter. Check the
  PROJUDI case history for the real numbers (9, 12, 15, 16...). Using `01, 02, 03`
  creates wrong directory names.
- **Directory naming is ALWAYS `{NN}-{tipo}/`** — `NN` is the PROJUDI seq number.
  `09-decisao-juiz/` is correct. `decisao-emenda-inicial/` is WRONG.
  Each PROJUDI sequence gets its own directory — never group multiple seqs together.
- **One seq = one directory.** Seq 9 (judge decision) and seq 12 (new petition) are TWO
  separate directories even if they're about the same topic.
- **Save manifest in case dir, not /tmp/** — use `$CASES_DIR/<slug>/.lawdog-import.json`
  so it survives reboots and stays with the case.
