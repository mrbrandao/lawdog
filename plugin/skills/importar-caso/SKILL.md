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

Write JSON manifest, invoke script:

```bash
uv run "${CLAUDE_SKILL_DIR}/scripts/importar_caso.py" \
    --slug "<case-slug>" \
    --cases-dir "${LAWDOG_CASES_DIR:-$HOME/lawdog-cases}" \
    --manifest "/tmp/lawdog_manifest_<slug>.json"
```

## Gotchas

- **Never create anything before Phase 3 confirmation.**
- **Batch limit is 20 files** — preserves context window.
- **caso.md NOT overwritten** if it already exists.
- **External files COPIED** (originals preserved). **Internal files MOVED** (no duplicates).
- **⚠️ mandatory before confirmation question** — must appear immediately before it.
- **Directory naming is ALWAYS `{NN}-{tipo}/`** — `NN` is the PROJUDI sequence number,
  NOT a descriptive name. `09-decisao-juiz/` is correct. `decisao-emenda-inicial/` is
  WRONG. Each PROJUDI sequence is its own directory — never group multiple seqs together.
  Valid type slugs: `peticao-inicial`, `peticao`, `decisao-juiz`, `manifestacao-reu`, `intimacao`.
- **One seq = one directory.** Seq 9 (judge decision) and seq 12 (new petition) are TWO
  separate directories even if about the same legal topic. The description goes in the
  filename inside the directory, not in the directory name itself.
