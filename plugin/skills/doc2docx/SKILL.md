---
name: doc2docx
description: >-
  Converts .md or .txt documents to editable .docx via pandoc.
  Use when the user wants to edit a lawdog-generated document in Word or LibreOffice.
  The original .md is preserved in docs/ — DOCX is generated in the same directory.
  Activate on: /lawdog:doc2docx, editable version, edit in Word, generate DOCX,
  versão editável, quero editar no Word, gerar DOCX.
compatibility: >-
  Requires pandoc in PATH. No other dependencies.
  Check: command -v pandoc
allowed-tools: Bash
metadata:
  author: mrbrandao
  version: "1.0"
---

## Trigger

User asks for an editable version of a lawdog-generated document.
Example: "Gostei da petição, mas quero editar. Pode gerar um DOCX?"

## Fluxo

1. Identify the `.md` file in `docs/` for the current petition.
2. Determine the output path in the same `docs/` directory:
   - If `docs/<name>.docx` already exists, use `-1`, `-2` suffix (no spaces).
3. Run:

```bash
pandoc "docs/<name>.md" -o "docs/<name>.docx"
```

4. Report the full path. Remind user: to include in `juntada/`, convert to
   PDF first with `/lawdog:doc2pdf`.

## Gotchas

- **DOCX is for editing only.** PROJUDI requires PDF. Convert with
  `/lawdog:doc2pdf` after editing.
- **Conflict resolution** is the agent's responsibility: check if the `.docx`
  exists before running pandoc, and adjust the output filename accordingly.
  The agent uses the Bash tool to check: `[ -f "docs/<name>.docx" ]`
