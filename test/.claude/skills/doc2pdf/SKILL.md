---
name: doc2pdf
description: >-
  Converts text documents (.md, .txt, .doc, .docx) to PDF with judicial
  typography via pandoc + pdflatex + base-legal.latex template.
  .doc/.docx files are converted via LibreOffice headless.
  Activate on: /lawdog:doc2pdf, convert to PDF, document for juntada,
  documento para PDF, converter para PDF.
compatibility: >-
  Requires uv in PATH. pandoc + pdflatex for .md/.txt.
  libreoffice for .doc/.docx. All invoked via subprocess.
  Check: command -v uv && command -v pandoc && command -v pdflatex
allowed-tools: Bash
metadata:
  author: mrbrandao
  version: "1.0"
---

## Protocolos importados

Read `protocols/document-standards.md` before generating any document.

## Trigger

Invoked by `/lawdog:juntada` for documents. Direct use: `/lawdog:doc2pdf`

## Fluxo

1. Run:

```bash
uv run "${CLAUDE_SKILL_DIR}/scripts/doc2pdf.py" \
    -i "<input>" -o "<output>" \
    -t "${CLAUDE_SKILL_DIR}/../../templates/base-legal.latex"
```

2. Check output size against `LAWDOG_PDF_SIZE`:

```bash
MAX="${LAWDOG_PDF_SIZE:-4194304}"
SIZE=$(stat -c%s "<output>" 2>/dev/null || stat -f%z "<output>")
```

3. If `SIZE > MAX`: invoke `/lawdog:pdf-split -i <output> -o <prefix>`
4. Return path(s) and size(s).

## Gotchas

- **LibreOffice headless** sometimes writes the PDF with the input filename
  rather than the `-o` destination. The script handles the rename, but if
  LibreOffice is not installed, `.doc/.docx` conversion will fail.
- **Template path** is resolved relative to the script via `Path(__file__).parent`.
  Always invoke via `${CLAUDE_SKILL_DIR}/scripts/doc2pdf.py` for correct resolution.
- **No PEP 723 deps** — this script has no Python package deps (only stdlib).
  It calls pandoc and libreoffice via subprocess. `uv run` still works correctly
  with an empty `dependencies = []` block.
